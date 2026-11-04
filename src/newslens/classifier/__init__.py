"""News-style classification module for NewsLens."""

from newslens.classifier.model import (
    classify_probability,
    load_pipeline,
    predict_text,
    verify_checksum,
)
from newslens.classifier.text_clean import TextCleaner, clean_text, strip_source_artifacts

__all__ = [
    "TextCleaner",
    "clean_text",
    "strip_source_artifacts",
    "classify_probability",
    "load_pipeline",
    "predict_text",
    "verify_checksum",
]
