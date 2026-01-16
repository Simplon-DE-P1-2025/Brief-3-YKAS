import os
from datetime import datetime
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path
import plotly.express as px


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    st.error("DATABASE_URL introuvable dans .env")
    st.stop()

@st.cache_resource
def get_engine():
    return create_engine(DB_URL)

engine = get_engine()
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception:
    st.error("🚨 Impossible de se connecter à la base.")
    st.stop()

# --- FONCTIONS DE CHARGEMENT DONNÉES ---
@st.cache_data
def load_data():
    """Charge les données depuis les fichiers Parquet"""
    data = {}
    files = {
        "ops": "operations_validated.parquet",
        "flo": "flotteurs_validated.parquet",
        "hum": "resultats_humain_validated.parquet",
        "stats": "operations_stats_validated.parquet"
    }
    
    for key, filename in files.items():
        path = DATA_DIR / filename
        if path.exists():
            try:
                data[key] = pd.read_parquet(path)
                for col in data[key].columns:
                    if 'date' in col.lower() or 'heure' in col.lower():
                        data[key][col] = pd.to_datetime(data[key][col], errors='coerce', utc=True)
            except Exception:
                data[key] = pd.DataFrame()
        else:
            data[key] = pd.DataFrame()

    df_ops = data["ops"]
    if not df_ops.empty:
        if 'date_heure_reception_alerte' in df_ops.columns:
            df_ops['date'] = df_ops['date_heure_reception_alerte']
        elif 'date_operation' in df_ops.columns:
            df_ops['date'] = df_ops['date_operation']
        else:
            cols = [c for c in df_ops.columns if 'date' in c.lower()]
            if cols:
                df_ops['date'] = df_ops[cols[0]]
    
    return df_ops, data["flo"], data["hum"], data["stats"]

# --- FONCTIONS POSTGRESQL (uniquement si mode PostgreSQL) ---
if DB_MODE == "postgresql":
    def run_query(query, params=None):
        """Exécute une requête SQL (INSERT/UPDATE/DELETE)."""
        try:
            with engine.begin() as conn:
                conn.execute(text(query), params or {})
            return True, "Succès"
        except Exception as e:
            return False, str(e)

    def load_table(table_name):
        """Charge une table depuis PostgreSQL"""
        try:
            with engine.connect() as conn:
                df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                for col in df.columns:
                    if 'date' in col.lower() or 'heure' in col.lower():
                        df[col] = pd.to_datetime(df[col], utc=True, errors='coerce')
                return df
        except Exception as e:
            st.error(f"Erreur lecture table {table_name}: {e}")
            return pd.DataFrame()

    def get_smart_dropdown_list():
        """Génère la liste pour l'autocomplétion"""
        try:
            with engine.connect() as conn:
                query = """
                    SELECT operation_id, evenement, "cross", date_heure_reception_alerte 
                    FROM operations 
                    ORDER BY operation_id DESC 
                    LIMIT 2000
                """
                df = pd.read_sql(query, conn)
                if df.empty:
                    return pd.DataFrame()
                df['label'] = df.apply(
                    lambda x: f"{x['operation_id']} | {str(x['date_heure_reception_alerte'])[:10]} | {x['cross']} | {x['evenement']}", 
                    axis=1
                )
                return df
        except Exception as e:
            st.error(f"⚠️ Erreur : {e}")
            return pd.DataFrame()

    def get_one_operation(op_id):
        """Récupère une seule opération"""
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM operations WHERE operation_id = :id"), conn, params={"id": op_id})
            return df.iloc[0] if not df.empty else None

# --- FONCTIONS GRAPHIQUES ---
def plot_schema():
    """Dessine le diagramme ER"""
    if not HAS_GRAPHVIZ:
        st.warning("Graphviz non disponible")
        return
    
    graph = graphviz.Digraph()
    graph.attr(rankdir='LR')
    
    graph.node('OPS', 'OPERATIONS\n(PK: operation_id)\nDate, Cross, Evénement...')
    graph.node('FLO', 'FLOTTEURS\n(FK: operation_id)\nType, Pavillon...')
    graph.node('HUM', 'RESULTATS_HUMAIN\n(FK: operation_id)\nNombre, Résultat, Catégorie...')
    graph.node('STATS', 'OPERATIONS_STATS\n(FK: operation_id)\nDurée, Distances...')
    
    graph.edge('OPS', 'FLO', label='1 to N')
    graph.edge('OPS', 'HUM', label='1 to N')
    graph.edge('OPS', 'STATS', label='1 to 1')
    
    st.graphviz_chart(graph)

