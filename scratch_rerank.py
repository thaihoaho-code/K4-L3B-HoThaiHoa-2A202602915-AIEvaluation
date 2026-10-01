import json
from pathlib import Path
from template import QAPair, rerank_by_overlap, RAGASEvaluator
import sys

def main():
    actual_path = Path("artifacts/actual_answers.json")
    golden_path = Path("golden_dataset.json")

    actual_data = json.loads(actual_path.read_text(encoding="utf-8"))
    golden_data = json.loads(golden_path.read_text(encoding="utf-8"))

    actual_by_id = {ans["id"]: ans for ans in actual_data["answers"]}

    evaluator = RAGASEvaluator()

    # Pick 5 cases. Let's find cases where precision < 1.0 to see improvement, or any cases.
    # Looking at the table from earlier: E01, M04, M05, M06, M07, A02, A03 had Precision < 1.0.
    # Let's pick: E01, M04, M05, M06, A03.
    target_ids = ["E01", "M04", "M05", "M06", "A03"]
    
    print("| ID | Recall before | Recall after | Precision before | Precision after | Delta Precision |")
    print("|---|---:|---:|---:|---:|---:|")

    recalls_b, recalls_a = [], []
    precs_b, precs_a = [], []
    deltas = []

    for qid in target_ids:
        golden = next(q for q in golden_data["qa_pairs"] if q["id"] == qid)
        actual = actual_by_id[qid]

        expected_answer = golden["expected_answer"]
        question = golden["question"]
        contexts = [c["text"] for c in actual["retrieved_contexts"]]

        # Before
        recall_b = evaluator.evaluate_context_recall(contexts, expected_answer)
        prec_b = evaluator.evaluate_context_precision(contexts, expected_answer)

        # Rerank
        contexts_after = rerank_by_overlap(contexts, question)

        # After
        recall_a = evaluator.evaluate_context_recall(contexts_after, expected_answer)
        prec_a = evaluator.evaluate_context_precision(contexts_after, expected_answer)

        delta = prec_a - prec_b

        recalls_b.append(recall_b)
        recalls_a.append(recall_a)
        precs_b.append(prec_b)
        precs_a.append(prec_a)
        deltas.append(delta)

        print(f"| {qid} | {recall_b:.3f} | {recall_a:.3f} | {prec_b:.3f} | {prec_a:.3f} | {delta:.3f} |")

    avg_recall_b = sum(recalls_b)/len(recalls_b)
    avg_recall_a = sum(recalls_a)/len(recalls_a)
    avg_prec_b = sum(precs_b)/len(precs_b)
    avg_prec_a = sum(precs_a)/len(precs_a)
    avg_delta = sum(deltas)/len(deltas)

    print(f"| **Avg** | {avg_recall_b:.3f} | {avg_recall_a:.3f} | {avg_prec_b:.3f} | {avg_prec_a:.3f} | {avg_delta:.3f} |")

if __name__ == '__main__':
    main()
