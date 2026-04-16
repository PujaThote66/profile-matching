from rank_bm25 import BM25Okapi
import re

def tokenize(text):
    """
    Lightweight tokenizer:
    - keeps c#, vb.net, asp.net, ai/ml intact
    - removes punctuation
    """
    return re.findall(r"[a-zA-Z0-9#+.]+", text.lower())


def bm25_scores(jd_text, candidate_profiles):
    """
    Compute normalized BM25 similarity scores
    between JD and candidate profiles.

    ✅ Returns JSON-safe Python floats
    """

    # Tokenize candidate profiles
    tokenized_profiles = [
        tokenize(profile)
        for profile in candidate_profiles
    ]

    bm25 = BM25Okapi(tokenized_profiles)

    # Tokenize JD
    query_tokens = tokenize(jd_text)

    # Raw BM25 scores (NumPy types)
    raw_scores = bm25.get_scores(query_tokens)

    max_score = float(max(raw_scores)) if max(raw_scores) > 0 else 1.0

    # ✅ Convert NumPy → Python float
    return [float(score) / max_score for score in raw_scores]