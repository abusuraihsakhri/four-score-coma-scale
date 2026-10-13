#!/usr/bin/env python3
"""FOUR (Full Outline of UnResponsiveness) score: four domains, 0–4 each.

Scores are assigned by a trained examiner; this module only validates and adds them.
Reference: Wijdicks et al. Ann Neurol. 2005;58:585–593. doi:10.1002/ana.20611
"""
import argparse
import csv
import json
import os
import tempfile
from pathlib import Path

DOMAINS = ("eye", "motor", "brainstem", "respiration")


def _point(value, domain):
    """Accept integer point values or their plain decimal representation from CSV."""
    if isinstance(value, bool):
        raise ValueError(f"{domain} must be an integer from 0 to 4")
    if isinstance(value, int):
        point = value
    elif isinstance(value, str) and value.strip() in ("0", "1", "2", "3", "4"):
        point = int(value.strip())
    else:
        raise ValueError(f"{domain} must be an integer from 0 to 4")
    if not 0 <= point <= 4:
        raise ValueError(f"{domain} must be an integer from 0 to 4")
    return point


def calculate_metrics(*, eye, motor, brainstem, respiration):
    """Return a descriptive FOUR total; no unvalidated diagnostic cutoffs."""
    parts = {
        name: _point(value, name)
        for name, value in zip(DOMAINS, (eye, motor, brainstem, respiration))
    }
    return {
        "tool": "four-score-coma-scale",
        "score": sum(parts.values()),
        "max_score": 16,
        "components": parts,
        "note": "A lower score indicates more impaired findings; interpret in clinical context.",
    }


def process_batch(input_csv: str, output_csv: str) -> int:
    """Validate all rows before atomically replacing the output CSV."""
    with open(input_csv, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames
        if not headers or len(headers) != len(set(headers)):
            raise ValueError("CSV requires a nonempty header with unique column names")
        missing = set(DOMAINS).difference(headers)
        if missing:
            raise ValueError("CSV is missing required columns: " + ", ".join(sorted(missing)))
        if "four_score_total" in headers:
            raise ValueError("CSV input already contains reserved column four_score_total")
        rows = []
        for line_no, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Row {line_no}: extra CSV fields")
            try:
                result = calculate_metrics(**{name: row[name] for name in DOMAINS})
            except ValueError as exc:
                raise ValueError(f"Row {line_no}: {exc}") from exc
            rows.append({**row, "four_score_total": result["score"]})

    destination = Path(output_csv)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", newline="", encoding="utf-8", dir=destination.parent,
            prefix=".four-score-", suffix=".csv", delete=False
        ) as stream:
            temporary = stream.name
            writer = csv.DictWriter(stream, fieldnames=headers + ["four_score_total"])
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, destination)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    return len(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="FOUR coma score (0–16)")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Score one clinical examination")
    for name in DOMAINS:
        single.add_argument(f"--{name}", type=int, required=True, choices=range(5))
    batch = commands.add_parser("batch", help="Score rows in a CSV")
    batch.add_argument("-i", "--input", required=True, help="Source CSV")
    batch.add_argument("-o", "--output", default="results.csv", help="Destination CSV")
    args = parser.parse_args(argv)
    if args.command == "single":
        print(json.dumps(calculate_metrics(**{name: getattr(args, name) for name in DOMAINS}), indent=2))
    else:
        try:
            count = process_batch(args.input, args.output)
        except (ValueError, OSError, csv.Error) as exc:
            parser.error(str(exc))
        print(f"Processed {count} records -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
