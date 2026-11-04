"""NewsLens checker schema — Pydantic models for evidence-based claim checking.

Clean-room implementation. No code derived from fact-checker-agent (no license found).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    """A single retrieved source with its stance toward the claim."""

    url: str
    title: str = ""
    stance: Literal["supports", "refutes", "mixed", "unrelated"] = "unrelated"
    snippet: str = ""


class Verdict(BaseModel):
    """Structured evidence-based verdict returned by the LLM reasoning step."""

    verdict: Literal["supported", "refuted", "misleading", "unverifiable"]
    confidence: Literal["high", "medium", "low"]
    summary: str = Field(..., description="One- or two-sentence plain-language summary.")
    reasoning: str = Field(..., description="Explanation of how evidence supports the verdict.")
    caveats: str = Field(
        default="",
        description="Caveats, known limitations, or contradictions in evidence.",
    )
    sources: list[Source] = Field(
        default_factory=list,
        description="Subset of retrieved sources the model cites. URLs must match search results.",
    )


class SearchResult(BaseModel):
    """A single result returned by the Tavily search wrapper."""

    url: str
    title: str = ""
    snippet: str = ""
