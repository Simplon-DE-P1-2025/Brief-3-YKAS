import pandas as pd
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE_DIR / "data" / "processed"
DEST_DIR = BASE_DIR / "app_data"
DEST_DIR.mkdir(exist_ok=True)

def convert(filename):
    # Cherche le fichier (normal ou validated)
    csv_path = SOURCE_DIR / filename
    if not csv_path.exists():
        csv_path = SOURCE_DIR / filename.replace(".csv", "_validated.csv")
    
    if csv_path.exists():
        print(f"🔄 Conversion de {filename}...")
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Sauvegarde en Parquet (compression automatique)
        parquet_name = filename.replace(".csv", ".parquet")
        dest_path = DEST_DIR / parquet_name
        
        df.to_parquet(dest_path)
        print(f"✅ {parquet_name} généré dans app_data/")
    else:
        print(f"⚠️ {filename} introuvable.")

if __name__ == "__main__":
    convert("operations_validated.csv")
    convert("flotteurs_validated.csv")
    convert("resultats_humain_validated.csv") 
    convert("operations_stats_validated.csv")