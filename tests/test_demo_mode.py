"""Tests for Phase 4: Offline Demo Mode and separation guarantees.

Confirms:
1. Demo mode makes zero external API calls (no Groq or Tavily network access).
2. Demo results are visibly labeled with DEMO_FIXTURE_LABEL across summary, caveats, and sources.
3. Live mode still strictly requires valid credentials.
4. Live errors do not silently switch to fixture data.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from newslens.checker.fixtures import (
    DEMO_FIXTURE_LABEL,
    DEMO_SAMPLE_CLAIMS,
    get_demo_fixture,
)
from newslens.checker.schema import Verdict
from newslens.checker.search import search_both
from newslens.checker.agent import check_claim


# ---------------------------------------------------------------------------
# 1. Demo mode makes no external API calls
# ---------------------------------------------------------------------------


def test_demo_mode_makes_no_external_api_calls():
    """Verify get_demo_fixture never instantiates or calls TavilyClient or Groq."""
    with patch("newslens.checker.search.TavilyClient") as mock_tavily, \
         patch("newslens.checker.agent.Groq") as mock_groq:

        for claim in DEMO_SAMPLE_CLAIMS.values():
            results, allowed_urls, verdict = get_demo_fixture(claim)
            assert len(results) > 0
            assert len(allowed_urls) > 0
            assert isinstance(verdict, Verdict)

        # Also test arbitrary custom claim
        c_results, c_allowed, c_verdict = get_demo_fixture("Some random unindexed claim.")
        assert len(c_results) > 0
        assert isinstance(c_verdict, Verdict)

        # Assert no calls were made to external clients
        mock_tavily.assert_not_called()
        mock_groq.assert_not_called()


# ---------------------------------------------------------------------------
# 2. Demo results are visibly labeled as fixtures
# ---------------------------------------------------------------------------


def test_demo_results_are_visibly_labeled_as_fixtures():
    """Verify DEMO_FIXTURE_LABEL is present in summary, caveats, and source titles."""
    for claim in DEMO_SAMPLE_CLAIMS.values():
        results, allowed_urls, verdict = get_demo_fixture(claim)

        # Label must be in summary and caveats
        assert DEMO_FIXTURE_LABEL in verdict.summary, (
            f"Summary for '{claim}' missing fixture label"
        )
        assert DEMO_FIXTURE_LABEL in verdict.caveats, (
            f"Caveats for '{claim}' missing fixture label"
        )

        # Sources must indicate fixture status
        assert len(verdict.sources) > 0
        for src in verdict.sources:
            assert "[DEMO FIXTURE]" in src.title or "[DEMO" in src.title

        for item in results:
            assert "[DEMO FIXTURE]" in item["title"]


def test_custom_claim_in_demo_mode_is_clearly_labeled():
    """Verify that arbitrary un-fixture claims are explicitly labeled as demo notice."""
    results, allowed_urls, verdict = get_demo_fixture("A completely unique user claim")
    assert DEMO_FIXTURE_LABEL in verdict.summary
    assert DEMO_FIXTURE_LABEL in verdict.caveats
    assert verdict.verdict == "unverifiable"
    assert "Offline Demo Mode" in verdict.reasoning


# ---------------------------------------------------------------------------
# 3. Live mode still strictly requires credentials
# ---------------------------------------------------------------------------


def test_live_search_requires_credentials():
    """Live search_both must reject blank or missing credentials."""
    with pytest.raises(RuntimeError, match="TAVILY_API_KEY is required"):
        search_both("Some valid claim", tavily_api_key="")


def test_live_agent_requires_credentials():
    """Live check_claim must reject blank or missing credentials."""
    with pytest.raises(RuntimeError, match="GROQ_API_KEY is required"):
        check_claim("Some valid claim", [], set(), groq_api_key="")


# ---------------------------------------------------------------------------
# 4. Live errors do not silently switch to fixture data
# ---------------------------------------------------------------------------


def test_live_search_error_is_raised_not_silenced():
    """When Tavily fails during live mode, an exception is raised, NOT fixture data."""
    mock_client = MagicMock()
    mock_client.search.side_effect = RuntimeError("Tavily service 503 Service Unavailable")

    with patch("newslens.checker.search.TavilyClient", return_value=mock_client):
        with pytest.raises(RuntimeError, match="Tavily"):
            search_both("Some claim", tavily_api_key="real-looking-key")


def test_live_groq_error_is_raised_not_silenced():
    """When Groq fails during live mode, an exception is raised, NOT fixture data."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("Groq connection timeout")

    with patch("newslens.checker.agent.Groq", return_value=mock_client):
        with pytest.raises(RuntimeError, match="Groq"):
            check_claim("Some claim", [{"url": "http://a.com", "title": "t", "snippet": "s"}],
                        {"http://a.com"}, groq_api_key="real-looking-key")
