"""NewsLens checker — Groq LLM reasoning agent.

Clean-room implementation. No code derived from fact-checker-agent (no license found).

Uses Groq's native JSON-schema structured output with llama-3.3-70b-versatile.
API keys are passed per-request; they are never written to os.environ.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.parse import urlparse

from groq import Groq  # type: ignore[import-untyped]

from newslens.checker.schema import Source, Verdict
from newslens.checker.search import CLAIM_MAX_CHARS, sanitize

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_GROQ_MODEL: str = "openai/gpt-oss-120b"
GROQ_MODEL: str = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
GROQ_TIMEOUT: float = 45.0
GROQ_MAX_TOKENS: int = 4096

SYSTEM_PROMPT: str = """\
You are a neutral, evidence-based fact-checking assistant for an educational web application.

Your task:
1. Read the claim provided inside <claim> tags.
2. Read the evidence inside <evidence> tags. The evidence is a numbered list of web results (title, URL, snippet).
3. Evaluate whether the evidence supports, refutes, or neither supports nor refutes the claim.
4. Return ONLY valid JSON matching the schema described below — no prose, no markdown fences.

Verdict values (exactly one):
- "supported"    — majority of relevant evidence clearly supports the claim
- "refuted"      — majority of relevant evidence clearly contradicts the claim
- "misleading"   — claim is technically true but framed to mislead, or evidence is mixed/selective
- "unverifiable" — evidence is absent, irrelevant, or too contradictory to draw a conclusion

Rules:
- Base your verdict ONLY on the evidence provided. Do not use prior knowledge.
- If evidence is weak, sparse, or contradictory, prefer "unverifiable" or "misleading".
- In sources[], list ONLY URLs that appear in the evidence block. Do not invent URLs. Citing the 3 to 5 most relevant sources with concise snippets is preferred.
- Keep summary ≤ 2 sentences. Keep reasoning ≤ 6 sentences.
- Never assert that something is absolutely true or false — this is an educational tool.
"""


def _normalize_url(url: str) -> str:
    """Normalize a URL for comparison: lowercase host, strip www., strip scheme, strip trailing /."""
    try:
        parsed = urlparse(url.lower().strip())
        host = parsed.netloc.lstrip("www.")
        path = parsed.path.rstrip("/")
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{host}{path}{query}"
    except Exception:
        return url.lower().strip()


def _is_allowed(url: str, allowed_urls: set[str]) -> bool:
    """Return True iff *url* (after normalization) matches a URL in *allowed_urls*."""
    norm = _normalize_url(url)
    return any(_normalize_url(a) == norm for a in allowed_urls)


def _format_evidence(results: list[dict[str, Any]]) -> str:
    """Render search results as a fenced evidence block for the LLM prompt."""
    lines: list[str] = []
    for i, item in enumerate(results, start=1):
        title = item.get("title", "(no title)")
        url = item.get("url", "")
        snippet = item.get("snippet", "")
        lines.append(f"{i}. Title: {title}\n   URL: {url}\n   Snippet: {snippet}")
    evidence_text = "\n\n".join(lines) if lines else "(No evidence retrieved.)"
    return f"<evidence>\n{evidence_text}\n</evidence>"


def check_claim(
    claim: str,
    search_results: list[dict[str, Any]],
    allowed_urls: set[str],
    groq_api_key: str,
    *,
    model: str = GROQ_MODEL,
) -> Verdict | None:
    """Run Groq LLM reasoning and return a filtered :class:`Verdict`.

    The LLM is instructed via fenced ``<claim>`` and ``<evidence>`` blocks.
    User-supplied content is sanitized before insertion.
    After the model responds, ``verdict.sources`` is filtered to only URLs
    present in *allowed_urls* — fabricated URLs are silently removed.

    Args:
        claim: The user-supplied factual claim (≤ CLAIM_MAX_CHARS).
        search_results: List of ``{url, title, snippet}`` dicts from Tavily.
        allowed_urls: Set of permitted URLs built from Tavily response only.
        groq_api_key: Groq API key — passed directly to the client, not to os.environ.
        model: Groq model identifier.

    Returns:
        Filtered :class:`Verdict` on success, ``None`` if the model response
        cannot be parsed or validated.

    Raises:
        ValueError: If *claim* is empty or too long.
        RuntimeError: If *groq_api_key* is blank or the API call fails.
    """
    # --- Input validation ---
    if not claim or not claim.strip():
        raise ValueError("Claim must not be empty.")
    if len(claim) > CLAIM_MAX_CHARS:
        raise ValueError(f"Claim exceeds maximum length of {CLAIM_MAX_CHARS} characters.")
    if not groq_api_key or not groq_api_key.strip():
        raise RuntimeError("GROQ_API_KEY is required but was not provided.")

    # --- Sanitize claim for prompt insertion ---
    safe_claim = sanitize(claim, CLAIM_MAX_CHARS)
    claim_block = f"<claim>\n{safe_claim}\n</claim>"
    evidence_block = _format_evidence(search_results)

    user_message = f"{claim_block}\n\n{evidence_block}"

    # --- Call Groq ---
    try:
        client = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "verdict",
                    "schema": Verdict.model_json_schema(),
                },
            },
            max_tokens=GROQ_MAX_TOKENS,
            timeout=GROQ_TIMEOUT,
        )
    except Exception as exc:
        msg = str(exc)
        msg_lower = msg.lower()
        if "429" in msg or "rate limit" in msg_lower or "tpm" in msg_lower or "rpm" in msg_lower:
            raise RuntimeError(
                "Groq rate limit reached (tokens or requests per minute). "
                "Please wait a moment before trying again."
            ) from exc
        if "401" in msg or "invalid_api_key" in msg_lower or "unauthorized" in msg_lower:
            raise RuntimeError(
                "Groq authentication failed: invalid API key. "
                "Please check your credentials in the sidebar or .env."
            ) from exc
        if "timeout" in msg_lower:
            raise RuntimeError(
                f"Groq request timed out ({GROQ_TIMEOUT:.0f}s limit). The service may be experiencing high load."
            ) from exc
        if "max completion tokens" in msg_lower or "json_validate_failed" in msg_lower:
            raise RuntimeError(
                "The analysis response exceeded token capacity before completing JSON generation. "
                "Please try a slightly shorter claim or narrower query."
            ) from exc
        raise RuntimeError(f"Groq API call failed: {exc}") from exc

    # --- Parse and validate response ---
    raw_content: str = response.choices[0].message.content or ""
    content_to_parse = raw_content.strip()
    # Strip markdown code blocks if present
    if content_to_parse.startswith("```"):
        content_to_parse = re.sub(r"^```(?:json)?\s*", "", content_to_parse, flags=re.IGNORECASE)
        content_to_parse = re.sub(r"\s*```$", "", content_to_parse)

    try:
        parsed_data = json.loads(content_to_parse)
    except json.JSONDecodeError:
        return None

    try:
        verdict = Verdict.model_validate(parsed_data)
    except Exception:
        return None

    # --- Filter sources to allowlist only ---
    verdict.sources = [s for s in verdict.sources if _is_allowed(s.url, allowed_urls)]

    return verdict
