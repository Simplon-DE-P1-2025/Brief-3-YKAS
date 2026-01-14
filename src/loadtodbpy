import os
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
from dotenv import load_dotenv
from src.models import Base 

# --- CONFIGURATION ---
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# On limite à 1000 opérations pour l'exemple
LIMIT = 1000

# Nettoyage URL Neon (Windows fix)
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://").replace("&channel_binding=require", "")

def get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)

def load_sample(filename, table_name, engine, parent_ids=None):
    """Charge un échantillon propre et lié."""
    
    path = PROCESSED_DIR / filename
    if not path.exists():
        path = PROCESSED_DIR / filename.replace(".csv", "_validated.csv")
    
    if not path.exists():
        print(f"⏩ [SKIP] {filename} introuvable.")
        return None

    print(f"📂 [LECTURE] {path.name}...")
    # On lit un peu plus large pour avoir de la matière
    df = pd.read_csv(path, nrows=50000, low_memory=False)
    
    # --- NETTOYAGE ---
    df = df.where(pd.notnull(df), None)
    df.columns = df.columns.str.replace('_m999', '')
    if 'date_operation' in df.columns: df.rename(columns={'date_operation': 'date'}, inplace=True)

    for col in df.columns:
        if "date" in col.lower() or "heure" in col.lower():
            try: df[col] = pd.to_datetime(df[col], errors='coerce')
            except: pass

    # Sécurité Colonnes
    try:
        valid_cols = Base.metadata.tables[table_name].columns.keys()
        df = df[[c for c in df.columns if c in valid_cols]]
    except: pass

    # --- FILTRAGE INTELLIGENT ---
    if table_name == "operations":
        # On garde les 1000 premiers
        df = df.head(LIMIT)
        # On sauvegarde les IDs pour filtrer les enfants après
        valid_ids = df['operation_id'].tolist()
        print(f"🎯 Sélection de {len(df)} opérations pilotes.")
        
    else:
        # Pour les enfants, on ne garde QUE ceux liés aux parents chargés
        if parent_ids and 'operation_id' in df.columns:
            df = df[df['operation_id'].isin(parent_ids)]
        
        # On limite aussi pour pas surcharger
        df = df.head(LIMIT * 2) 
        valid_ids = None

    # Dédoublonnage
    if 'operation_id' in df.columns and table_name in ['operations', 'operations_stats']:
        df = df.drop_duplicates(subset=['operation_id'])

    # --- ENVOI ---
    if not df.empty:
        print(f"🚀 [ENVOI] {len(df)} lignes vers {table_name}...")
        df.to_sql(table_name, engine, if_exists='append', index=False, chunksize=100)
        print(f"✅ [OK] {table_name} chargé.")
    else:
        print(f"⚠️ [VIDE] Aucune donnée correspondante pour {table_name}.")

    return valid_ids

def main():
    print("=== CHARGEMENT ÉCHANTILLON (1000 LIGNES) ===\n")
    engine = get_engine()

    print("🧹 Reset de la base Neon...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # 1. Charger les parents et récupérer leurs IDs
    ids_operations = load_sample("operations.csv", "operations", engine)

    # 2. Charger les enfants en utilisant ces IDs
    if ids_operations:
        load_sample("flotteurs.csv", "flotteurs", engine, ids_operations)
        load_sample("resultats_humain.csv", "resultats_humain", engine, ids_operations)
        load_sample("operations_stats.csv", "operations_stats", engine, ids_operations)

    print("\n=== TERMINE : PRÊT POUR STREAMLIT ===")

if __name__ == "__main__":
    main()