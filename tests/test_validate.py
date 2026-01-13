import pytest
import pandas as pd
from src import validate
from src.schemas import OperationsSchema

def test_validate_split_logic(tmp_path, monkeypatch):
    """
    Test d'intégration : Vérifie que validate.py sépare bien 
    les bonnes lignes des mauvaises.
    """
    # 1. Préparation des faux dossiers
    mock_input = tmp_path / "data" / "normalize"
    mock_processed = tmp_path / "data" / "processed"
    mock_rejects = tmp_path / "data" / "rejects"
    
    for p in [mock_input, mock_processed, mock_rejects]:
        p.mkdir(parents=True)

    # 2. Mock des chemins dans le module validate
    monkeypatch.setattr(validate, "INPUT_DIR", mock_input)
    monkeypatch.setattr(validate, "PROCESSED_DIR", mock_processed)
    monkeypatch.setattr(validate, "REJECTS_DIR", mock_rejects)

    # 3. Création d'un CSV complet (pour éviter l'erreur de colonnes manquantes)
    # Ligne 1 (ID 100) : OK (2024)
    # Ligne 2 (ID 101) : KO (1995 -> Trop vieux)
    df = pd.DataFrame({
        "operation_id": [100, 101],
        "latitude": [45.0, 45.0], 
        "longitude": [-1.0, -1.0],
        "date_heure_reception_alerte": ["2024-01-01 12:00:00", "1995-01-01 12:00:00"],
        # Colonnes bouche-trou pour satisfaire le schéma
        "type_operation": [None, None], "pourquoi_alerte": [None, None],
        "moyen_alerte": [None, None], "qui_alerte": [None, None],
        "categorie_qui_alerte": [None, None], "cross": [None, None],
        "departement": [None, None], "est_metropolitain": [None, None],
        "evenement": [None, None], "categorie_evenement": [None, None],
        "autorite": [None, None], "seconde_autorite": [None, None],
        "zone_responsabilite": [None, None], "vent_direction": [None, None],
        "vent_direction_categorie": [None, None], "vent_force": [None, None],
        "mer_force": [None, None], "date_heure_fin_operation": [None, None],
        "numero_sitrep": [None, None], "cross_sitrep": [None, None],
        "fuseau_horaire": [None, None], "systeme_source": [None, None]
    })
    
    # On sauvegarde le fichier "normalisé" fictif
    filename = "operations_normalized.csv" 
    df.to_csv(mock_input / filename, index=False)

    # 4. Exécution
    # On passe "operations.csv" car le script ajoute lui-même "_normalized"
    validate.validate_and_split("operations.csv", OperationsSchema)

    # 5. Vérifications
    # ATTENTION : Noms corrigés ici (_validated / _rejected)
    valid_file = mock_processed / "operations_validated.csv"
    reject_file = mock_rejects / "operations_rejected.csv"

    assert valid_file.exists(), "Le fichier validé n'a pas été créé"
    assert reject_file.exists(), "Le fichier rejeté n'a pas été créé"

    # Vérifie le contenu
    df_valid = pd.read_csv(valid_file)
    df_reject = pd.read_csv(reject_file)

    assert len(df_valid) == 1, "Il devrait y avoir 1 ligne valide (2024)"
    assert df_valid.iloc[0]["operation_id"] == 100

    assert len(df_reject) == 1, "Il devrait y avoir 1 ligne rejetée (1995)"
    assert df_reject.iloc[0]["operation_id"] == 101