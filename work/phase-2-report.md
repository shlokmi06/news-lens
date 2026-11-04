# NewsLens — Phase 2 Report

**Date:** 2026-11-03  
**Author:** Antigravity (AI coding assistant)  
**Project workspace:** `C:\Users\dinesh\.gemini\antigravity\scratch\newslens`

---

## 1. Files Added and Changed

### New files
| Path | Purpose |
|------|---------|
| `src/newslens/checker/__init__.py` | Package init; re-exports public symbols |
| `src/newslens/checker/schema.py` | Pydantic models: `Verdict`, `Source`, `SearchResult` |
| `src/newslens/checker/search.py` | Tavily search wrapper; builds URL allowlist |
| `src/newslens/checker/agent.py` | Groq LLM reasoning; URL whitelist enforcement; `_is_allowed` helper |
| `tests/test_checker.py` | 12 offline unit tests for the checker module |

### Modified files
| Path | Change |
|------|--------|
| `src/newslens/app.py` | Wrapped classifier in `tab1`; added `tab2` for claim checker; sidebar API key inputs; added `load_dotenv()` |
| `pyproject.toml` | Added `pydantic>=2.0`, `python-dotenv>=1.0`, `groq>=0.9.0`, `tavily-python>=0.5.0` to `[project].dependencies` |
| `requirements.txt` | Same additions; updated header to Phase 2 |
| `.env.example` | Added `GROQ_API_KEY` and `TAVILY_API_KEY` placeholders with links |

### Unchanged Phase 1 files
`src/newslens/classifier/` (all files), `src/newslens/config.py`, `src/newslens/__init__.py`, `tests/test_classifier.py`, `models/pipeline.joblib`, `models/pipeline.sha256`, `models/metrics.json`, `data/True.csv`, `data/Fake.csv`, `README.md`, `.gitignore`

---

## 2. Architecture and Request Flow

```
User enters claim (≤ 500 chars)
        │
        ▼
[Input validation + sanitization]
  - Strip <evidence>/<claim> fence tags
  - Whitespace collapse
  - Length truncation
        │
        ▼
[search_both()]  → Tavily API (two queries)
  Query 1: claim text
  Query 2: "{claim} debunked fact check false"
        │
        ▼
[URL allowlist built] ← ONLY from results[].url in API response dict
        │
        ▼
[check_claim()]  → Groq API (llama-3.3-70b-versatile)
  System: neutral fact-checker prompt
  User:   <claim>...</claim>  +  <evidence>...</evidence>
  Format: json_schema (Pydantic Verdict schema)
        │
        ▼
[Whitelist filter]
  Remove any sources whose URL is not in allowed_urls set
        │
        ▼
[Display verdict, confidence, reasoning, caveats, sources]
```

**Key security properties:**
- User claim is sanitized before insertion into the prompt (fence tags stripped).
- URL allowlist is built exclusively from `results[].url` in the Tavily response — not from body text, not from LLM output.
- After the LLM responds, `verdict.sources` is filtered against the allowlist — fabricated URLs are silently removed.
- API keys are passed per-request to `Groq(api_key=...)` and `TavilyClient(api_key=...)`; they are never written to `os.environ`.
- Keys are sourced from: Streamlit sidebar input → `.env` file (via `python-dotenv`) — with the `.env` file excluded from version control via `.gitignore`.

---

## 3. Python and Dependency Versions

**Runtime:**
- Python: 3.12.6
- Venv: `C:\Users\dinesh\.gemini\antigravity\scratch\newslens\.venv`

**Phase 2 additions (verified installed via pip):**

| Package | Installed version |
|---------|------------------|
| `pydantic` | 2.14.2 |
| `pydantic-core` | 2.50.2 |
| `python-dotenv` | 1.2.4 |
| `groq` | 1.7.0 |
| `tavily-python` | 0.8.5 |
| `httpx` | 0.28.1 |
| `httpcore` | 1.0.9 |
| `distro` | 1.9.0 |
| `tiktoken` | 0.14.0 |
| `regex` | 2026.9.29 |
| `sniffio` | 1.3.1 |

**Phase 1 (unchanged):**

| Package | Installed version |
|---------|------------------|
| `streamlit` | 1.45.1 |
| `scikit-learn` | 1.9.1 |
| `pandas` | 2.2.3 |
| `numpy` | 2.2.6 |
| `joblib` | 1.5.1 |
| `pytest` | 9.2.0 |

