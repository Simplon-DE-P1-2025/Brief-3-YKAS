import pytest
import sys
import os
from pathlib import Path

# --- BLOC MAGIQUE POUR CORRIGER L'ERREUR D'IMPORT ---
# 1. On récupère le chemin du dossier racine du projet (deux niveaux au-dessus de ce fichier)
# tests/ -> racine/
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. On ajoute ce chemin à la liste des endroits où Python cherche des fichiers
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
# ----------------------------------------------------

# Maintenant, on peut importer depuis 'src' proprement
# Assure-toi que ton fichier dans src s'appelle bien 'load_to_db.py'
# Si ton fichier s'appelle 'load.py', change la ligne ci-dessous par : from src import load as load_to_db
try:
    from src import load_to_db
except ImportError:
    # Fallback : si tu as appelé ton fichier 'load.py' ou 'loadtoneon.py'
    try:
        from src import load as load_to_db
    except ImportError:
        from src import loadtoneon as load_to_db

class TestLoadToDb:
    
    def test_import_success(self):
        """Vérifie simplement que le module peut être importé sans erreur."""
        assert load_to_db is not None

    def test_chunk_size_config(self):
        """Vérifie que la config CHUNK_SIZE est bien définie (si elle existe)."""
        # On vérifie si la variable existe dans le module
        if hasattr(load_to_db, 'CHUNK_SIZE'):
            assert isinstance(load_to_db.CHUNK_SIZE, int)
            assert load_to_db.CHUNK_SIZE > 0