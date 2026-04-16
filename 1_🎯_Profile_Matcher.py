# app.py

import streamlit as st
import pandas as pd
from matcher import score_candidates
import spacy
import os

# ---------------------------
# Ensure spaCy model is available
# ---------------------------
try:
    spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="Profile Matcher",
    layout="wide"
)

st.title("🎯 Profile Matching")
st.write("Works for **any job role** using automatic JD keyword extraction")

# ---------------------------
# Job Description
# ---------------------------
jd = st.text_area(
    "🧾 Job Description",
    height=180,
    placeholder="Paste the job description here..."
)

# ---------------------------
# Algorithm Selection
# ---------------------------
st.markdown("### ⚙️ Matching Algorithm")

selected_algo = st.radio(
    "Select matching strategy:",
    [
        "Semantic Only",
        "BM25 Only",
        "Keyword / Skill Match Only"
    ]
)

# ---------------------------
# Candidate Count Selection
# ---------------------------
st.markdown("### 👥 Candidate Selection")

num_candidates = st.number_input(
    "How many candidates do you want to match?",
    min_value=1,
    max_value=50,
    value=5,
    step=1
)

# ---------------------------
# Candidate Profiles
# ---------------------------
st.markdown("### 📄 Candidate Profiles")

candidates = []
empty_indices = []

for i in range(num_candidates):
    profile = st.text_area(
        f"Candidate {i + 1}",
        height=90,
        placeholder=f"Enter profile/resume summary for Candidate {i + 1}"
    )

    if not profile.strip():
        empty_indices.append(i + 1)

    candidates.append(profile)

# ---------------------------
# Match Button with Validation
# ---------------------------
if st.button("🔍 Match Candidates"):

    # ❌ Case 1: JD empty
    if not jd.strip():
        st.error("❌ Job Description cannot be empty.")
        st.stop()

    # ❌ Case 2: No candidate profiles entered
    elif len(empty_indices) == num_candidates:
        st.error(
            "❌ No candidate profiles provided.\n\n"
            "👉 Please enter at least one candidate profile."
        )
        st.stop()

    # ⚠️ Case 3: Partial candidate profiles missing
    elif empty_indices:
        st.warning(
            f"⚠️ You selected **{num_candidates} candidates**, but "
            f"profiles are missing for: "
            f"{', '.join(map(str, empty_indices))}.\n\n"
            "👉 Please fill **all candidate profiles** before matching."
        )
        st.stop()

    # ✅ Case 4: All inputs valid
    else:
        with st.spinner("Matching candidates..."):
            results, extracted_keywords = score_candidates(
                jd,
                candidates,
                selected_algo
            )

        df = (
            pd.DataFrame(results)
            .sort_values("final_score", ascending=False)
            .reset_index(drop=True)
        )

        # ======================================================
        # ✅ NEW: Store shared data for multi‑page usage
        # ======================================================
        st.session_state["jd"] = jd
        st.session_state["candidates"] = candidates

        # Store FULL results per algorithm
        if "algorithm_results" not in st.session_state:
            st.session_state["algorithm_results"] = {}

        st.session_state["algorithm_results"][selected_algo] = df

        # Store TOP candidates per algorithm (handles ties)
        top_score = df["final_score"].max()
        top_candidates = df[df["final_score"] == top_score]["candidate"].tolist()

        if "top_candidates" not in st.session_state:
            st.session_state["top_candidates"] = {}

        st.session_state["top_candidates"][selected_algo] = top_candidates

        # ======================================================
        # UI Rendering
        # ======================================================

        # Extracted Keywords
        st.subheader("📌 Extracted JD Key Phrases")
        if extracted_keywords:
            st.write(", ".join(extracted_keywords))
        else:
            st.info("No significant key phrases could be extracted from the JD.")

        # Results Table
        st.subheader("✅ Candidate Scores")
        st.dataframe(
            df.drop(columns=["matched_phrases"]),
            use_container_width=True
        )

        # Best Match / Tie Handling (UI)
        if len(top_candidates) == 1:
            st.success(
                f"🏆 Best Match: **{top_candidates[0]}** "
                f"using **{selected_algo}** "
                f"with **{top_score}%** match"
            )
        else:
            st.success(
                f"🏆 Best Matches (Tie at {top_score}% using {selected_algo})"
            )
            for cand in top_candidates:
                st.markdown(f"- ✅ **{cand}**")
