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
            "moyen_alerte": ["VHF phonie"],
            "qui_alerte": ["Témoin"],
            "categorie_qui_alerte": ["Organisme ou personne privée"],
            "cross": ["Etel"],
            "departement": ["56"],
            "est_metropolitain": [True],
            "evenement": ["Autre événement"],
            "categorie_evenement": ["Autres affaires nécessitant opération"],
            "autorite": ["Préfet maritime"],
            "seconde_autorite": [None],
            "zone_responsabilite": ["Eaux territoriales"],
            "latitude": [45.0],
            "longitude": [-1.0],
            "vent_direction": [None],
            "vent_direction_categorie": [None],
            "vent_force": [None],
            "mer_force": [None],
            "date_heure_reception_alerte": [pd.to_datetime("2024-01-01 12:00:00")],
            "date_heure_fin_operation": [pd.to_datetime("2024-01-01 14:00:00")],
            "numero_sitrep": [None],
            "cross_sitrep": [None],
            "fuseau_horaire": [None],
            "systeme_source": [None]
        })
        OperationsSchema.validate(data)

    def test_operations_schema_invalid_geo(self):
        """Vérifie que la latitude > 90 est rejetée."""
        data = pd.DataFrame({
            "operation_id": [1],
            "latitude": [150.0], # INVALID
            "longitude": [0.0],
            # Colonnes minimales pour passer le mode strict=False mais structurellement ok
            "date_heure_reception_alerte": [pd.to_datetime("2024-01-01")]
        })
        # Note: Pandera peut lever SchemaErrors ou SchemaError selon la config
        with pytest.raises((pa.errors.SchemaErrors, pa.errors.SchemaError)):
            OperationsSchema.validate(data, lazy=True)

    # --- 2. Test Flotteurs ---
    def test_flotteurs_schema_valid(self):
        data = pd.DataFrame({
            "operation_id": [10],
            "numero_ordre": [1],
            "pavillon": ["Français"],
            "resultat_flotteur": ["Remorqué"],
            "type_flotteur": ["Plaisance à voile"],
            "categorie_flotteur": ["Plaisance"],
            "numero_immatriculation": [None]
        })
        FlotteursSchema.validate(data)

    # --- 3. Test Résultats Humains ---
    def test_resultats_humain_invalid_negatif(self):
        data = pd.DataFrame({
            "operation_id": [1],
            "categorie_personne": ["Pêcheur"],
            "resultat_humain": ["Sauvé"],
            "nombre": [-5], # INVALID
            "dont_nombre_blesse": [0]
        })
        with pytest.raises((pa.errors.SchemaErrors, pa.errors.SchemaError)):
            ResultatsHumainSchema.validate(data, lazy=True)

    # --- 4. Test Stats ---
    def test_stats_schema_valid(self):
        """Vérifie que les données statistiques passent."""
        # On crée un DF minimal avec les colonnes obligatoires
        data = pd.DataFrame({
            "operation_id": [99],
            "date": [pd.to_datetime("2024-01-01")],
            "annee": [2024],
            "mois": [1],
            "jour": [1],
            "mois_texte": ["Janvier"],
            "semaine": [1],
            "annee_semaine": ["2024-01"],
            "jour_semaine": ["Lundi"],
            "phase_journee": ["matinée"],
            # Booléens
            "est_weekend": [False], "est_jour_ferie": [True], "est_vacances_scolaires": [False],
            "concerne_plongee": [False], "implique_wingfoil": [False], "avec_clandestins": [False],
            "est_dans_stm": [False], "est_dans_dst": [False], "sans_flotteur_implique": [False],
            # Floats
            "distance_cote_metres": [0.0], "distance_cote_milles_nautiques": [0.0],
            "maree_coefficient": [90.0],
            # Strings
            "nom_stm": [None], "nom_dst": [None], "prefecture_maritime": [None], 
            "maree_port": [None], "maree_categorie": [None],
            # Ints (Stats) - On en met quelques uns, le schéma strict=False tolère les manquants si non définis obligatoires, 
            # mais ici on a défini les colonnes dans le schéma donc il les faut.
            "nombre_personnes_blessees": [0],
            "nombre_personnes_assistees": [0],
            "nombre_personnes_decedees": [0],
            # ... (Pour abréger le test, on suppose que les autres sont à 0 ou gérés par fillna dans le process réel)
        })
        
        # Pour que le test passe sans lister les 50 colonnes de stats, 
        # on ajoute dynamiquement les colonnes manquantes du schéma avec 0
        for col_name in OperationsStatsSchema.to_schema().columns.keys():
            if col_name not in data.columns:
                data[col_name] = 0
                
        OperationsStatsSchema.validate(data)