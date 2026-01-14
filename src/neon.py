import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# On force la modif si tu ne l'as pas faite dans le .env
url = os.getenv("DATABASE_URL").replace("&channel_binding=require", "")

print(f"🔌 Tentative de connexion vers Neon (USA)...")
print(f"URL : {url.split('@')[1]}") # On affiche juste la fin pour vérifier

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        # Petite requête simple
        result = conn.execute(text("SELECT version();"))
        print(f"✅ SUCCÈS ! Connecté à : {result.fetchone()[0]}")
        
        # Test de création de table
        conn.execute(text("CREATE TABLE IF NOT EXISTS test_ping (id serial);"))
        print("✅ Écriture réussie (Table test créée).")
        
except Exception as e:
    print(f"❌ ÉCHEC : {e}")