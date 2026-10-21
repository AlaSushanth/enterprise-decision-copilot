import re
from enum import Enum
from typing import Dict, Any
from src.config import GEMINI_API_KEY

class QueryIntent(str, Enum):
    SQL_ONLY = "SQL_ONLY"
    DOCS_ONLY = "DOCS_ONLY"
    HYBRID_DECISION = "HYBRID_DECISION"

class AgenticRouter:
    """Intelligently routes analytical inquiries to SQL, Vector RAG, or Hybrid Analysis."""
    
    def route_query(self, user_question: str) -> Dict[str, Any]:
        q = user_question.lower()
        
        # Check LLM routing if API is available
        if GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=GEMINI_API_KEY)
                prompt = f"""Classify the user's business question into exactly ONE of the following categories:
- SQL_ONLY: purely asks for numbers, sums, counts, data metrics, tables.
- DOCS_ONLY: purely asks for regulations, policy text, definitions, strategy descriptions without needing database metrics.
- HYBRID_DECISION: asks "why", root causes, strategy recommendations, combines numbers with business context.

Question: "{user_question}"

Respond with ONLY the category name.
"""
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                pred = resp.text.strip()
                if pred in [e.value for e in QueryIntent]:
                    return {
                        "intent": QueryIntent(pred),
                        "reasoning": f"LLM classification identified intent as {pred}."
                    }
            except Exception:
                pass

        # Robust heuristic rule routing
        why_words = ["why", "reason", "cause", "drop", "recommend", "action", "recover", "strategy", "impact", "decline"]
        sql_words = ["how much", "total", "average", "sum", "count", "revenue", "target", "retention", "percent", "numbers", "table", "data"]
        doc_words = ["policy", "regulation", "directive", "guideline", "ema", "logistics", "competitor move", "contract"]

        has_why = any(w in q for w in why_words)
        has_sql = any(w in q for w in sql_words)
        has_doc = any(w in q for w in doc_words)

        if has_why or (has_sql and has_doc):
            return {
                "intent": QueryIntent.HYBRID_DECISION,
                "reasoning": "Detected request for quantitative variance combined with causal diagnosis and strategic recommendations."
            }
        elif has_sql and not has_doc:
            return {
                "intent": QueryIntent.SQL_ONLY,
                "reasoning": "Detected purely quantitative inquiry against structured database."
            }
        else:
            return {
                "intent": QueryIntent.DOCS_ONLY,
                "reasoning": "Detected qualitative inquiry targeting business reports and regulatory documents."
            }
