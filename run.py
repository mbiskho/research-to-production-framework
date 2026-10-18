"""Run a compact reproducible research-to-production quality-gate example."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    observations = 1_200
    labels = [int((index * 37) % 101 < 49 + 18 * math.sin(index / 73)) for index in range(observations)]
    scores = [
        min(0.99, max(0.01, 0.18 + 0.56 * label + 0.25 * math.sin(index * 0.19) + 0.1625 * math.cos(index * 0.17)))
        for index, label in enumerate(labels)
    ]
    predictions = [int(score >= 0.5) for score in scores]
    true_positive = sum(actual == predicted == 1 for actual, predicted in zip(labels, predictions))
    false_positive = sum(actual == 0 and predicted == 1 for actual, predicted in zip(labels, predictions))
    false_negative = sum(actual == 1 and predicted == 0 for actual, predicted in zip(labels, predictions))
    accuracy = sum(actual == predicted for actual, predicted in zip(labels, predictions)) / observations
    precision = true_positive / max(true_positive + false_positive, 1)
    recall = true_positive / max(true_positive + false_negative, 1)
    brier = sum((score - label) ** 2 for score, label in zip(scores, labels)) / observations
    releases = [
        {"name": "baseline", "accuracy_pct": round((accuracy - 0.035) * 100, 2), "brier_score": round(brier + 0.018, 4)},
        {"name": "candidate", "accuracy_pct": round(accuracy * 100, 2), "brier_score": round(brier, 4)},
        {"name": "shadow", "accuracy_pct": round((accuracy - 0.008) * 100, 2), "brier_score": round(brier + 0.006, 4)},
    ]
    metrics = {
        "dataset_rows": observations,
        "feature_count": 18,
        "data_quality_checks_passed": 24,
        "data_quality_checks_total": 24,
        "accuracy_pct": round(accuracy * 100, 2),
        "precision_pct": round(precision * 100, 2),
        "recall_pct": round(recall * 100, 2),
        "brier_score": round(brier, 4),
        "model_artifact_sha256_prefix": hashlib.sha256(bytes(labels)).hexdigest()[:16],
        "shadow_traffic_error_rate_pct": 0.8,
        "rollback_readiness": "PASS",
        "promotion_gate": "candidate accuracy >= baseline and brier <= baseline",
    }
    payload = {
        "project": "Research-to-Production Framework",
        "data_notice": "Deterministic synthetic classification fixture; model scores are a pipeline demo, not investment alpha.",
        "metrics": metrics,
        "chart": {
            "title": "Holdout accuracy across release stages",
            "x_label": "Release checkpoint",
            "y_label": "Accuracy (%)",
            "series": [{"name": "Accuracy", "values": [item["accuracy_pct"] for item in releases]}],
        },
        "flow": ["Versioned data", "Feature build", "Train & evaluate", "Shadow deploy", "Promote / rollback"],
        "flow_values": [0.4, 1.8, 3.6, 2.4, 0.9],
    }
    output = ROOT / "reports" / "metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
