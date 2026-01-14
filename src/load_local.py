import os
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from src.models import Base 

# --- CONFIGURATION LOCALHOST (DOCKER) ---
DATABASE_URL = "postgresql://admin:admin@localhost:5432/maritime"

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

CHUNK_SIZE = 5000 

def get_engine():
    print(f"🔌 Connexion à : {DATABASE_URL}")
    return create_engine(DATABASE_URL)

def load_full_file(filename, table_name, engine, parent_ids=None):
    """Charge TOUT le fichier (Mode Clean & Debug)."""
    
    # Gestion des chemins
    path = PROCESSED_DIR / filename
    if not path.exists():
        path = PROCESSED_DIR / filename.replace(".csv", "_validated.csv")
    
    if not path.exists():
        print(f"⏩ [SKIP] {filename} introuvable.")
        return None

    print(f"📂 [LECTURE] {path.name}...")
    
    # 1. Lecture
    df = pd.read_csv(path, low_memory=False)

    # --- DEBUG : AFFICHER LES COLONNES RÉELLES ---
    # C'est ici qu'on verra si les noms sont bizarres
    print(f"   👀 Colonnes trouvées (5 premières) : {list(df.columns)[:5]}")
    
    # --- NETTOYAGE STANDARD ---
    df = df.where(pd.notnull(df), None)
    
    # J'AI SUPPRIMÉ LA LIGNE _m999 ICI ❌

    # Standardisation date (si besoin)
    if 'date_operation' in df.columns: 
        df.rename(columns={'date_operation': 'date'}, inplace=True)

    # Conversion Dates
    for col in df.columns:
        if "date" in col.lower() or "heure" in col.lower():
            try: df[col] = pd.to_datetime(df[col], errors='coerce')
            except: pass

    # Sécurité Colonnes (On ne garde que ce qui correspond au modèle SQL)
    try:
        valid_cols = Base.metadata.tables[table_name].columns.keys()
        
        # On vérifie les colonnes qui vont être rejetées (pour comprendre)
        rejected = [c for c in df.columns if c not in valid_cols]
        if rejected:
            print(f"   ⚠️ Colonnes ignorées (absentes du modèle) : {rejected[:5]} ...")

        df = df[[c for c in df.columns if c in valid_cols]]
    except Exception as e:
        print(f"⚠️ Warning filtrage colonnes : {e}")

    # --- FILTRAGE INTELLIGENT ---
    valid_ids = None
    
    if table_name == "operations":
        valid_ids = set(df['operation_id'].dropna().tolist())
        print(f"🎯 Chargement de {len(df)} opérations.")
        
    else:
        if parent_ids and 'operation_id' in df.columns:
            initial_len = len(df)
            df = df[df['operation_id'].isin(parent_ids)]
            filtered_len = len(df)
            if initial_len != filtered_len:
                print(f"   ✂️ {initial_len - filtered_len} orphelins retirés.")

    # Dédoublonnage
    if 'operation_id' in df.columns and table_name in ['operations', 'operations_stats']:
        df = df.drop_duplicates(subset=['operation_id'])

    # --- ENVOI ---
    if not df.empty:
        print(f"🚀 [ENVOI] {len(df)} lignes vers '{table_name}'...")
        try:
            df.to_sql(table_name, engine, if_exists='append', index=False, chunksize=CHUNK_SIZE)
            print(f"✅ [OK] {table_name} terminé.")
        except Exception as e:
            print(f"❌ Erreur SQL sur {table_name}: {e}")
            # Si ça plante ici, c'est souvent un problème de type de données
    else:
        print(f"⚠️ [VIDE] Aucune donnée à charger pour {table_name}.")

    return valid_ids

def main():
    print("=== 🏗️ CHARGEMENT LOCAL (CLEAN VERSION) ===\n")
    
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Connexion Docker réussie.\n")
    except Exception as e:
        print(f"❌ ÉCHEC CONNEXION : {e}")
        return

    print("🧹 Nettoyage de la base locale...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    ids_operations = load_full_file("operations.csv", "operations", engine)

    if ids_operations:
        load_full_file("flotteurs.csv", "flotteurs", engine, ids_operations)
        load_full_file("resultats_humain.csv", "resultats_humain", engine, ids_operations)
        load_full_file("operations_stats.csv", "operations_stats", engine, ids_operations)

    print("\n=== 🎉 TERMINE ===")

if __name__ == "__main__":
    main()