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

def run_query(query, params=None):
    try:
        with engine.begin() as conn:
            conn.execute(text(query), params or {})
        return True, "Succès"
    except Exception as e:
        return False, str(e)

def load_table(table_name):
    """Charge une table complète depuis la base de données."""
    try:
        with engine.connect() as conn:
            # pd.read_sql gère déjà la conversion des types de date/heure de la BDD
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        return df
    except Exception as e:
        st.error(f"Erreur de lecture de la table '{table_name}': {e}")
        return pd.DataFrame()

def get_smart_dropdown_list():
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

            df["label"] = df.apply(
                lambda x: f"{x['operation_id']} | {str(x['date_heure_reception_alerte'])[:10]} | {x['cross']} | {x['evenement']}",
                axis=1
            )
            return df
    except Exception:
        return pd.DataFrame()

def get_one_operation(op_id):
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM operations WHERE operation_id = :id"), conn, params={"id": op_id})
        return df.iloc[0] if not df.empty else None

def main():
    st.sidebar.title("⚓ SeCMAR Manager")
    menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "🔎 Explorateur", "🛠️ Gestion (CRUD)", "📜 Audit"])

    if menu == "📊 Dashboard":
        st.title("📊 Vue d'ensemble")
        df = load_table("operations")

        if not df.empty:
            c1, c2 = st.columns(2)
            c1.metric("Opérations", len(df))
            if "date_heure_reception_alerte" in df.columns:
                last = df["date_heure_reception_alerte"].max()
                c2.metric("Dernière Opération", last.strftime("%d/%m/%Y") if pd.notnull(last) else "N/A")
            else:
                c2.metric("Dernière Opération", "N/A")

            if "cross" in df.columns:
                st.plotly_chart(px.pie(df, names="cross", title="Répartition par CROSS"))

        else:
            st.warning("Aucune donnée. Lance 'python -m src.load_local'.")

    elif menu == "🔎 Explorateur":
        st.title("🔎 Données (tables)")
        t = st.selectbox("Table", ["operations", "flotteurs", "resultats_humain", "operations_stats", "audit_operations"])
        st.dataframe(load_table(t), use_container_width=True)

    elif menu == "🛠️ Gestion (CRUD)":
        st.title("🛠️ Gestion des Opérations")
        df_smart = get_smart_dropdown_list()

        tab1, tab2, tab3 = st.tabs(["➕ Créer", "✏️ Modifier", "🗑️ Supprimer"])

        # CREATE
        with tab1:
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

        # UPDATE
        with tab2:
            st.subheader("Modifier")
            if df_smart.empty:
                st.warning("Aucune donnée.")
            else:
                sel = st.selectbox("Rechercher (ID | Date | CROSS)", df_smart["label"], key="upd_sel")
                oid = int(sel.split(" | ")[0])
                data = get_one_operation(oid)

                if data is not None:
                    with st.form("upd"):
                        c1, c2 = st.columns(2)

                        d_val = data.get("date_heure_reception_alerte")
                        if pd.isnull(d_val):
                            d_val = datetime.now().date()
                        elif hasattr(d_val, "date"):
                            d_val = d_val.date()

                        new_date = c1.date_input("Date", value=d_val)
                        new_evt = c2.text_input("Événement", value=data.get("evenement", ""))
                        new_cross = c1.selectbox(
                            "CROSS",
                            ["Etel", "Corsen", "Jobourg", "Gris-Nez", "La Garde", "Antilles-Guyane", "La Réunion", "Lagarde"],
                            index=0
                        )

                        if st.form_submit_button("Valider"):
                            sql = """UPDATE operations
                                     SET evenement=:evt, "cross"=:cr, date_heure_reception_alerte=:dt
                                     WHERE operation_id=:id"""
                            ok, msg = run_query(sql, {"evt": new_evt, "cr": new_cross, "dt": new_date, "id": oid})
                            if ok:
                                st.success("Mise à jour OK !")
                                st.rerun()
                            else:
                                st.error(msg)

        # DELETE
        with tab3:
            st.subheader("Supprimer")
            if not df_smart.empty:
                sel_del = st.selectbox("Rechercher à supprimer", df_smart["label"], key="del_sel")
                did = int(sel_del.split(" | ")[0])
                data_del = get_one_operation(did)

                if data_del is not None:
                    st.warning(f"Vous allez supprimer l'opération {did} ({data_del.get('evenement','')})")
                    if st.button("🔥 Confirmer Suppression"):
                        ok, msg = run_query("DELETE FROM operations WHERE operation_id = :id", {"id": did})
                        if ok:
                            st.success("Supprimé.")
                            st.rerun()
                        else:
                            st.error(msg)

    elif menu == "📜 Audit":
        st.title("📜 Historique des transactions (Audit)")
        st.caption("Insert / Update / Delete sur operations (triggers PostgreSQL).")

        try:
            with engine.connect() as conn:
                df_a = pd.read_sql("""
                    SELECT audit_id, changed_at, changed_by, action, operation_id, old_row, new_row
                    FROM audit_operations
                    ORDER BY changed_at DESC
                    LIMIT 200
                """, conn)

            if df_a.empty:
                st.info("Aucune transaction auditée pour le moment.")
            else:
                st.dataframe(df_a, use_container_width=True)
        except Exception as e:
            st.error(f"Impossible de lire audit_operations : {e}")
            st.info("Vérifie que load_local.py a bien appliqué references/audit_operations/audit_operations.sql")

if __name__ == "__main__":
    main()