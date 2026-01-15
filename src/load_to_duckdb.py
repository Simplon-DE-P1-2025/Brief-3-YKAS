"""
Module de chargement des données CSV vers DuckDB.
Responsabilité : ETL (Extract-Transform-Load) des fichiers validés.
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional
from src.config import CSV_FILES, TABLE_NAMES, BATCH_SIZE
from src.db_manager import db_manager

logger = logging.getLogger(__name__)


class DuckDBDataLoader:
    """Chargeur de données CSV vers DuckDB avec gestion transactionnelle."""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def load_csv_to_table(
        self, 
        csv_path: Path, 
        table_name: str,
        batch_size: int = BATCH_SIZE
    ) -> int:
        """
        Charge un fichier CSV dans une table DuckDB.
        
        Args:
            csv_path: Chemin vers le fichier CSV
            table_name: Nom de la table cible
            batch_size: Taille des batchs pour l'insertion
            
        Returns:
            Nombre de lignes insérées
            
        Raises:
            FileNotFoundError: Si le CSV n'existe pas
            Exception: Si le chargement échoue
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"Fichier CSV introuvable : {csv_path}")
        
        logger.info(f"📂 Chargement de {csv_path.name} → {table_name}")
        
        try:
            # Lecture du CSV avec gestion des types
            df = pd.read_csv(
                csv_path,
                low_memory=False,
                parse_dates=[col for col in pd.read_csv(csv_path, nrows=0).columns 
                            if 'date' in col.lower() or 'heure' in col.lower()]
            )
            
            # Nettoyage : remplacement des NaN par None (NULL en SQL)
            df = df.where(pd.notnull(df), None)
            
            row_count = len(df)
            logger.info(f"   → {row_count} lignes à insérer")
            
            # Insertion par batch via DuckDB (ultra-rapide)
            with self.db_manager.get_connection() as conn:
                # DuckDB peut insérer directement un DataFrame Pandas
                conn.execute(f"INSERT INTO {table_name} SELECT * FROM df")
            
            logger.info(f"   ✅ {row_count} lignes insérées dans {table_name}")
            return row_count
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de {csv_path.name} : {e}")
            raise
    
    def load_all_data(self) -> Dict[str, int]:
        """
        Charge tous les fichiers CSV définis dans la configuration.
        
        Returns:
            Dictionnaire {nom_fichier: nombre_lignes_insérées}
            
        Raises:
            Exception: Si au moins un chargement échoue
        """
        logger.info("🚀 Démarrage du chargement complet des données")
        
        results = {}
        errors = []
        
        for key, csv_path in CSV_FILES.items():
            table_name = TABLE_NAMES[key]
            
            try:
                count = self.load_csv_to_table(csv_path, table_name)
                results[key] = count
            except Exception as e:
                errors.append(f"{key}: {e}")
                logger.error(f"Échec du chargement de {key}")
        
        if errors:
            error_msg = "\n".join(errors)
            raise Exception(f"Erreurs lors du chargement :\n{error_msg}")
        
        # Résumé
        total = sum(results.values())
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ CHARGEMENT TERMINÉ - {total} lignes insérées au total")
        for key, count in results.items():
            logger.info(f"   • {key:20s} : {count:>8,} lignes")
        logger.info(f"{'='*60}\n")
        
        return results
    
    def verify_data_integrity(self) -> bool:
        """
        Vérifie l'intégrité des données après chargement.
        
        Returns:
            True si toutes les tables contiennent des données
        """
        logger.info("🔍 Vérification de l'intégrité des données...")
        
        all_good = True
        
        for key, table_name in TABLE_NAMES.items():
            count = self.db_manager.get_table_count(table_name)
            
            if count == 0:
                logger.warning(f"⚠️  Table {table_name} est vide !")
                all_good = False
            else:
                logger.info(f"   ✓ {table_name:20s} : {count:>8,} lignes")
        
        return all_good


# Instance singleton
duckdb_data_loader = DuckDBDataLoader()
