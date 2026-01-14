import streamlit as st
import pandas as pd
import plotly.express as px
import graphviz
from pathlib import Path

# --- CONFIGURATION ---
st.set_page_config(page_title="SeCMAR Analytics", layout="wide", page_icon="⚓")

# --- CHARGEMENT DES DONNÉES (Architecture Parquet) ---
CURRENT_DIR = Path(__file__).parent
DATA_DIR = CURRENT_DIR.parent / "app_data"

@st.cache_data
def load_data():
    data = {}
    files = {
        "ops": "operations_validated.parquet",
        "flo": "flotteurs_validated.parquet",
        "hum": "resultats_humain_validated.parquet",
        "stats": "operations_stats_validated.parquet"
    }
    
    # 1. Chargement des fichiers
    for key, filename in files.items():
        path = DATA_DIR / filename
        if path.exists():
            try:
                data[key] = pd.read_parquet(path)
                # Conversion automatique de toutes les colonnes temporelles
                for col in data[key].columns:
                    if 'date' in col.lower() or 'heure' in col.lower():
                        data[key][col] = pd.to_datetime(data[key][col], errors='coerce', utc=True)
            except Exception:
                data[key] = pd.DataFrame()
        else:
            data[key] = pd.DataFrame()

    # 2. CORRECTION CRITIQUE : Création de la colonne 'date' standardisée pour Ops
    # On cherche la colonne qui contient la date principale
    df_ops = data["ops"]
    if not df_ops.empty:
        if 'date_heure_reception_alerte' in df_ops.columns:
            df_ops['date'] = df_ops['date_heure_reception_alerte']
        elif 'date_operation' in df_ops.columns:
            df_ops['date'] = df_ops['date_operation']
        else:
            # Fallback : on prend la première colonne qui contient "date" dans son nom
            cols = [c for c in df_ops.columns if 'date' in c.lower()]
            if cols:
                df_ops['date'] = df_ops[cols[0]]
            else:
                st.error("Impossible de trouver une colonne de date dans le fichier opérations.")
    
    return df_ops, data["flo"], data["hum"], data["stats"]

# --- FONCTIONS GRAPHIQUES ---
def plot_schema():
    """Dessine le diagramme ER pour le brief"""
    graph = graphviz.Digraph()
    graph.attr(rankdir='LR')
    
    # Tables
    graph.node('OPS', 'OPERATIONS\n(PK: operation_id)\nDate, Cross, Evénement...')
    graph.node('FLO', 'FLOTTEURS\n(FK: operation_id)\nType, Pavillon...')
    graph.node('HUM', 'RESULTATS_HUMAIN\n(FK: operation_id)\nNombre, Résultat, Catégorie...')
    graph.node('STATS', 'OPERATIONS_STATS\n(FK: operation_id)\nDurée, Distances...')
    
    # Relations
    graph.edge('OPS', 'FLO', label='1 to N')
    graph.edge('OPS', 'HUM', label='1 to N')
    graph.edge('OPS', 'STATS', label='1 to 1')
    
    st.graphviz_chart(graph)

