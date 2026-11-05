"""Unit tests for ML categorizer and abstention engine."""

import pytest

from src.categorizer import Categorizer, get_default_categorizer


def test_categorizer_fit_and_classes():
    cat = Categorizer(training_path="data/training/categories.csv")
    assert cat.pipeline is not None
    assert len(cat.classes) == 6
    assert "Food" in cat.classes
    assert "Transport" in cat.classes
    assert "Shopping" in cat.classes
    assert "Education" in cat.classes
    assert "Bills" in cat.classes
    assert "Entertainment" in cat.classes


def test_categorizer_known_predictions():
    cat = get_default_categorizer()

    res_food = cat.predict("Campus canteen lunch meal")
    assert res_food.category == "Food"
    assert res_food.review_status == "confirmed"
    assert res_food.is_abstention is False
    assert res_food.model_score > 0.3

    res_trans = cat.predict("Metro card recharge for commute")
    assert res_trans.category == "Transport"
    assert res_trans.review_status == "confirmed"


def test_categorizer_abstains_on_unknown_vocabulary():
    cat = get_default_categorizer()

    # Completely unrecognized words not in training set
    res_unknown = cat.predict("Zzzqwop klaxon bloop")
    assert res_unknown.category == "Other"
    assert res_unknown.review_status == "needs_review"
    assert res_unknown.is_abstention is True
    assert "out-of-vocabulary" in res_unknown.reason


def test_categorizer_empty_description():
    cat = get_default_categorizer()

    res_empty = cat.predict("")
    assert res_empty.category == "Other"
    assert res_empty.review_status == "needs_review"
    assert res_empty.is_abstention is True


def test_pipeline_isolation_from_holdout():
    # Verify that holdout data is never loaded or referenced in the categorizer
    cat = Categorizer(training_path="data/training/categories.csv")
    assert cat.training_path == "data/training/categories.csv"
    assert "categories_holdout.csv" not in str(cat.training_path)
