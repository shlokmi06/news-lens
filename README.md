# NewsLens

NewsLens is an educational Streamlit web application designed to demonstrate and contrast two fundamentally distinct approaches to analyzing informational content:

1. **News-Style Risk Classifier:** A supervised machine learning model (TF-IDF + Logistic Regression) that predicts whether submitted text stylistically resembles examples labeled "real" or "fake" in historical training data. It features an explicit `UNCERTAIN` margin rather than forcing an artificial binary choice. **This does NOT verify factual truth.**
2. **Evidence-Based Claim Checker:** An agentic verification workflow that accepts one specific factual claim, issues balanced web searches for both supporting and refuting evidence via the Tavily Search API, and uses an LLM (Groq `llama-3.3-70b-versatile`) to reason over the retrieved evidence with strict URL citation whitelisting.

> ⚠️ **Core Principle:** The two analyses remain strictly separate in both the user interface and the codebase. **They are never combined into a single "truth score".** Style similarity to historical wire reporting does not make a statement true, and non-traditional writing style does not make a statement false.

---

## Operating Modes

NewsLens offers two operating modes for the Claim Checker:

| Feature | 🟢 Offline Demo Mode (Default / Zero Setup) | 🌐 Live Search Mode (Production) |
|:---|:---|:---|
| **API Keys Required** | **None** (100% offline) | `GROQ_API_KEY` and `TAVILY_API_KEY` |
| **Data Source** | Pre-recorded, clearly labeled static fixtures | Live Tavily web search API |
| **Reasoning Engine** | Static demonstration templates | Groq LPU (`llama-3.3-70b-versatile`) |
| **UI Experience** | Full UI cards, stances, confidence ratings | Full UI cards, stances, confidence ratings |
| **Sample Claims** | Quick-load buttons for Refuted, Supported, Misleading | Any user-entered claim (≤ 500 chars) |
| **Visual Labeling** | Prominent `[DEMO / FIXTURE DATA]` warnings | Live educational disclaimer |

> 📌 **Status Note:** Live verification against external APIs remains **pending** until an administrator supplies active third-party credentials and runs the live validation check. The application defaults safely to Offline Demo Mode when credentials are not configured.

---

## Architecture Overview

```text
                                 [ User Input ]
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
      [ Tab 1: Style Classifier ]                [ Tab 2: Claim Checker ]
                 │                                           │
         Text Normalization                        Select Operating Mode:
                 │                         ┌─────────────────┴─────────────────┐
        TF-IDF Vectorization               ▼                                   ▼
                 │                 [ Offline Demo Mode ]               [ Live Search Mode ]
        Logistic Regression                │                                   │
                 │                 Pre-recorded Fixtures               Dual Query Search:
       Uncertainty Band Logic              │                           1. <claim>
       [REAL / UNCERTAIN / FAKE]   Tagged: [DEMO FIXTURE]              2. <claim> debunked
                 │                         │                                   │
         Style Risk Report                 │                           Tavily Search API
                                           │                                   │
                                           │                           URL Allowlist Built
                                           │                                   │
                                           │                           Groq LLM Reasoning
                                           │                       (llama-3.3-70b-versatile)
                                           │                                   │
                                           │                       Citation Whitelist Filter
                                           │                                   │
                                           └─────────────────┬─────────────────┘
                                                             ▼
                                                    Structured Verdict
                                              [supported / refuted /
                                               misleading / unverifiable]
```

---

## Installation & Setup

### Prerequisites
- **Python 3.12** (Windows: `py -3.12`, Linux/macOS: `python3.12`)
- Git

### 1. Clone the Repository & Set Up Virtual Environment

**Windows (PowerShell):**
```powershell
git clone <repo-url> newslens
cd newslens
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
git clone <repo-url> newslens
cd newslens
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

Install production requirements:
```bash
pip install -r requirements.txt
```

Or install the package in editable development mode with test dependencies:
```bash
pip install -e ".[dev]"
```

---

## Credential Configuration (For Live Mode)

In **Offline Demo Mode**, no credentials are required.

To enable **Live Search Mode**:
1. **Groq API Key:** For high-speed LLM reasoning with `llama-3.3-70b-versatile`. Free tier available at [console.groq.com/keys](https://console.groq.com/keys).
2. **Tavily API Key:** For search queries and structured web snippets. Free tier provides 1,000 queries/month at [app.tavily.com](https://app.tavily.com).

### Setting Up Credentials

1. Copy the example configuration template:
   ```powershell
   Copy-Item .env.example .env     # Windows PowerShell
   # or
   cp .env.example .env            # Linux / macOS
   ```

2. Open `.env` and fill in your keys:
   ```env
   GROQ_API_KEY=gsk_your_groq_api_key_here
   TAVILY_API_KEY=tvly-your_tavily_api_key_here
   ```

3. **Per-Session Entry:** Alternatively, you can enter credentials directly into the password-masked fields in the Streamlit sidebar during your session.

### Security & Privacy Guarantee
- API keys are passed per-request directly to the API clients (`Groq(api_key=...)` and `TavilyClient(api_key=...)`).
- Visitor keys are **never** written to global `os.environ` or persisted to server logs.
- Live mode errors **never** silently fall back to demo fixtures.
- The `.env` file is excluded from git tracking via `.gitignore`. Never commit API keys to version control.

---

## Running the Application

### Local Python Execution
Launch the Streamlit web dashboard:
```bash
streamlit run src/newslens/app.py
```

The app will open in your default browser at `http://localhost:8501`.

