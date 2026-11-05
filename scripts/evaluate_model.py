"""Evaluate the ML categorization pipeline on untouched holdout data.

Runnable from project root:
    python scripts/evaluate_model.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

from src.categorizer import Categorizer


def main():
    print("=" * 65)
    print("  Student Finance Assistant — ML Categorizer Evaluation")
    print("=" * 65)

    training_path = "data/training/categories.csv"
    holdout_path = "data/evaluation/categories_holdout.csv"

    if not Path(training_path).exists():
        print(f"Error: Training file not found at {training_path}")
        sys.exit(1)

    if not Path(holdout_path).exists():
        print(f"Error: Holdout file not found at {holdout_path}")
        sys.exit(1)

    train_df = pd.read_csv(training_path)
    holdout_df = pd.read_csv(holdout_path)

    print(f"Training samples:  {len(train_df)}")
    print(f"Holdout samples:   {len(holdout_df)}")
    print(f"Training classes:  {sorted(train_df['category'].unique())}")
    print("-" * 65)

    # Initialize model (fits exclusively on training data)
    categorizer = Categorizer(training_path=training_path)

    y_true = holdout_df["category"].tolist()
    descriptions = holdout_df["description"].tolist()

    y_pred = []
    scores = []
    review_statuses = []
    reasons = []
    abstention_count = 0

    per_sample_results = []

    for desc, true_cat in zip(descriptions, y_true):
        res = categorizer.predict(desc)
        y_pred.append(res.category)
        scores.append(res.model_score)
        review_statuses.append(res.review_status)
        reasons.append(res.reason)
        if res.is_abstention:
            abstention_count += 1

        per_sample_results.append(
            {
                "description": desc,
                "true_category": true_cat,
                "predicted_category": res.category,
                "model_score": round(res.model_score, 4),
                "review_status": res.review_status,
                "is_abstention": res.is_abstention,
                "reason": res.reason,
                "is_correct": res.category == true_cat,
            }
        )

    accuracy = accuracy_score(y_true, y_pred)
    all_labels = sorted(list(set(y_true + y_pred)))
    report_dict = classification_report(y_true, y_pred, labels=all_labels, output_dict=True, zero_division=0)
    report_text = classification_report(y_true, y_pred, labels=all_labels, zero_division=0)

    print("\nHoldout Classification Report:")
    print(report_text)
    print(f"Overall Accuracy:   {accuracy:.4f} ({accuracy * 100:.1f}%)")
    print(f"Abstentions:        {abstention_count} / {len(holdout_df)} ({abstention_count / len(holdout_df) * 100:.1f}%)")
    print("-" * 65)

    os.makedirs("reports", exist_ok=True)
    report_output_path = "reports/model_evaluation.json"

    evaluation_data = {
        "metadata": {
            "model_type": "TF-IDF + LogisticRegression",
            "training_samples": len(train_df),
            "holdout_samples": len(holdout_df),
            "confidence_threshold": categorizer.confidence_threshold,
            "training_path": training_path,
            "holdout_path": holdout_path,
        },
        "metrics": {
            "overall_accuracy": round(accuracy, 4),
            "macro_precision": round(report_dict["macro avg"]["precision"], 4),
            "macro_recall": round(report_dict["macro avg"]["recall"], 4),
            "macro_f1": round(report_dict["macro avg"]["f1-score"], 4),
            "abstention_count": abstention_count,
            "abstention_rate": round(abstention_count / len(holdout_df), 4),
        },
        "per_category_metrics": {
            cat: {
                "precision": round(report_dict[cat]["precision"], 4),
                "recall": round(report_dict[cat]["recall"], 4),
                "f1_score": round(report_dict[cat]["f1-score"], 4),
                "support": report_dict[cat]["support"],
            }
            for cat in all_labels
            if cat in report_dict
        },
        "samples": per_sample_results,
        "honest_limitations": [
            "Model is trained exclusively on synthetic student transaction descriptions.",
            "Evaluation dataset has 18 synthetic holdout records and does not reflect broad banking production data.",
            "Model scores are uncalibrated softmax outputs and must not be interpreted as posterior probabilities.",
            "Vocabulary gaps or unrecognized merchant names trigger abstention ('Other' / 'needs_review').",
        ],
    }

    with open(report_output_path, "w", encoding="utf-8") as f:
        json.dump(evaluation_data, f, indent=2)

    print(f"Report written to: {report_output_path}")
    print("=" * 65)


if __name__ == "__main__":
    main()
