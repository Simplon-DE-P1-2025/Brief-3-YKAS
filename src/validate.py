import pandas as pd
import pandera as pa
from pathlib import Path

# On importe les schémas définis dans src/schemas.py
from src.schemas import (
    OperationsSchema, 
    FlotteursSchema, 
    ResultatsHumainSchema, 
    OperationsStatsSchema
)

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "normalize"  # On lit ce qui sort de l'étape 1
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REJECTS_DIR = BASE_DIR / "data" / "rejects"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REJECTS_DIR.mkdir(parents=True, exist_ok=True)

def validate_and_split(original_filename, schema):
    """
    Lit normalize/fichier_normalized.csv -> Valide -> Sauvegarde processed/fichier_validated.csv
    """
    # On reconstruit le nom du fichier d'entrée attendu (celui généré par normalize.py)
    input_filename = original_filename.replace(".csv", "_normalized.csv")
    input_path = INPUT_DIR / input_filename
    
    if not input_path.exists():
        print(f"[WARN] Fichier introuvable : {input_filename}. (Avez-vous lancé python -m src.normalize ?)")
        return

    print(f"\n[VALID] Validation de '{input_filename}'...")
    
    try:
        df = pd.read_csv(input_path, low_memory=False)
    except Exception as e:
        print(f"[ERROR] Lecture impossible : {e}")
        return

    # --- Conversion des Types (Dates) ---
    date_cols = [col for col in df.columns if 'date' in col or 'heure' in col]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors='coerce')

    # --- Validation Pandera ---
    try:
        schema.validate(df, lazy=True)
        valid_df = df
        rejects_df = pd.DataFrame()
        print(f"[OK] 100% Valide ({len(df)} lignes).")

    except pa.errors.SchemaErrors as err:
        print(f"[WARN] {len(err.failure_cases)} erreurs de validation détectées.")
        
        # Isoler les lignes valides et rejetées
        error_indices = err.failure_cases["index"].dropna().unique()
        rejects_df = df.loc[error_indices]
        valid_df = df.drop(index=error_indices)

        print(f"   -> {len(valid_df)} lignes CONFORMES")
        print(f"   -> {len(rejects_df)} lignes NON CONFORMES")

        # --- Amélioration : Sauvegarder les raisons du rejet ---
        reasons_filename = original_filename.replace('.csv', '_reasons.csv')
        reasons_path = REJECTS_DIR / reasons_filename
        err.failure_cases.to_csv(reasons_path, index=False)
        print(f"[SAVE] Détails des rejets : {reasons_path.name}")

    # --- Sauvegarde avec les nouveaux suffixes ---
    if not valid_df.empty:
        # Ex: operations.csv -> operations_validated.csv
        out_name = original_filename.replace(".csv", "_validated.csv")
        valid_df.to_csv(PROCESSED_DIR / out_name, index=False)
        print(f"[SAVE] Validés : {out_name}")
    
    if not rejects_df.empty:
        # Ex: operations.csv -> operations_rejected.csv
        rej_name = original_filename.replace(".csv", "_rejected.csv")
        rejects_df.to_csv(REJECTS_DIR / rej_name, index=False)
        print(f"[SAVE] Rejetés : {rej_name}")

def main():
    print(">>> Démarrage de la VALIDATION <<<\n")

    # On garde la liste des noms originaux pour s'y retrouver
    tasks = [
        ("operations.csv", OperationsSchema),
        ("flotteurs.csv", FlotteursSchema),
        ("resultats_humain.csv", ResultatsHumainSchema),
        ("operations_stats.csv", OperationsStatsSchema),
    ]

    for filename, schema_class in tasks:
        validate_and_split(filename, schema_class)

    print("\n>>> Validation terminée.")

if __name__ == "__main__":
    main()