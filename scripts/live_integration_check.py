"""NewsLens — Standalone Live Integration Verification Script.

Runs an end-to-end verification against live Tavily and Groq APIs if credentials
are configured in `.env` or the current environment.

USAGE:
    python scripts/live_integration_check.py

SECURITY & QUOTA NOTICE:
    - Never prints or logs API keys.
    - Consumes 2 Tavily search requests and 1 Groq LPU completion.
    - If credentials are not set, exits cleanly with setup instructions.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root and src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv

load_dotenv(project_root / ".env")


def main() -> int:
    print("=" * 65)
    print("NewsLens Phase 3 — Live Service Integration Validation")
    print("=" * 65)

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    is_groq_placeholder = not groq_key or groq_key.startswith("your_") or "placeholder" in groq_key.lower()
    is_tavily_placeholder = not tavily_key or tavily_key.startswith("your_") or "placeholder" in tavily_key.lower()

    if is_groq_placeholder or is_tavily_placeholder:
        print("\n[STATUS: PENDING - CREDENTIALS REQUIRED]")
        print("Live integration check requires valid credentials in .env:")
        if is_groq_placeholder:
            print("  - GROQ_API_KEY: Missing or placeholder.")
        else:
            print("  - GROQ_API_KEY: Configured [OK].")

        if is_tavily_placeholder:
            print("  - TAVILY_API_KEY: Missing or placeholder.")
        else:
            print("  - TAVILY_API_KEY: Configured [OK].")

        print("\nTo run this live verification:")
        print("  1. Copy .env.example to .env:  cp .env.example .env")
        print("  2. Add your free API keys to .env:")
        print("       - Groq:   https://console.groq.com/keys")
        print("       - Tavily: https://app.tavily.com")
        print("  3. Run:  python scripts/live_integration_check.py")
        print("=" * 65)
        return 0

    print("\n[CREDENTIALS DETECTED]")
    print(f"  - GROQ_API_KEY:   Set ({len(groq_key)} chars, redacted)")
    print(f"  - TAVILY_API_KEY: Set ({len(tavily_key)} chars, redacted)")

    from newslens.checker.agent import GROQ_MODEL, check_claim
    from newslens.checker.search import counter_query, search_both

    claim = "The Great Wall of China is visible from space with the naked eye."
    print(f"\n[TEST CLAIM]: \"{claim}\"")

    # 1. Dual Query Inspection
    c_query = counter_query(claim)
    print("\n1. Search Query Verification:")
    print(f"   Supporting Query: \"{claim}\"")
    print(f"   Debunking Query:  \"{c_query}\"")

    # 2. Search Retrieval
    print("\n2. Executing Tavily Search...")
    try:
        results, allowed_urls = search_both(claim, tavily_key, max_results=3)
    except Exception as exc:
        print(f"   [FAIL] Tavily search error: {exc}")
        return 1

    print(f"   Retrieved {len(results)} total deduplicated results.")
    print(f"   URL Allowlist size: {len(allowed_urls)} distinct URLs.")

    # Verify every allowed URL comes from results[].url
    result_urls = {r["url"] for r in results}
    assert allowed_urls == result_urls, "Allowlist does not match results[].url!"
    print("   [PASS] Allowlist exclusively derived from structured API result URLs.")

    for i, r in enumerate(results[:3], start=1):
        print(f"     [{i}] {r['title'][:60]} -> {r['url']}")

    # 3. LLM Reasoning & Citation Whitelist
    print(f"\n3. Executing Groq LLM Reasoning (model: {GROQ_MODEL})...")
    try:
        verdict = check_claim(
            claim=claim,
            search_results=results,
            allowed_urls=allowed_urls,
            groq_api_key=groq_key,
        )
    except Exception as exc:
        print(f"   [FAIL] Groq reasoning error: {exc}")
        return 1

    if verdict is None:
        print("   [FAIL] Model response could not be parsed into Verdict schema.")
        return 1

    print("   [PASS] Structured Verdict generated successfully.")
    print(f"   Verdict:    {verdict.verdict.upper()}")
    print(f"   Confidence: {verdict.confidence.upper()}")
    print(f"   Summary:    {verdict.summary}")
    print(f"   Reasoning:  {verdict.reasoning}")
    if verdict.caveats:
        print(f"   Caveats:    {verdict.caveats}")

    print("\n4. Citation Integrity Check:")
    print(f"   Cited sources count: {len(verdict.sources)}")
    for s in verdict.sources:
        in_whitelist = s.url in allowed_urls
        print(f"     - [{s.stance.upper()}] {s.title} ({s.url}) -> Whitelisted: {in_whitelist}")
        assert in_whitelist, f"Fabricated URL escaped whitelist: {s.url}"

    print("   [PASS] All cited sources verified against Tavily allowlist.")

    print("\n" + "=" * 65)
    print("ALL LIVE INTEGRATION CHECKS PASSED.")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
