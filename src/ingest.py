import os
import requests
from pathlib import Path
from typing import Dict, Optional

# --- CONFIGURATION ---
DATASET_ID = "operations-coordonnees-par-les-cross"
API_URL = f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}/"

# Définition des dossiers (data/raw)
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

# Mapping : "Nom exact sur data.gouv" -> (Dossier destination, Nom fichier local)
TARGET_FILES: Dict[str, tuple] = {
    "operations.csv": (RAW_DIR, "operations.csv"),
    "flotteurs.csv": (RAW_DIR, "flotteurs.csv"),
    "resultats_humain.csv": (RAW_DIR, "resultats_humain.csv"),
    "operations_stats.csv": (RAW_DIR, "operations_stats.csv"),
}


def download_file(url: str, folder: Path, filename: str) -> Optional[Path]:
    """
    Télécharge UN SEUL fichier avec gestion des timeouts et stream.
    """
    output_path = folder / filename

    try:
        print(f"Téléchargement de '{filename}'...")
        # Timeout de 30s pour éviter les blocages si le réseau est lent
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"[OK] Enregistré dans : {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Échec sur {filename} : {e}")
        return None


def main():
    # Création automatique du dossier data/raw s'il n'existe pas
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Récupération des métadonnées via API pour : {DATASET_ID}...")

    try:
        # On interroge l'API pour avoir les vrais liens de téléchargement à jour
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Impossible de contacter l'API data.gouv.fr : {e}")
        return

    # On parcourt les ressources disponibles sur la page du dataset
    resources = data.get('resources', [])
    found_count = 0

    for resource in resources:
        title = resource.get('title')
        url = resource.get('url')

        # Si le titre correspond à l'un de nos fichiers cibles
        if title in TARGET_FILES:
            target_folder, target_name = TARGET_FILES[title]
            download_file(url, target_folder, target_name)
            found_count += 1

    print(f"Terminé ! {found_count} fichiers récupérés sur {len(TARGET_FILES)} attendus.")


if __name__ == "__main__":
    main()