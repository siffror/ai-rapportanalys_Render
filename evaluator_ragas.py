from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from ragas.testset import Testset

def evaluate_rag_sample(question: str, answer: str, contexts: list[str], ground_truth: str = "") -> dict:
    testset = Testset.from_dicts([
        {
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "ground_truths": [ground_truth] if ground_truth else [],
        }
    ])

    metrics = [faithfulness, answer_relevancy]

    results = evaluate(testset, metrics=metrics)
    return {
        "faithfulness": results["faithfulness"].iloc[0],
        "answer_relevancy": results["answer_relevancy"].iloc[0],
    }
