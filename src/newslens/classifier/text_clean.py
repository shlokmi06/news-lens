"""Shared text normalization utilities for NewsLens classifier.

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

import re
from collections.abc import Iterable

from sklearn.base import BaseEstimator, TransformerMixin

URL_RE = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
EMAIL_RE = re.compile(r"\S+@\S+")
NON_ASCII_RE = re.compile(r"[^\x00-\x7F]+")
WHITESPACE_RE = re.compile(r"\s+")

# Dataset-specific source/style markers (Reuters wire-service patterns)
DATELINE_RE = re.compile(r"^.{0,80}?\(reuters\)\s*-\s*", flags=re.IGNORECASE)
REUTERS_RE = re.compile(r"\breuters\b", flags=re.IGNORECASE)


def strip_source_artifacts(text: str | None) -> str:
    """Remove dataset-specific source markers (Reuters datelines and mentions).

    This leakage control forces the model to rely on broader linguistic patterns
    rather than memorizing wire-source publisher tokens.
    """
    if not isinstance(text, str):
        return ""
    value = DATELINE_RE.sub("", text)
    value = REUTERS_RE.sub(" ", value)
    return WHITESPACE_RE.sub(" ", value).strip()


def clean_text(text: str | None) -> str:
    """Normalize text while preserving token boundaries useful for TF-IDF.

    Removes URLs, emails, non-ASCII characters, and repeated whitespace.
    """
    if not isinstance(text, str):
        return ""

    value = text.lower()
    value = URL_RE.sub(" ", value)
    value = EMAIL_RE.sub(" ", value)
    value = NON_ASCII_RE.sub(" ", value)
    value = WHITESPACE_RE.sub(" ", value).strip()
    return value


class TextCleaner(BaseEstimator, TransformerMixin):
    """scikit-learn compatible transformer for consistent pipeline preprocessing."""

    def __init__(self, strip_source: bool = False) -> None:
        self.strip_source = strip_source

    def fit(self, X: Iterable[object], y: object | None = None) -> TextCleaner:
        return self

    def transform(self, X: Iterable[object]) -> list[str]:
        strip_source = getattr(self, "strip_source", False)
        cleaned: list[str] = []
        for x in X:
            value = x if isinstance(x, str) else ""
            if strip_source:
                value = strip_source_artifacts(value)
            cleaned.append(clean_text(value))
        return cleaned
