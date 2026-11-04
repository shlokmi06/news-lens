"""NewsLens evidence-based claim checker package.

Clean-room implementation — no code derived from fact-checker-agent (no license found).
"""

from newslens.checker.agent import GROQ_MODEL, check_claim
from newslens.checker.fixtures import (
    DEMO_FIXTURE_LABEL,
    DEMO_SAMPLE_CLAIMS,
    get_demo_fixture,
)
from newslens.checker.schema import SearchResult, Source, Verdict
from newslens.checker.search import counter_query, sanitize, search_both

__all__ = [
    "Verdict",
    "Source",
    "SearchResult",
    "search_both",
    "sanitize",
    "counter_query",
    "check_claim",
    "GROQ_MODEL",
    "DEMO_FIXTURE_LABEL",
    "DEMO_SAMPLE_CLAIMS",
    "get_demo_fixture",
]
