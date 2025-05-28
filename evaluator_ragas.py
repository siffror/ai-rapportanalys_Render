from typing import List, Dict
import difflib

def simple_rag_evaluation(question: str, answer: str, contexts: List[str]) -> Dict:
    """
    En enkel heuristisk utvärdering av ett RAG-svar:
    - Faithfulness: hur mycket av svaret finns i kontexten (likhet)
    - Relevancy: likhet mellan svaret och frågan (förenklat)
    """
    full_context = " ".join(contexts)

    # Faithfulness = likhet mellan context och svar
    matcher = difflib.SequenceMatcher(None, full_context.lower(), answer.lower())
    faithfulness_score = matcher.ratio()

    # Relevancy = hur mycket av frågan återspeglas i svaret
    matcher2 = difflib.SequenceMatcher(None, question.lower(), answer.lower())
    relevancy_score = matcher2.ratio()

    return {
        "faithfulness": round(faithfulness_score, 2),
        "answer_relevancy": round(relevancy_score, 2)
    }
