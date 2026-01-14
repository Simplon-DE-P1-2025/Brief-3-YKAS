import pandas as pd
from pathlib import Path

# --- CONFIG ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "app_data"

def check_file(filename, parent_ids=None):
    path = DATA_DIR / filename
    print(f"\n🔍 ANALYSE : {filename} ...")
    
    if not path.exists():
        print(f"   ❌ ERREUR : Fichier introuvable !")
        return None, None

    try:
        # Lecture
        df = pd.read_parquet(path)
        rows = len(df)
        cols = len(df.columns)
        
        # 1. Check Volume
        if rows == 0:
            print(f"   ❌ ALERTE : Le fichier est VIDE !")
        elif rows < 1000:
            print(f"   ⚠️ WARNING : Seulement {rows} lignes (C'est peut-être l'échantillon test ?)")
        else:
            print(f"   ✅ VOLUME : {rows:,} lignes (C'est de la grosse donnée !)")

        # 2. Check Colonnes Vitales
        print(f"   ℹ️  Colonnes : {cols}")
        
        # 3. Check Intégrité (Lien avec le Parent)
        ids = None
        if 'operation_id' in df.columns:
            ids = set(df['operation_id'].unique())
            if parent_ids is not None:
                # On regarde combien d'enfants ont un parent qui n'existe pas
                orphans = df[~df['operation_id'].isin(parent_ids)]
                nb_orphans = len(orphans)
                if nb_orphans == 0:
                    print(f"   ✅ INTÉGRITÉ : 100% des lignes sont bien liées aux opérations.")
                else:
                    pct = (nb_orphans / rows) * 100
                    print(f"   ⚠️ ORPHELINS : {nb_orphans} lignes ({pct:.1f}%) ne trouvent pas leur opération parente.")
        
        return df, ids

    except Exception as e:
        print(f"   ❌ CRASH : Impossible de lire le fichier ({e})")
        return None, None

def main():
    print("=== 🛡️ DATA QUALITY CHECK ===\n")
    
    # 1. Analyser le PARENT (Opérations)
    # On gère les variantes de nom (validated ou non)
    ops_file = "operations_validated.parquet" if (DATA_DIR / "operations_validated.parquet").exists() else "operations.parquet"
    df_ops, ops_ids = check_file(ops_file)
    
    if ops_ids:
        # 2. Analyser les ENFANTS en vérifiant le lien
        for file in ["flotteurs_validated.parquet", "resultats_humain_validated.parquet", "operations_stats_validated.parquet"]:
            # On gère aussi si le nom n'a pas _validated
            if not (DATA_DIR / file).exists():
                file = file.replace("_validated", "")
            
            check_file(file, parent_ids=ops_ids)

    print("\n=== FIN DU RAPPORT ===")

if __name__ == "__main__":
    main()