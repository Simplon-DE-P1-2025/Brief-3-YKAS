import pytest
import pandas as pd
import pandera.pandas as pa 
from datetime import datetime
from src.schemas import (
    OperationsSchema, 
    FlotteursSchema, 
    ResultatsHumainSchema, 
    OperationsStatsSchema
)

class TestSchemas:
    
    # --- 1. Test Operations ---
    def test_operations_schema_valid(self):
        """Vérifie qu'une opération correcte passe."""
        data = pd.DataFrame({
            "operation_id": [1],
            "type_operation": ["SAR"],
            "pourquoi_alerte": ["Test"],
            "moyen_alerte": ["Tel"],
            "latitude": [45.0],
            "longitude": [-1.0],
            "date_heure_reception_alerte": ["2024-01-01 12:00:00"],
            "date_heure_fin_operation": ["2024-01-01 14:00:00"],
        })
        OperationsSchema.validate(data)

    def test_operations_schema_invalid_geo(self):
        """Vérifie que la latitude > 90 est rejetée."""
        data = pd.DataFrame({
            "operation_id": [1],
            "latitude": [150.0],
            "moyen_alerte": ["X"],
            "date_heure_reception_alerte": ["2024-01-01 12:00:00"],
            "date_heure_fin_operation": ["2024-01-01 14:00:00"],
        })
        with pytest.raises(pa.errors.SchemaErrors):
            OperationsSchema.validate(data, lazy=True)

    def test_flotteurs_schema_valid(self):
        data = pd.DataFrame({
            "operation_id": [10],
            "numero_ordre": [1],
            "type_flotteur": ["Plaisance"],
        })
        FlotteursSchema.validate(data)

    def test_flotteurs_schema_invalid_regex(self):
        data = pd.DataFrame({
            "operation_id": [10],
            "numero_ordre": [1],
            "type_flotteur": ["Bateau@#!"],
        })
        with pytest.raises(pa.errors.SchemaErrors):
            FlotteursSchema.validate(data, lazy=True)

    def test_resultats_humain_invalid_negatif(self):
        data = pd.DataFrame({
            "operation_id": [1],
            "categorie_personne": ["Pêcheur"],
            "resultat_humain": ["Sauvé"],
            "nombre": [-5], # Impossible (négatif)
            "dont_nombre_blesse": [0]
        })
        with pytest.raises(pa.errors.SchemaErrors):
            ResultatsHumainSchema.validate(data, lazy=True)

    # --- 4. Test Stats ---
    def test_stats_schema_enum_valid(self):
        """Vérifie que les données statistiques passent."""
        data = pd.DataFrame({
            "operation_id": [99],
            "date": ["2024-01-01"],
            "annee": [2024],
            "mois": [1],
            "jour": [1],
            "mois_texte": ["Janvier"],
            "jour_semaine": ["Lundi"],
            "phase_journee": ["matinée"],
            "est_weekend": [False],
            "est_jour_ferie": [True],
            "concerne_plongee": [False],
            "distance_cote_milles_nautiques": [10.5], 
            "maree_coefficient": [95],
            "nombre_personnes_blessees": [0],
            "nombre_personnes_assistees": [0],
            "nombre_personnes_decedees": [0],
            "nombre_personnes_disparues": [0],
            "nombre_personnes_secourues": [0],
            "nombre_personnes_impliquees": [0],
            "nombre_flotteurs_plaisance_impliques": [0],
            "nombre_flotteurs_commerce_impliques": [0],
            "nombre_flotteurs_peche_impliques": [0],
        })
        OperationsStatsSchema.validate(data)

    def test_stats_schema_enum_invalid(self):
        """Vérifie qu'un mois inconnu est rejeté."""
        data = pd.DataFrame({
            "operation_id": [99],
            "date": ["2024-01-01"],
            "annee": [2024],
            "mois": [1],
            "jour": [1],
            "mois_texte": ["MoisInconnu"], 
            "jour_semaine": ["Lundi"],
            "phase_journee": ["matinée"],
            "est_weekend": [False],
            "est_jour_ferie": [False],
            "concerne_plongee": [False],
            "distance_cote_milles_nautiques": [10.5],
            "maree_coefficient": [95],
            "nombre_personnes_blessees": [0],
            "nombre_personnes_assistees": [0],
            "nombre_personnes_decedees": [0],
            "nombre_personnes_disparues": [0],
            "nombre_personnes_secourues": [0],
            "nombre_personnes_impliquees": [0],
            "nombre_flotteurs_plaisance_impliques": [0],
            "nombre_flotteurs_commerce_impliques": [0],
            "nombre_flotteurs_peche_impliques": [0],
        })
        with pytest.raises(pa.errors.SchemaErrors):
            OperationsStatsSchema.validate(data, lazy=True)