# Phase 0 Audit Report: NewsLens Architecture & Feasibility Analysis

**Project Name:** NewsLens  
**Phase:** Phase 0 (Discovery, Inspection, Compliance & Architecture Audit)  
**Inspection Date:** 2026-11-03  
**Status:** Complete — Buildability Verdict: **Conditional Approval (Legal Blocker on Reference 2 Code Reuse)**  
**Target Output Path:** `work/phase-0-audit.md`  

---

## 1. Executive Summary & Buildability Verdict

NewsLens is an educational Streamlit application designed to combine two independent, clearly separated analytical lenses:
1. **News-Style Risk Classification:** A supervised TF-IDF + Logistic Regression model that classifies whether input text stylistically resembles known "real" or "fake" news examples in its training set, providing an `UNCERTAIN` band rather than forcing a brittle binary answer. This is explicitly framed as style-risk modeling, not factual truth verification.
2. **Evidence-Based Claim Checking:** An agentic workflow where a user enters one specific factual claim, triggering automated web searches for both supporting and refuting evidence, followed by LLM-driven reasoning that produces structured verdicts (`supported`, `refuted`, `misleading`, `unverifiable`) with strictly verified citations.

### Buildability Verdict: Conditional Buildability
- **Technical Feasibility:** **High**. A single unified Python 3.12 environment can cleanly satisfy the dependency requirements for both components without core dependency conflicts. Both pipelines can be hosted concurrently within a single Streamlit web application.
- **Architecture & Concept Soundness:** **Sound**. Both reference projects emphasize that stylistic text classification must never be confused with evidence-backed truth verification. Keeping the two analyses isolated in both code and UI directly reflects best practices in responsible AI.
- **Legal / Compliance Blocker:** **CRITICAL BLOCKER on Reference 2 Direct Code Reuse**.
  - Reference 1 (`Fake-News-Detector`) has an explicit **MIT License**, permitting code reuse with attribution.
  - Reference 2 (`fact-checker-agent`) has **NO LICENSE** anywhere in its repository, pyproject, or commit history. Under copyright law and GitHub Terms of Service, all rights are reserved by the author (Faisal Imam). **Direct copying, distribution, or inclusion of Reference 2's code in NewsLens is strictly legally prohibited.**
  - **Resolution Path:** NewsLens must either (a) secure an explicit open-source license grant from the author of `fact-checker-agent`, or (b) implement a **clean-room re-implementation** of the dual-search and verified-citation agent workflow using standard, permissively licensed open-source packages (such as LangChain/LangGraph or direct API calls).

---

## 2. What Each Reference Project Actually Does

