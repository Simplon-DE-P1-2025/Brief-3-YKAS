import pytest
from src.normalize import normalize_text

class TestNormalize:
    
    def test_normalize_basic(self):
        """Vérifie la mise en minuscule et suppression d'espaces."""
        raw = "  BONJOUR   "
        expected = "bonjour"
        assert normalize_text(raw) == expected

    def test_normalize_accents(self):
        """Vérifie la suppression des accents."""
        raw = "Hélène à la Pêche"
        expected = "helene a la peche"
        assert normalize_text(raw) == expected

    def test_normalize_mixed(self):
        """Test complet."""
        raw = "  Ça Vâ Être Propre !  "
        # Le '!' reste, le 'ç' devient 'c', le 'â' devient 'a'
        expected = "ca va etre propre !" 
        assert normalize_text(raw) == expected

    def test_normalize_non_string(self):
        """Vérifie que les nombres ou None ne plantent pas."""
        assert normalize_text(None) is None
        assert normalize_text(123) == 123