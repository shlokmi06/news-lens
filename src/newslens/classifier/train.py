"""Train and evaluate the News-Style Classifier pipeline.

-----------------------------------------------------------------------------
Attribution & License Notice:
Derived from Fake News Style-Risk Detector (https://github.com/AmirhosseinHonardoust/Fake-News-Detector)
Original work Copyright (c) 2025 Amir (Amir Honardoust)
Licensed under the MIT License:

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-----------------------------------------------------------------------------
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from newslens.classifier.text_clean import TextCleaner
from newslens.config import DATA_DIR, MODELS_DIR


def write_checksum(path: Path) -> Path:
    """Write <path>.sha256 sidecar containing hex SHA-256 digest."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    sidecar = path.with_name(path.name + ".sha256")
    sidecar.write_text(f"{digest}\n", encoding="utf-8")
    return sidecar


def load_dataset(data_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    true_csv = data_dir / "True.csv"
    fake_csv = data_dir / "Fake.csv"

    if not true_csv.exists() or not fake_csv.exists():
        raise FileNotFoundError(f"Missing CSV files in {data_dir}. Expected True.csv and Fake.csv")

    df_true = pd.read_csv(true_csv)
    df_true["label"] = 0  # REAL

    df_fake = pd.read_csv(fake_csv)
    df_fake["label"] = 1  # FAKE

    df = pd.concat([df_true, df_fake], ignore_index=True)
    total_before = len(df)

    # Combine title + text when title is present
    if "title" in df.columns:
        df["text"] = df["title"].fillna("") + " " + df["text"].fillna("")

    df = df.dropna(subset=["text"]).drop_duplicates(subset=["text"]).reset_index(drop=True)
    total_after = len(df)

    profile = {
        "total_rows_before": total_before,
        "total_rows_after": total_after,
        "removed_duplicates": total_before - total_after,
        "real_count": int((df["label"] == 0).sum()),
        "fake_count": int((df["label"] == 1).sum()),
    }
    return df, profile


def train_classifier(
    data_dir: Path = DATA_DIR,
    out_dir: Path = MODELS_DIR,
    strip_source: bool = False,
    random_state: int = 42,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df, profile = load_dataset(data_dir)

    X = df["text"].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=random_state, stratify=y
    )

    pipeline = Pipeline(
        [
            ("cleaner", TextCleaner(strip_source=strip_source)),
            (
                "vectorizer",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=25000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=1.0,
                    max_iter=1000,
                    random_state=random_state,
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)

    # Evaluation on holdout test set
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "dataset_profile": profile,
        "strip_source_artifacts": strip_source,
        "holdout_test": {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "macro_f1": float(f1_score(y_test, y_pred, average="macro")),
            "roc_auc": float(roc_auc_score(y_test, y_prob)),
            "test_samples": len(y_test),
        },
    }

    # Save artifacts
    model_path = out_dir / "pipeline.joblib"
    joblib.dump(pipeline, model_path)
    write_checksum(model_path)

    metrics_path = out_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train NewsLens Style Classifier")
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="Path to CSV data directory")
    parser.add_argument("--out-dir", default=str(MODELS_DIR), help="Output directory for model artifacts")
    parser.add_argument(
        "--strip-source-artifacts",
        action="store_true",
        help="Strip Reuters datelines to evaluate style without publisher markers",
    )
    args = parser.parse_args()

    metrics = train_classifier(
        data_dir=Path(args.data_dir),
        out_dir=Path(args.out_dir),
        strip_source=args.strip_source_artifacts,
    )
    print("Training complete:")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
