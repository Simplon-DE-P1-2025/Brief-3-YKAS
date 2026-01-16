import os
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from dotenv import load_dotenv
from src.models import Base

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CHUNK_SIZE = 5000

def get_engine():
    if not DATABASE_URL:
        raise ValueError("La variable DATABASE_URL est introuvable dans le fichier .env")
    return create_engine(DATABASE_URL)

def apply_audit_sql(engine):
    """Applique le SQL d'audit (table + triggers) sur public.operations."""
    audit_path = BASE_DIR / "references" / "audit_operations.sql"
    if not audit_path.exists():
        print(f"[WARN] Audit SQL introuvable: {audit_path}")
        return

    sql = audit_path.read_text(encoding="utf-8")

    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute(sql)  # le fichier contient BEGIN/COMMIT + multi statements
        raw.commit()
        print("[OK] Audit SQL appliqué (audit_operations + triggers).")
    except Exception as e:
        raw.rollback()
        print(f"[ERROR] Erreur application audit SQL: {e}")
    finally:
        try:
            cur.close()
        except Exception:
            pass
        raw.close()

def load_file(filename, table_name, engine, parent_ids=None):
    path = PROCESSED_DIR / filename
    if not path.exists():
        path = PROCESSED_DIR / filename.replace(".csv", "_validated.csv")
    if not path.exists():
        print(f"[SKIP] Fichier {filename} introuvable.")
        return None

    print(f"[LECTURE] Chargement de {path.name}...")
    df = pd.read_csv(path, low_memory=False)
    # Remplacement des NaN par None pour la compatibilité SQL
    df = df.where(pd.notnull(df), None)

    # Le renommage et la conversion de date sont maintenant faits dans normalize.py et validate.py

    # Filtrage des colonnes selon le modèle SQLAlchemy
    try:
        valid_cols = Base.metadata.tables[table_name].columns.keys()
        df = df[[c for c in df.columns if c in valid_cols]]
    except Exception as e:
        print(f"[WARN] Filtrage colonnes impossible pour {table_name}: {e}")

    valid_ids = None

    if table_name == "operations":
        if "operation_id" in df.columns:
            df = df.drop_duplicates(subset=["operation_id"])
            valid_ids = set(df["operation_id"].dropna().tolist())
    else:
        if parent_ids and "operation_id" in df.columns:
            df = df[df["operation_id"].isin(parent_ids)]
        if table_name == "operations_stats" and "operation_id" in df.columns:
            df = df.drop_duplicates(subset=["operation_id"])

    if not df.empty:
        try:
            df.to_sql(table_name, engine, if_exists="append", index=False, chunksize=CHUNK_SIZE)
            print(f"[OK] {len(df)} lignes importées dans '{table_name}'.")
        except Exception as e:
            print(f"[ERROR] Echec import {table_name}: {e}")
    else:
        print(f"[INFO] Aucune donnée à charger pour {table_name}.")

    return valid_ids

def main():
    print("=== CHARGEMENT DE LA BASE DE DONNEES LOCALE ===\n")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Connexion réussie.\n")
    except Exception as e:
        print(f"[FATAL] Erreur connexion : {e}")
        return

    print("[INFO] Reset du schéma...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # IMPORTANT: triggers audit après création de la table operations
    apply_audit_sql(engine)

    ids_operations = load_file("operations.csv", "operations", engine)

    if ids_operations:
        load_file("flotteurs.csv", "flotteurs", engine, ids_operations)
        load_file("resultats_humain.csv", "resultats_humain", engine, ids_operations)
        load_file("operations_stats.csv", "operations_stats", engine, ids_operations)

    print("\n=== TERMINÉ ===")

if __name__ == "__main__":
    main()
