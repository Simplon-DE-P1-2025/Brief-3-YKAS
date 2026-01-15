"""
Script CLI d'initialisation de la base de données DuckDB.
Usage : python src/init_db.py [--reset]

Responsabilité :
- Créer le schéma de la base de données
- Charger les données CSV validées
- Vérifier l'intégrité
"""
import argparse
import logging
import sys
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Imports des modules du projet
from src.db_manager import db_manager
from src.load_to_duckdb import duckdb_data_loader


def parse_args():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Initialisation de la base de données YKAS"
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Supprime et recrée la base de données'
    )
    return parser.parse_args()


def initialize_database(reset: bool = False):
    """
    Initialise la base de données complète.
    
    Args:
        reset: Si True, supprime et recrée la DB
        
    Returns:
        True si succès, False sinon
    """
    try:
        logger.info("="*70)
        logger.info("🔧 INITIALISATION DE LA BASE DE DONNÉES YKAS")
        logger.info("="*70)
        
        # Étape 1 : Reset si demandé
        if reset:
            logger.info("⚠️  Mode RESET activé - Suppression de la DB existante")
            db_manager.drop_database()
        
        # Étape 2 : Vérification de l'état
        if db_manager.is_initialized():
            logger.info("✓ Base de données déjà initialisée")
            
            # Afficher les statistiques
            logger.info("\n📊 Statistiques actuelles :")
            for table_name in ["operations", "flotteur", "resultat_humain", "operation_stats"]:
                count = db_manager.get_table_count(table_name)
                logger.info(f"   • {table_name:20s} : {count:>8,} lignes")
            
            if not reset:
                logger.info("\n💡 Utilisez --reset pour réinitialiser")
                return True
        
        # Étape 3 : Création du schéma
        logger.info("\n📋 Création du schéma...")
        db_manager.initialize_schema()
        
        # Étape 4 : Chargement des données
        logger.info("\n📦 Chargement des données CSV...")
        results = duckdb_data_loader.load_all_data()
        
        # Étape 5 : Vérification
        logger.info("\n🔍 Vérification de l'intégrité...")
        if duckdb_data_loader.verify_data_integrity():
            logger.info("\n" + "="*70)
            logger.info("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
            logger.info("="*70)
            return True
        else:
            logger.error("\n❌ Problème d'intégrité détecté")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ ÉCHEC DE L'INITIALISATION : {e}", exc_info=True)
        return False


def main():
    """Point d'entrée principal du script."""
    args = parse_args()
    
    success = initialize_database(reset=args.reset)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()