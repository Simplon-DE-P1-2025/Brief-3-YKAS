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

# --- FONCTIONS UTILITAIRES ---

def run_query(query, params=None):
    """Exécute une requête SQL (INSERT/UPDATE/DELETE)."""
    try:
        with engine.begin() as conn:
            conn.execute(text(query), params or {})
        return True, "Succès"
    except Exception as e:
        return False, str(e)

def load_table(table_name):
    """Pour l'explorateur de données"""
    try:
        with engine.connect() as conn:
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            # Conversion date auto
            for col in df.columns:
                if 'date' in col.lower() or 'heure' in col.lower():
                    df[col] = pd.to_datetime(df[col], utc=True, errors='coerce')
            return df
    except Exception as e:
        st.error(f"Erreur lecture table {table_name}: {e}")
        return pd.DataFrame()

def get_smart_dropdown_list():
    """Génère la liste pour l'autocomplétion : 'ID | Date | CROSS | Event'"""
    # J'ai retiré le Try/Except silencieux pour que tu voies l'erreur si ça plante
    try:
        with engine.connect() as conn:
            # Note : "cross" est entre guillemets car c'est un mot clé réservé SQL
            query = """
                SELECT operation_id, evenement, "cross", date_heure_reception_alerte 
                FROM operations 
                ORDER BY operation_id DESC 
                LIMIT 2000
            """
            df = pd.read_sql(query, conn)
            
            # Si le DataFrame est vide, on renvoie vide
            if df.empty:
                return pd.DataFrame()

            # On crée une colonne combinée pour l'affichage
            df['label'] = df.apply(
                lambda x: f"{x['operation_id']} | {str(x['date_heure_reception_alerte'])[:10]} | {x['cross']} | {x['evenement']}", 
                axis=1
            )
            return df
    except Exception as e:
        # AFFICHE L'ERREUR SQL SI ELLE EXISTE (C'est souvent un nom de colonne incorrect)
        st.error(f"⚠️ Erreur lors du chargement de la liste déroulante : {e}")
        st.info("Conseil : Vérifie dans l'onglet 'Explorateur de Données' les vrais noms de tes colonnes (ex: 'date' vs 'date_heure_reception_alerte').")
        return pd.DataFrame()

def get_one_operation(op_id):
    """Récupère une seule opération proprement"""
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM operations WHERE operation_id = :id"), conn, params={"id": op_id})
        return df.iloc[0] if not df.empty else None

# --- INTERFACE PRINCIPALE ---
def main():
    st.sidebar.title("⚓ SeCMAR Manager")
    
    menu = st.sidebar.radio(
        "Navigation", 
        ["📊 Dashboard", "🔎 Explorateur de Données", "🛠️ Gestion (CRUD)", "💾 Modèle de Données"]
    )

    # =========================================================================
    # 1. DASHBOARD
    # =========================================================================
    if menu == "📊 Dashboard":
        st.title("📊 Vue d'ensemble")
        df_ops = load_table("operations")
        
        if not df_ops.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Opérations", len(df_ops))
            c2.metric("CROSS Actifs", df_ops['cross'].nunique() if 'cross' in df_ops.columns else 0)
            c3.metric("Dernière maj", datetime.now().strftime("%H:%M"))
            
            if 'cross' in df_ops.columns:
                st.subheader("Répartition par CROSS")
                st.plotly_chart(px.pie(df_ops, names='cross', hole=0.4), use_container_width=True)
        else:
            st.warning("La base est vide. As-tu lancé 'python -m src.load_local' ?")

    # =========================================================================
    # 2. EXPLORATEUR
    # =========================================================================
    elif menu == "🔎 Explorateur de Données":
        st.title("🔎 Explorateur de Tables")
        table = st.selectbox("Table", ["operations", "flotteurs", "resultats_humain", "operations_stats"])
        df = load_table(table)
        st.write(f"**{len(df)} enregistrements**")
        st.dataframe(df, use_container_width=True)

    # =========================================================================
    # 3. GESTION CRUD
    # =========================================================================
    elif menu == "🛠️ Gestion (CRUD)":
        st.title("🛠️ Gestion des Opérations")
        
        # Chargement de la liste avec gestion d'erreur visible
        df_smart = get_smart_dropdown_list()
        
        tab_create, tab_update, tab_delete = st.tabs(["➕ Créer", "✏️ Modifier (Update)", "🗑️ Supprimer (Delete)"])

        # --- CREATE ---
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

        # --- UPDATE ---
        with tab_update:
            st.subheader("Modifier une opération")
            
            if df_smart.empty:
                st.warning("Aucune donnée disponible ou erreur SQL (voir plus haut).")
            else:
                choice = st.selectbox("🔍 Rechercher (ID | Date | CROSS)", df_smart['label'], key="upd_sel")
                op_id = int(choice.split(" | ")[0])
                data = get_one_operation(op_id)
                
                if data is not None:
                    st.info(f"Édition : **{data['evenement']}** ({data['cross']})")
                    
                    with st.form("upd_form"):
                        c1, c2 = st.columns(2)
                        
                        # Gestion index CROSS
                        liste_cross = ["Etel", "Corsen", "Jobourg", "Gris-Nez", "La Garde", "Antilles-Guyane", "La Réunion"]
                        idx_cross = liste_cross.index(data['cross']) if data['cross'] in liste_cross else 0
                        
                        new_cross = c1.selectbox("CROSS", liste_cross, index=idx_cross)
                        new_evt = c2.text_input("Événement", value=data['evenement'])
                        
                        d_val = data['date_heure_reception_alerte']
                        if isinstance(d_val, str): d_val = datetime.strptime(d_val, "%Y-%m-%d").date()
                        new_date = c1.date_input("Date", value=d_val)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.form_submit_button("✅ Valider"):
                            sql = """UPDATE operations SET evenement=:evt, "cross"=:cr, date_heure_reception_alerte=:dt WHERE operation_id=:id"""
                            ok, msg = run_query(sql, {"evt": new_evt, "cr": new_cross, "dt": new_date, "id": op_id})
                            if ok:
                                st.success("Mise à jour OK !")
                                st.rerun()
                            else:
                                st.error(msg)

        # --- DELETE ---
        with tab_delete:
            st.subheader("Suppression")
            
            if df_smart.empty:
                st.warning("Rien à supprimer.")
            else:
                choice_del = st.selectbox("🔍 Choisir l'opération à supprimer", df_smart['label'], key="del_sel")
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

    # =========================================================================
    # 4. MODÈLE (CORRIGÉ)
    # =========================================================================
    elif menu == "💾 Modèle de Données":
        st.title("💾 Structure BDD")
        if HAS_GRAPHVIZ:
            # CORRECTION DU BUG GRAPHVIZ ICI
            g = graphviz.Digraph()
            g.attr(rankdir='LR')  # On définit l'attribut APRES l'init
            
            g.node('O', 'OPERATIONS')
            g.node('F', 'FLOTTEURS')
            g.node('H', 'HUMAINS')
            g.edge('O', 'F', '1-N')
            g.edge('O', 'H', '1-N')
            st.graphviz_chart(g)
        else:
            st.info("Graphviz non installé.")

if __name__ == "__main__":
    main()
