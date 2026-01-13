import pytest
import pandas as pd
import pandera as pa
from datetime import datetime
from src.schemas import OperationsSchema, ResultatsHumainSchema

class TestSchemas:

    def _get_base_operation_df(self):
        """
        Helper pour créer un DataFrame Opérations avec toutes les colonnes requises par le schéma.
        Valeurs par défaut : None (car nullable=True pour la plupart).
        """
        return pd.DataFrame({
            "operation_id": [1],
            # Champs obligatoires (nullable=False)
            "latitude": [45.0], 
            "longitude": [-1.0],
            # Champs optionnels (nullable=True) mais qui doivent exister
            "type_operation": [None],
            "pourquoi_alerte": [None],
            "moyen_alerte": [None],
            "qui_alerte": [None],
            "categorie_qui_alerte": [None],
            "cross": [None],
            "departement": [None],
            "est_metropolitain": [None],
            "evenement": [None],
            "categorie_evenement": [None],
            "autorite": [None],
            "seconde_autorite": [None],
            "zone_responsabilite": [None],
            "vent_direction": [None],
            "vent_direction_categorie": [None],
            "vent_force": [None],
            "mer_force": [None],
            "date_heure_reception_alerte": [pd.to_datetime("2024-01-01")], # Valeur par défaut valide
            "date_heure_fin_operation": [None],
            "numero_sitrep": [None],
            "cross_sitrep": [None],
            "fuseau_horaire": [None],
            "systeme_source": [None]
        })

    # --- TESTS OPÉRATIONS ---
    def test_operations_date_valide(self):
        """Une date en 2024 doit passer."""
        df = self._get_base_operation_df()
        # Le DF de base a déjà une date en 2024, donc ça doit passer
        OperationsSchema.validate(df)

    def test_operations_date_trop_vielle(self):
        """Une date en 1990 doit échouer (Règle > 2000)."""
        df = self._get_base_operation_df()
        df["date_heure_reception_alerte"] = pd.to_datetime("1990-01-01")
        
        with pytest.raises(pa.errors.SchemaErrors):
            OperationsSchema.validate(df, lazy=True)

    def test_operations_gps_manquant(self):
        """Pas de GPS = Rejet (nullable=False)."""
        df = self._get_base_operation_df()
        df["latitude"] = [None] # Interdit !
        
        with pytest.raises(pa.errors.SchemaErrors):
            OperationsSchema.validate(df, lazy=True)

    # --- TESTS RÉSULTATS HUMAINS ---
    def test_humain_logique_ko(self):
        """Impossible d'avoir plus de blessés que de personnes impliquées."""
        # Ici le schéma est plus petit, on peut définir le DF directement
        df = pd.DataFrame({
            "operation_id": [1],
            "nombre": [2],              # 2 personnes
            "dont_nombre_blesse": [5],  # 5 blessés ?! -> Erreur
            # Colonnes manquantes ajoutées pour satisfaire le schéma
            "resultat_humain": ["inconnu"],
            "categorie_personne": ["plaisancier"]
        })
        with pytest.raises(pa.errors.SchemaErrors):
            ResultatsHumainSchema.validate(df, lazy=True)