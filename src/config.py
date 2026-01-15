"""
Configuration centralisée pour le projet YKAS.
Gère les chemins et paramètres selon l'environnement (dev/prod).
"""
from pathlib import Path
import os

# ============================================================================
# CHEMINS DE BASE
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
APP_DATA_DIR = BASE_DIR / "app_data"

# ============================================================================
# BASE DE DONNÉES
# ============================================================================
DB_DIR = SRC_DIR / "duckdb_init"
DB_FILE = DB_DIR / "initialisation_data.duckdb"
SQL_SCHEMA_FILE = SRC_DIR / "script_init_db.sql"

# ============================================================================
# DONNÉES SOURCES (CSV validés)
# ============================================================================
PROCESSED_DIR = DATA_DIR / "processed"
CSV_FILES = {
    "operations": PROCESSED_DIR / "operations_validated.csv",
    "flotteurs": PROCESSED_DIR / "flotteurs_validated.csv",
    "resultats_humain": PROCESSED_DIR / "resultats_humain_validated.csv",
    "operations_stats": PROCESSED_DIR / "operations_stats_validated.csv"
}

# ============================================================================
# DONNÉES PARQUET (pour Streamlit)
# ============================================================================
PARQUET_FILES = {
    "operations": APP_DATA_DIR / "operations_validated.parquet",
    "flotteurs": APP_DATA_DIR / "flotteurs_validated.parquet",
    "resultats_humain": APP_DATA_DIR / "resultats_humain_validated.parquet",
    "operations_stats": APP_DATA_DIR / "operations_stats_validated.parquet"
}

# ============================================================================
# MAPPING CSV → TABLE
# ============================================================================
TABLE_NAMES = {
    "operations": "operations",
    "flotteurs": "flotteur",
    "resultats_humain": "resultat_humain",
    "operations_stats": "operation_stats"
}

# ============================================================================
# PARAMÈTRES
# ============================================================================
BATCH_SIZE = 10000  # Pour insertion par batch
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
IS_PRODUCTION = os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud"
