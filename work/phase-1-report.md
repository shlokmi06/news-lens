# Phase 1 Implementation Report: NewsLens Style-Risk Classifier

**Project Name:** NewsLens  
**Phase:** Phase 1 (Environment Setup & News-Style Classifier Integration)  
**Execution Date:** 2026-11-03  
**Status:** Complete — All Verification Tests Passing  
**Report File Path:** `work/phase-1-report.md`  

---

## 1. Executive Summary

Phase 1 of NewsLens has been successfully implemented. A dedicated Python 3.12 virtual environment was established, and the news-style risk classifier was integrated into a clean, modular package structure (`newslens.classifier`, `newslens.config`, and `newslens.app`). 

In strict adherence to project requirements:
- **MIT License Preservation:** Reference 1's MIT license and copyright notice (Copyright (c) 2025 Amir Honardoust) are preserved and attributed in all derived modules.
- **Fact-Checker Isolation:** Reference 2's unlicensed code was **completely excluded**; no evidence checking or web search was implemented.
- **Educational Guardrails:** The Streamlit interface explicitly warns users that the model evaluates stylistic writing patterns, not factual truth.
- **Verified Operation:** All code, dataset operations, model retraining, unit tests, and Streamlit app executions were directly executed and verified.

---

## 2. Files Added and Workspace Changes

The following files were created in the project workspace (`C:\Users\dinesh\.gemini\antigravity\scratch\newslens`):

```text
newslens/
├── .env.example                          # Configuration template (no secrets required)
├── .gitignore                            # Exclusions for Python caches, venv, and editor files
├── README.md                             # Setup guide, run instructions, and attribution
├── pyproject.toml                        # Project configuration and dependency specifications
├── requirements.txt                      # Pinned dependency requirements
├── data/
│   ├── Fake.csv                          # Permitted binary training data (999 fake-style rows)
│   └── True.csv                          # Permitted binary training data (992 real-style rows)
├── models/
│   ├── pipeline.joblib                   # Serialized scikit-learn pipeline (trained under Python 3.12)
│   ├── pipeline.joblib.sha256            # SHA-256 sidecar checksum
│   └── metrics.json                      # Holdout evaluation metrics and dataset profile
├── src/
│   └── newslens/
│       ├── __init__.py                   # Package initialization
│       ├── app.py                        # Streamlit web application with style classification UI
│       ├── config.py                     # Paths, decision thresholds, and educational disclaimers
│       └── classifier/
│           ├── __init__.py               # Classifier module exports
│           ├── text_clean.py             # TextCleaner transformer & regex cleaning (MIT licensed)
│           ├── model.py                  # Checksum verification, model loading, and inference (MIT licensed)
│           └── train.py                  # Local training and evaluation script (MIT licensed)
├── tests/
│   └── test_classifier.py                # 7 automated unit tests (cleaner, margins, checksums, inference)
└── work/
    ├── phase-0-audit.md                  # Preserved Phase 0 audit report
    └── phase-1-report.md                 # This Phase 1 implementation report
```

*Note on Upstream Preservation:* The reference clones in `references/fake-news-detector` and `references/fact-checker-agent` were left completely intact and unmodified. No upstream git branches or repositories were altered.

---

## 3. Python and Dependency Versions Used

The project was constructed and verified under **Python 3.12.6** (Windows 64-bit):

| Package | Installed Version | Role |
| :--- | :--- | :--- |
| **Python** | `3.12.6` | Runtime environment (`py -3.12`) |
| **scikit-learn** | `1.9.1` | TF-IDF vectorization and Logistic Regression pipeline |
| **pandas** | `2.3.3` | Dataset loading and deduplication |
| **numpy** | `2.5.4` | Numerical array handling and probability computation |
| **joblib** | `1.6.0` | Pipeline serialization and deserialization |
| **streamlit** | `1.66.1` | Web application interface |
| **pytest** | `9.2.0` | Test runner and assertions |

---

## 4. Model Loading, Retraining, and Verification

### 4.1 Bundled Artifact Verification & Scikit-Learn Compatibility
When loading the pre-trained `pipeline.joblib` artifact bundled in Reference 1:
1. **Module Name Resolution:** The original artifact was pickled under the top-level module `text_clean.TextCleaner`. Loading it within the `newslens` package initially resulted in `ModuleNotFoundError: No module named 'text_clean'`. This was solved in `newslens.classifier.model.load_pipeline` by registering a compatibility alias in `sys.modules["text_clean"]` pointing to `newslens.classifier.text_clean`.
2. **Scikit-Learn Version Warning:** Reference 1's model was trained with scikit-learn 1.6.1 on Python 3.10. Unpickling in scikit-learn 1.9.1 triggered an `InconsistentVersionWarning`. While inference executed (`[0.9809, 0.0191]`), unpickling across minor versions can be fragile.

