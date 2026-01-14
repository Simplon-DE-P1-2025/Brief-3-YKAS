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
# On force un chunksize petit pour éviter le timeout Render
CHUNK_SIZE = 500 

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("⚠️  Pas de DATABASE_URL, mode SQLite local.")
    DATABASE_URL = "sqlite:///data/maritime.db"
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_engine():
    return create_engine(DATABASE_URL, echo=False)

def clean_data(df, table_name):
    """Nettoie les données avant l'envoi."""
    # 1. Remplacer les NaN par None (NULL SQL)
    df = df.where(pd.notnull(df), None)
    
    # 2. Gestion spécifique pour operations_stats (colonnes _m999)
    if table_name == 'operations_stats':
        df.columns = df.columns.str.replace('_m999', '')
        if 'date_operation' in df.columns:
            df.rename(columns={'date_operation': 'date'}, inplace=True)

    # 3. Conversion des dates
    for col in df.columns:
        if "date" in col.lower() or "heure" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                pass
    return df

def load_file(filename, table_name, engine):
    """Charge un fichier CSV."""
    # Trouve le fichier (csv, _validated, ou _processed)
    candidates = [filename, filename.replace(".csv", "_validated.csv"), filename.replace(".csv", "_processed.csv")]
    file_path = next((PROCESSED_DIR / f for f in candidates if (PROCESSED_DIR / f).exists()), None)

    if not file_path:
        print(f"⏩ [SKIP] {table_name} : Fichier introuvable.")
        return

    print(f"📂 [READ] {file_path.name} ({table_name})...")
    df = pd.read_csv(file_path, low_memory=False)
    
    if df.empty: return

    # Nettoyage
    df = clean_data(df, table_name)
    total_rows = len(df)
    
    print(f"🚀 [LOAD] Injection de {total_rows} lignes par paquets de {CHUNK_SIZE}...")
    
    try:
        # L'argument method='multi' accélère, et chunksize évite le timeout
        df.to_sql(
            table_name, 
            engine, 
            if_exists='append', 
            index=False, 
            method='multi', 
            chunksize=CHUNK_SIZE
        )
        print(f"✅ [OK] {table_name} terminé avec succès.")
        
    except Exception as e:
        print(f"❌ [CRASH] Erreur sur {table_name}: {e}")
        # On ne relance pas l'erreur pour essayer de charger les autres tables quand même

def main():
    print("=== DÉMARRAGE DU CHARGEMENT (MODE SECURE) ===\n")
    engine = get_engine()

    # 1. Reset de la base (Attention, ça supprime tout !)
    print("🧹 Nettoyage de la base de données...")
    try:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        print("✨ Tables recréées à neuf.")
    except Exception as e:
        print(f"❌ Erreur de connexion/reset : {e}")
        return

    # 2. Chargement dans l'ordre (Parent -> Enfant)
    files_to_load = [
        ("operations.csv", "operations"),
        ("flotteurs.csv", "flotteurs"),
        ("resultats_humain.csv", "resultats_humain"),
        ("operations_stats.csv", "operations_stats")
    ]

    for filename, table_name in files_to_load:
        load_file(filename, table_name, engine)
        print("-" * 30)

    print("\n=== TERMINE ===")

if __name__ == "__main__":
    main()