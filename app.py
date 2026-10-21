import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd
from src.decision_synthesizer import DecisionSynthesizer
from src.config import GEMINI_API_KEY, OPENAI_API_KEY

st.set_page_config(
    page_title="Enterprise Decision Intelligence Copilot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 8px;
    }
    .badge-hybrid { background-color: #E8F0FE; color: #1A73E8; border: 1px solid #1A73E8; }
    .badge-sql { background-color: #E6F4EA; color: #137333; border: 1px solid #137333; }
    .badge-doc { background-color: #FEF7E0; color: #B06000; border: 1px solid #B06000; }
    .card {
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #E0E0E0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_synthesizer():
    return DecisionSynthesizer()

synthesizer = get_synthesizer()

# Sidebar
with st.sidebar:
    st.title("💼 Decision Copilot")
    st.caption("Hybrid RAG + Text-to-SQL + Responsible AI for Enterprise Strategy")
    st.divider()

    st.subheader("💡 Sample Business Inquiries")
    sample_queries = [
        "Why did Europe sales drop in Q3 2024 and what competitor actions caused it?",
        "What was the total revenue and target variance for North America in 2024?",
        "What are the European Medicines Agency EMA safety buffer inventory requirements?",
        "Compare competitor market share and therapy pricing in Europe for Q2 and Q3."
    ]

    selected_sample = None
    for idx, sq in enumerate(sample_queries):
        if st.button(f"📌 {sq[:55]}...", key=f"sample_{idx}", use_container_width=True):
            selected_sample = sq

    st.divider()
    st.subheader("⚙️ System Status")
    st.markdown("• **Engine:** DuckDB + ChromaDB")
    st.markdown("• **Retrieval:** Hybrid BM25 + Dense Semantic Hash")
    st.markdown("• **Guardrail:** Groundedness & Citation Auditor")
    if GEMINI_API_KEY:
        st.success("✓ Gemini API Connected")
    else:
        st.info("ℹ️ Running in Local High-Fidelity Analytics Mode")

# Main Interface
st.title("📊 Enterprise Decision Intelligence Copilot")
st.markdown("Ask multi-dimensional strategic questions combining **enterprise tabular metrics** with **unstructured market research**.")

# Query Input
query = st.text_input(
    "Enter business inquiry or strategic decision question:",
    value=selected_sample if selected_sample else "",
    placeholder="e.g., Why did European profit margins drop in Q3 and what actions do strategy reports recommend?",
    help="Routes automatically across DuckDB SQL tables and ChromaDB vector reports."
)

col_btn, col_clear = st.columns([1, 6])
run_analysis = col_btn.button("🚀 Analyze", type="primary", use_container_width=True)

if run_analysis or query:
    if not query.strip():
        st.warning("Please enter a question to analyze.")
    else:
        with st.spinner("Synthesizing metrics, documents, and decision recommendations..."):
            result = synthesizer.synthesize_decision(query)

        # Routing Badge
        intent = result["intent"]
        if intent == "HYBRID_DECISION":
            badge_html = '<span class="metric-badge badge-hybrid">🔄 HYBRID DECISION ANALYSIS</span>'
        elif intent == "SQL_ONLY":
            badge_html = '<span class="metric-badge badge-sql">📊 STRUCTURED SQL DATA</span>'
        else:
            badge_html = '<span class="metric-badge badge-doc">📄 STRATEGY DOCUMENT RAG</span>'

        st.markdown(f"**Intent Classification:** {badge_html} &nbsp; *({result['routing_reasoning']})*", unsafe_allow_html=True)
        st.write("")

        # Two-column layout: Left for Brief, Right for Data & Visuals
        col_main, col_data = st.columns([3, 2])

        with col_main:
            st.subheader("📋 Executive Decision Brief")
            st.markdown(result["executive_brief"])

            # Export Button
            st.download_button(
                label="📥 Download Executive Brief (Markdown)",
                data=result["executive_brief"],
                file_name="executive_decision_brief.md",
                mime="text/markdown"
            )

        with col_data:
            # Responsible AI Card
            audit = result["audit_report"]
            status_color = "green" if audit["compliance_status"] == "PASSED" else "orange"
            st.subheader("🛡️ Responsible AI Audit")
            st.markdown(f"""
            * **Groundedness Score:** `{audit['confidence_score'] * 100}%`
            * **Audit Status:** <span style="color:{status_color}; font-weight:bold;">{audit['compliance_status']}</span>
            * **Source Citations Found:** `{len(result['citations'])}`
            """, unsafe_allow_html=True)

            if audit["flags"]:
                with st.expander("⚠️ Audit Advisory Details"):
                    for flag in audit["flags"]:
                        st.markdown(f"- {flag}")

            # Structured Data Visualizer
            if result.get("sql_results"):
                st.subheader("📈 Quantitative Data & Trends")
                df = result["sql_results"]["data"]
                
                # Check for numerical column to plot
                num_cols = [c for c in df.columns if df[c].dtype in ['float64', 'int64'] and c != 'year']
                if num_cols and len(df) > 1:
                    chart_col = num_cols[0]
                    cat_col = 'quarter' if 'quarter' in df.columns else df.columns[0]
                    st.bar_chart(df, x=cat_col, y=chart_col)

                with st.expander("🔍 View Extracted SQL Data Table"):
                    st.dataframe(df, use_container_width=True)

                with st.expander("💻 Executed DuckDB Query"):
                    st.code(result["sql_results"]["sql"], language="sql")

            # Document Citations Drawer
            if result.get("doc_chunks"):
                st.subheader("📚 Cited Strategy Sources")
                for chunk in result["doc_chunks"]:
                    with st.expander(f"📄 {chunk['source']}"):
                        st.markdown(chunk["content"])
