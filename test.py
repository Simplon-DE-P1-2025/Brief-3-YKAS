# import duckdb as db 
import pandas as pd
from pathlib import Path
import os 

# # lecture de la donnée 
# data_dir = Path(__file__).resolve().parent / "data"/"processed"

# df_ops = pd.read_csv(data_dir / "operations_validated.csv", low_memory=False)
# df_flo = pd.read_csv(data_dir / "flotteurs_validated.csv", low_memory=False)
# df_hum = pd.read_csv(data_dir / "resultats_humain_validated.csv", low_memory=False)
# df_stats = pd.read_csv(data_dir / "operations_stats_validated.csv", low_memory=False)

# print(df_ops.columns, df_flo.columns, df_hum.columns, df_stats.columns)