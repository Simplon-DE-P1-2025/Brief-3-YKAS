import pytest
import pandas as pd
from src import process
from src.schemas import OperationsSchema

def test_process_file_nominal(tmp_path, monkeypatch):
    mock_raw = tmp_path / "data" / "raw"
    mock_processed = tmp_path / "data" / "processed"
    mock_rejects = tmp_path / "data" / "rejects"

    mock_raw.mkdir(parents=True)
    mock_processed.mkdir(parents=True)
    mock_rejects.mkdir(parents=True)

    monkeypatch.setattr(process, "RAW_DIR", mock_raw)
    monkeypatch.setattr(process, "PROCESSED_DIR", mock_processed)
    monkeypatch.setattr(process, "REJECTS_DIR", mock_rejects)

    # DataFrame avec TOUTES les colonnes requises par OperationsSchema
    # On met des valeurs valides pour les champs contrôlés par 'isin'
    df_data = pd.DataFrame({
        "operation_id": [1, 2],
        "type_operation": ["SAR", "SAR"],
        "moyen_alerte": ["VHF phonie", "Téléphone mobile à terre"],
        "qui_alerte": ["Témoin", "Famille / Proche"],
        "categorie_qui_alerte": ["Organisme ou personne privée", "Organisme ou personne privée"],
        "cross": ["Etel", "Corsen"],
        "departement": ["56", "29"],
        "est_metropolitain": [True, True],
        "evenement": ["Autre événement", "Baignade"],
        "categorie_evenement": ["Autres affaires nécessitant opération", "Accidents individuels à personnes"],
        "autorite": ["Préfet maritime", "Préfet maritime"],
        "seconde_autorite": [None, None],
        "zone_responsabilite": ["Eaux territoriales", "Plage et 300 mètres"],
        "latitude": [45.0, 48.0],
        "longitude": [-1.0, -4.5],
        "vent_direction": [None, None],
        "vent_direction_categorie": [None, None],
        "vent_force": [None, None],
        "mer_force": [None, None],
        "date_heure_reception_alerte": ["2024-01-01 12:00:00", "2024-01-01 12:00:00"],
        "date_heure_fin_operation": ["2024-01-01 14:00:00", "2024-01-01 14:00:00"],
        "numero_sitrep": [None, None],
        "cross_sitrep": [None, None],
        "fuseau_horaire": [None, None],
        "systeme_source": [None, None],
        "pourquoi_alerte": [None, None]
    })

    test_filename = "operations.csv"
    df_data.to_csv(mock_raw / test_filename, index=False)

    process.process_file(test_filename, OperationsSchema)

    processed_file = mock_processed / "operations_processed.csv"
    assert processed_file.exists(), "Le fichier processed n'a pas été créé !"
    
    # Vérification optionnelle : s'assurer que les lignes ont été conservées
    df_result = pd.read_csv(processed_file)
    assert len(df_result) == 2, "Les lignes valides n'ont pas été sauvegardées dans processed"


def test_process_file_missing(tmp_path, monkeypatch):
    """Test le cas où le fichier source n'existe pas."""
    mock_raw = tmp_path / "data" / "raw"
    mock_raw.mkdir(parents=True)
    
    monkeypatch.setattr(process, "RAW_DIR", mock_raw)
    
    # On ne crée pas le fichier CSV ici
    
    # Vérifie que la fonction gère l'erreur proprement (pas de crash)
    try:
        process.process_file("missing.csv", OperationsSchema)
    except FileNotFoundError:
        pytest.fail("La fonction ne devrait pas lever FileNotFoundError mais le gérer.")
    except Exception as e:
        # Selon votre implémentation, vous pouvez vouloir laisser passer ou non
        # Si votre code fait juste un print("Erreur"), ça passera.
        pass