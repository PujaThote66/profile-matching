# matcher.py

import re
from sentence_transformers import CrossEncoder, SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

from keyword_extractor import extract_key_phrases
from bm25_utils import bm25_scores


# ------------------------------------------------
# Models
# ------------------------------------------------
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
embedder = SentenceTransformer("all-MiniLM-L6-v2")


# ------------------------------------------------
# Phrase cleaning
# ------------------------------------------------
def clean_phrases(phrases):
    BAD_WORDS = {
        "experience", "years", "skills", "required",
        "participate", "build", "building", "responsible",
        "monitoring", "performance", "optimization"
    }

    cleaned = []
    for p in phrases:
        p = p.lower().strip()
        tokens = p.split()

        if len(tokens) > 4:
            continue
        if all(t in BAD_WORDS for t in tokens):
            continue
        if any(c.isalpha() for c in p):
            cleaned.append(p)

    return list(set(cleaned))


# ------------------------------------------------
# Skill confidence logic
# ------------------------------------------------
NEGATION_PATTERNS = [
    r"\bno\b", r"\bnot\b", r"\bwithout\b",
    r"\blacks?\b", r"\bnever\b", r"\bno experience\b"
]

HARD_NEGATIVE_PATTERNS = [
    r"\bno hands[- ]on experience\b",
    r"\bno practical experience\b",
    r"\bno real[- ]world experience\b",
    r"\bnot hands[- ]on\b"
]

WEAK_CONFIDENCE_PATTERNS = [
    r"\blimited\b", r"\bbasic\b", r"\bbeginner\b",
    r"\bentry[- ]level\b", r"\bexposure\b",
    r"\bsome experience\b", r"\bintroductory\b"
]

STRONG_PATTERNS = [
    r"\bdeveloped\b", r"\bbuilt\b", r"\bimplemented\b",
    r"\bled\b", r"\bdeployed\b", r"\bowned\b"
]

SKILL_WINDOW = 6


def get_skill_confidence(text, skill):
    text = text.lower()
    tokens = text.split()
    skill_tokens = skill.split()

    for i in range(len(tokens) - len(skill_tokens) + 1):
        if tokens[i:i + len(skill_tokens)] == skill_tokens:
            start = max(0, i - SKILL_WINDOW)
            end = min(len(tokens), i + len(skill_tokens) + SKILL_WINDOW)
            context = " ".join(tokens[start:end])

            if any(re.search(p, context) for p in HARD_NEGATIVE_PATTERNS):
                return 0.0
            if any(re.search(p, context) for p in NEGATION_PATTERNS):
                return 0.0
            if any(re.search(p, context) for p in WEAK_CONFIDENCE_PATTERNS):
                return 0.4
            if any(re.search(p, context) for p in STRONG_PATTERNS):
                return 1.0

            return 0.6

    return 0.0


# ------------------------------------------------
# Skill aggregation helpers
# ------------------------------------------------
def keyword_coverage(profile, phrases):
    if not phrases:
        return 0.0
    scores = []
    for p in phrases:
        conf = get_skill_confidence(profile, p)
        if conf > 0:
            scores.append(conf)
    return sum(scores) / len(phrases) if scores else 0.0


def matched_phrases(profile, phrases):
    return {
        p: round(get_skill_confidence(profile, p), 2)
        for p in phrases
        if get_skill_confidence(profile, p) > 0
    }


# ------------------------------------------------
# Dynamic skill clustering
# ------------------------------------------------
def cluster_skills(jd_phrases, max_clusters=4):
    if len(jd_phrases) <= 2:
        return [jd_phrases]

    embeddings = embedder.encode(jd_phrases)

    n_clusters = min(max_clusters, len(jd_phrases) // 2 + 1)

    clustering = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="cosine",
        linkage="average"
    )

    labels = clustering.fit_predict(embeddings)

    clusters = {}
    for phrase, label in zip(jd_phrases, labels):
        clusters.setdefault(label, []).append(phrase)

    return list(clusters.values())


# ------------------------------------------------
# FINAL SCORING
# ------------------------------------------------
def score_candidates(jd, candidates, algo_choice="Semantic Only"):
    jd_phrases = clean_phrases(extract_key_phrases(jd))
    skill_clusters = cluster_skills(jd_phrases)

    pairs = [[jd, c] for c in candidates]
    raw_semantic = cross_encoder.predict(pairs)

    min_s, max_s = min(raw_semantic), max(raw_semantic)
    semantic_scores = [
        float((s - min_s) / (max_s - min_s)) if max_s != min_s else 0.0
        for s in raw_semantic
    ]

    bm25_scores_list = [float(x) for x in bm25_scores(" ".join(jd_phrases), candidates)]
    results = []

    for i, profile in enumerate(candidates):

        skill_score = float(keyword_coverage(profile, jd_phrases))

        if algo_choice == "Semantic Only":
            final = semantic_scores[i]
        elif algo_choice == "BM25 Only":
            final = bm25_scores_list[i]
        elif algo_choice == "Keyword / Skill Match Only":
            final = skill_score
        else:
            raise ValueError(f"Unsupported algorithm: {algo_choice}")

        final = float(min(final * 100 * 1.4, 100))

        results.append({
            "candidate": f"Candidate {i + 1}",
            "final_score": round(float(final), 2),
            "matched_phrases": {
                k: float(v) for k, v in matched_phrases(profile, jd_phrases).items()
            }
        })

    return results, jd_phrases