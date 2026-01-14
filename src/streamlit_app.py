import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from src.models import Base 

# --- GESTION ROBUSTE DE GRAPHVIZ ---
try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

# --- CONFIGURATION ---
st.set_page_config(page_title="SeCMAR Local (Docker)", layout="wide", page_icon="⚓")

# --- CONNEXION SQL (DOCKER LOCAL) ---
DB_URL = "postgresql://admin:admin@localhost:5432/maritime"

@st.cache_resource
def get_db_connection():
    return create_engine(DB_URL)

try:
    engine = get_db_connection()
except Exception as e:
    st.error("Impossible de se connecter à Docker. Vérifie que le conteneur tourne.")
    st.stop()

# --- CHARGEMENT DES DONNÉES (DIRECT SQL) ---
def load_data():
    try:
        with engine.connect() as conn:
            # On lit tout
            df_ops = pd.read_sql("SELECT * FROM operations", conn)
            df_flo = pd.read_sql("SELECT * FROM flotteurs", conn)
            df_hum = pd.read_sql("SELECT * FROM resultats_humain", conn)
            
        # --- CORRECTION DU NOM DE COLONNE DATE ---
        # PostgreSQL a la colonne 'date_heure_reception_alerte', on la standardise en 'date'
        if not df_ops.empty:
            if 'date_heure_reception_alerte' in df_ops.columns:
                df_ops['date'] = pd.to_datetime(df_ops['date_heure_reception_alerte'], utc=True)
            elif 'date_operation' in df_ops.columns:
                 df_ops['date'] = pd.to_datetime(df_ops['date_operation'], utc=True)
            
            # On s'assure que les autres dates sont bien converties
            cols_date = [c for c in df_ops.columns if 'date' in c or 'heure' in c]
            for col in cols_date:
                df_ops[col] = pd.to_datetime(df_ops[col], utc=True, errors='coerce')
                
        return df_ops, df_flo, df_hum
    except Exception as e:
        st.error(f"❌ Erreur SQL : {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- INTERFACE ---
def main():
    st.sidebar.title("Navigation (Local DB)")
    page = st.sidebar.radio("Menu", ["📊 Dashboard Live", "🛠️ Gestion (CRUD Réel)", "💾 Schéma BDD"])

    # Chargement
    df_ops, df_flo, df_hum = load_data()

    if df_ops.empty:
        st.warning("⚠️ La base de données semble vide ou éteinte.")
        st.info("💡 Astuce : As-tu lancé 'docker-compose up' puis 'python -m src.load_local' ?")
        return

    # === PAGE 1 : DASHBOARD ===
    if page == "📊 Dashboard Live":
        st.title("⚓ Dashboard Opérations (Données SQL)")
        st.metric("Total Opérations en Base", len(df_ops))
        
        # Filtre Année (On utilise la colonne 'date' qu'on vient de créer)
        if 'date' in df_ops.columns:
            years = sorted(df_ops['date'].dt.year.dropna().unique(), reverse=True)
            if years:
                selected_year = st.selectbox("Filtrer par année", years)
                df_filtered = df_ops[df_ops['date'].dt.year == selected_year]
                st.write(f"Opérations en {selected_year} : {len(df_filtered)}")
                
                if 'cross' in df_filtered.columns:
                    fig = px.bar(df_filtered['cross'].value_counts(), orientation='h', title="Activité par CROSS")
                    st.plotly_chart(fig)
            else:
                st.warning("Pas de dates valides trouvées.")
        else:
            st.error("Colonne de date introuvable (Vérifie le modèle SQL).")

    # === PAGE 2 : CRUD RÉEL ===
    elif page == "🛠️ Gestion (CRUD Réel)":
        st.title("🛠️ Interface de Gestion")
        st.info("Modifications en temps réel sur PostgreSQL (Docker).")

        tab1, tab2 = st.tabs(["➕ Ajouter", "❌ Supprimer"])

        with tab1:
            with st.form("add_op"):
                st.subheader("Nouvelle Opération")
                op_id = st.number_input("ID Opération", min_value=999999, step=1)
                evt = st.text_input("Type d'événement", "SAR")
                cross = st.selectbox("CROSS", ["Etel", "Corsen", "Jobourg", "Gris-Nez", "La Garde"])
                date_op = st.date_input("Date")
                
                if st.form_submit_button("Sauvegarder"):
                    try:
                        with engine.connect() as conn:
                            # CORRECTION ICI : On utilise le VRAI nom de la colonne SQL
                            query = text("""
                                INSERT INTO operations (operation_id, evenement, cross, date_heure_reception_alerte)
                                VALUES (:id, :evt, :cross, :date)
                            """)
                            conn.execute(query, {"id": op_id, "evt": evt, "cross": cross, "date": date_op})
                            conn.commit()
                        st.success(f"✅ Opération {op_id} ajoutée !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur SQL : {e}")

        with tab2:
            st.subheader("Suppression")
            id_to_del = st.number_input("ID à supprimer", step=1)
            if st.button("🗑️ Supprimer"):
                try:
                    with engine.connect() as conn:
                        conn.execute(text("DELETE FROM operations WHERE operation_id = :id"), {"id": id_to_del})
                        conn.commit()
                    st.success(f"Opération {id_to_del} supprimée.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
            
            if 'date' in df_ops.columns:
                st.dataframe(df_ops.sort_values('date', ascending=False).head(5))
            else:
                st.dataframe(df_ops.head(5))

    # === PAGE 3 : SCHEMA ===
    elif page == "💾 Schéma BDD":
        st.title("Structure de la Base")
        
        if HAS_GRAPHVIZ:
            try:
                graph = graphviz.Digraph()
                graph.attr(rankdir='LR')
                graph.node('OPS', 'OPERATIONS (SQL)\nPK: operation_id')
                graph.node('FLO', 'FLOTTEURS (SQL)\nFK: operation_id')
                graph.node('HUM', 'RESULTATS_HUMAIN (SQL)\nFK: operation_id')
                
                graph.edge('OPS', 'FLO', label='1-N')
                graph.edge('OPS', 'HUM', label='1-N')
                
                st.graphviz_chart(graph)
            except Exception as e:
                st.warning("Graphviz est installé mais l'exécutable système est introuvable.")
                st.error(e)
        else:
            st.warning("⚠️ La librairie 'graphviz' n'est pas installée.")
            st.code("pip install graphviz")
            st.info("En attendant, voici la structure textuelle : \nOperations --(1:N)--> Flotteurs\nOperations --(1:N)--> Resultats Humains")

if __name__ == "__main__":
    main()

###############################################################################################
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import graphviz
# from pathlib import Path

# # --- CONFIGURATION ---
# st.set_page_config(page_title="SeCMAR Analytics", layout="wide", page_icon="⚓")

# # --- CHARGEMENT DES DONNÉES (Architecture Parquet) ---
# CURRENT_DIR = Path(__file__).parent
# DATA_DIR = CURRENT_DIR.parent / "app_data"

# @st.cache_data
# def load_data():
#     data = {}
#     files = {
#         "ops": "operations_validated.parquet",
#         "flo": "flotteurs_validated.parquet",
#         "hum": "resultats_humain_validated.parquet",
#         "stats": "operations_stats_validated.parquet"
#     }
    
#     # 1. Chargement des fichiers
#     for key, filename in files.items():
#         path = DATA_DIR / filename
#         if path.exists():
#             try:
#                 data[key] = pd.read_parquet(path)
#                 # Conversion automatique de toutes les colonnes temporelles
#                 for col in data[key].columns:
#                     if 'date' in col.lower() or 'heure' in col.lower():
#                         data[key][col] = pd.to_datetime(data[key][col], errors='coerce', utc=True)
#             except Exception:
#                 data[key] = pd.DataFrame()
#         else:
#             data[key] = pd.DataFrame()

#     # 2. CORRECTION CRITIQUE : Création de la colonne 'date' standardisée pour Ops
#     df_ops = data["ops"]
#     if not df_ops.empty:
#         # Recherche intelligente de la colonne date
#         if 'date_heure_reception_alerte' in df_ops.columns:
#             df_ops['date'] = df_ops['date_heure_reception_alerte']
#         elif 'date_operation' in df_ops.columns:
#             df_ops['date'] = df_ops['date_operation']
#         else:
#             cols = [c for c in df_ops.columns if 'date' in c.lower()]
#             if cols:
#                 df_ops['date'] = df_ops[cols[0]]
    
#     return df_ops, data["flo"], data["hum"], data["stats"]

# # --- FONCTIONS GRAPHIQUES ---
# def plot_schema():
#     """Dessine le diagramme ER pour le brief"""
#     graph = graphviz.Digraph()
#     graph.attr(rankdir='LR')
    
#     # Tables
#     graph.node('OPS', 'OPERATIONS\n(PK: operation_id)\nDate, Cross, Evénement...')
#     graph.node('FLO', 'FLOTTEURS\n(FK: operation_id)\nType, Pavillon...')
#     graph.node('HUM', 'RESULTATS_HUMAIN\n(FK: operation_id)\nNombre, Résultat, Catégorie...')
#     graph.node('STATS', 'OPERATIONS_STATS\n(FK: operation_id)\nDurée, Distances...')
    
#     # Relations
#     graph.edge('OPS', 'FLO', label='1 to N')
#     graph.edge('OPS', 'HUM', label='1 to N')
#     graph.edge('OPS', 'STATS', label='1 to 1')
    
#     st.graphviz_chart(graph)

# # --- INTERFACE PRINCIPALE ---
# def main():
#     st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Logo_Marine_nationale.svg/1200px-Logo_Marine_nationale.svg.png", width=100)
#     st.sidebar.title("Navigation")
#     page = st.sidebar.radio("Aller vers", ["📊 Dashboard Stratégique", "🔎 Analyse Opérationnelle", "💾 Modèle & Audit", "🛠️ CRUD (Démo)"])

#     # Chargement
#     with st.spinner("Récupération des archives SECMAR..."):
#         df_ops, df_flo, df_hum, df_stats = load_data()

#     if df_ops.empty or 'date' not in df_ops.columns:
#         st.error("Données introuvables ou colonne 'date' manquante. Vérifiez le dossier app_data.")
#         return

#     # --- FILTRES GLOBAUX ---
#     st.sidebar.markdown("---")
#     st.sidebar.header("Filtres")
    
#     years = sorted(df_ops['date'].dt.year.dropna().unique(), reverse=True)
    
#     if not years:
#         st.warning("Aucune année valide trouvée dans les données.")
#         return

#     selected_year = st.sidebar.selectbox("Année", years)
    
#     # Filtrage des données
#     ops_yr = df_ops[df_ops['date'].dt.year == selected_year]
#     ids_yr = ops_yr['operation_id'].unique()
    
#     # Filtrage des enfants (avec sécurité si vide)
#     flo_yr = df_flo[df_flo['operation_id'].isin(ids_yr)] if not df_flo.empty else pd.DataFrame()
#     hum_yr = df_hum[df_hum['operation_id'].isin(ids_yr)] if not df_hum.empty else pd.DataFrame()

#     # === PAGE 1 : DASHBOARD STRATEGIQUE ===
#     if page == "📊 Dashboard Stratégique":
#         st.title(f"⚓ Bilan des Opérations {selected_year}")
        
#         # KPIS
#         k1, k2, k3, k4 = st.columns(4)
#         k1.metric("Opérations Totales", len(ops_yr))
#         k2.metric("Moyens Engagés", len(flo_yr))
#         k3.metric("Personnes Impliquées", len(hum_yr))
        
#         # Calcul Taux de réussite
#         if not hum_yr.empty and 'resultat_humain' in hum_yr.columns:
#             sauves = hum_yr[hum_yr['resultat_humain'].str.contains('sauve', case=False, na=False)]
#             taux = (len(sauves) / len(hum_yr)) * 100 if len(hum_yr) > 0 else 0
#             k4.metric("Taux de Sauvetage", f"{taux:.1f}%")
#         else:
#             k4.metric("Taux de Sauvetage", "N/A")

#         # GRAPHIQUES
#         c1, c2 = st.columns(2)
#         with c1:
#             st.subheader("Saisonnalité des interventions")
#             if not ops_yr.empty:
#                 ops_yr['Mois'] = ops_yr['date'].dt.month_name()
#                 monthly_counts = ops_yr['Mois'].value_counts().reset_index()
#                 monthly_counts.columns = ['Mois', 'Nombre']
#                 st.bar_chart(data=monthly_counts.set_index('Mois'))
            
#         with c2:
#             st.subheader("Répartition par CROSS")
#             if 'cross' in ops_yr.columns:
#                 fig = px.pie(ops_yr, names='cross', hole=0.4)
#                 st.plotly_chart(fig, use_container_width=True)

#         # CARTE
#         if 'latitude' in ops_yr.columns and 'longitude' in ops_yr.columns:
#             st.subheader("Cartographie des incidents")
#             map_data = ops_yr.dropna(subset=['latitude', 'longitude'])
#             if not map_data.empty:
#                 st.map(map_data.head(1000), size=20, color='#0044ff')

#     # === PAGE 2 : ANALYSE OPERATIONNELLE ===
#     elif page == "🔎 Analyse Opérationnelle":
#         st.title("🔎 Analyse Détaillée")
        
#         tab1, tab2 = st.tabs(["Types d'événements", "Moyens Nautiques"])
        
#         with tab1:
#             st.subheader("Top Incidents")
#             if 'evenement' in ops_yr.columns:
#                 top_evts = ops_yr['evenement'].value_counts().head(15).sort_values(ascending=True)
#                 fig = px.bar(top_evts, orientation='h', title="Top 15 événements")
#                 st.plotly_chart(fig, use_container_width=True)
            
#         with tab2:
#             st.subheader("Flotte engagée")
#             # ⚠️ CORRECTION ICI : Gestion des NaN pour éviter le crash Plotly
#             if not flo_yr.empty and 'categorie_flotteur' in flo_yr.columns:
#                 # On remplit les trous par "Inconnu"
#                 flo_clean = flo_yr.fillna("Inconnu")
#                 try:
#                     fig2 = px.sunburst(flo_clean, path=['categorie_flotteur', 'type_flotteur'], title="Hiérarchie des moyens")
#                     st.plotly_chart(fig2, use_container_width=True)
#                 except ValueError:
#                     st.warning("Données insuffisantes pour afficher la hiérarchie solaire.")
#             else:
#                 st.info("Pas de données de flotteurs pour cette année.")

#     # === PAGE 3 : MODELE & AUDIT ===
#     elif page == "💾 Modèle & Audit":
#         st.title("Architecture des Données")
        
#         c1, c2 = st.columns([2, 1])
#         with c1:
#             st.subheader("Modèle Relationnel (Schéma)")
#             try:
#                 plot_schema()
#             except Exception:
#                 st.warning("Graphviz n'est pas installé ou détecté.")
            
#         with c2:
#             st.subheader("Règles de Gestion")
#             st.info("""
#             * **Unicité** : PK = `operation_id`.
#             * **Intégrité** : FK contraintes sur flotteurs/humains.
#             * **Typage** : Dates UTC.
#             """)

#         st.markdown("---")
#         st.subheader("📜 Journal d'Audit (Simulation)")
#         audit_data = pd.DataFrame({
#             "Timestamp": ["2026-01-14 09:00", "2026-01-14 09:15", "2026-01-14 10:30"],
#             "User": ["Admin", "DataEng_Junior", "System"],
#             "Action": ["INSERT", "UPDATE", "BATCH_LOAD"],
#             "Table": ["operations", "resultats_humain", "flotteurs"],
#             "Status": ["SUCCESS", "SUCCESS", "SUCCESS"]
#         })
#         st.dataframe(audit_data, use_container_width=True)

#     # === PAGE 4 : CRUD DEMO ===
#     elif page == "🛠️ CRUD (Démo)":
#         st.title("Interface de Gestion (CRUD)")
#         st.warning("⚠️ Mode DÉMO : Base SQL déconnectée pour performance Cloud.")
        
#         with st.form("new_op"):
#             st.subheader("Ajouter une opération")
#             c1, c2 = st.columns(2)
#             c1.date_input("Date")
#             c1.text_input("CROSS (ex: Etel)")
#             c2.selectbox("Type d'événement", ["Sans avarie", "Assistance", "Evacuation"])
#             c2.number_input("Latitude", value=47.0)
#             if st.form_submit_button("Enregistrer"):
#                 st.success("✅ Transaction envoyée au serveur (Simulation)")

# if __name__ == "__main__":
#     main()