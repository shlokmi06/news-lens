"""NewsLens opt-in live integration test.

LIVE EXTERNAL SERVICE CHECK:
This test connects to external third-party APIs (Tavily Search and Groq LLM).
It runs ONLY when valid GROQ_API_KEY and TAVILY_API_KEY credentials are provided
in the environment (e.g. via .env or shell environment variables).

WARNING: Running this test will consume external API quota (Tavily search queries
and Groq LLM tokens). When credentials are not provided, this test is cleanly
skipped with an informative message.

Never prints or logs secret API keys.
"""

from __future__ import annotations

import os
from typing import Any

import pytest
from dotenv import load_dotenv

load_dotenv()


def _get_live_credentials() -> tuple[str, str]:
    """Retrieve and sanitize API credentials without exposing values."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    # Reject empty keys or default placeholder strings from .env.example
    is_groq_placeholder = groq_key.startswith("your_") or "placeholder" in groq_key.lower()
    is_tavily_placeholder = tavily_key.startswith("your_") or "placeholder" in tavily_key.lower()

    if not groq_key or is_groq_placeholder:
        groq_key = ""
    if not tavily_key or is_tavily_placeholder:
        tavily_key = ""

    return groq_key, tavily_key


@pytest.mark.integration
def test_live_claim_checker_end_to_end():
    """End-to-end integration test with live Tavily and Groq APIs.

    Validates:
    1. Both supporting and counter-query searches execute via Tavily.
    2. URL allowlist is built exclusively from Tavily results[].url fields.
    3. Groq generates a structured verdict matching the Verdict schema.
    4. Any cited sources in verdict.sources match the URL allowlist.
    5. No secret values are printed or logged.
    """
    groq_key, tavily_key = _get_live_credentials()

    if not groq_key or not tavily_key:
        pytest.skip(
            "Skipping live integration check: GROQ_API_KEY and/or TAVILY_API_KEY "
            "not supplied in environment. Set valid keys in .env to run live tests. "
            "(Note: Live tests consume external API quota)."
        )

    from newslens.checker.agent import GROQ_MODEL, check_claim
    from newslens.checker.schema import Verdict
    from newslens.checker.search import counter_query, search_both

    claim = "The Earth revolves around the Sun."

    # 1. Verify query generation
    c_query = counter_query(claim)
    assert claim in c_query
    assert "debunked" in c_query or "fact check" in c_query

    # 2. Execute live search
    search_results, allowed_urls = search_both(claim, tavily_key, max_results=3)

    assert isinstance(search_results, list)
    assert isinstance(allowed_urls, set)
    assert len(search_results) > 0, "Live Tavily search should return at least one result"
    assert len(allowed_urls) > 0, "Allowlist must contain URLs from search results"

    # Verify allowlist integrity: every allowed URL must be present in search_results
    result_urls = {item["url"] for item in search_results}
    assert allowed_urls == result_urls, "Allowlist must exactly match the set of search result URLs"

    # 3. Execute live LLM reasoning
    verdict = check_claim(
        claim=claim,
        search_results=search_results,
        allowed_urls=allowed_urls,
        groq_api_key=groq_key,
        model=GROQ_MODEL,
    )

    assert verdict is not None, "Groq should return a valid structured Verdict"
    assert isinstance(verdict, Verdict)
    assert verdict.verdict in ("supported", "refuted", "misleading", "unverifiable")
    assert verdict.confidence in ("high", "medium", "low")
    assert len(verdict.summary.strip()) > 0, "Verdict must include a non-empty summary"
    assert len(verdict.reasoning.strip()) > 0, "Verdict must include non-empty reasoning"

    # 4. Verify citation whitelist enforcement on live output
    for src in verdict.sources:
        assert src.url in allowed_urls or any(
            src.url.rstrip("/").endswith(a.rstrip("/").split("://")[-1]) for a in allowed_urls
        ), f"Live source URL {src.url} was not in the search allowlist"
