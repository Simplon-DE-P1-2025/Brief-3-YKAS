import os
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from dotenv import load_dotenv
from src.models import Base 

# --- CONFIGURATION ---
# Chargement du fichier .env à la racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CHUNK_SIZE = 5000 

def get_engine():
    if not DATABASE_URL:
        raise ValueError("La variable DATABASE_URL est introuvable dans le fichier .env")
    return create_engine(DATABASE_URL)

def load_file(filename, table_name, engine, parent_ids=None):
    """Charge un fichier CSV dans la base de données."""
    
    # Gestion des chemins (tente le nom direct, sinon la version _validated)
    path = PROCESSED_DIR / filename
    if not path.exists():
        path = PROCESSED_DIR / filename.replace(".csv", "_validated.csv")
    
    if not path.exists():
        print(f"[SKIP] Fichier {filename} introuvable.")
        return None

    print(f"[LECTURE] Chargement de {path.name}...")
    
    # Lecture
    df = pd.read_csv(path, low_memory=False)
    
    # Nettoyage de base (NaN -> None pour SQL)
    df = df.where(pd.notnull(df), None)

    # Standardisation date
    if 'date_operation' in df.columns: 
        df.rename(columns={'date_operation': 'date'}, inplace=True)

    # Conversion des colonnes temporelles
    for col in df.columns:
        if "date" in col.lower() or "heure" in col.lower():
            try: 
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except: 
                pass

    # Filtrage des colonnes selon le modèle SQLAlchemy
    try:
        valid_cols = Base.metadata.tables[table_name].columns.keys()
        df = df[[c for c in df.columns if c in valid_cols]]
    except Exception as e:
        print(f"[WARN] Erreur lors du filtrage des colonnes : {e}")

    # Filtrage et intégrité référentielle
    valid_ids = None
    
    if table_name == "operations":
        valid_ids = set(df['operation_id'].dropna().tolist())
        # Dédoublonnage spécifique aux opérations
        df = df.drop_duplicates(subset=['operation_id'])
    else:
        # Pour les tables enfants, on ne garde que ce qui est lié à une opération existante
        if parent_ids and 'operation_id' in df.columns:
            initial_len = len(df)
            df = df[df['operation_id'].isin(parent_ids)]
            diff = initial_len - len(df)
            if diff > 0:
                print(f"[INFO] {diff} enregistrements orphelins ignorés.")
        
        # Dédoublonnage stats (si nécessaire)
        if table_name == 'operations_stats' and 'operation_id' in df.columns:
             df = df.drop_duplicates(subset=['operation_id'])

    # Envoi vers PostgreSQL
    if not df.empty:
        try:
            df.to_sql(table_name, engine, if_exists='append', index=False, chunksize=CHUNK_SIZE)
            print(f"[OK] {len(df)} lignes importées dans '{table_name}'.")
        except Exception as e:
            print(f"[ERROR] Echec de l'import pour {table_name}: {e}")
    else:
        print(f"[INFO] Aucune donnée à charger pour {table_name}.")

    return valid_ids

def main():
    print("=== CHARGEMENT DE LA BASE DE DONNEES LOCALE ===\n")
    
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Connexion à la base de données réussie.\n")
    except Exception as e:
        print(f"[FATAL] Impossible de se connecter à la base : {e}")
        return

    print("[INFO] Réinitialisation du schéma de la base...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Chargement ordonné (Parents d'abord, Enfants ensuite)
    ids_operations = load_file("operations.csv", "operations", engine)

    if ids_operations:
        load_file("flotteurs.csv", "flotteurs", engine, ids_operations)
        load_file("resultats_humain.csv", "resultats_humain", engine, ids_operations)
        load_file("operations_stats.csv", "operations_stats", engine, ids_operations)

    print("\n=== TERMINÉ ===")

if __name__ == "__main__":
    main()