### Docker Container (Optional)
A minimal `Dockerfile` is provided for containerized deployment:

```bash
# Build the container image
docker build -t newslens:latest .

# Run the container (Demo Mode / Offline)
docker run -p 8501:8501 newslens:latest

# Run the container with Live Mode credentials
docker run -p 8501:8501 -e GROQ_API_KEY="gsk_..." -e TAVILY_API_KEY="tvly-..." newslens:latest
```

*Note: Container build and execution requires Docker Engine or Docker Desktop installed on the host system.*

---

## Testing & Verification

### 1. Offline Test Suite (31 unit tests)
All 31 unit tests run completely offline in < 20 seconds without requiring external API keys:
```bash
pytest tests -v
```

The suite covers:
- **Classifier tests (`test_classifier.py`):** Normalization, uncertainty margins, toy pipeline predictions, SHA-256 sidecar checksums.
- **Checker tests (`test_checker.py`):** Schema validation, URL allowlist parsing, prompt injection fence removal, rate limit error trapping, markdown-fenced JSON handling.
- **Demo mode tests (`test_demo_mode.py`):** Guarantees zero external API calls in demo mode, verifies visible `[DEMO FIXTURE]` labeling, verifies credential enforcement in live mode, and ensures live errors never fall back to fixtures.

### 2. Live Integration Check (Opt-In)
When valid `GROQ_API_KEY` and `TAVILY_API_KEY` credentials are configured in `.env`, run the live check:

```bash
# Via pytest:
pytest tests/test_integration.py -v

# Or via the standalone inspection script:
python scripts/live_integration_check.py
```

*Note: Live integration checks consume 2 Tavily search requests and 1 Groq LPU completion.* If keys are absent, the check safely skips with setup instructions.

---

## Evaluation Results & Limitations

### 1. Classifier Evaluation & Publisher Confounding Caveat

Trained on a balanced 1,991-article corpus derived from the ISOT dataset (992 real-style, 999 fake-style):

| Metric | Holdout Test Score (20% Stratified Split) |
|:---|:---|
| **Accuracy** | **99.25%** |
| **Macro F1** | **99.25%** |
| **ROC-AUC** | **99.96%** |

> ⚠️ **The Reuters Dateline Shortcut:**
> Over **99.8%** of "REAL" articles in the ISOT training dataset originate from Reuters wire dispatches and begin with a standard dateline (e.g., `"WASHINGTON (Reuters) - ..."`), while "FAKE" articles originate from unverified political blogs.
> The classifier achieves >99% accuracy primarily by recognizing wire-service formatting, formal journalism markers, and publication datelines. **It does not possess real-world knowledge and cannot determine whether an event actually occurred.**

### 2. Evidence Checker Scope & Limitations
- **Single-Claim Scope:** Evaluates one specific factual claim (up to 500 characters) at a time. It does not extract claims automatically from entire articles.
- **Dependency on Search Indexing:** Live mode depends on what Tavily returns. Obscure or breaking claims may produce zero relevant results, resulting in `unverifiable`.
- **Free-Tier Rate Limits:** Heavy interactive usage may temporarily encounter Groq token/minute (TPM) limits or Tavily monthly quota limits. The application catches these and surfaces readable error notifications.
- **Adversarial Content Fencing:** All untrusted web snippets are enclosed in XML tags (`<evidence>`) and sanitized to prevent prompt injection from affecting LLM reasoning.
- **Strict Citation Whitelist:** The LLM can only cite URLs present in Tavily's structured search response. Fabricated citations are automatically purged.
- **Educational Aid:** The evidence checker is an educational aid and does not constitute a legally binding or authoritative fact-check.

---

## Attribution & Licenses

- **News-Style Classifier:** Derived from [Fake News Style-Risk Detector](https://github.com/AmirhosseinHonardoust/Fake-News-Detector) by Amir Honardoust, used under the **MIT License** (Copyright (c) 2025 Amir Honardoust).
- **Evidence-Based Claim Checker:** Independent **clean-room implementation**. The reference project `fact-checker-agent` lacks an open-source license; none of its code or proprietary materials were copied, adapted, or redistributed.
- **Dataset:** ISOT Fake News Dataset (University of Victoria).
- **Third-Party Libraries:**
  - `scikit-learn`, `joblib`, `pandas`, `numpy`: BSD / Apache 2.0
  - `streamlit`: Apache 2.0
  - `pydantic`: MIT License
  - `groq`: Apache 2.0
  - `tavily-python`: MIT License
  - `python-dotenv`: BSD 3-Clause
