# keyword_extractor.py

import spacy
import re
from collections import Counter

nlp = spacy.load("en_core_web_sm")

NON_SKILL_TERMS = {
    "experience", "knowledge", "skills", "years", "year",
    "responsibility", "responsibilities", "candidate",
    "role", "team", "collaboration", "expertise",
    "strong experience", "the ideal candidate", "we"
}

SKILL_TRIGGERS = [
    "experience with",
    "hands on",
    "hands-on",
    "proficient in",
    "expertise in",
    "knowledge of",
    "worked with",
    "using",
    "skills in"
]

def extract_key_phrases(text, max_phrases=20):
    text = text.lower()
    doc = nlp(text)

    candidates = []

    # 1️⃣ Noun‑phrase extraction
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip().lower()
        tokens = phrase.split()

        if not (1 <= len(tokens) <= 3):
            continue
        if phrase in NON_SKILL_TERMS:
            continue
        if any(w in {"experience", "knowledge"} for w in tokens):
            continue
        if all(token in nlp.Defaults.stop_words for token in tokens):
            continue
        if not re.search(r"[a-zA-Z0-9+#.]", phrase):
            continue

        candidates.append(phrase)

    # 2️⃣ Context‑based extraction
    for trigger in SKILL_TRIGGERS:
        if trigger in text:
            parts = text.split(trigger)
            for part in parts[1:]:
                segment = part.split(",")[0].strip()
                words = segment.split()

                if 1 <= len(words) <= 3 and segment not in NON_SKILL_TERMS:
                    candidates.append(segment)

    # 3️⃣ Frequency ranking
    freq = Counter(candidates)

    extracted = []
    for phrase, _ in freq.most_common():
        if phrase not in NON_SKILL_TERMS:
            extracted.append(phrase)
        if len(extracted) >= max_phrases:
            break

    return extracted
