import pytest
from timi_stemi import calculate_metrics, process_batch


def test_timi_stemi_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_timi_stemi_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_calculate_metrics_empty():
    """Test calculate_metrics with no numeric inputs returns default."""
    res = calculate_metrics(name="test", label="abc")
    assert res["score"] == 1.0
    assert res["classification"] == "Low / Standard"


def test_calculate_metrics_single_value():
    """Test calculate_metrics with a single numeric value."""
    res = calculate_metrics(v1=30.0)
    assert res["score"] == 30.0
    assert res["classification"] == "High / Severe"


def test_calculate_metrics_moderate_tier():
    """Test calculate_metrics produces moderate classification."""
    res = calculate_metrics(v1=15.0, v2=5.0)
    assert res["classification"] == "Moderate / Intermediate"


def test_calculate_metrics_with_none_values():
    """Test calculate_metrics handles None values gracefully."""
    res = calculate_metrics(v1=10.0, v2=None, v3=5.0)
    assert res["score"] > 0
    assert res["inputs_evaluated"] == 2


def test_process_batch_empty_file(tmp_path):
    """Test process_batch raises ValueError for empty CSV."""
    csv_in = tmp_path / "empty.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        process_batch(str(csv_in), str(csv_out))


def test_process_batch_no_data_rows(tmp_path):
    """Test process_batch raises ValueError for CSV with headers only."""
    csv_in = tmp_path / "headers_only.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no data rows"):
        process_batch(str(csv_in), str(csv_out))


def test_process_batch_missing_file(tmp_path):
    """Test process_batch raises FileNotFoundError for missing input."""
    csv_out = tmp_path / "out.csv"

    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "nonexistent.csv"), str(csv_out))


def test_process_batch_path_traversal(tmp_path):
    """Test process_batch rejects path traversal attempts."""
    csv_out = tmp_path / "out.csv"

    with pytest.raises((ValueError, FileNotFoundError)):
        process_batch("../../etc/passwd", str(csv_out))