---

## 4. Model Identifier and Source

- **Groq model used:** `llama-3.3-70b-versatile`
- **Source:** Groq official documentation (searched 2026-11-03); confirmed current, 128K context window, JSON schema structured output supported.
- **Structured output method:** `response_format={"type": "json_schema", "json_schema": {"name": "verdict", "schema": Verdict.model_json_schema()}}` — native Groq SDK, no LangChain dependency.
- **No live API call was made** in tests; all Groq calls are mocked offline. Integration with real keys was not run (no keys configured) — this is expected per the task requirement to not claim results that weren't actually run.

---

## 5. Credential Setup Instructions

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Edit `.env` and fill in real keys:
   ```
   GROQ_API_KEY=gsk_...          # https://console.groq.com/keys (free tier)
   TAVILY_API_KEY=tvly-...       # https://app.tavily.com (free tier)
   ```
3. The `.env` file is in `.gitignore` and will not be committed.
4. Keys can alternatively be entered in the sidebar each session (password-masked inputs).
5. **Never commit real keys.** The `.env.example` file contains placeholder strings only.

---

## 6. Test Commands and Results

### Command
```powershell
Set-Location "C:\Users\dinesh\.gemini\antigravity\scratch\newslens"
.\.venv\Scripts\pytest.exe tests -v
```

### Result (verified, exit code 0)
```
platform win32 -- Python 3.12.6, pytest-9.2.0, pluggy-1.7.0
collected 19 items

tests/test_checker.py::test_schema_rejects_invalid_verdict PASSED        [  5%]
tests/test_checker.py::test_schema_rejects_invalid_confidence PASSED     [ 10%]
tests/test_checker.py::test_allowlist_valid_url_passes PASSED            [ 15%]
tests/test_checker.py::test_allowlist_fabricated_url_rejected PASSED     [ 21%]
tests/test_checker.py::test_allowlist_built_from_api_url_field_only PASSED [ 26%]
tests/test_checker.py::test_sanitize_removes_fence_tags PASSED           [ 31%]
tests/test_checker.py::test_empty_claim_raises_value_error PASSED        [ 36%]
tests/test_checker.py::test_blank_groq_key_raises_runtime_error PASSED   [ 42%]
tests/test_checker.py::test_malformed_groq_response_returns_none PASSED  [ 47%]
tests/test_checker.py::test_fabricated_source_filtered_from_verdict PASSED [ 52%]
tests/test_checker.py::test_counter_query_format PASSED                  [ 57%]
tests/test_checker.py::test_valid_verdict_round_trip PASSED              [ 63%]
tests/test_classifier.py::test_clean_text_basic PASSED                   [ 68%]
tests/test_classifier.py::test_strip_source_artifacts PASSED             [ 73%]
tests/test_classifier.py::test_text_cleaner_transformer PASSED           [ 78%]
tests/test_classifier.py::test_classify_probability_uncertainty_band PASSED [ 84%]
tests/test_classifier.py::test_classify_probability_validation PASSED    [ 89%]
tests/test_classifier.py::test_predict_text_with_toy_pipeline PASSED     [ 94%]
tests/test_classifier.py::test_checksum_verification PASSED              [100%]

======================== 19 passed in 65.43s (0:01:05) ========================
```

**19/19 passed.** Phase 1 classifier tests (7) and Phase 2 checker tests (12) both pass. Duration is dominated by `test_checksum_verification` loading `models/pipeline.joblib` from disk.

### App launch verification
```powershell
.\.venv\Scripts\python.exe -c "
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('src/newslens/app.py')
at.run(timeout=30)
assert not at.exception
print('OK - app launched successfully')
"
```
**Result:** `OK - app launched successfully` — `at.exception` was empty (`ElementList()`). The Streamlit `ScriptRunContext` warning is expected and benign in test/bare mode.

---

## 7. Sample Expected Claim Check Output (Illustrative)

> No live API keys were configured; the following illustrates the expected UI output for a successful check. Actual results depend on real-time search and model response.

**Claim:** "The Great Wall of China is visible from space with the naked eye."