### Reference 1: Fake News Style-Risk Detector (`Fake-News-Detector`)
- **Author:** Amir Honardoust
- **Repository:** [https://github.com/AmirhosseinHonardoust/Fake-News-Detector](https://github.com/AmirhosseinHonardoust/Fake-News-Detector)
- **Inspected Commit:** `f02ce2b78d85ea76d198cd1f4f5a0f8bfe31fac7`
- **Core Functionality:**
  - Trains a binary text classification pipeline combining `TextCleaner` (custom scikit-learn transformer), `TfidfVectorizer`, and `LogisticRegression`.
  - Normalizes text: lowercasing, stripping URLs, emails, non-ASCII characters, and whitespace.
  - Employs an uncertainty band (`uncertainty_margin` default 0.10 centered around threshold 0.50): returns `UNCERTAIN` if `0.45 <= p(fake) <= 0.55`, otherwise `REAL` or `FAKE`.
  - Performs dataset leakage analysis: detects that ~99.8% of "REAL" articles contain the token "Reuters" while <1% of "FAKE" articles do, demonstrating that high raw accuracy is primarily driven by source-recognition artifacts.
  - Provides a `--strip-source-artifacts` de-leaked training mode and source-confounding diagnostic reports.
  - Implements checksum verification (`.sha256` sidecars) and scikit-learn compatibility shims (`ensure_sklearn_compatibility`) to mitigate pickle deserialization issues.
  - Exposes both a command-line interface (`src/detect_fake_news.py`) and a Streamlit dashboard (`src/streamlit_app.py`).
  - **Explicit Non-Goals:** Does not verify external truth, does not search the web, and does not act as a fact-checker.

### Reference 2: Fact Checker Agent (`fact-checker-agent`)
- **Author:** Faisal Imam
- **Repository:** [https://github.com/faisalimam1/fact-checker-agent](https://github.com/faisalimam1/fact-checker-agent)
- **Inspected Commit:** `e4dc77f8f94f13156c6c52686a719a8422933583`
- **Core Functionality:**
  - Implements an autonomous fact-checking agent using LangChain, LangGraph, Groq (`ChatGroq` with `llama-3.3-70b-versatile` default), and Tavily Search API.
  - **Dual-Search Retrieval:** Before the LLM runs, it automatically issues two web searches: one for the user claim, and a counter-query (`<claim> debunked fact check false`) to avoid confirmation bias.
  - **Structured Verdict:** Enforces a validated Pydantic model (`Verdict`) returning one of four strict verdicts: `supported`, `refuted`, `misleading`, or `unverifiable`, accompanied by confidence level (`high`, `medium`, `low`), summary, reasoning, sources, and caveats.
  - **Prompt Fencing & Injection Defense:** Encloses untrusted claim and scraped search snippets inside `<claim>` and `<evidence>` tags, sanitizing any closing XML tags and escaping special characters.
  - **Search Tool Guardrail & Whitelist Enforcement:** Wraps Tavily Search in a constrained tool (`make_search_tool`) exposing only `query` (preventing attackers from manipulating search domains or depth) and enforcing a budget of at most 3 follow-up searches.
  - **Citation Verification:** Whitelists exact URLs returned in Tavily's `results[].url`. After LLM synthesis, any cited URL that does not match the whitelist is systematically dropped before display to prevent hallucinated citations.
  - **Multi-Tenancy & Key Isolation:** Passes API keys per request rather than storing them in global `os.environ` to prevent credential leakage in shared Streamlit sessions.
  - Exposes both a CLI (`cli.py`) and a Streamlit UI (`streamlit_app.py`) driven by an identical generator (`iter_progress`).

---

## 3. Repository & Workspace Findings

### Current Workspace State
- **Initial State:** Prior to Phase 0 execution, no workspace or project code existed in the development environment.
- **Workspace Directory:** Established project root at `C:\Users\dinesh\.gemini\antigravity\scratch\newslens`.
- **References Directory:** `references/` directory created within the project workspace, where public clones were downloaded for read-only inspection:
  - `references/fake-news-detector/`
  - `references/fact-checker-agent/`
- **Integrity:** Originals remain unmodified; no upstream git push operations were attempted.
- **Existing User Work:** Confirmed no prior user files were overwritten or removed.

### Reference Repositories Comparison Matrix

| Attribute | Reference 1: `Fake-News-Detector` | Reference 2: `fact-checker-agent` |
| :--- | :--- | :--- |
| **Primary Framework** | scikit-learn, pandas, numpy, joblib | LangChain, LangGraph, Pydantic, Tavily, Groq |
| **Python Requirement** | `>=3.10` | `>=3.12, <3.14` |
| **Web UI** | Streamlit (`>=1.33, <2.0`) | Streamlit (`>=1.40`, pinned `1.60.0`) |
| **External API Keys** | None (100% offline local inference) | Groq API Key & Tavily API Key |
| **Model Artifacts** | `outputs/pipeline.joblib` (~1.4 MB) | External API LLM (`llama-3.3-70b-versatile`) |
| **Local Data Files** | `data/True.csv`, `data/Fake.csv` (~4 MB total) | None (retrieves live web data) |
| **License** | **MIT License** (Copyright (c) 2025 Amir) | **NO LICENSE** (All Rights Reserved) |
| **Attribution Requirement** | MIT copyright notice preservation required | Direct code reuse legally blocked |

---

## 4. License, Attribution & Legal Audit

### 4.1 Classifier (`Fake-News-Detector`)
- **Code License:** Explicit MIT License found in `LICENSE` file:
  ```text
  MIT License
  Copyright (c) 2025 Amir
  ```
- **Reuse Terms:** Permitted for commercial and private use, modification, distribution, and sublicensing, subject to including the original copyright notice and permission notice in all copies or substantial portions of the software.
- **Dataset Terms:**
  - Files `data/True.csv` and `data/Fake.csv` are downsampled subsets derived from the widely circulated ISOT Fake News Dataset (University of Victoria).
  - The dataset consists of scraped Reuters news articles and unverified political blogs from 2016–2017.
  - While educational reuse is standard practice, the data has well-documented source bias and cannot be treated as a general factual ground truth.
- **Model Weights:** Serialized as `outputs/pipeline.joblib`. Under MIT license terms, the pipeline can be loaded or retrained.

### 4.2 Fact-Checker Agent (`fact-checker-agent`)
- **Code License:** **NONE**.
  - A recursive search of the repository and full git history (all 5 commits from inception to HEAD) confirmed the absence of any license file (`LICENSE`, `COPYING`, etc.) and no license declaration in `pyproject.toml` or `README.md`.
  - Under international copyright conventions and GitHub Terms of Service, silence implies **All Rights Reserved**. The author retains full exclusive copyright.
- **Reuse Ruling:** **Direct code copying, adaptation, or redistribution is BLOCKED.**
- **Legal Compliance Strategy for NewsLens:**
  1. *Option A (Permission):* Request author Faisal Imam to add an explicit open-source license (MIT or Apache 2.0).
  2. *Option B (Clean-Room Re-Implementation - Recommended):* Architectural concepts and engineering workflows (dual retrieval queries, Pydantic verdict models, regex URL whitelisting, prompt fencing) are ideas/methods, not copyrightable code expressions. NewsLens can implement these patterns independently using standard open-source libraries (`langchain`, `pydantic`, `requests`/`tavily-python`) without copying source files.

---

## 5. Dependency & Environment Compatibility

### 5.1 Python Version Plausibility
- `Fake-News-Detector` specifies: `requires-python = ">=3.10"`
- `fact-checker-agent` specifies: `requires-python = ">=3.12,<3.14"`
- Host system check:
  - Default Python: Python 3.13.9
  - Available Python via launcher: Python 3.12 (64-bit) (`py -0` confirms `-V:3.12 *`)
- **Verdict:** A single virtual environment using **Python 3.12** cleanly satisfies both constraint sets:
  $$\text{Python 3.12} \in [\ge 3.10] \cap [\ge 3.12, < 3.14]$$

### 5.2 Dependency Collision Analysis
Inspecting `fake-news-detector/requirements.txt` vs `fact-checker-agent/requirements.txt`:

| Package Domain | Reference 1 Requirement | Reference 2 Requirement | Single-Env Harmonized Target | Risk / Conflict Level |
| :--- | :--- | :--- | :--- | :--- |
| **Streamlit** | `streamlit>=1.33,<2.0` | `streamlit>=1.40` (pinned `1.60.0`) | `streamlit>=1.40,<2.0` | **None** (compatible) |
| **Pydantic** | *(none)* | `pydantic>=2.0` | `pydantic>=2.10,<3.0` | **None** |
| **Data / ML** | `scikit-learn>=1.4,<2.0`, `pandas>=2.0,<3.0`, `numpy>=1.25,<3.0`, `joblib>=1.3,<2.0` | *(none)* | `scikit-learn~=1.6.1`, `pandas~=2.2.3`, `numpy~=1.26.4`, `joblib~=1.4.2` | **Low** |
| **LangChain Core** | *(none)* | `langchain>=1.3`, `langchain-core>=0.3`, `langgraph>=1.0` | `langchain>=1.3.14`, `langchain-core>=1.5.3`, `langgraph>=1.2.10` | **Low** |
| **Integrations** | *(none)* | `langchain-groq>=0.3`, `langchain-tavily>=0.2`, `python-dotenv>=1.0` | `langchain-groq~=1.1.3`, `langchain-tavily~=0.2.18`, `python-dotenv~=1.2.2` | **Low** |

### 5.3 Model Serialization & Artifact Compatibility
- `Fake-News-Detector`'s bundled artifact `outputs/pipeline.joblib` was created with `scikit-learn==1.6.1` on Python 3.10 (recorded in `outputs/artifact_environment.json`).
- If scikit-learn version differences occur in Python 3.12, the repository includes `src/model_compat.py` with `ensure_sklearn_compatibility()`, and provides a quick local training script (`python src/train_model.py`) that generates fresh artifacts in under 10 seconds.

### 5.4 Tooling Note
`uv` is not present on the host PATH. Standard `python -m venv` and `pip` can be utilized cleanly without external binary dependencies.

---

## 6. API Keys, Network, Data & Hardware Constraints

### 6.1 API Keys & Secrets
- **Style Classifier:** No API keys or remote accounts required.
- **Claim Checker:**
  - `GROQ_API_KEY`: Required for LLM inference (Llama-3.3-70B). Free tier available from Groq Console.
  - `TAVILY_API_KEY`: Required for Tavily Search API. Free tier allows 1,000 queries per month.
- **Handling Strategy:** Must support user-provided keys via Streamlit sidebar (without leaking into global `os.environ`), with optional local `.env` fallback for development.

### 6.2 Network & Bandwidth
- **Classifier:** 100% offline inference.
- **Claim Checker:** Requires outbound HTTPS network calls to:
  - `api.groq.com:443` (LLM completions)
  - `api.tavily.com:443` (Web search)
- Timeouts must be enforced on outbound requests (e.g. 20s for search, 30s for LLM) to prevent unhandled thread hangs in Streamlit.

### 6.3 Data & Storage
- Total disk footprint for code, data, and models is negligible (< 20 MB):
  - Training CSVs: `data/True.csv` (1.8 MB), `data/Fake.csv` (2.0 MB).
  - Serialized pipeline: `pipeline.joblib` (1.4 MB).
- No heavy local embeddings or PyTorch weights are required.

### 6.4 Hardware Constraints
- Minimal CPU and memory overhead:
  - Inference executes in < 50ms on standard CPU for TF-IDF + Logistic Regression.
  - LLM compute is offloaded to Groq LPUs.
  - Runs comfortably on standard client hardware (e.g. 2 cores, 4 GB RAM).

---

## 7. Main Integration Risks & Mitigations

1. **Cognitive / UI Bleed (Combining Scores):**
   - *Risk:* Users or stakeholders might attempt to blend the classifier probability and the fact-checker verdict into a single composite "Trust Score".
   - *Mitigation:* Strict UI segregation. Display the tools either in two separate tabs (`Style Analysis` vs. `Claim Verification`) or two distinctly bordered, side-by-side containers with explicit educational disclaimers explaining that style similarity does not equate to factual truth.
2. **Legal Infringement on Unlicensed Reference Code:**
   - *Risk:* Accidental copy-pasting of Reference 2 files into the NewsLens repository.
   - *Mitigation:* Author all claim-checking logic via clean-room development under Phase 1, treating Reference 2 solely as a behavioral blueprint.
3. **API Rate Limiting & Quota Depletion:**
   - *Risk:* Free-tier quotas on Tavily (1,000 monthly searches) or Groq may be exhausted during interactive testing.
   - *Mitigation:* Implement caching (`st.cache_data` for search queries), client-side input validation, and a mock/offline mode for testing without active API keys.
4. **Adversarial Web Content (Prompt Injection):**
   - *Risk:* Search results retrieved from the open web may contain malicious prompt injections designed to manipulate the LLM verdict.
   - *Mitigation:* Retain prompt fencing (`<claim>` and `<evidence>`), sanitize closing fence tokens, truncate snippet lengths, and enforce structured Pydantic output validation.
5. **Pickle / Joblib Arbitrary Code Execution:**
   - *Risk:* Deserializing untrusted `.joblib` files poses security risks.
   - *Mitigation:* Verify SHA-256 sidecars prior to unpickling, or retrain the pipeline directly within the deployment setup.

---

## 8. Recommended First-Release Scope (MVP)

To ensure rapid delivery, stability, and adherence to requirements, the first release must maintain a tight educational focus:

### In Scope
- **Input Modalities:**
  - One text area for pasting news text / article excerpt for the News-Style Classifier.
  - One single-line input field for entering one specific factual claim (max 500 chars) for Evidence-Based Claim Checking.
- **Classification Output:**
  - Returns `REAL`, `FAKE`, or `UNCERTAIN` based on configurable threshold and uncertainty margin.
  - Shows fake-probability score and explanation of dataset limitations (Reuters confounding).
- **Claim Checking Output:**
  - Automatically performs balanced search (claim + debunk query).
  - Returns structured verdict (`supported`, `refuted`, `misleading`, `unverifiable`) with confidence level.
  - Displays verified source citations with clickable links and stance indicators.
  - An expandable audit panel showing all sources inspected.
- **Configuration & Security:**
  - Sidebar for API key entry (Groq and Tavily) with `.env` fallback.
  - Clear visual demarcation and disclaimer banner stating the two analyses are fundamentally distinct.

### Out of Scope (Explicitly Excluded)
- Image, audio, video, or URL-scraping inputs.
- Multi-user authentication, user databases, or session tracking.
- Automated multi-claim extraction from full-length articles (the user must select and input one specific claim).
- Fine-tuning or local hosting of large language models.

---

## 9. Proposed Project Folder Structure

```text
newslens/
├── .env.example                  # Template for required API keys (GROQ_API_KEY, TAVILY_API_KEY)
├── .gitignore                    # Python, virtualenv, joblib artifacts, secrets exclusions
├── README.md                     # NewsLens overview, architecture, educational rationale, setup
├── pyproject.toml                # Unified Python 3.12 project metadata and dependency specification
├── requirements.txt              # Pinned production dependencies for deployment
├── work/
│   └── phase-0-audit.md          # This audit report
├── references/                   # Read-only reference clones (excluded from version control/distribution)
│   ├── fake-news-detector/
│   └── fact-checker-agent/
├── src/
│   └── newslens/
│       ├── __init__.py
│       ├── app.py                # Main Streamlit web application
│       ├── classifier/           # Component 1: News-Style Risk Classifier (MIT-derived/clean)
│       │   ├── __init__.py
│       │   ├── text_clean.py     # TextCleaner transformer & normalization
│       │   ├── model.py          # Model loading, SHA-256 verification, and inference
│       │   └── train.py          # Script for local model training and artifact generation
│       ├── checker/              # Component 2: Evidence-Based Claim Checker (Clean-Room Implementation)
│       │   ├── __init__.py
│       │   ├── schema.py         # Pydantic models (Verdict, Source, SearchQuery)
│       │   ├── search.py         # Tavily search wrapper, query generation, URL whitelisting
│       │   ├── agent.py          # LLM reasoning orchestration (Groq/LangChain)
│       │   └── prompts.py        # System prompt and untrusted content fencing
│       └── ui/
│           ├── __init__.py
│           ├── components.py     # Streamlit cards, metric widgets, disclaimers
│           └── styles.py         # CSS and badge styling (verdicts, stances)
├── data/                         # Small training dataset for classifier
│   ├── True.csv
│   └── Fake.csv
├── models/                       # Model artifacts and checksums
│   ├── pipeline.joblib
│   └── pipeline.joblib.sha256
└── tests/
    ├── test_classifier.py        # Unit tests for text cleaning and inference
    ├── test_citation_guard.py    # Unit tests for URL whitelisting & fence sanitization
    └── test_schema.py            # Unit tests for Pydantic Verdict validation
```

---

## 10. Concrete Acceptance Criteria for Phase 1

1. **Environment & Packaging:**
   - A single virtual environment (`.venv`) created with Python 3.12 installs all dependencies specified in `pyproject.toml` without version errors.
2. **Classifier Module Integration:**
   - MIT license from Reference 1 is preserved with full attribution in `src/newslens/classifier/`.
   - The classifier module loads the pipeline, validates checksums, and accurately infers `REAL`, `FAKE`, or `UNCERTAIN` on test phrases.
   - Text shorter than the minimum word count prompts a clear warning rather than failing silently.
3. **Claim Checker Clean-Room Implementation:**
   - Independent implementation of the dual-search mechanism (claim query + debunk query).
   - Strict Pydantic output validation ensuring verdicts conform to `supported`, `refuted`, `misleading`, or `unverifiable`.
   - Active URL whitelist verification preventing any ungrounded links from rendering.
   - Robust prompt fencing preventing injection payloads from escaping `<evidence>` blocks.
4. **Streamlit UI Segregation:**
   - The UI presents the Style Classifier and Claim Checker in strictly separate sections with clear headers and independent triggers.
   - A prominent educational notice explains why the two results are distinct and must never be merged into a single truth metric.
5. **Testing Suite:**
   - Automated unit test suite (`pytest`) passing with tests covering text normalization, uncertainty margins, citation whitelisting, and schema validation.

---

## 11. Questions & Decisions for Product Owner

1. **Reference 2 Code Strategy:**
   - *Decision Needed:* Do you approve proceeding with a **clean-room re-implementation** of the claim-checking agent workflow using LangChain/LangGraph and Tavily/Groq APIs, or would you prefer contacting the author (Faisal Imam) to request formal licensing?
2. **LLM Provider Redundancy:**
   - *Question:* Groq with Llama-3.3-70B offers fast inference on free tier, but rate limits can be tight (e.g. RPM/TPM ceilings). Should Phase 1 include a fallback provider (e.g., Google Gemini API or OpenAI-compatible endpoint) configured via environment variables?
3. **UI Presentation Layout:**
   - *Preference:* Do you prefer a **Tabbed Layout** (`[ Tab 1: Style-Risk Classifier ]` | `[ Tab 2: Evidence Claim-Checker ]`) or a **Two-Column Side-by-Side Dashboard**? (Tabs offer stronger psychological separation between style and truth; side-by-side allows simultaneous comparison).
4. **Dataset Retraining Policy:**
   - *Question:* Should Phase 1 bundle the pre-trained joblib artifact from Reference 1 directly, or should the build step automatically retrain a fresh pipeline from the bundled CSV data on the target machine during initialization?

---

## 12. Sources Inspected & Inspection Log

- **Inspection Date:** 2026-11-03 (Local time 19:48:47+05:30)
- **Reference 1 Repository:**
  - URL: `https://github.com/AmirhosseinHonardoust/Fake-News-Detector`
  - Commit SHA: `f02ce2b78d85ea76d198cd1f4f5a0f8bfe31fac7`
  - Inspected Files: `LICENSE`, `README.md`, `pyproject.toml`, `requirements.txt`, `src/text_clean.py`, `src/detect_fake_news.py`, `src/model_compat.py`, `src/train_model.py`, `src/streamlit_app.py`, `docs/data_statement.md`, `docs/model_card.md`, `docs/security.md`, `outputs/artifact_environment.json`.
- **Reference 2 Repository:**
  - URL: `https://github.com/faisalimam1/fact-checker-agent`
  - Commit SHA: `e4dc77f8f94f13156c6c52686a719a8422933583`
  - Inspected Files: `README.md`, `pyproject.toml`, `requirements.txt`, `uv.lock`, `.env.example`, `cli.py`, `streamlit_app.py`, `src/factchecker/agent.py`, `src/factchecker/config.py`, `src/factchecker/__init__.py`, `tests/test_citation_guard.py`, full git commit log (5 commits).
