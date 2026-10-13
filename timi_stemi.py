#!/usr/bin/env python3
"""TIMI risk score for ST-elevation myocardial infarction (STEMI).

Implements the presentation-time 0–14 point score published by Morrow et al.
(Circulation. 2000;102:2031–2037. doi:10.1161/01.CIR.102.17.2031).
The mortality percentages describe the original InTIME II population and are
not individualized probabilities or treatment recommendations.
"""

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict

PREDICTOR_COLUMNS = (
    "age",
    "diabetes_hypertension_angina",
    "systolic_bp",
    "heart_rate",
    "killip_class",
    "weight_kg",
    "anterior_st_elevation_or_lbbb",
    "time_to_treatment_hours",
)

MORTALITY_30_DAY_PERCENT = (0.8, 1.6, 2.2, 4.4, 7.3, 12.4, 16.1, 23.4, 26.8, 35.9)


def _number(name: str, value: Any, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number, not a boolean")
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{name} must be a finite number between {minimum:g} and {maximum:g}")
    return number


def _integer(name: str, value: Any, *, minimum: int, maximum: int) -> int:
    number = _number(name, value, minimum=minimum, maximum=maximum)
    if not number.is_integer():
        raise ValueError(f"{name} must be an integer")
    return int(number)


def _boolean(name: str, value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("yes", "true", "1"):
            return True
        if normalized in ("no", "false", "0"):
            return False
    if type(value) is int and value in (0, 1):
        return bool(value)
    raise ValueError(f"{name} must be yes/no, true/false, or 1/0")


def calculate_metrics(
    *,
    age: int,
    diabetes_hypertension_angina: bool,
    systolic_bp: float,
    heart_rate: float,
    killip_class: int,
    weight_kg: float,
    anterior_st_elevation_or_lbbb: bool,
    time_to_treatment_hours: float,
) -> Dict[str, Any]:
    """Calculate original TIMI STEMI points and observed 30-day mortality.

    All eight inputs are required; a missing predictor is never assumed absent.
    The history variable is one point if *any* of diabetes, hypertension or
    prior angina is present, not one point per condition.
    """
    age = _integer("age", age, minimum=0, maximum=120)
    systolic_bp = _number("systolic_bp", systolic_bp, minimum=1, maximum=400)
    heart_rate = _number("heart_rate", heart_rate, minimum=1, maximum=350)
    killip_class = _integer("killip_class", killip_class, minimum=1, maximum=4)
    weight_kg = _number("weight_kg", weight_kg, minimum=1, maximum=500)
    time_to_treatment_hours = _number(
        "time_to_treatment_hours", time_to_treatment_hours, minimum=0, maximum=1000
    )
    history = _boolean("diabetes_hypertension_angina", diabetes_hypertension_angina)
    anterior = _boolean("anterior_st_elevation_or_lbbb", anterior_st_elevation_or_lbbb)

    points = {
        "age": 3 if age >= 75 else 2 if age >= 65 else 0,
        "diabetes_hypertension_angina": int(history),
        "systolic_bp": 3 if systolic_bp < 100 else 0,
        "heart_rate": 2 if heart_rate > 100 else 0,
        "killip_class": 2 if killip_class >= 2 else 0,
        "weight_kg": 1 if weight_kg < 67 else 0,
        "anterior_st_elevation_or_lbbb": int(anterior),
        "time_to_treatment_hours": 1 if time_to_treatment_hours > 4 else 0,
    }
    score = sum(points.values())
    return {
        "tool": "timi-stemi-risk-score",
        "score": score,
        "score_max": 14,
        "mortality_30_day_percent": MORTALITY_30_DAY_PERCENT[min(score, 9)],
        "endpoint": "All-cause mortality at 30 days (original InTIME II cohort)",
        "points": points,
        "disclaimer": "Historical cohort estimate only; not a treatment or triage rule.",
    }


def _csv_row_inputs(row: Dict[str, str]) -> Dict[str, Any]:
    missing = [name for name in PREDICTOR_COLUMNS if row.get(name) is None or not str(row[name]).strip()]
    if missing:
        raise ValueError("missing required field(s): " + ", ".join(missing))
    return {key: row[key] for key in PREDICTOR_COLUMNS}


def process_batch(input_csv: str, output_csv: str) -> None:
    """Validate the complete input before writing a CSV with calculated results."""
    input_path, output_path = Path(input_csv).resolve(), Path(output_csv).resolve()
    if input_path == output_path:
        raise ValueError("Input and output files must differ")
    if not input_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")
    if input_path.stat().st_size == 0:
        raise ValueError("Input CSV is empty")

    with input_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or ())
        if not fieldnames:
            raise ValueError("Input CSV has no headers")
        if len(fieldnames) != len(set(fieldnames)):
            raise ValueError("Input CSV contains duplicate headers")
        rows = list(reader)

    if not rows:
        raise ValueError("Input CSV has headers but no data rows")
    result_columns = ("score", "mortality_30_day_percent")
    if any(field in fieldnames for field in result_columns):
        raise ValueError("Input CSV already contains result columns")

    results = []
    for row_number, row in enumerate(rows, start=2):
        if None in row:
            raise ValueError(f"CSV row {row_number}: unexpected extra columns")
        try:
            calculated = calculate_metrics(**_csv_row_inputs(row))
        except ValueError as exc:
            raise ValueError(f"CSV row {row_number}: {exc}") from exc
        # Prevent spreadsheet formula execution in user-supplied text columns.
        safe_row = {
            key: ("'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@"))
                  and key not in PREDICTOR_COLUMNS else value)
            for key, value in row.items()
        }
        safe_row.update({name: calculated[name] for name in result_columns})
        results.append(safe_row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames + list(result_columns))
        writer.writeheader()
        writer.writerows(results)
    print(f"Processed {len(results)} records -> {output_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Original TIMI STEMI 30-day mortality score")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Calculate one complete STEMI presentation")
    single.add_argument("--age", type=int, required=True)
    single.add_argument("--dm-htn-angina", action="store_true", dest="diabetes_hypertension_angina")
    single.add_argument("--sbp", type=float, required=True, dest="systolic_bp")
    single.add_argument("--heart-rate", type=float, required=True, dest="heart_rate")
    single.add_argument("--killip", type=int, required=True, dest="killip_class")
    single.add_argument("--weight", type=float, required=True, dest="weight_kg")
    single.add_argument("--anterior-or-lbbb", action="store_true", dest="anterior_st_elevation_or_lbbb")
    single.add_argument("--time-to-treatment", type=float, required=True, dest="time_to_treatment_hours")
    batch = commands.add_parser("batch", help="Score CSV rows with named predictor columns")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            values = vars(args).copy()
            values.pop("command")
            print(json.dumps(calculate_metrics(**values), indent=2))
        else:
            process_batch(args.input, args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
