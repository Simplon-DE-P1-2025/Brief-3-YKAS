# import duckdb as db 
# import pandas as pd
# from pathlib import Path
# from src.config import DB_FILE 
from src.db_manager import db_manager
db_manager.initialize_schema()