# --- INTERFACE PRINCIPALE ---
def main():
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Logo_Marine_nationale.svg/1200px-Logo_Marine_nationale.svg.png", width=100)
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Aller vers", ["📊 Dashboard Stratégique", "🔎 Analyse Opérationnelle", "💾 Modèle & Audit", "🛠️ CRUD (Démo)"])

    # Chargement
    with st.spinner("Récupération des archives SECMAR..."):
        df_ops, df_flo, df_hum, df_stats = load_data()

    if df_ops.empty or 'date' not in df_ops.columns:
        st.error("Données introuvables ou colonne 'date' manquante. Vérifiez le dossier app_data.")
        return

    # --- FILTRES GLOBAUX ---
    st.sidebar.markdown("---")
    st.sidebar.header("Filtres")
    
    # Sécurité sur le dropna pour éviter les erreurs si des dates sont nulles
    years = sorted(df_ops['date'].dt.year.dropna().unique(), reverse=True)
    
    if not years:
        st.warning("Aucune année valide trouvée dans les données.")
        return

    selected_year = st.sidebar.selectbox("Année", years)
    
    # Filtrage des données
    ops_yr = df_ops[df_ops['date'].dt.year == selected_year]
    ids_yr = ops_yr['operation_id'].unique()
    
    # Filtrage des enfants (si les tables ne sont pas vides)
    flo_yr = df_flo[df_flo['operation_id'].isin(ids_yr)] if not df_flo.empty else pd.DataFrame()
    hum_yr = df_hum[df_hum['operation_id'].isin(ids_yr)] if not df_hum.empty else pd.DataFrame()

    # === PAGE 1 : DASHBOARD STRATEGIQUE ===
    if page == "📊 Dashboard Stratégique":
        st.title(f"⚓ Bilan des Opérations {selected_year}")
        
        # KPIS
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Opérations Totales", len(ops_yr))
        k2.metric("Moyens Engagés", len(flo_yr))
        k3.metric("Personnes Impliquées", len(hum_yr))
        
        # Calcul Taux de réussite
        if not hum_yr.empty and 'resultat_humain' in hum_yr.columns:
            sauves = hum_yr[hum_yr['resultat_humain'].str.contains('sauve', case=False, na=False)]
            # Eviter la division par zéro
            taux = (len(sauves) / len(hum_yr)) * 100 if len(hum_yr) > 0 else 0
            k4.metric("Taux de Sauvetage", f"{taux:.1f}%")
        else:
            k4.metric("Taux de Sauvetage", "N/A")

        # GRAPHIQUES
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Saisonnalité des interventions")
            if not ops_yr.empty:
                # Tri des mois correct
                ops_yr['Mois'] = ops_yr['date'].dt.month_name()
                monthly_counts = ops_yr['Mois'].value_counts().reset_index()
                monthly_counts.columns = ['Mois', 'Nombre']
                # Ordre chronologique approximatif pour le graphique
                st.bar_chart(data=monthly_counts.set_index('Mois'))
            
        with c2:
            st.subheader("Répartition par CROSS")
            if 'cross' in ops_yr.columns:
                fig = px.pie(ops_yr, names='cross', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)

        # CARTE
        if 'latitude' in ops_yr.columns and 'longitude' in ops_yr.columns:
            st.subheader("Cartographie des incidents")
            map_data = ops_yr.dropna(subset=['latitude', 'longitude'])
            if not map_data.empty:
                st.map(map_data.head(1000), size=20, color='#0044ff')

    # === PAGE 2 : ANALYSE OPERATIONNELLE ===
    elif page == "🔎 Analyse Opérationnelle":
        st.title("🔎 Analyse Détaillée")
        
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
                fig2 = px.sunburst(flo_yr, path=['categorie_flotteur', 'type_flotteur'], title="Hiérarchie des moyens")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Pas de données de flotteurs pour cette année.")

    # === PAGE 3 : MODELE & AUDIT ===
    elif page == "💾 Modèle & Audit":
        st.title("Architecture des Données")
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Modèle Relationnel (Schéma)")
            try:
                plot_schema()
            except Exception:
                st.warning("Graphviz n'est pas installé sur le serveur, affichage impossible.")
            
        with c2:
            st.subheader("Règles de Gestion")
            st.info("""
            * **Unicité** : PK = `operation_id`.
            * **Intégrité** : FK contraintes sur flotteurs/humains.
            * **Typage** : Dates UTC.
            """)

        st.markdown("---")
        st.subheader("📜 Journal d'Audit (Simulation)")
        audit_data = pd.DataFrame({
            "Timestamp": ["2026-01-14 09:00", "2026-01-14 09:15", "2026-01-14 10:30"],
            "User": ["Admin", "DataEng_Junior", "System"],
            "Action": ["INSERT", "UPDATE", "BATCH_LOAD"],
            "Table": ["operations", "resultats_humain", "flotteurs"],
            "Status": ["SUCCESS", "SUCCESS", "SUCCESS"]
        })
        st.dataframe(audit_data, use_container_width=True)

    # === PAGE 4 : CRUD DEMO ===
    elif page == "🛠️ CRUD (Démo)":
        st.title("Interface de Gestion (CRUD)")
        st.warning("⚠️ Mode DÉMO : Base SQL déconnectée pour performance Cloud.")
        
        with st.form("new_op"):
            st.subheader("Ajouter une opération")
            c1, c2 = st.columns(2)
            c1.date_input("Date")
            c1.text_input("CROSS (ex: Etel)")
            c2.selectbox("Type d'événement", ["Sans avarie", "Assistance", "Evacuation"])
            c2.number_input("Latitude", value=47.0)
            if st.form_submit_button("Enregistrer"):
                st.success("✅ Transaction envoyée au serveur (Simulation)")

if __name__ == "__main__":
    main()