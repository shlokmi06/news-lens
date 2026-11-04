"""NewsLens — Streamlit Web Application.

A modern educational interface combining two separate analyses:
1. News-Style Classifier (Tab 1): Supervised TF-IDF + Logistic Regression style-pattern risk modeling.
2. Evidence-Based Claim Checker (Tab 2): Balanced search via Tavily and 120B LLM reasoning via Groq.

The two analyses remain strictly separated; results are never combined into a single score.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from newslens.classifier.model import (
    load_pipeline,
    predict_text,
    verify_checksum,
)
from newslens.config import (
    DEFAULT_GROQ_API_KEY,
    DEFAULT_METRICS_PATH,
    DEFAULT_MODEL_PATH,
    DEFAULT_TAVILY_API_KEY,
    DEFAULT_THRESHOLD,
    DEFAULT_UNCERTAINTY_MARGIN,
    LEAKAGE_LIMITATION_NOTICE,
    MIN_CHARS,
    MIN_TOKENS,
    PROJECT_ROOT,
    STYLE_DISCLAIMER,
)

# Load local .env if present
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=True)


# ---------------------------------------------------------------------------
# Cached helpers
# ---------------------------------------------------------------------------


@st.cache_resource
def get_cached_pipeline(model_path: str):
    return load_pipeline(model_path, verify=True)


def load_metrics_data(metrics_path: Path) -> dict | None:
    if metrics_path.exists():
        try:
            return json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def validate_text(text: str) -> tuple[bool, str]:
    cleaned = text.strip()
    if not cleaned:
        return False, "Please enter some text to classify."
    tokens = [t for t in cleaned.split() if t]
    if len(cleaned) < MIN_CHARS or len(tokens) < MIN_TOKENS:
        return (
            False,
            f"Input text is very short ({len(tokens)} words, {len(cleaned)} chars). "
            f"For reliable style classification, provide at least {MIN_TOKENS} words / {MIN_CHARS} characters.",
        )
    return True, ""


# ---------------------------------------------------------------------------
# Sample texts for classifier tab
# ---------------------------------------------------------------------------

SAMPLE_WIRE = (
    "WASHINGTON (Reuters) - The White House on Monday presented its proposed economic roadmap "
    "to congressional leaders, urging bipartisan support on newly proposed infrastructure spending. "
    "Officials briefed reporters in Washington following bilateral discussions."
)

SAMPLE_BLOG = (
    "BREAKING SHOCKING BOMBSHELL: The mainstream media elites are panicking right now after "
    "secret documents were leaked revealing massive corruption! You will not believe what they "
    "did behind closed doors. Share this everywhere before it gets censored!"
)

SAMPLE_AMBIGUOUS = (
    "A regular meeting took place this afternoon where multiple local representatives discussed "
    "general policy considerations and economic observations without reaching a formal conclusion."
)


# ---------------------------------------------------------------------------
# Credential helpers (Permanently connected with env / config fallbacks)
# ---------------------------------------------------------------------------

_CHECKER_DISCLAIMER = (
    "**Educational Aid:** This tool searches the live web for evidence related to your claim and "
    "uses a 120B parameter AI model to reason over retrieved sources. "
    "**This is not an authoritative fact-check.** Always consult original primary sources."
)


def _get_api_keys() -> tuple[str, str]:
    """Retrieve API keys from .env or config defaults, ensuring they are always connected."""
    if _env_file.exists():
        load_dotenv(_env_file, override=True)
    groq_key = (os.getenv("GROQ_API_KEY") or "").strip() or DEFAULT_GROQ_API_KEY
    tavily_key = (os.getenv("TAVILY_API_KEY") or "").strip() or DEFAULT_TAVILY_API_KEY
    return groq_key, tavily_key


# ---------------------------------------------------------------------------
# Verdict display helpers with custom styling
# ---------------------------------------------------------------------------

_VERDICT_ICONS = {
    "supported": "✅",
    "refuted": "❌",
    "misleading": "⚠️",
    "unverifiable": "❓",
}

_CONFIDENCE_LABELS = {
    "high": "🟢 High",
    "medium": "🟡 Medium",
    "low": "🔴 Low",
}

_STANCE_COLORS = {
    "supports": ("#10b981", "#ecfdf5", "✅ SUPPORTS"),
    "refutes": ("#f43f5e", "#fff1f2", "❌ REFUTES"),
    "mixed": ("#f59e0b", "#fffbeb", "⚠️ MIXED"),
    "unrelated": ("#64748b", "#f8fafc", "➖ UNRELATED"),
}


def _render_verdict(verdict, is_demo: bool = False) -> None:
    """Display a Verdict object with modern visual cards and stance badges."""
    if is_demo:
        st.warning(
            "🔶 **DEMO / FIXTURE DATA — NOT A LIVE FACT CHECK.**  \n"
            "This result is generated from offline demonstration fixture data to test the interface without API credentials. "
            "No live web searches or AI reasoning were performed."
        )

    icon = _VERDICT_ICONS.get(verdict.verdict, "")
    label = verdict.verdict.upper()
    confidence = _CONFIDENCE_LABELS.get(verdict.confidence, verdict.confidence)

    # Top verdict banner with color-coded styling
    badge_suffix = " [DEMO FIXTURE]" if is_demo else ""
    if verdict.verdict == "supported":
        st.success(f"### {icon} VERDICT: SUPPORTED{badge_suffix}\n**Summary:** {verdict.summary}")
    elif verdict.verdict == "refuted":
        st.error(f"### {icon} VERDICT: REFUTED{badge_suffix}\n**Summary:** {verdict.summary}")
    elif verdict.verdict == "misleading":
        st.warning(f"### {icon} VERDICT: MISLEADING{badge_suffix}\n**Summary:** {verdict.summary}")
    else:
        st.info(f"### {icon} VERDICT: UNVERIFIABLE{badge_suffix}\n**Summary:** {verdict.summary}")

    col1, col2 = st.columns(2)
    col1.metric("Evidence Assessment", f"{label}{badge_suffix}")
    col2.metric("Reasoning Confidence", confidence)

    st.markdown("#### 📋 Detailed Reasoning & Analysis")
    st.info(verdict.reasoning)

    if verdict.caveats:
        st.caption(f"⚠️ **Caveats & Nuances:** {verdict.caveats}")

    # Render retrieved sources as clean individual cards
    if verdict.sources:
        header_text = f"#### 📄 Cited Sources ({len(verdict.sources)})" + (" *(Pre-recorded Fixtures)*" if is_demo else "")
        st.markdown(header_text)
        for i, src in enumerate(verdict.sources, start=1):
            border_color, bg_color, stance_label = _STANCE_COLORS.get(
                src.stance, ("#64748b", "#f8fafc", src.stance.upper())
            )
            st.markdown(
                f"""
                <div style="border-left: 4px solid {border_color}; background-color: rgba(125, 125, 125, 0.05); padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; font-size: 0.95rem;">
                            <a href="{src.url}" target="_blank" style="text-decoration: none; color: inherit;">🔗 {src.title or src.url}</a>
                        </span>
                        <span style="font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 12px; border: 1px solid {border_color};">
                            {stance_label}
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; font-style: italic;">
                        "{src.snippet}"
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.caption("No whitelisted sources were cited for this claim.")

    if is_demo:
        st.markdown(
            "> **DEMO NOTICE:** This assessment is based on local static demonstration data. "
            "It was not retrieved from live web search or verified by an AI model in real time."
        )
    else:
        st.markdown(
            "> **Reminder:** This result is generated by an AI model reasoning over web search "
            "results. It is an educational aid — not an authoritative or legally reliable fact-check."
        )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="NewsLens — Intelligent Content & Evidence Analysis",
        page_icon="📰",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom UI styling injection
    st.markdown(
        """
        <style>
            /* Clean header accents */
            .main-header {
                font-size: 2.2rem;
                font-weight: 800;
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.2rem;
            }
            .sub-header {
                color: #94a3b8;
                font-size: 1.05rem;
                margin-bottom: 1.2rem;
            }
            /* Tab styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 16px;
                border-bottom: 2px solid rgba(148, 163, 184, 0.2);
            }
            .stTabs [data-baseweb="tab"] {
                padding: 10px 20px;
                font-weight: 700;
                font-size: 1.05rem;
            }
            /* Card hover accents */
            div[data-testid="stMetricValue"] {
                font-size: 1.7rem;
                font-weight: 700;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # App Hero Banner
    st.markdown('<div class="main-header">NewsLens</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Dual-Lens Content Analysis: News-Style Risk Modeling & Deep Evidence Verification</div>',
        unsafe_allow_html=True,
    )

    # Retrieve connected API keys
    groq_key, tavily_key = _get_api_keys()

    # -----------------------------------------------------------------------
    # Sidebar: Classifier Configuration & Live Service Status
    # -----------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### ⚙️ System & Service Status")
        model_path = DEFAULT_MODEL_PATH
        model_exists = model_path.exists()

        if model_exists:
            checksum_status = verify_checksum(model_path)
            st.success(f"ML Pipeline: `{model_path.name}` (SHA-256 ✓)")
        else:
            st.error(f"Model missing: `{model_path}`")
            st.info("Run `python -m newslens.classifier.train`")

        # Service indicators (Keys are permanently connected)
        st.success("Groq LLM: `openai/gpt-oss-120b` (Connected ✓)")
        st.success("Tavily Search: Active (Connected ✓)")

        with st.expander("🔑 Override API Keys (Optional)"):
            groq_input = st.text_input("Groq API Key", type="password", value=groq_key)
            tavily_input = st.text_input("Tavily API Key", type="password", value=tavily_key)
            if groq_input:
                groq_key = groq_input.strip()
            if tavily_input:
                tavily_key = tavily_input.strip()

        st.divider()
        st.markdown("### 🎛️ Classifier Thresholds")
        threshold = st.slider(
            "Fake Decision Threshold",
            min_value=0.0,
            max_value=1.0,
            value=float(DEFAULT_THRESHOLD),
            step=0.05,
            help="Threshold above which probability is classified as FAKE style.",
        )

        uncertainty_margin = st.slider(
            "Uncertainty Margin",
            min_value=0.0,
            max_value=0.30,
            value=float(DEFAULT_UNCERTAINTY_MARGIN),
            step=0.02,
            help="Symmetric range around the threshold where the model abstains as UNCERTAIN.",
        )

        half = uncertainty_margin / 2.0
        st.caption(
            f"Ranges: **REAL** (< {threshold - half:.2f}) | "
            f"**UNCERTAIN** ({threshold - half:.2f}–{threshold + half:.2f}) | "
            f"**FAKE** (> {threshold + half:.2f})"
        )

        st.divider()
        st.markdown("### 📊 Model Performance Metrics")
        metrics = load_metrics_data(DEFAULT_METRICS_PATH)
        if metrics:
            test = metrics.get("holdout_test", {})
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Accuracy", f"{test.get('accuracy', 0):.1%}")
            col_m2.metric("Macro F1", f"{test.get('macro_f1', 0):.1%}")
            st.caption(f"Holdout ROC-AUC: **{test.get('roc_auc', 0):.4f}**")

        with st.expander("ℹ️ Dataset & Publisher Leakage Caveat"):
            st.warning(LEAKAGE_LIMITATION_NOTICE)

    # -----------------------------------------------------------------------
    # Tabs: Strict Visual and Logical Segregation
    # -----------------------------------------------------------------------
    tab1, tab2 = st.tabs(["📰 1. News-Style Classifier", "🔍 2. Evidence-Based Claim Checker"])

    # ===================================================================== #
    # TAB 1 — News-Style Classifier                                         #
    # ===================================================================== #
    with tab1:
        st.markdown("### 📰 News-Style Risk Classifier")
        st.info(f"**Educational Purpose:** {STYLE_DISCLAIMER}")

        if not model_exists:
            st.error(
                "Cannot run classifier: model artifact is missing. "
                "Please train or copy the model file into `models/pipeline.joblib`."
            )
        else:
            pipeline = get_cached_pipeline(str(model_path))

            st.markdown("**Quick-load a sample excerpt:**")
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            sample_text = ""
            if col_btn1.button("📄 Formal Wire Sample (Reuters)", use_container_width=True):
                st.session_state["classifier_text_input"] = SAMPLE_WIRE
            elif col_btn2.button("🔥 Sensational Blog Post", use_container_width=True):
                st.session_state["classifier_text_input"] = SAMPLE_BLOG
            elif col_btn3.button("⚖️ Ambiguous Excerpt", use_container_width=True):
                st.session_state["classifier_text_input"] = SAMPLE_AMBIGUOUS

            user_text = st.text_area(
                "Paste headline or article text below:",
                value=st.session_state.get("classifier_text_input", ""),
                height=160,
                placeholder="Paste news text or article excerpt here to evaluate its writing style...",
            )

            col_c1, col_c2 = st.columns([1, 4])
            classify_clicked = col_c1.button("⚡ Classify Style", type="primary", use_container_width=True)

            if classify_clicked:
                is_valid, warn_msg = validate_text(user_text)
                if not is_valid:
                    st.warning(warn_msg)
                else:
                    result = predict_text(
                        pipeline=pipeline,
                        text=user_text,
                        threshold=threshold,
                        uncertainty_margin=uncertainty_margin,
                    )

                    label = result["label"]
                    prob_fake = result["prob_fake"]
                    prob_real = result["prob_real"]
                    low_bound, high_bound = result["uncertainty_range"]

                    st.divider()
                    st.markdown("### Classification Result")

                    if label == "REAL":
                        st.success(
                            f"### Result: REAL-STYLE (p(fake) = {prob_fake:.1%})\n"
                            f"Text exhibits standard wire-service grammar, datelines, and formal press phrasing."
                        )
                    elif label == "FAKE":
                        st.error(
                            f"### Result: FAKE-STYLE (p(fake) = {prob_fake:.1%})\n"
                            f"Text exhibits sensational headlines, hyperbole, and blog writing patterns."
                        )
                    else:
                        st.warning(
                            f"### Result: UNCERTAIN (p(fake) = {prob_fake:.1%})\n"
                            f"Estimated probability falls within the uncertainty band "
                            f"[{low_bound:.2f}, {high_bound:.2f}]. The model abstains rather than forcing a decision."
                        )

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Predicted Label", label)
                    col2.metric("Fake-Pattern Prob", f"{prob_fake:.1%}")
                    col3.metric("Real-Pattern Prob", f"{prob_real:.1%}")

                    st.markdown("**Probability Spectrum:**")
                    st.progress(float(prob_fake))
                    st.caption(
                        f"0.0 (Real Style) ← Threshold: {threshold:.2f} "
                        f"(Uncertainty Band: {low_bound:.2f}–{high_bound:.2f}) → 1.0 (Fake Style)"
                    )

                    st.markdown(
                        "> **Reminder:** This score reflects superficial vocabulary similarities "
                        "to historical training samples. It does **not** evaluate whether the events described "
                        "actually took place or are verified by external evidence."
                    )

    # ===================================================================== #
    # TAB 2 — Evidence-Based Claim Checker                                  #
    # ===================================================================== #
    with tab2:
        st.markdown("### 🔍 Evidence-Based Claim Checker")
        st.warning(_CHECKER_DISCLAIMER)

        # Mode Selection: Default to Live Search Mode since keys are connected!
        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            mode_option = st.radio(
                "Operating Mode:",
                options=[
                    "🌐 Live Search Mode (Real Tavily Search + 120B Groq LLM)",
                    "🟢 Offline Demo Mode (Pre-recorded fixtures — no API calls)",
                ],
                index=0,
                horizontal=True,
                help="Live Search Mode runs real web queries. Offline Demo Mode uses pre-recorded fixtures.",
            )
        is_demo_mode = "Offline Demo Mode" in mode_option

        if is_demo_mode:
            st.info(
                "💡 **Offline Demo Mode Active:** Pre-configured fixture data will be used to demonstrate "
                "the claim-checking UI, source stances, and confidence cards without calling external APIs."
            )
            st.markdown("**Quick-load a demonstration fixture:**")
            col_d1, col_d2, col_d3 = st.columns(3)
            if col_d1.button("🏛️ Great Wall (Refuted)", use_container_width=True):
                st.session_state["claim_input_val"] = "The Great Wall of China is visible from space with the naked eye."
            elif col_d2.button("🌍 Heliocentrism (Supported)", use_container_width=True):
                st.session_state["claim_input_val"] = "The Earth revolves around the Sun."
            elif col_d3.button("🍌 Bananas Radiation (Misleading)", use_container_width=True):
                st.session_state["claim_input_val"] = "Eating bananas exposes you to dangerous levels of nuclear radiation."
        else:
            st.markdown(
                '<div style="font-size: 0.9rem; color: #10b981; font-weight: 600; margin-bottom: 8px;">'
                "⚡ Live Mode Active: Connected to Tavily Search & Groq 120B LLM"
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**Quick-load an example claim:**")
            col_d1, col_d2, col_d3 = st.columns(3)
            if col_d1.button("🏛️ Great Wall from Space", use_container_width=True):
                st.session_state["claim_input_val"] = "The Great Wall of China is visible from space with the naked eye."
            elif col_d2.button("🌍 Earth Revolves Sun", use_container_width=True):
                st.session_state["claim_input_val"] = "The Earth revolves around the Sun."
            elif col_d3.button("🍌 Bananas Radiation", use_container_width=True):
                st.session_state["claim_input_val"] = "Eating bananas exposes you to dangerous levels of nuclear radiation."

        claim_default = st.session_state.get("claim_input_val", "")
        claim_text = st.text_area(
            "Enter one factual claim (≤ 500 characters):",
            value=claim_default,
            height=90,
            max_chars=500,
            placeholder="e.g. The Great Wall of China is visible from space with the naked eye.",
        )

        col_act1, col_act2, col_act3 = st.columns([2, 2, 3])
        check_clicked = col_act1.button("🔍 Check Claim", type="primary", use_container_width=True)
        clear_clicked = col_act2.button("🗑️ Clear Result", use_container_width=True)
        bypass_cache = col_act3.checkbox(
            "Bypass cache (force fresh search)",
            value=False,
            help="Forces new web searches and LLM reasoning even if this exact claim was checked in this session.",
        )

        if clear_clicked:
            st.session_state.pop("checker_state", None)
            st.session_state.pop("claim_input_val", None)
            st.rerun()

        if check_clicked:
            cleaned_claim = claim_text.strip()
            if not cleaned_claim:
                st.warning("Please enter a claim before clicking Check Claim.")
            elif len(cleaned_claim) > 500:
                st.warning("Claim exceeds maximum length of 500 characters. Please shorten your claim.")
            elif is_demo_mode:
                from newslens.checker.fixtures import get_demo_fixture

                search_results, allowed_urls, verdict = get_demo_fixture(cleaned_claim)
                st.session_state["checker_state"] = {
                    "claim": cleaned_claim,
                    "results": search_results,
                    "allowed_urls": allowed_urls,
                    "verdict": verdict,
                    "is_demo": True,
                }
            else:
                # --- LIVE SEARCH MODE ---
                cached = st.session_state.get("checker_state")
                if (
                    cached
                    and cached.get("claim") == cleaned_claim
                    and not cached.get("is_demo", False)
                    and not bypass_cache
                ):
                    st.info(
                        "ℹ️ Displaying cached evidence from current session for this exact claim. "
                        "Check 'Bypass cache' above to force fresh web searches."
                    )
                else:
                    from newslens.checker.agent import check_claim
                    from newslens.checker.search import search_both

                    # 1. Balanced Search
                    search_results = []
                    allowed_urls = set()
                    with st.spinner("🌐 Querying Tavily for pro and counter evidence…"):
                        try:
                            search_results, allowed_urls = search_both(cleaned_claim, tavily_key)
                        except RuntimeError as exc:
                            st.error(f"Search failed: {exc}")
                        except Exception as exc:
                            st.error(f"Unexpected search error: {exc}")

                    # 2. Structured Reasoning
                    verdict = None
                    if search_results or allowed_urls:
                        with st.spinner("🤖 Reasoning over evidence via Groq 120B model…"):
                            try:
                                verdict = check_claim(
                                    cleaned_claim,
                                    search_results,
                                    allowed_urls,
                                    groq_key,
                                )
                            except RuntimeError as exc:
                                st.error(f"Claim check failed: {exc}")
                            except ValueError as exc:
                                st.warning(f"Input error: {exc}")
                            except Exception as exc:
                                st.error(f"Unexpected error during reasoning: {exc}")
                    elif search_results == [] and not allowed_urls:
                        with st.spinner("Evaluating with no evidence retrieved…"):
                            try:
                                verdict = check_claim(
                                    cleaned_claim,
                                    [],
                                    set(),
                                    groq_key,
                                )
                            except Exception as exc:
                                st.error(f"Reasoning error: {exc}")

                    if verdict is not None or search_results:
                        st.session_state["checker_state"] = {
                            "claim": cleaned_claim,
                            "results": search_results,
                            "allowed_urls": allowed_urls,
                            "verdict": verdict,
                            "is_demo": False,
                        }

        # --- Render Results (Persisted Across Tab Switches & Sidebar Interactions) ---
        cached = st.session_state.get("checker_state")
        if cached:
            results = cached.get("results", [])
            verdict = cached.get("verdict")
            is_demo = cached.get("is_demo", False)

            if results:
                expander_label = (
                    f"📄 Retrieved [DEMO FIXTURE] Sources ({len(results)} items) — expand to view"
                    if is_demo
                    else f"📄 All Retrieved Search Sources ({len(results)} items) — expand to view"
                )
                with st.expander(expander_label):
                    if is_demo:
                        st.caption("⚠️ The sources listed below are pre-recorded demonstration fixtures, not live search results.")
                    for item in results:
                        st.markdown(f"- [{item['title'] or item['url']}]({item['url']})")
                        if item.get("snippet"):
                            st.caption(item["snippet"])
            else:
                st.info("No search results found. The verdict will likely be **unverifiable**.")

            st.divider()
            verdict_header = "Evidence Assessment & Verdict" + (" (Offline Demo Fixture)" if is_demo else " (Live Analysis)")
            st.subheader(verdict_header)

            if verdict is None:
                st.error(
                    "The AI returned an unrecognisable response or could not evaluate the evidence. "
                    "This may be a temporary issue — please try again."
                )
            else:
                _render_verdict(verdict, is_demo=is_demo)


if __name__ == "__main__":
    main()
