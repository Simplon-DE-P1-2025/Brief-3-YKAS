"""
Gestionnaire de connexion et opérations DuckDB.
Responsabilité : Encapsulation de la logique DB.
"""
import duckdb
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
from src.config import DB_FILE, DB_DIR, SQL_SCHEMA_FILE

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestionnaire centralisé pour les opérations DuckDB."""
    
    def __init__(self, db_path: Path = DB_FILE):
        """
        Initialise le gestionnaire de base de données.
        
        Args:
            db_path: Chemin vers le fichier DuckDB
        """
        self.db_path = db_path
        self._ensure_db_dir()
    
    def _ensure_db_dir(self):
        """Crée le dossier de la DB s'il n'existe pas."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self, read_only: bool = False):
        """
        Context manager pour les connexions DuckDB.
        Garantit la fermeture automatique.
        
        Args:
            read_only: Mode lecture seule
            
        Yields:
            Connection DuckDB
            
        Example:
            with db_manager.get_connection() as conn:
                conn.execute("SELECT * FROM operations")
        """
        conn = None
        try:
            conn = duckdb.connect(str(self.db_path), read_only=read_only)
            logger.debug(f"Connexion ouverte à {self.db_path}")
            yield conn
        except Exception as e:
            logger.error(f"Erreur de connexion DB : {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("Connexion fermée")
    
    def db_exists(self) -> bool:
        """Vérifie si le fichier DB existe."""
        return self.db_path.exists()
    
    def is_initialized(self) -> bool:
        """
        Vérifie si la DB est initialisée (contient les tables).
        
        Returns:
            True si les 4 tables principales existent
        """
        if not self.db_exists():
            return False
        
        try:
            with self.get_connection(read_only=True) as conn:
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = {t[0] for t in tables}
                required = {"operations", "flotteur", "resultat_humain", "operation_stats"}
                return required.issubset(table_names)
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification de la DB : {e}")
            return False
    
    def initialize_schema(self):
        """
        Exécute le script SQL de création des tables.
        
        Raises:
            FileNotFoundError: Si le script SQL n'existe pas
            Exception: Si l'exécution échoue
        """
        if not SQL_SCHEMA_FILE.exists():
            raise FileNotFoundError(f"Script SQL introuvable : {SQL_SCHEMA_FILE}")
        
        logger.info("Initialisation du schéma de la base de données...")
        
        with open(SQL_SCHEMA_FILE, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        with self.get_connection() as conn:
            conn.execute(sql_script)
        
        logger.info("✅ Schéma créé avec succès")
    
    def get_table_count(self, table_name: str) -> int:
        """
        Retourne le nombre de lignes dans une table.
        
        Args:
            table_name: Nom de la table
            
        Returns:
            Nombre de lignes
        """
        with self.get_connection(read_only=True) as conn:
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            return result[0] if result else 0
    
    def drop_database(self):
        """Supprime le fichier de base de données."""
        if self.db_path.exists():
            self.db_path.unlink()
            logger.info(f"Base de données supprimée : {self.db_path}")


# Instance singleton
db_manager = DatabaseManager()
