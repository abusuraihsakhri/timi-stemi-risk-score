"""Clinical reference cases and CSV/CLI regression tests for TIMI STEMI."""
import csv
import math
import subprocess
import sys

import pytest
from timi_stemi import calculate_metrics, process_batch

LOW = dict(
    age=64, diabetes_hypertension_angina=False, systolic_bp=100,
    heart_rate=100, killip_class=1, weight_kg=67,
    anterior_st_elevation_or_lbbb=False, time_to_treatment_hours=4,
)


def score(**changes):
    return calculate_metrics(**{**LOW, **changes})


@pytest.mark.parametrize(("age", "points"), [(0, 0), (64, 0), (65, 2), (74, 2), (75, 3), (100, 3)])
def test_age_bands(age, points):
    assert score(age=age)["score"] == points


@pytest.mark.parametrize(("factor", "change", "points"), [
    ("diabetes_hypertension_angina", True, 1),
    ("systolic_bp", 99.99, 3),
    ("heart_rate", 100.01, 2),
    ("killip_class", 2, 2),
    ("weight_kg", 66.99, 1),
    ("anterior_st_elevation_or_lbbb", True, 1),
    ("time_to_treatment_hours", 4.01, 1),
])
def test_each_predictor(factor, change, points):
    assert score(**{factor: change})["score"] == points


def test_score_boundaries_and_full_range():
    assert score()["score"] == 0
    assert score()["mortality_30_day_percent"] == 0.8
    maximum = score(age=75, diabetes_hypertension_angina=True, systolic_bp=99,
                    heart_rate=101, killip_class=4, weight_kg=66,
                    anterior_st_elevation_or_lbbb=True, time_to_treatment_hours=5)
    assert maximum["score"] == 14
    assert sum(maximum["points"].values()) == 14
    assert maximum["mortality_30_day_percent"] == 35.9


@pytest.mark.parametrize(("point_score", "expected"), [
    (0, 0.8), (1, 1.6), (2, 2.2), (3, 4.4), (4, 7.3),
    (5, 12.4), (6, 16.1), (7, 23.4), (8, 26.8),
])
def test_original_mortality_table(point_score, expected):
    from timi_stemi import MORTALITY_30_DAY_PERCENT
    assert MORTALITY_30_DAY_PERCENT[point_score] == expected


@pytest.mark.parametrize("changes", [
    {"age": -1}, {"age": 65.5}, {"killip_class": 5}, {"systolic_bp": 0},
    {"heart_rate": float("inf")}, {"weight_kg": float("nan")},
    {"time_to_treatment_hours": -1}, {"diabetes_hypertension_angina": "maybe"},
    {"anterior_st_elevation_or_lbbb": None},
])
def test_invalid_inputs_rejected(changes):
    with pytest.raises(ValueError):
        score(**changes)


def test_missing_required_inputs_rejected():
    with pytest.raises(TypeError):
        calculate_metrics(age=60)


def test_batch_reads_named_columns_and_preserves_metadata(tmp_path):
    inp = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    header = list(LOW) + ["study_id"]
    with inp.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()
        writer.writerow({**LOW, "study_id": "CASE_A"})
        writer.writerow({**LOW, "age": 75, "systolic_bp": 80, "study_id": "CASE_B"})
    process_batch(str(inp), str(out))
    with out.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["study_id"] == "CASE_A"
    assert rows[0]["score"] == "0"
    assert rows[1]["score"] == "6"
    assert rows[1]["mortality_30_day_percent"] == "16.1"


def test_batch_rejects_bad_row_without_output(tmp_path):
    inp = tmp_path / "bad.csv"
    out = tmp_path / "out.csv"
    inp.write_text("age,systolic_bp\n70,90\n")
    with pytest.raises(ValueError, match="row 2.*missing"):
        process_batch(str(inp), str(out))
    assert not out.exists()


def test_batch_empty_file(tmp_path):
    inp = tmp_path / "empty.csv"
    inp.write_text("")
    with pytest.raises(ValueError, match="empty"):
        process_batch(str(inp), str(tmp_path / "out.csv"))


def test_batch_header_only(tmp_path):
    inp = tmp_path / "header.csv"
    inp.write_text(",".join(LOW) + "\n")
    with pytest.raises(ValueError, match="no data rows"):
        process_batch(str(inp), str(tmp_path / "out.csv"))


def test_batch_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "missing.csv"), str(tmp_path / "out.csv"))


def test_batch_refuses_overwrite(tmp_path):
    inp = tmp_path / "in.csv"
    inp.write_text("value\n1\n")
    with pytest.raises(ValueError, match="differ"):
        process_batch(str(inp), str(inp))


def test_csv_formula_injection_escaped(tmp_path):
    inp = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    with inp.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[*LOW, "note"])
        writer.writeheader()
        writer.writerow({**LOW, "note": "=2+2"})
    process_batch(str(inp), str(out))
    with out.open(newline="", encoding="utf-8") as file:
        row = next(csv.DictReader(file))
    assert row["note"] == "'=2+2"


def test_cli_single(tmp_path):
    import io
    from contextlib import redirect_stdout
    from timi_stemi import main
    args = ["single", "--age", "75", "--sbp", "90", "--heart-rate", "100",
            "--killip", "1", "--weight", "80", "--time-to-treatment", "4"]
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        main(args)
    import json
    assert json.loads(stdout.getvalue())["score"] == 6
