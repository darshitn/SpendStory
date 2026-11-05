"""Machine Learning categorization pipeline using TF-IDF and Logistic Regression.

Provides explainable, local inference for uncategorized student transactions.
Includes vocabulary-overlap checks and confidence thresholding to trigger explicit
human review ('needs_review' -> 'Other') for unrecognized or ambiguous descriptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

DEFAULT_CONFIDENCE_THRESHOLD = 0.25
DEFAULT_TRAINING_PATH = "data/training/categories.csv"


@dataclass(frozen=True)
class PredictionResult:
    category: str
    model_score: float
    review_status: str  # 'confirmed' or 'needs_review'
    is_abstention: bool
    reason: str


class Categorizer:
    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        training_path: str = DEFAULT_TRAINING_PATH,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.training_path = training_path
        self.pipeline: Optional[Pipeline] = None
        self.classes: list[str] = []
        self._fit()

    def _fit(self) -> None:
        p = Path(self.training_path)
        if not p.exists():
            raise FileNotFoundError(f"Training data not found at '{self.training_path}'")

        df = pd.read_csv(p)
        if "description" not in df.columns or "category" not in df.columns:
            raise ValueError(f"Training CSV must contain 'description' and 'category' columns.")

        X = df["description"].astype(str)
        y = df["category"].astype(str)

        self.pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        min_df=1,
                        sublinear_tf=True,
                        token_pattern=r"(?u)\b\w+\b",
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        C=1.0,
                        max_iter=300,
                        random_state=42,
                        solver="lbfgs",
                    ),
                ),
            ]
        )

        self.pipeline.fit(X, y)
        self.classes = list(self.pipeline.classes_)

    def predict(self, description: str) -> PredictionResult:
        """Predict the expense category for a transaction description.

        Abstains to 'Other' with 'needs_review' if:
        1. Description has zero recognized vocabulary tokens (OOV).
        2. Top model confidence score is below self.confidence_threshold.
        """
        if self.pipeline is None:
            raise RuntimeError("Categorizer pipeline is not fitted.")

        cleaned = " ".join(str(description).strip().split())
        if not cleaned:
            return PredictionResult(
                category="Other",
                model_score=0.0,
                review_status="needs_review",
                is_abstention=True,
                reason="Empty description",
            )

        # 1. Check vocabulary overlap
        vectorizer: TfidfVectorizer = self.pipeline.named_steps["tfidf"]
        feature_names = vectorizer.vocabulary_
        analyzer = vectorizer.build_analyzer()
        tokens = analyzer(cleaned)

        known_tokens = [t for t in tokens if t in feature_names]
        if not known_tokens:
            # Completely out of vocabulary
            return PredictionResult(
                category="Other",
                model_score=0.0,
                review_status="needs_review",
                is_abstention=True,
                reason="Unrecognized vocabulary (out-of-vocabulary)",
            )

        # 2. Classifier probability estimation
        probas = self.pipeline.predict_proba([cleaned])[0]
        max_idx = probas.argmax()
        top_category = self.classes[max_idx]
        top_score = float(probas[max_idx])

        # 3. Confidence thresholding
        if top_score < self.confidence_threshold:
            return PredictionResult(
                category="Other",
                model_score=top_score,
                review_status="needs_review",
                is_abstention=True,
                reason=f"Low model confidence ({top_score:.2f} < {self.confidence_threshold:.2f})",
            )

        return PredictionResult(
            category=top_category,
            model_score=top_score,
            review_status="confirmed",
            is_abstention=False,
            reason="Confident prediction",
        )


_CACHED_CATEGORIZER: Optional[Categorizer] = None


def get_default_categorizer() -> Categorizer:
    """Return a cached, globally available categorizer instance."""
    global _CACHED_CATEGORIZER
    if _CACHED_CATEGORIZER is None:
        _CACHED_CATEGORIZER = Categorizer()
    return _CACHED_CATEGORIZER
