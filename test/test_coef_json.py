import json
import pytest
import sys
import os

sys.path.append("..")
sys.path.append(".")
import airiana_core


# Sample coefficient data for testing
SAMPLE_COEF = {0: {10: 1.5, 20: 2.5}, 1: {5: 0.8}, 2: {}, 3: {15: 3.2}}


class TestLoadCoefJson:
    """Tests for load_coef_json() function."""

    def test_load_valid_file(self, tmp_path):
        """Test loading a properly formatted JSON file with nested int keys."""
        # Create a temporary JSON file
        test_file = tmp_path / "coef_test.json"
        data = {"0": {"10": 1.5, "20": 2.5}, "1": {"5": 0.8}, "2": {}, "3": {"15": 3.2}}
        with open(test_file, "w") as f:
            json.dump(data, f)

        # Load and verify
        result = airiana_core.load_coef_json(str(test_file))
        assert result == SAMPLE_COEF
        assert isinstance(result, dict)
        assert all(isinstance(k, int) for k in result.keys())
        assert all(isinstance(dk, int) for v in result.values() for dk in v.keys())

    def test_load_file_not_found(self, tmp_path):
        """Test that missing file returns default structure."""
        nonexistent_file = tmp_path / "does_not_exist.json"
        result = airiana_core.load_coef_json(str(nonexistent_file))

        # Should return default structure
        assert result == {0: {}, 1: {}, 2: {}, 3: {}}

    def test_load_invalid_json(self, tmp_path):
        """Test that corrupted JSON returns default structure."""
        bad_file = tmp_path / "bad.json"
        with open(bad_file, "w") as f:
            f.write("{ this is not valid json }")

        result = airiana_core.load_coef_json(str(bad_file))
        assert result == {0: {}, 1: {}, 2: {}, 3: {}}

    def test_load_type_conversion(self, tmp_path):
        """Test that string keys/values convert to int/float correctly."""
        test_file = tmp_path / "types_test.json"
        # JSON stores all keys as strings
        data = {"0": {"100": 5.5, "200": 10.25}, "1": {}, "2": {}, "3": {}}
        with open(test_file, "w") as f:
            json.dump(data, f)

        result = airiana_core.load_coef_json(str(test_file))

        # Verify all keys are integers
        assert result[0][100] == 5.5
        assert result[0][200] == 10.25
        assert isinstance(result[0][100], float)

    def test_load_default_filename(self, tmp_path, monkeypatch):
        """Test that default parameter 'coeficients.json' is used."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create the default filename
        test_data = {"0": {}, "1": {}, "2": {}, "3": {}}
        with open("coeficients.json", "w") as f:
            json.dump(test_data, f)

        # Call without filename parameter
        result = airiana_core.load_coef_json()
        assert result == {0: {}, 1: {}, 2: {}, 3: {}}

    def test_load_empty_file(self, tmp_path):
        """Test that empty JSON object returns default structure."""
        test_file = tmp_path / "empty.json"
        with open(test_file, "w") as f:
            json.dump({}, f)

        result = airiana_core.load_coef_json(str(test_file))
        assert result == {}

    def test_load_preserves_nested_values(self, tmp_path):
        """Test that nested values are preserved accurately."""
        test_file = tmp_path / "nested_test.json"
        data = {"0": {"10": 1.5, "20": 2.5, "30": 3.7}, "1": {"5": 0.8, "15": 1.2}}
        with open(test_file, "w") as f:
            json.dump(data, f)

        result = airiana_core.load_coef_json(str(test_file))
        assert result[0][10] == 1.5
        assert result[0][20] == 2.5
        assert result[0][30] == 3.7
        assert result[1][5] == 0.8
        assert result[1][15] == 1.2


class TestSaveCoefJson:
    """Tests for save_coef_json() function."""

    def test_save_valid_data(self, tmp_path):
        """Test saving a valid coefficient dictionary to file."""
        test_file = tmp_path / "save_test.json"
        airiana_core.save_coef_json(SAMPLE_COEF, str(test_file))

        # Verify file exists and contains valid JSON
        assert test_file.exists()
        with open(test_file, "r") as f:
            loaded_data = json.load(f)
        assert loaded_data is not None

    def test_save_key_conversion(self, tmp_path):
        """Test that integer keys are converted to strings in JSON output."""
        test_file = tmp_path / "keys_test.json"
        airiana_core.save_coef_json(SAMPLE_COEF, str(test_file))

        with open(test_file, "r") as f:
            data = json.load(f)

        # JSON should have string keys
        assert all(isinstance(k, str) for k in data.keys())
        for nested_dict in data.values():
            assert all(isinstance(k, str) for k in nested_dict.keys())

    def test_save_file_formatting(self, tmp_path):
        """Test that file is created with correct JSON formatting."""
        test_file = tmp_path / "format_test.json"
        airiana_core.save_coef_json(SAMPLE_COEF, str(test_file))

        with open(test_file, "r") as f:
            content = f.read()

        # Verify it's properly indented
        assert "  " in content  # Should have indentation
        data = json.loads(content)
        assert data is not None

    def test_save_default_filename(self, tmp_path, monkeypatch):
        """Test that default parameter 'coeficients.json' is used."""
        monkeypatch.chdir(tmp_path)
        airiana_core.save_coef_json(SAMPLE_COEF)

        # Verify default file was created
        assert os.path.exists("coeficients.json")
        with open("coeficients.json", "r") as f:
            data = json.load(f)
        assert data is not None

    def test_save_empty_dict(self, tmp_path):
        """Test saving an empty coefficient dictionary."""
        test_file = tmp_path / "empty_save.json"
        empty_coef = {0: {}, 1: {}, 2: {}, 3: {}}
        airiana_core.save_coef_json(empty_coef, str(test_file))

        assert test_file.exists()
        with open(test_file, "r") as f:
            data = json.load(f)
        assert data == {"0": {}, "1": {}, "2": {}, "3": {}}

    def test_save_overwrites_existing(self, tmp_path):
        """Test that save overwrites existing file."""
        test_file = tmp_path / "overwrite_test.json"

        # Save initial data
        initial = {0: {1: 1.0}, 1: {}, 2: {}, 3: {}}
        airiana_core.save_coef_json(initial, str(test_file))

        # Save new data
        updated = {0: {1: 2.0, 2: 3.0}, 1: {}, 2: {}, 3: {}}
        airiana_core.save_coef_json(updated, str(test_file))

        # Verify only new data exists
        with open(test_file, "r") as f:
            data = json.load(f)
        assert float(data["0"]["1"]) == 2.0
        assert float(data["0"]["2"]) == 3.0


class TestCoefJsonRoundtrip:
    """Tests for save and load working together."""

    def test_save_load_roundtrip(self, tmp_path):
        """Test that save followed by load returns original data."""
        test_file = tmp_path / "roundtrip_test.json"

        # Save original data
        airiana_core.save_coef_json(SAMPLE_COEF, str(test_file))

        # Load it back
        result = airiana_core.load_coef_json(str(test_file))

        # Should match original
        assert result == SAMPLE_COEF

    def test_roundtrip_preserves_types(self, tmp_path):
        """Test that roundtrip preserves numeric types correctly."""
        test_file = tmp_path / "types_roundtrip.json"
        original = {0: {10: 1.5, 20: 2.0}, 1: {5: 0.8}, 2: {}, 3: {}}

        airiana_core.save_coef_json(original, str(test_file))
        result = airiana_core.load_coef_json(str(test_file))

        # Verify types
        assert isinstance(result[0][10], float)
        assert result[0][10] == 1.5
        assert result[0][20] == 2.0

    def test_roundtrip_with_complex_data(self, tmp_path):
        """Test roundtrip with more complex nested structure."""
        test_file = tmp_path / "complex_roundtrip.json"
        complex_data = {
            0: {10: 1.1, 20: 2.2, 30: 3.3, 40: 4.4},
            1: {5: 0.5, 15: 1.5, 25: 2.5},
            2: {100: 10.0},
            3: {50: 5.0, 60: 6.0, 70: 7.0},
        }

        airiana_core.save_coef_json(complex_data, str(test_file))
        result = airiana_core.load_coef_json(str(test_file))

        assert result == complex_data
