import pytest
import tempfile
import requests
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.ingest import download_file

class TestIngest:
    """Test cases for the ingest module."""

    @patch('src.ingest.requests.get')
    def test_download_file_success(self, mock_get):
        """Teste le téléchargement réussi d'un fichier unique."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = MagicMock(return_value=[b"data1", b"data2"])
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            filename = "test.csv"
            
            result = download_file("http://fake.url", tmp_path, filename)

            assert result == tmp_path / filename
            assert result.exists()
            assert result.read_bytes() == b"data1data2"
            assert mock_get.call_count == 1

    @patch('src.ingest.requests.get')
    def test_download_file_failure(self, mock_get):
        """Teste la gestion d'une erreur (ex: 404)."""
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            result = download_file("http://fake.url/missing", tmp_path, "missing.csv")

            assert result is None
            assert len(list(tmp_path.iterdir())) == 0  