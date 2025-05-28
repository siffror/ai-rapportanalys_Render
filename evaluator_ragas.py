from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from ragas.testset import Testset
from typing import List, Dict
import pandas as pd  # ✅ detta måste läggas till

def evaluate_rag_sample(question: str, answer: str, contexts: List[str], ground_truth: str = "") -> Dict:
    """
    Utvärderar en enda fråga/svar med Ragas.
    """
    test_data = [{
        "question": question,
        "answer": answer,
        "contexts": contexts,
        "ground_truths": [ground_truth] if ground_truth else []
    }]

    # ✅ Ny metod: skapa testset från pandas DataFrame
    testset = Testset.from_pandas(pd.DataFrame(test_data))

    results = evaluate(
        testset,
        metrics=[faithfulness, answer_relevancy]
    )

    scores = {
        "faithfulness": results["faithfulness"].iloc[0],
        "answer_relevancy": results["answer_relevancy"].iloc[0]
    }
    return scores
