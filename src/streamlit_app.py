import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Dashboard SECMAR", layout="wide")

@st.cache_data
def load_data():
    # Lecture du Parquet local
    path = Path("app_data/operations.parquet")
    if not path.exists():
        return None
    return pd.read_parquet(path)

st.title("⚓ Dashboard SECMAR (Version Parquet)")
st.caption("Données historiques complètes (sans BDD)")

df = load_data()

if df is not None:
    # Conversion date pour le filtre
    if 'date_heure_reception_alerte' in df.columns:
        df['date'] = pd.to_datetime(df['date_heure_reception_alerte'], utc=True)
        
    # KPI
    col1, col2 = st.columns(2)
    col1.metric("Opérations Totales", len(df))
    col2.metric("CROSS impliqués", df['cross'].nunique())

    # Graphique
    st.subheader("Répartition par CROSS")
    fig = px.bar(df['cross'].value_counts().reset_index(), x='cross', y='count')
    st.plotly_chart(fig, use_container_width=True)
    
    # Aperçu
    st.dataframe(df.head(50))
else:
    st.error("Erreur : Fichier app_data/operations.parquet introuvable.")