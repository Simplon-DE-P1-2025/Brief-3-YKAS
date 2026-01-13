import os
import pandas as pd
import pandera as pa
from pathlib import Path

from src.schemas import (
    OperationsSchema, 
    FlotteursSchema, 
    ResultatsHumainSchema, 
    OperationsStatsSchema
)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REJECTS_DIR = BASE_DIR / "data" / "rejects"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REJECTS_DIR.mkdir(parents=True, exist_ok=True)

def process_file(filename, schema):
    """
    Lit un fichier brut, le valide via Pandera, et sauvegarde :
    - Les données valides dans data/processed/ (avec suffixe _processed)
    - Les données invalides dans data/rejects/
    """
    file_path = RAW_DIR / filename
    if not file_path.exists():
        print(f"[WARN] Fichier introuvable : {filename} (ignoré)")
        return

    print(f"\n[INFO] Traitement de '{filename}'...")
    
    # 1. Lecture du CSV
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception as e:
        print(f"[ERROR] Erreur critique lecture CSV : {e}")
        return

    # 2. Conversion des Types (Dates)
    date_cols = [col for col in df.columns if 'date' in col or 'heure' in col]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors='coerce')

    # 3. Validation Pandera
    try:
        schema.validate(df, lazy=True)
        valid_df = df
        rejects_df = pd.DataFrame()
        print(f"[OK] Validation parfaite : {len(df)} lignes valides.")

    except pa.errors.SchemaErrors as err:
        print(f"[WARN] Validation partielle : {len(err.failure_cases)} anomalies détectées.")
        
        failure_cases = err.failure_cases
        error_indices = failure_cases["index"].dropna().unique()
        safe_error_indices = [i for i in error_indices if i in df.index]
        
        if safe_error_indices:
            rejects_df = df.loc[safe_error_indices]
            valid_df = df.drop(index=safe_error_indices)
        else:
            print("[WARN] Erreurs globales détectées sans index précis. Rejet total par sécurité.")
            rejects_df = df
            valid_df = pd.DataFrame(columns=df.columns)

        print(f"   -> {len(valid_df)} lignes valides conservées")
        print(f"   -> {len(rejects_df)} lignes rejetées")

    # 4. Sauvegarde
    if not valid_df.empty:
        new_filename = filename.replace(".csv", "_processed.csv")
        output_path = PROCESSED_DIR / new_filename
        
        valid_df.to_csv(output_path, index=False)
        print(f"[OK] Sauvegardé dans : {output_path}")
    
    if not rejects_df.empty:
        reject_path = REJECTS_DIR / f"rejects_{filename}"
        rejects_df.to_csv(reject_path, index=False)
        print(f"[INFO] Rejets sauvegardés dans : {reject_path}")

def main():
    print("Demarrage du nettoyage des données...\n")

    tasks = [
        ("operations.csv", OperationsSchema),
        ("flotteurs.csv", FlotteursSchema),
        ("resultats_humain.csv", ResultatsHumainSchema),
        ("operations_stats.csv", OperationsStatsSchema),
    ]

    for filename, schema_class in tasks:
        process_file(filename, schema_class)

    print("\nTerminé. Vérifie le dossier 'data/processed'.")

if __name__ == "__main__":
    main()