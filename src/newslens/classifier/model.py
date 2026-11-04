"""Model loading, validation, and inference helpers for NewsLens classifier.

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

import hashlib
import sys
from pathlib import Path
from typing import Any

import joblib

import newslens.classifier.text_clean as text_clean_mod
from newslens.classifier.text_clean import TextCleaner

_CHUNK_SIZE = 1 << 20  # 1 MiB


def sha256_file(path: str | Path) -> str:
    """Return the hex SHA-256 digest of a file, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checksum(path: str | Path) -> bool | None:
    """Verify a file against its .sha256 sidecar.

    Returns True/False when a sidecar exists, or None when none is found.
    """
    path = Path(path)
    sidecar = path.with_name(path.name + ".sha256")
    if not sidecar.exists():
        return None
    expected = sidecar.read_text(encoding="utf-8").split()[0].strip()
    return sha256_file(path) == expected


def ensure_sklearn_compatibility(pipeline: Any) -> Any:
    """Patch known cross-version sklearn differences in-place."""
    classifier = None
    if hasattr(pipeline, "named_steps"):
        classifier = pipeline.named_steps.get("classifier")
    elif pipeline.__class__.__name__ == "LogisticRegression":
        classifier = pipeline

    if classifier is not None and classifier.__class__.__name__ == "LogisticRegression":
        if not hasattr(classifier, "multi_class"):
            classifier.multi_class = "auto"

    return pipeline


def load_pipeline(path: str | Path, *, verify: bool = True) -> Any:
    """Load a saved pipeline, verify checksum sidecar, and apply compat repairs.

    Ensures compatibility with legacy pickled modules by registering
    module aliases for 'text_clean' in sys.modules prior to deserialization.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model pipeline not found at {path}")

    if verify and verify_checksum(path) is False:
        raise ValueError(
            f"Checksum mismatch for {path}. The artifact does not match its "
            f"{path.name}.sha256 sidecar; it may be corrupted or modified."
        )

    # Register compatibility alias so pickled artifacts referencing top-level
    # 'text_clean.TextCleaner' resolve cleanly inside the newslens package.
    if "text_clean" not in sys.modules:
        sys.modules["text_clean"] = text_clean_mod

    pipeline = joblib.load(path)
    return ensure_sklearn_compatibility(pipeline)


def classify_probability(
    prob_fake: float,
    threshold: float = 0.50,
    uncertainty_margin: float = 0.10,
) -> str:
    """Convert fake probability into REAL, FAKE, or UNCERTAIN label.

    The uncertainty margin is centered symmetrically around the decision threshold.
    With default threshold=0.50 and margin=0.10, probabilities between 0.45 and 0.55
    are classified as UNCERTAIN.
    """
    if not 0.0 <= prob_fake <= 1.0:
        raise ValueError("prob_fake must be between 0.0 and 1.0")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")
    if uncertainty_margin < 0.0:
        raise ValueError("uncertainty_margin must be non-negative")

    half_margin = uncertainty_margin / 2.0
    lower_bound = max(0.0, threshold - half_margin)
    upper_bound = min(1.0, threshold + half_margin)

    if lower_bound <= prob_fake <= upper_bound:
        return "UNCERTAIN"
    return "FAKE" if prob_fake > upper_bound else "REAL"


def predict_text(
    pipeline: Any,
    text: str,
    threshold: float = 0.50,
    uncertainty_margin: float = 0.10,
) -> dict[str, Any]:
    """Run classifier inference on a single text string."""
    probabilities = pipeline.predict_proba([text])[0]
    # Class order is [REAL, FAKE] (0 = REAL, 1 = FAKE)
    prob_real = float(probabilities[0])
    prob_fake = float(probabilities[1])

    label = classify_probability(prob_fake, threshold, uncertainty_margin)
    confidence = max(prob_real, prob_fake)

    half_margin = uncertainty_margin / 2.0
    uncertainty_range = (
        max(0.0, threshold - half_margin),
        min(1.0, threshold + half_margin),
    )

    return {
        "label": label,
        "prob_fake": prob_fake,
        "prob_real": prob_real,
        "confidence": confidence,
        "threshold": threshold,
        "uncertainty_margin": uncertainty_margin,
        "uncertainty_range": uncertainty_range,
    }
