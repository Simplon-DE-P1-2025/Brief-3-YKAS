import os
import requests
from pathlib import Path
from typing import Dict, Optional

# --- CONFIGURATION ---
DATASET_ID = "operations-coordonnees-par-les-cross"
API_URL = f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}/"

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
REF_DIR = BASE_DIR / "references"

TARGET_FILES: Dict[str, tuple] = {
    "operations.csv": (RAW_DIR, "operations.csv"),
    "flotteurs.csv": (RAW_DIR, "flotteurs.csv"),
    "resultats_humain.csv": (RAW_DIR, "resultats_humain.csv"),
    "moyens.csv": (RAW_DIR, "moyens.csv"),
    "Script SQL création tables": (REF_DIR, "schema_officiel.sql")
}

def download_file(url: str, folder: Path, filename: str) -> Optional[Path]:
    """
    Télécharge UN SEUL fichier avec gestion des timeouts.
    """
    output_path = folder / filename
    
    try:
        print(f"⬇️  Téléchargement de '{filename}'...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"✅ [OK] Enregistré dans : {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        print(f"❌ [ERREUR] Échec sur {filename} : {e}")
        return None

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REF_DIR.mkdir(parents=True, exist_ok=True)

    print(f"🔍 Récupération des métadonnées via API pour : {DATASET_ID}...")
    
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Impossible de contacter l'API data.gouv.fr : {e}")
        return

    resources = data.get('resources', [])
    found_count = 0

    for resource in resources:
        title = resource.get('title')
        url = resource.get('url')
        
        match_info = None
        if title in TARGET_FILES:
            match_info = TARGET_FILES[title]
        elif "Script SQL" in title:
            match_info = TARGET_FILES["Script SQL création tables"]

        if match_info:
            target_folder, target_name = match_info
            download_file(url, target_folder, target_name)
            found_count += 1

    print(f"\n🎉 Terminé ! {found_count} fichiers récupérés.")

if __name__ == "__main__":
    main()