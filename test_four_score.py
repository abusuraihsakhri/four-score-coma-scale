"""Regression tests for validated clinical FOUR (0–16) scoring."""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from four_score import calculate_metrics, process_batch, main


@pytest.mark.parametrize("point,total", [(0, 0), (1, 4), (2, 8), (3, 12), (4, 16)])
def test_uniform_components(point, total):
    result = calculate_metrics(eye=point, motor=point, brainstem=point, respiration=point)
    assert result["score"] == total
    assert result["max_score"] == 16


def test_mixed_components():
    result = calculate_metrics(eye=4, motor=3, brainstem=2, respiration=1)
    assert result["score"] == 10
    assert result["components"] == {"eye": 4, "motor": 3, "brainstem": 2, "respiration": 1}


@pytest.mark.parametrize("bad", [-1, 5, 2.0, 2.5, float("nan"), float("inf"), None, True, "", "2.0", "x"])
def test_invalid_domain_value(bad):
    with pytest.raises(ValueError, match="eye"):
        calculate_metrics(eye=bad, motor=0, brainstem=0, respiration=0)


def test_all_domains_required():
    with pytest.raises(TypeError):
        calculate_metrics(eye=4, motor=4, brainstem=4)


def test_batch_correct_scores_and_preserves_columns(tmp_path):
    src, dst = tmp_path / "source.csv", tmp_path / "output.csv"
    src.write_text("case,eye,motor,brainstem,respiration\nA,4,3,2,1\nB,0,0,0,0\n", encoding="utf-8")
    assert process_batch(str(src), str(dst)) == 2
    with dst.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [
        {"case": "A", "eye": "4", "motor": "3", "brainstem": "2", "respiration": "1", "four_score_total": "10"},
        {"case": "B", "eye": "0", "motor": "0", "brainstem": "0", "respiration": "0", "four_score_total": "0"},
    ]


def test_batch_rejects_invalid_row_without_modifying_existing_output(tmp_path):
    src, dst = tmp_path / "source.csv", tmp_path / "output.csv"
    src.write_text("eye,motor,brainstem,respiration\n4,4,4,4\n3,,2,1\n", encoding="utf-8")
    dst.write_text("existing", encoding="utf-8")
    with pytest.raises(ValueError, match="Row 3"):
        process_batch(str(src), str(dst))
    assert dst.read_text(encoding="utf-8") == "existing"


@pytest.mark.parametrize("source", [
    "eye,motor,brainstem\n4,4,4\n",
    "eye,motor,eye,brainstem,respiration\n4,4,4,4,4\n",
    "eye,motor,brainstem,respiration,four_score_total\n4,4,4,4,16\n",
    "eye,motor,brainstem,respiration\n4,4,4,4,unexpected\n",
])
def test_invalid_csv_schema(tmp_path, source):
    src = tmp_path / "source.csv"
    src.write_text(source, encoding="utf-8")
    with pytest.raises(ValueError):
        process_batch(str(src), str(tmp_path / "output.csv"))


def test_cli_single(capsys):
    assert main(["single", "--eye", "4", "--motor", "3", "--brainstem", "2", "--respiration", "1"]) == 0
    assert json.loads(capsys.readouterr().out)["score"] == 10
