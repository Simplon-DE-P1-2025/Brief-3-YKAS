import pandas as pd
from pathlib import Path
import unicodedata

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
NORMALIZE_DIR = BASE_DIR / "data" / "normalize"

# Création du dossier intermédiaire
NORMALIZE_DIR.mkdir(parents=True, exist_ok=True)

def normalize_text(text):
    """
    Standardise une chaîne de caractères :
    1. Sépare les accents (NFKD)
    2. Supprime les caractères non-ASCII (les accents)
    3. Passe en minuscule
    4. Supprime les espaces superflus
    """
    if not isinstance(text, str):
        return text
    
    try:
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('utf-8')
        return text.lower().strip()
    except Exception:
        return text

def clean_and_normalize(filename):
    """
    Lit raw/fichier.csv -> Nettoie -> Sauvegarde normalize/fichier_normalized.csv
    """
    input_path = RAW_DIR / filename
    
    # Construction du nom de sortie : 'operations.csv' -> 'operations_normalized.csv'
    output_filename = filename.replace(".csv", "_normalized.csv")
    output_path = NORMALIZE_DIR / output_filename

    if not input_path.exists():
        print(f"[WARN] Fichier introuvable dans raw : {filename}")
        return

    print(f"[NORM] Traitement de '{filename}'...")
    
    try:
        # Lecture
        df = pd.read_csv(input_path, low_memory=False)

        # --- Déplacement de la logique de renommage depuis load_local.py ---
        if filename == "operations.csv":
            if "date_operation" in df.columns and "date_heure_reception_alerte" not in df.columns:
                df.rename(columns={"date_operation": "date_heure_reception_alerte"}, inplace=True)

        elif filename == "operations_stats.csv":
            if "date_operation" in df.columns and "date" not in df.columns:
                df.rename(columns={"date_operation": "date"}, inplace=True)
        
        # Sélection des colonnes texte
        string_cols = df.select_dtypes(include=['object']).columns
        
        # Application de la normalisation sur chaque colonne texte
        for col in string_cols:
            df[col] = df[col].apply(normalize_text)
            
        # Sauvegarde
        df.to_csv(output_path, index=False)
        print(f"[OK] Fichier normalisé : {output_path.name}")

    except Exception as e:
        print(f"[ERROR] Échec normalisation {filename} : {e}")

def main():
    print(">>> Démarrage de la NORMALISATION <<<\n")
    
    files_to_process = [
        "operations.csv",
        "flotteurs.csv",
        "resultats_humain.csv",
        "operations_stats.csv",
    ]

    for filename in files_to_process:
        clean_and_normalize(filename)
        
    print(f"\n>>> Normalisation terminée. Vérifie le dossier '{NORMALIZE_DIR}'.")

if __name__ == "__main__":
    main()