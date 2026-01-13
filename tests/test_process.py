import pytest
import pandas as pd
import shutil
from pathlib import Path
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
    
    df_data = pd.DataFrame({
        "operation_id": [1, 2],
        "type_operation": ["SAR", "SAR"],
        "moyen_alerte": ["VHF", "Tel"],
        "latitude": [45.0, 200.0],  
        "longitude": [-1.0, -1.0],
        "date_heure_reception_alerte": ["2024-01-01 12:00:00", "2024-01-01 12:00:00"],
        "date_heure_fin_operation": ["2024-01-01 14:00:00", "2024-01-01 14:00:00"]
    })
    
    test_filename = "operations.csv"
    df_data.to_csv(mock_raw / test_filename, index=False)
    
    process.process_file(test_filename, OperationsSchema)
    
    
    processed_file = mock_processed / "operations_processed.csv"
    assert processed_file.exists(), "Le fichier processed n'a pas été créé !"
    
    df_valid = pd.read_csv(processed_file)
    assert len(df_valid) == 1, "Il devrait y avoir exactement 1 ligne valide."
    assert df_valid.iloc[0]["operation_id"] == 1
    
    rejects_file = mock_rejects / "rejects_operations.csv"
    assert rejects_file.exists(), "Le fichier rejects n'a pas été créé !"
    
    df_reject = pd.read_csv(rejects_file)
    assert len(df_reject) == 1, "Il devrait y avoir exactement 1 ligne rejetée."
    assert df_reject.iloc[0]["operation_id"] == 2

def test_process_file_missing(tmp_path, monkeypatch, capsys):
    mock_raw = tmp_path / "raw"
    mock_raw.mkdir()
    monkeypatch.setattr(process, "RAW_DIR", mock_raw)
    
    process.process_file("fantome.csv", OperationsSchema)
    
    captured = capsys.readouterr()
    assert "[WARN] Fichier introuvable" in captured.out