### 4.2 Local Retraining Verification
To establish a fully clean, native artifact for Python 3.12 / scikit-learn 1.9.1, `newslens.classifier.train` was executed directly against `data/True.csv` and `data/Fake.csv`.
- Execution command: `python -m newslens.classifier.train`
- Training duration: < 4 seconds.
- Output artifacts generated:
  - `models/pipeline.joblib` (native Python 3.12 / sklearn 1.9.1 artifact)
  - `models/pipeline.joblib.sha256`
  - `models/metrics.json`
- Verification: The newly trained pipeline loads without any warnings, passes SHA-256 sidecar validation, and executes sample predictions seamlessly.

---

## 5. Classifier Performance and Documented Data Limitations

### 5.1 Holdout Performance Metrics
From `models/metrics.json` on a 20% stratified holdout set (399 samples):
- **Holdout Accuracy:** **99.25%** (`0.9925`)
- **Holdout Macro F1:** **99.25%** (`0.9925`)
- **Holdout ROC-AUC:** **99.96%** (`0.9996`)
- **Class Balance:** REAL: 992 rows, FAKE: 999 rows (after removing 7 duplicates).

### 5.2 Documented Dataset Limitations (Publisher Confounding)
As documented in the Phase 0 audit and emphasized throughout NewsLens:
1. **The Reuters Dateline Shortcut:** Over 99% of REAL examples in the ISOT-derived corpus begin with a standard Reuters dateline (e.g., `"WASHINGTON (Reuters) - ..."`), while FAKE examples originate from partisan blogs without wire formatting.
2. **Style vs. Truth:** A model trained on this data achieves >99% accuracy primarily by identifying Reuters wire-service house style, datelines, and formal press phrasing. It does not possess knowledge of real-world facts.
3. **Uncertainty Band:** When ambiguous or unformatted text is supplied, the classifier leverages its uncertainty margin (default $[0.45, 0.55]$) to output `UNCERTAIN` rather than forcing a low-confidence guess.

---

## 6. App Launch Verification & Automated Tests

### 6.1 Unit Tests Passing (`pytest`)
All 7 unit tests in `tests/test_classifier.py` passed in 2.88 seconds:
- `test_clean_text_basic`: Verified URL, email, and whitespace normalization.
- `test_strip_source_artifacts`: Verified dateline and token stripping.
- `test_text_cleaner_transformer`: Verified scikit-learn transformer protocol.
- `test_classify_probability_uncertainty_band`: Verified boundary conditions for REAL, UNCERTAIN, and FAKE.
- `test_classify_probability_validation`: Verified parameter validation.
- `test_predict_text_with_toy_pipeline`: Verified probability and prediction format.
- `test_checksum_verification`: Verified SHA-256 detection of valid and tampered files.

### 6.2 Streamlit Application Launch & Execution Verification
Two independent verification methods were conducted:
1. **Network Serving Check:**
   - Command: `streamlit run src/newslens/app.py --server.headless true --server.port 8505`
   - Result: Returned **HTTP Status 200** with clean socket binding. Process was cleanly terminated.
2. **Programmatic Component Test (`streamlit.testing.v1.AppTest`):**
   - Headless execution via Streamlit's official testing framework completed with **0 exceptions**.
   - Verified presence of page title `"NewsLens"`, subheader `"News-Style Risk Classifier"`, dataset limitation alerts, sliders, text inputs, and action buttons.

---

## 7. Unresolved Issues and Blockers

- **No Technical Blockers in Phase 1:** The Phase 1 scope (Python 3.12 environment, classifier module, local training, unit tests, and minimal Streamlit UI) is complete, functional, and verified.
- **Phase 2 Dependency:** As established in Phase 0, Reference 2 (`fact-checker-agent`) lacks an open-source license. When Phase 2 (evidence claim checking) begins, it must be developed as a **clean-room implementation** using LangChain/LangGraph and search APIs, rather than copying Reference 2's source code.

---

## 8. Recommended Next Phase

### Phase 2: Clean-Room Evidence-Based Claim Checker Integration
1. **Implement Independent Claim Checking Engine:**
   - Define Pydantic verdict schemas (`supported`, `refuted`, `misleading`, `unverifiable`).
   - Implement dual search queries (claim search + debunk counter-query) using Tavily Search API.
   - Implement a citation URL whitelist verification guard to eliminate ungrounded source links.
2. **Modular UI Integration:**
   - Add a distinct second section or tab in the Streamlit application for evidence checking.
   - Maintain strict separation between the News-Style Classifier and the Evidence Claim Checker.
3. **Testing & Credential Management:**
   - Add unit tests for citation whitelisting and prompt fencing.
   - Provide non-shared API key inputs in the sidebar.
