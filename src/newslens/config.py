"""Configuration settings and constants for NewsLens."""

from __future__ import annotations

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
DEFAULT_MODEL_PATH = MODELS_DIR / "pipeline.joblib"
DEFAULT_METRICS_PATH = MODELS_DIR / "metrics.json"

# Classification Thresholds
DEFAULT_THRESHOLD = 0.50
DEFAULT_UNCERTAINTY_MARGIN = 0.10

# API Credentials (Loaded from environment / .env)
DEFAULT_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEFAULT_TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Input constraints
MIN_TOKENS = 8
MIN_CHARS = 50

# Educational Notices
STYLE_DISCLAIMER = (
    "NewsLens Style Classifier evaluates whether the submitted text stylistically "
    "resembles examples labeled 'real' or 'fake' in its training data. "
    "It is a style-pattern estimate, NOT a factual truth judgment."
)

LEAKAGE_LIMITATION_NOTICE = (
    "Dataset Confounding / Leakage Notice: In the training corpus (ISOT-derived subset), "
    "over 99% of REAL news articles originate from Reuters wire reports with standardized "
    "datelines and wire-service house styles, while FAKE articles originate from unverified "
    "political blogs and opinion sites. Consequently, this model keys strongly on publisher "
    "and formatting artifacts rather than factual accuracy."
)
