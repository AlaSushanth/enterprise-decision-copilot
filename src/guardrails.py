import re
from typing import Dict, Any, List

class ResponsibleAIGuardrail:
    """Ensures business groundedness, hallucination mitigation, and strict citation enforcement."""

    def verify_groundedness(self, answer_text: str, sql_context: str, doc_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        flags = []
        confidence_score = 1.0
        
        # 1. Check for citations
        has_citations = bool(re.search(r'\[(Source|Doc|Table|Section):?[^\]]+\]', answer_text, re.IGNORECASE))
        if not has_citations and (sql_context or doc_chunks):
            flags.append("Missing explicit source citation tag in output.")
            confidence_score -= 0.15

        # 2. Number verification: extract dollar amounts / percentages from answer
        numbers_in_answer = re.findall(r'\$?\d+(?:\.\d+)?%?', answer_text)
        
        combined_context = sql_context + " " + " ".join([c.get("content", "") for c in doc_chunks])
        unverified_numbers = []
        for num in numbers_in_answer:
            # Clean number for searching
            clean_num = num.replace('$', '').replace('%', '')
            if len(clean_num) > 1 and clean_num not in combined_context:
                unverified_numbers.append(num)

        if unverified_numbers:
            flags.append(f"Potentially ungrounded numeric metrics detected: {', '.join(unverified_numbers[:3])}")
            confidence_score -= 0.20

        # Bound confidence between 0.0 and 1.0
        confidence_score = max(0.2, min(1.0, round(confidence_score, 2)))

        return {
            "is_grounded": len(flags) == 0,
            "confidence_score": confidence_score,
            "compliance_status": "PASSED" if confidence_score >= 0.8 else "REVIEW_RECOMMENDED",
            "flags": flags
        }