**Expected verdict:** `refuted` or `misleading`  
**Expected confidence:** `high`  
**Expected summary:** "Multiple authoritative sources, including NASA astronauts, confirm that the Great Wall is not visible from space with the naked eye."  
**Expected sources:** 2–5 URLs from Tavily results, filtered to allowlist only.

---

## 8. Limitations

- **Free-tier rate limits:** Tavily free tier allows ~1,000 API calls/month; Groq free tier imposes per-minute and per-day token limits. Heavy use will hit limits.
- **Single-claim only:** One claim per request. No cross-claim correlation, no full-article claim extraction.
- **Search quality:** Verdict quality depends entirely on what Tavily returns. If relevant sources are not indexed, the verdict will be `unverifiable`.
- **No image/audio input, no user accounts, no history.**
- **Model hallucination risk:** Despite fenced prompts and allowlist filtering, the LLM may still reason incorrectly. The educational disclaimer in the UI addresses this.
- **Not a factual oracle:** The checker confirms or refutes based on evidence found online, not on ground truth. The same limitations apply as for any web-search-based fact-checker.
- **Network dependency:** Both Tavily and Groq require outbound internet access. Offline use is not supported.

---

## 9. Licensing Compliance

- **Classifier:** Derived from `AmirhosseinHonardoust/Fake-News-Detector` under MIT license. Copyright notice preserved in `src/newslens/classifier/__init__.py`. Attribution also in `README.md`.
- **Claim checker:** Clean-room implementation. The `fact-checker-agent` reference repository has **no license** (all rights reserved). No code, no logic, and no direct adaptations from that repository were used. Only its public README description of desired behavior was referenced.
- **Groq SDK (`groq==1.7.0`):** Apache 2.0 license.
- **Tavily SDK (`tavily-python==0.8.5`):** MIT license.
- **Pydantic (`pydantic==2.14.2`):** MIT license.
- **python-dotenv (`python-dotenv==1.2.4`):** BSD 3-Clause license.

---

## 10. Phase 1 Classifier Behavior: Unchanged

- The classifier tab is functionally identical to Phase 1.
- All 7 Phase 1 tests continue to pass (verified in this session, exit code 0).
- The only `app.py` change affecting the classifier is wrapping its content in `with tab1:` — no logic, threshold, or model loading change.
- `models/pipeline.joblib` was not modified.

---

## 11. Unresolved Issues / Open Items

| Issue | Severity | Notes |
|-------|----------|-------|
| No live integration test (no API keys configured) | Medium | Expected per task requirements; manual test needed with real keys before production use |
| Groq `json_schema` structured output may fail on model updates | Low | Model `llama-3.3-70b-versatile` is current as of 2026-11-03; verify if Groq changes model support |
| Tavily `timeout` parameter behavior | Low | `tavily-python` SDK may not surface httpx timeouts directly; test with slow networks |
| Streamlit `st.stop()` inside tabs | Low | `st.stop()` in a tab stops the entire script; acceptable for Phase 2, but consider `st.warning` + `return` in a refactor |

---

## 12. Recommended Next Phase (Phase 3)

**Phase 3 scope suggestion:**

1. **Live integration test suite:** Add `tests/test_integration.py` (skipped unless `GROQ_API_KEY` and `TAVILY_API_KEY` are present in environment). Run once with real keys before each release.
2. **Rate-limit UX:** Surface Groq/Tavily rate-limit errors with actionable messages ("Free tier exhausted — try again in 1 minute").
3. **Caching:** Cache claim results by normalized claim text for the session (avoid duplicate API calls on resubmit).
4. **README update:** Add "Claim Checker" section to README with setup steps and screenshot.
5. **Multi-claim extraction (optional, out of Phase 2 scope):** Accept a full article and extract 3–5 candidate claims using a lightweight NLP approach, then let the user pick one to check.

---

## 13. Sources Inspected

- Groq model list / documentation: https://console.groq.com/docs/models — inspected 2026-11-03
- Tavily Python SDK: https://docs.tavily.com/sdk/python — inspected 2026-11-03
- Pydantic v2 docs: https://docs.pydantic.dev/latest/ — inspected 2026-11-03
- Reference repository README only (no code used): https://github.com/faisalimam1/fact-checker-agent — inspected 2026-11-03

---

*Phase 2 complete. Stopping here per task instructions. Ready for product-owner review.*
