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

        # Strategic decision-making signals (asking for root causes, recovery actions, counter-strategies)
        hybrid_patterns = [
            r"\bwhy\b", r"\broot[\s-]causes?\b", r"\breasons?\s+for\b", r"\breasons?\s+behind\b",
            r"\bwhat\s+caused\b", r"\bwhy\s+did\b", r"\bcauses?\s+behind\b",
            r"\brecommend", r"\bactions?\s+to\b", r"\brecover", r"\bturnaround",
            r"\bnext\s+steps\b", r"\bwhat\s+should\b", r"\bhow\s+should\b", r"\bhow\s+to\b",
            r"\bsuggest", r"\bstrategic\s+moves?\b", r"\bstrategic\s+actions?\b",
            r"\bstrategies\s+for\b", r"\bcounter\b", r"\bpropose\b", r"\bheadwinds?\b",
            r"\breversal\b", r"\bsolutions?\s+to\b", r"\bdefense\b", r"\bcounter-?\s*strategy\b",
            r"\bturn\s*around\b", r"\bdiagnos", r"\brationale\s+behind\b", r"\bpricing\s+defense\b"
        ]

        # Quantitative/SQL signals: metrics, sums, counts, tables, revenue, targets
        sql_patterns = [
            r"\bhow\s+much\b", r"\btotal\b", r"\baverage\b", r"\bsum\b", r"\bcount\b",
            r"\brevenue\b", r"\btarget\b", r"\bretention\b", r"\bpercent", r"\bnumbers?\b",
            r"\btables?\b", r"\bmetrics?\b", r"\bquarter\b", r"\bq[1-4]\b",
            r"\bsales\s+figures\b", r"\bsales\s+breakdown\b", r"\bsales\s+performance\b",
            r"\bheadcount\b", r"\breps?\b", r"\bmarketing\s+spend\b", r"\bexpenditure\b",
            r"\bfigures?\b", r"\bbreakdown\b", r"\bmarket\s+share\b", r"\btreatment\s+price\b",
            r"\bpricing\s+figures\b", r"\bmaximum\s+revenue\b"
        ]

        # Qualitative/Doc signals: policies, guidelines, directives, compliance frameworks, regulatory decks
        doc_patterns = [
            r"\bpolicy\b", r"\bpolicies\b", r"\bregulation", r"\bdirective", r"\bguideline",
            r"\bema\b", r"\bfda\b", r"\blogistics\b", r"\bcompetitor\s+intelligence\b",
            r"\bcontractual\b", r"\brules?\b", r"\bcompliance\b", r"\bbuffer\b",
            r"\bsafety\s+stock\b", r"\bcold[\s-]chain", r"\bprotocols?\b", r"\bstandard\b",
            r"\bdocumentation\b", r"\bprocedures?\b", r"\bstatutory\b", r"\bframework\b",
            r"\bincident\b", r"\btelemetry\b", r"\bheatwaves?\b", r"\bsla\b",
            r"\belasticity\s+of\s+demand\b", r"\binsulation\b", r"\bpositioning\b"
        ]

        has_why = any(re.search(p, q) for p in hybrid_patterns)
        has_sql = any(re.search(p, q) for p in sql_patterns)
        has_doc = any(re.search(p, q) for p in doc_patterns)

        # Disambiguation:
        # If question has hybrid strategic decision signals OR (both quantitative SQL + qualitative Doc signals)
        if has_why or (has_sql and has_doc and any(w in q for w in ["drop", "affect", "loss", "decline", "impact", "underperform", "shrink", "realign", "fail", "slump", "variance"])):
            return {
                "intent": QueryIntent.HYBRID_DECISION,
                "reasoning": "Detected request for quantitative variance combined with causal diagnosis and strategic recommendations."
            }
        elif has_doc and not has_why and not (has_sql and any(w in q for w in ["calculate", "how much", "total", "sum", "count", "average"])):
            return {
                "intent": QueryIntent.DOCS_ONLY,
                "reasoning": "Detected qualitative inquiry targeting business reports and regulatory documents."
            }
        else:
            return {
                "intent": QueryIntent.SQL_ONLY,
                "reasoning": "Detected purely quantitative inquiry against structured database."
            }