# --- INTERFACE PRINCIPALE ---
def main():
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Logo_Marine_nationale.svg/1200px-Logo_Marine_nationale.svg.png", width=100)
    st.sidebar.title("Navigation")
    
    # Indicateur du mode actif
    mode_emoji = "🦆" if DB_MODE == "duckdb" else "🐘"
    st.sidebar.info(f"{mode_emoji} Mode : **{DB_MODE.upper()}**")
    
    if DB_MODE == "postgresql":
        page = st.sidebar.radio("Aller vers", ["📊 Dashboard", "🔎 Explorateur", "🛠️ CRUD", "💾 Modèle"])
    else:
        page = st.sidebar.radio("Aller vers", ["📊 Dashboard Stratégique", "🔎 Analyse Opérationnelle", "💾 Modèle & Audit"])

    # Chargement des données
    with st.spinner("Récupération des archives SECMAR..."):
        df_ops, df_flo, df_hum, df_stats = load_data()

    if df_ops.empty:
        st.error("Données introuvables. Vérifiez le dossier app_data.")
        return

    # === PAGES COMMUNES ===
    if page in ["📊 Dashboard Stratégique", "📊 Dashboard"]:
        st.title("📊 Vue d'ensemble")
        
        if DB_MODE == "postgresql":
            # Dashboard simple pour PostgreSQL
            df_ops_pg = load_table("operations")
            if not df_ops_pg.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Opérations", len(df_ops_pg))
                c2.metric("CROSS Actifs", df_ops_pg['cross'].nunique() if 'cross' in df_ops_pg.columns else 0)
                c3.metric("Dernière maj", datetime.now().strftime("%H:%M"))
                
                if 'cross' in df_ops_pg.columns:
                    st.plotly_chart(px.pie(df_ops_pg, names='cross', hole=0.4), use_container_width=True)
        else:
            # Dashboard complet pour DuckDB
            if 'date' not in df_ops.columns:
                st.error("Colonne 'date' manquante")
                return
            
            years = sorted(df_ops['date'].dt.year.dropna().unique(), reverse=True)
            if not years:
                st.warning("Aucune année valide")
                return
            
            selected_year = st.sidebar.selectbox("Année", years)
            ops_yr = df_ops[df_ops['date'].dt.year == selected_year]
            ids_yr = ops_yr['operation_id'].unique()
            
            flo_yr = df_flo[df_flo['operation_id'].isin(ids_yr)] if not df_flo.empty else pd.DataFrame()
            hum_yr = df_hum[df_hum['operation_id'].isin(ids_yr)] if not df_hum.empty else pd.DataFrame()
            
            st.title(f"⚓ Bilan des Opérations {selected_year}")
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Opérations Totales", len(ops_yr))
            k2.metric("Moyens Engagés", len(flo_yr))
            k3.metric("Personnes Impliquées", len(hum_yr))
            
            if not hum_yr.empty and 'resultat_humain' in hum_yr.columns:
                sauves = hum_yr[hum_yr['resultat_humain'].str.contains('sauve', case=False, na=False)]
                taux = (len(sauves) / len(hum_yr)) * 100 if len(hum_yr) > 0 else 0
                k4.metric("Taux de Sauvetage", f"{taux:.1f}%")
            else:
                k4.metric("Taux de Sauvetage", "N/A")
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Saisonnalité des interventions")
                if not ops_yr.empty:
                    ops_yr['Mois'] = ops_yr['date'].dt.month_name()
                    monthly_counts = ops_yr['Mois'].value_counts().reset_index()
                    monthly_counts.columns = ['Mois', 'Nombre']
                    st.bar_chart(data=monthly_counts.set_index('Mois'))
            
            with c2:
                st.subheader("Répartition par CROSS")
                if 'cross' in ops_yr.columns:
                    fig = px.pie(ops_yr, names='cross', hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
            
            if 'latitude' in ops_yr.columns and 'longitude' in ops_yr.columns:
                st.subheader("Cartographie des incidents")
                map_data = ops_yr.dropna(subset=['latitude', 'longitude'])
                if not map_data.empty:
                    st.map(map_data.head(1000), size=20, color='#0044ff')

    # === EXPLORATEUR (DuckDB) ===
    elif page == "🔎 Analyse Opérationnelle":
        st.title("🔎 Analyse Détaillée")
        
        years = sorted(df_ops['date'].dt.year.dropna().unique(), reverse=True)
        selected_year = st.sidebar.selectbox("Année", years)
        ops_yr = df_ops[df_ops['date'].dt.year == selected_year]
        ids_yr = ops_yr['operation_id'].unique()
        flo_yr = df_flo[df_flo['operation_id'].isin(ids_yr)] if not df_flo.empty else pd.DataFrame()
        
        tab1, tab2 = st.tabs(["Types d'événements", "Moyens Nautiques"])
        
        with tab1:
            st.subheader("Top Incidents")
            if 'evenement' in ops_yr.columns:
                top_evts = ops_yr['evenement'].value_counts().head(15).sort_values(ascending=True)
                fig = px.bar(top_evts, orientation='h', title="Top 15 événements")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Flotte engagée")
            if not flo_yr.empty and 'categorie_flotteur' in flo_yr.columns:
                flo_clean = flo_yr.fillna("Inconnu")
                try:
                    fig2 = px.sunburst(flo_clean, path=['categorie_flotteur', 'type_flotteur'], title="Hiérarchie des moyens")
                    st.plotly_chart(fig2, use_container_width=True)
                except ValueError:
                    st.warning("Données insuffisantes")

    # === EXPLORATEUR (PostgreSQL) ===
    elif page == "🔎 Explorateur":
        st.title("🔎 Explorateur de Tables")
        table = st.selectbox("Table", ["operations", "flotteurs", "resultats_humain", "operations_stats"])
        df = load_table(table)
        st.write(f"**{len(df)} enregistrements**")
        st.dataframe(df, use_container_width=True)

    # === CRUD (PostgreSQL uniquement) ===
    elif page == "🛠️ CRUD":
        st.title("🛠️ Gestion des Opérations")
        
        df_smart = get_smart_dropdown_list()
        tab_create, tab_update, tab_delete = st.tabs(["➕ Créer", "✏️ Modifier", "🗑️ Supprimer"])
        
        with tab_create:
            st.subheader("Nouvelle Opération")
            with st.form("add"):
                c1, c2 = st.columns(2)
                def_id = int(df_smart["operation_id"].max() + 1) if not df_smart.empty else 1
                nid = c1.number_input("ID", value=def_id, step=1)
                ncross = c1.selectbox("CROSS", ["Etel", "Corsen", "Jobourg", "Gris-Nez", "La Garde", "Antilles-Guyane", "La Réunion", "Lagarde"])
                nevt = c2.text_input("Événement", "SAR")
                ndate = c2.date_input("Date")

                if st.form_submit_button("Sauvegarder"):
                    sql = """INSERT INTO operations (operation_id, evenement, "cross", date_heure_reception_alerte)
                             VALUES (:id, :evt, :cr, :dt)"""
                    ok, msg = run_query(sql, {"id": nid, "evt": nevt, "cr": ncross, "dt": ndate})
                    if ok:
                        st.success(f"Opération {nid} créée !")
                        st.rerun()
                    else:
                        st.error(msg)
        
        with tab_update:
            st.subheader("Modifier une opération")
            if df_smart.empty:
                st.warning("Aucune donnée disponible")
            else:
                choice = st.selectbox("🔍 Rechercher", df_smart['label'], key="upd_sel")
                op_id = int(choice.split(" | ")[0])
                data = get_one_operation(op_id)
                
                if data is not None:
                    st.info(f"Édition : **{data['evenement']}** ({data['cross']})")
                    with st.form("upd_form"):
                        c1, c2 = st.columns(2)
                        liste_cross = ["Etel", "Corsen", "Jobourg", "Gris-Nez", "La Garde", "Antilles-Guyane", "La Réunion"]
                        idx_cross = liste_cross.index(data['cross']) if data['cross'] in liste_cross else 0
                        new_cross = c1.selectbox("CROSS", liste_cross, index=idx_cross)
                        new_evt = c2.text_input("Événement", value=data['evenement'])
                        d_val = data['date_heure_reception_alerte']
                        if isinstance(d_val, str):
                            d_val = datetime.strptime(d_val, "%Y-%m-%d").date()
                        new_date = c1.date_input("Date", value=d_val)
                        
                        if st.form_submit_button("✅ Valider"):
                            sql = """UPDATE operations SET evenement=:evt, "cross"=:cr, date_heure_reception_alerte=:dt WHERE operation_id=:id"""
                            ok, msg = run_query(sql, {"evt": new_evt, "cr": new_cross, "dt": new_date, "id": op_id})
                            if ok:
                                st.success("Mise à jour OK !")
                                st.rerun()
                            else:
                                st.error(msg)
        
        with tab_delete:
            st.subheader("Suppression")
            if df_smart.empty:
                st.warning("Rien à supprimer")
            else:
                choice_del = st.selectbox("🔍 Choisir l'opération", df_smart['label'], key="del_sel")
                del_id = int(choice_del.split(" | ")[0])
                data_del = get_one_operation(del_id)
                
                if data_del is not None:
                    st.warning(f"Vous allez supprimer l'opération {did} ({data_del.get('evenement','')})")
                    if st.button("🔥 Confirmer Suppression"):
                        ok, msg = run_query("DELETE FROM operations WHERE operation_id = :id", {"id": did})
                        if ok:
                            st.success("Supprimé.")
                            st.rerun()
                        else:
                            st.error(msg)

    # === MODÈLE ===
    elif page in ["💾 Modèle & Audit", "💾 Modèle"]:
        st.title("💾 Architecture des Données")
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Modèle Relationnel")
            plot_schema()
        
        with c2:
            st.subheader("Règles de Gestion")
            st.info("""
            * **Unicité** : PK = `operation_id`
            * **Intégrité** : FK sur flotteurs/humains
            * **Typage** : Dates UTC
            """)
        
        if DB_MODE == "duckdb":
            st.markdown("---")
            st.subheader("📜 Journal d'Audit (Simulation)")
            audit_data = pd.DataFrame({
                "Timestamp": ["2026-01-15 09:00", "2026-01-15 09:15", "2026-01-15 10:30"],
                "User": ["Admin", "DataEng_Junior", "System"],
                "Action": ["INSERT", "UPDATE", "BATCH_LOAD"],
                "Table": ["operations", "resultats_humain", "flotteurs"],
                "Status": ["SUCCESS", "SUCCESS", "SUCCESS"]
            })
            st.dataframe(audit_data, use_container_width=True)

if __name__ == "__main__":
    main()
