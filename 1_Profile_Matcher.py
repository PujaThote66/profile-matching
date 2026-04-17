import streamlit as st
import pandas as pd
import requests

# ------------------------------------------------
# Backend API
# ------------------------------------------------
API_BASE_URL = "https://profile-matching-api.onrender.com"

# ------------------------------------------------
# Page Config
# ------------------------------------------------
st.set_page_config(
    page_title="Profile Matcher",
    layout="wide"
)

# =================================================
# 🔑 GEMINI API KEY GATE (ADDED – UI SAFE)
# =================================================
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""

if not st.session_state.gemini_api_key:
    st.title("🔑 Gemini API Key Required")

    st.info(
        "Please enter your Gemini API key to continue.\n\n"
        "✅ Used only for this session\n"
        "✅ Not stored or logged"
    )

    api_key = st.text_input(
        "Enter Gemini API Key",
        type="password",
        placeholder="AIza..."
    )

    if st.button("Save & Continue"):
        if api_key.strip():
            st.session_state.gemini_api_key = api_key.strip()
            st.rerun()
        else:
            st.error("API key cannot be empty.")

    st.stop()

# ------------------------------------------------
# Headers for backend calls (NEW)
# ------------------------------------------------
HEADERS = {
    "X-GEMINI-API-KEY": st.session_state.gemini_api_key
}

# =================================================
# MAIN UI (UNCHANGED)
# =================================================
st.title("🎯 Profile Matching")
st.write("Works for **any job role** using automatic JD keyword extraction")

# ------------------------------------------------
# Job Description
# ------------------------------------------------
jd = st.text_area(
    "🧾 Job Description",
    height=180,
    placeholder="Paste the job description here..."
)

# ------------------------------------------------
# Algorithm Selection
# ------------------------------------------------
st.markdown("### ⚙️ Matching Algorithm")

selected_algo = st.radio(
    "Select matching strategy:",
    [
        "Semantic Only",
        "BM25 Only",
        "Keyword / Skill Match Only"
    ]
)

# ------------------------------------------------
# Candidate Count Selection
# ------------------------------------------------
st.markdown("### 👥 Candidate Selection")

num_candidates = st.number_input(
    "How many candidates do you want to match?",
    min_value=1,
    max_value=50,
    value=5,
    step=1
)

# ------------------------------------------------
# Candidate Profiles
# ------------------------------------------------
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

# ------------------------------------------------
# Match Button with Validation
# ------------------------------------------------
if st.button("🔍 Match Candidates"):

    if not jd.strip():
        st.error("❌ Job Description cannot be empty.")
        st.stop()

    elif len(empty_indices) == num_candidates:
        st.error(
            "❌ No candidate profiles provided.\n\n"
            "👉 Please enter at least one candidate profile."
        )
        st.stop()

    elif empty_indices:
        st.warning(
            f"⚠️ Profiles missing for candidates: "
            f"{', '.join(map(str, empty_indices))}.\n\n"
            "👉 Please fill all candidate profiles."
        )
        st.stop()

    payload = {
        "job_description": jd,
        "candidates": candidates,
        "algorithm": selected_algo
    }

    with st.spinner("Matching candidates..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/match",
                json=payload,
                headers=HEADERS,   # ✅ Gemini key sent here
                timeout=300
            )
        except Exception as e:
            st.error(f"Backend connection failed: {e}")
            st.stop()

    if response.status_code != 200:
        st.error(f"API error: {response.text}")
        st.stop()

    data = response.json()
    results = data["results"]
    extracted_keywords = data.get("extracted_keywords", [])

    df = (
        pd.DataFrame(results)
        .sort_values("final_score", ascending=False)
        .reset_index(drop=True)
    )

    # ------------------------------------------------
    # Store for Interview Panel page (UNCHANGED)
    # ------------------------------------------------
    st.session_state["jd"] = jd
    st.session_state["candidates"] = candidates

    if "algorithm_results" not in st.session_state:
        st.session_state["algorithm_results"] = {}

    st.session_state["algorithm_results"][selected_algo] = df

    top_score = df["final_score"].max()
    top_candidates = df[df["final_score"] == top_score]["candidate"].tolist()

    if "top_candidates" not in st.session_state:
        st.session_state["top_candidates"] = {}

    st.session_state["top_candidates"][selected_algo] = top_candidates

    # ------------------------------------------------
    # UI Output (UNCHANGED)
    # ------------------------------------------------
    st.subheader("📌 Extracted JD Key Phrases")
    if extracted_keywords:
        st.write(", ".join(extracted_keywords))
    else:
        st.info("No key phrases extracted.")

    st.subheader("✅ Candidate Scores")
    st.dataframe(
        df.drop(columns=["matched_phrases"], errors="ignore"),
        use_container_width=True
    )

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
