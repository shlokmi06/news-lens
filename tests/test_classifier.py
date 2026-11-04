"""Unit tests for the NewsLens News-Style Classifier."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from newslens.classifier.model import (
    classify_probability,
    load_pipeline,
    predict_text,
    sha256_file,
    verify_checksum,
)
from newslens.classifier.text_clean import (
    TextCleaner,
    clean_text,
    strip_source_artifacts,
)


def test_clean_text_basic():
    raw = "Breaking News! Check https://example.com/test and email me@news.org 100%!"
    cleaned = clean_text(raw)
    assert "https://" not in cleaned
    assert "me@news.org" not in cleaned
    assert "breaking news" in cleaned


def test_strip_source_artifacts():
    dateline_text = "WASHINGTON (Reuters) - The president gave a speech today about taxes."
    stripped = strip_source_artifacts(dateline_text)
    assert "(reuters)" not in stripped.lower()
    assert "reuters" not in stripped.lower()
    assert "The president gave a speech" in stripped


def test_text_cleaner_transformer():
    cleaner = TextCleaner(strip_source=True)
    docs = [
        "PARIS (Reuters) - Diplomatic talks resumed on Wednesday.",
        "Sensational clickbait post with https://fake.url/spam",
    ]
    transformed = cleaner.fit_transform(docs)
    assert len(transformed) == 2
    assert "reuters" not in transformed[0]
    assert "https://" not in transformed[1]


def test_classify_probability_uncertainty_band():
    # threshold 0.50, margin 0.10 -> UNCERTAIN between 0.45 and 0.55
    assert classify_probability(0.30, 0.50, 0.10) == "REAL"
    assert classify_probability(0.44, 0.50, 0.10) == "REAL"
    assert classify_probability(0.45, 0.50, 0.10) == "UNCERTAIN"
    assert classify_probability(0.50, 0.50, 0.10) == "UNCERTAIN"
    assert classify_probability(0.55, 0.50, 0.10) == "UNCERTAIN"
    assert classify_probability(0.56, 0.50, 0.10) == "FAKE"
    assert classify_probability(0.90, 0.50, 0.10) == "FAKE"


def test_classify_probability_validation():
    with pytest.raises(ValueError):
        classify_probability(-0.1)
    with pytest.raises(ValueError):
        classify_probability(1.1)
    with pytest.raises(ValueError):
        classify_probability(0.5, threshold=1.5)
    with pytest.raises(ValueError):
        classify_probability(0.5, uncertainty_margin=-0.05)


def test_predict_text_with_toy_pipeline():
    # Build a tiny toy pipeline
    texts = [
        "reuters official report on government budget and taxes",
        "official statement from wire press reuters report",
        "shocking secret revealed doctors do not want you to know",
        "bombshell alien conspiracy revealed share immediately",
    ]
    labels = [0, 0, 1, 1]

    pipe = Pipeline(
        [
            ("cleaner", TextCleaner()),
            ("vectorizer", TfidfVectorizer()),
            ("clf", LogisticRegression()),
        ]
    )
    pipe.fit(texts, labels)

    res = predict_text(pipe, "Official Reuters wire report", threshold=0.5, uncertainty_margin=0.1)
    assert "label" in res
    assert "prob_fake" in res
    assert "prob_real" in res
    assert res["label"] in ["REAL", "FAKE", "UNCERTAIN"]
    assert 0.0 <= res["prob_fake"] <= 1.0


def test_checksum_verification(tmp_path: Path):
    test_file = tmp_path / "sample.bin"
    test_file.write_bytes(b"hello world news")

    digest = sha256_file(test_file)
    sidecar = test_file.with_name("sample.bin.sha256")
    sidecar.write_text(f"{digest}\n", encoding="utf-8")

    assert verify_checksum(test_file) is True

    # Tamper with file
    test_file.write_bytes(b"tampered content")
    assert verify_checksum(test_file) is False
