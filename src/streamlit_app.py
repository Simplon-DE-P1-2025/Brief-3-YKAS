import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pathlib import Path

# --- CONFIGURATION ---
st.set_page_config(page_title="Dashboard SECMAR Complet", layout="wide", page_icon="⚓")

# --- CHEMINS (Adapté à ton architecture src/) ---
CURRENT_DIR = Path(__file__).parent
DATA_DIR = CURRENT_DIR.parent / "app_data"

# --- CHARGEMENT OPTIMISÉ (4 TABLES) ---
@st.cache_data
def load_all_data():
    data = {}
    
    # Liste de tes fichiers (Noms exacts selon ton upload)
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
            except Exception as e:
                st.error(f"Erreur lecture {filename}: {e}")
                data[key] = pd.DataFrame()
        else:
            st.warning(f"Fichier introuvable : {filename}")
            data[key] = pd.DataFrame()
    
    return data["ops"], data["flo"], data["hum"], data["stats"]

# --- APP ---
st.title("⚓ Dashboard SECMAR - Vue Complète")

with st.spinner("Chargement de l'ensemble des données..."):
    df_ops, df_flo, df_hum, df_stats = load_all_data()

if not df_ops.empty:
    # 1. PRÉPARATION & FILTRES GLOBAUX
    # Conversion date
    if 'date_heure_reception_alerte' in df_ops.columns:
        df_ops['date'] = pd.to_datetime(df_ops['date_heure_reception_alerte'], utc=True)
    
    # Sidebar
    st.sidebar.header("Filtres Globaux")
    
    # Filtre Année
    annees = sorted(df_ops['date'].dt.year.unique(), reverse=True)
    annee_select = st.sidebar.selectbox("Année", annees)
    
    # Filtre CROSS
    cross_list = ["Tous"] + sorted(df_ops['cross'].dropna().unique().tolist())
    cross_select = st.sidebar.selectbox("CROSS", cross_list)

    # --- APPLICATION DES FILTRES ---
    # On filtre d'abord les opérations
    mask = (df_ops['date'].dt.year == annee_select)
    if cross_select != "Tous":
        mask = mask & (df_ops['cross'] == cross_select)
    
    df_ops_filtered = df_ops[mask]
    
    # On récupère les IDs des opérations filtrées pour filtrer les autres tables
    valid_ids = df_ops_filtered['operation_id'].unique()
    
    # On filtre les enfants (Flotteurs, Humains, Stats)
    df_flo_filtered = df_flo[df_flo['operation_id'].isin(valid_ids)]
    df_hum_filtered = df_hum[df_hum['operation_id'].isin(valid_ids)]
    df_stats_filtered = df_stats[df_stats['operation_id'].isin(valid_ids)]

    # --- KPI GLOBAUX ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Opérations", len(df_ops_filtered))
    kpi2.metric("Personnes Impliquées", len(df_hum_filtered))
    # Calcul nombre moyen de flotteurs par opération
    avg_flo = len(df_flo_filtered) / len(df_ops_filtered) if len(df_ops_filtered) > 0 else 0
    kpi3.metric("Moyens engagés (Moyenne)", f"{avg_flo:.1f}")
    kpi4.metric("CROSS Concerné", cross_select if cross_select != "Tous" else "National")

    st.markdown("---")

    # --- ONGLETS ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Opérations & CROSS", "🚤 Moyens (Flotteurs)", "busts_in_silhouette: Bilan Humain"])

    # ONGLET 1 : OPÉRATIONS
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Répartition par Type d'événement")
            if 'evenement' in df_ops_filtered.columns:
                fig_evt = px.pie(df_ops_filtered, names='evenement', title='Top événements')
                fig_evt.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_evt, use_container_width=True)
        
        with col2:
            st.subheader("Activité par CROSS")
            cross_counts = df_ops_filtered['cross'].value_counts().reset_index()
            cross_counts.columns = ['CROSS', 'Nombre']
            fig_cross = px.bar(cross_counts, x='CROSS', y='Nombre', color='CROSS')
            st.plotly_chart(fig_cross, use_container_width=True)

    # ONGLET 2 : FLOTTEURS
    with tab2:
        st.subheader(f"Analyse des {len(df_flo_filtered)} moyens engagés")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'categorie_flotteur' in df_flo_filtered.columns:
                st.markdown("**Catégories de moyens**")
                flo_counts = df_flo_filtered['categorie_flotteur'].value_counts().head(10).reset_index()
                flo_counts.columns = ['Catégorie', 'Nombre']
                fig_flo = px.bar(flo_counts, x='Nombre', y='Catégorie', orientation='h', color='Nombre')
                st.plotly_chart(fig_flo, use_container_width=True)
        
        with col2:
            st.dataframe(df_flo_filtered.head(100), use_container_width=True)

    # ONGLET 3 : HUMAINS
    with tab3:
        st.subheader(f"Bilan humain ({len(df_hum_filtered)} personnes)")
        
        if 'resultat_humain' in df_hum_filtered.columns:
            # Graphique Résultat
            res_counts = df_hum_filtered['resultat_humain'].value_counts().reset_index()
            res_counts.columns = ['Résultat', 'Nombre']
            
            fig_hum = px.bar(res_counts, x='Résultat', y='Nombre', 
                             color='Résultat', title="Résultat des interventions")
            st.plotly_chart(fig_hum, use_container_width=True)
            
            # KPI Sauvetage
            sauves = len(df_hum_filtered[df_hum_filtered['resultat_humain'].str.contains("sauve", case=False, na=False)])
            st.metric("Personnes sauvées/secourues", sauves)
        else:
            st.warning("Colonne 'resultat_humain' manquante")

else:
    st.error("Impossible de charger les données principales (Opérations).")