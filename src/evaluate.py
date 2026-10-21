import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.decision_synthesizer import DecisionSynthesizer

BENCHMARK_TEST_SUITE = [
    {
        "id": "TC-01",
        "question": "Why did Europe sales drop in Q3 2024 and what competitor actions caused it?",
        "expected_intent": "HYBRID_DECISION",
        "expected_keywords": ["biopharma", "price", "4,100", "21.4"]
    },
    {
        "id": "TC-02",
        "question": "What was the total revenue for North America in Q2 and Q3 2024?",
        "expected_intent": "SQL_ONLY",
        "expected_keywords": ["north america", "33.2", "revenue"]
    },
    {
        "id": "TC-03",
        "question": "What are the European Medicines Agency EMA safety buffer inventory requirements?",
        "expected_intent": "DOCS_ONLY",
        "expected_keywords": ["ema", "90-day", "buffer", "inventory"]
    }
]

def run_evaluation_benchmark():
    print("=" * 65)
    print("🚀 Running Enterprise Decision Copilot Benchmark Evaluation Suite")
    print("=" * 65)

    synthesizer = DecisionSynthesizer()
    results = []
    
    start_time = time.time()
    
    for case in BENCHMARK_TEST_SUITE:
        print(f"\n[Evaluating {case['id']}] Query: '{case['question']}'")
        res = synthesizer.synthesize_decision(case["question"])
        
        intent_match = res["intent"] == case["expected_intent"]
        
        # Check keyword groundedness in generated brief
        brief_lower = res["executive_brief"].lower()
        matched_kw = [kw for kw in case["expected_keywords"] if kw.lower() in brief_lower]
        kw_coverage = len(matched_kw) / len(case["expected_keywords"])
        
        audit = res["audit_report"]
        
        case_summary = {
            "id": case["id"],
            "intent_match": intent_match,
            "keyword_recall": round(kw_coverage * 100, 1),
            "confidence_score": audit["confidence_score"],
            "compliance_status": audit["compliance_status"]
        }
        results.append(case_summary)
        print(f"  ✓ Intent Correct: {intent_match} ({res['intent']})")
        print(f"  ✓ Keyword Groundedness Recall: {case_summary['keyword_recall']}%")
        print(f"  ✓ Responsible AI Confidence Score: {audit['confidence_score'] * 100}%")
        print(f"  ✓ Audit Status: {audit['compliance_status']}")

    total_time = round(time.time() - start_time, 2)
    avg_recall = sum(r["keyword_recall"] for r in results) / len(results)
    avg_confidence = sum(r["confidence_score"] for r in results) / len(results) * 100

    print("\n" + "=" * 65)
    print("📊 BENCHMARK EVALUATION SUMMARY")
    print(f"• Total Test Cases Evaluated: {len(results)}")
    print(f"• Routing Intent Accuracy: {sum(1 for r in results if r['intent_match'])/len(results)*100:.1f}%")
    print(f"• Mean Keyword Context Recall: {avg_recall:.1f}%")
    print(f"• Mean Responsible AI Confidence: {avg_confidence:.1f}%")
    print(f"• Total Evaluation Latency: {total_time}s")
    print("=" * 65)

if __name__ == "__main__":
    run_evaluation_benchmark()
