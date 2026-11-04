"""NewsLens checker — Tavily search wrapper.

Clean-room implementation. No code derived from fact-checker-agent (no license found).

Performs two fixed queries (pro-claim + counter-claim) and returns a combined
list of deduplicated results together with the URL allowlist.  The allowlist is
built exclusively from URLs present in the Tavily API response dict — never from
scraped body text or LLM output.
"""

from __future__ import annotations

import re
from typing import Any

from tavily import TavilyClient  # type: ignore[import-untyped]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLAIM_MAX_CHARS: int = 500
SNIPPET_MAX_CHARS: int = 400
TITLE_MAX_CHARS: int = 120

# Matches any opening or closing fence tag (<evidence ...> or </claim>etc.)
# Used to strip prompt-injection attempts from user content.
_FENCE_RE = re.compile(r"</?\\s*(evidence|claim)\\s*[^>]*>", re.IGNORECASE)
# Simpler fallback that catches <evidence> </evidence> <claim> </claim> literally
_FENCE_LITERAL_RE = re.compile(
    r"</?\\s*(?:evidence|claim)\\s*>", re.IGNORECASE
)


def sanitize(text: str, limit: int) -> str:
    """Strip fence tags, collapse whitespace, and truncate to *limit* chars."""
    cleaned = _FENCE_RE.sub("", text)
    cleaned = _FENCE_LITERAL_RE.sub("", cleaned)
    # Also escape any remaining angle-bracket sequences that look like tags
    cleaned = re.sub(r"<\s*/?evidence[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<\s*/?claim[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned.split())  # collapse whitespace
    return cleaned[:limit]


def counter_query(claim: str) -> str:
    """Return a counter-evidence search query for the given claim."""
    return f"{claim} debunked fact check false"


def search_both(
    claim: str,
    tavily_api_key: str,
    *,
    max_results: int = 5,
    timeout: float = 20.0,
) -> tuple[list[dict[str, Any]], set[str]]:
    """Search Tavily for *claim* and its counter-query.

    Returns:
        results: Deduplicated list of ``{url, title, snippet}`` dicts.
        allowed_urls: Set of URL strings drawn **only** from ``results[].url``
            in the Tavily response — never from body text or LLM output.

    Raises:
        RuntimeError: If ``tavily_api_key`` is blank or the Tavily call fails
            with a non-retriable error.
    """
    if not tavily_api_key or not tavily_api_key.strip():
        raise RuntimeError("TAVILY_API_KEY is required but was not provided.")

    clean_claim = sanitize(claim, CLAIM_MAX_CHARS)
    if not clean_claim:
        raise ValueError("Claim must not be empty after sanitization.")

    client = TavilyClient(api_key=tavily_api_key)

    queries = [clean_claim, counter_query(clean_claim)]
    seen_urls: set[str] = set()
    allowed_urls: set[str] = set()
    results: list[dict[str, Any]] = []

    for query in queries:
        try:
            response = client.search(query=query, max_results=max_results)
        except Exception as exc:
            msg = str(exc)
            msg_lower = msg.lower()
            if "429" in msg or "rate limit" in msg_lower or "quota" in msg_lower:
                raise RuntimeError(
                    "Tavily search rate limit / monthly quota exceeded. "
                    "The free tier includes 1,000 queries per month."
                ) from exc
            if "401" in msg or "unauthorized" in msg_lower or "api key" in msg_lower:
                raise RuntimeError(
                    "Tavily authentication failed: invalid API key. "
                    "Please check your credentials in the sidebar or .env."
                ) from exc
            if "timeout" in msg_lower:
                raise RuntimeError(
                    "Tavily search timed out (20s limit). Check your network connection."
                ) from exc
            raise RuntimeError(f"Tavily search failed: {exc}") from exc

        raw_results: list[dict[str, Any]] = response.get("results", [])
        for item in raw_results:
            url: str = item.get("url", "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            # Allowlist built ONLY from API response field — not body text.
            allowed_urls.add(url)
            results.append(
                {
                    "url": url,
                    "title": sanitize(item.get("title", ""), TITLE_MAX_CHARS),
                    "snippet": sanitize(item.get("content", ""), SNIPPET_MAX_CHARS),
                }
            )

    return results, allowed_urls
