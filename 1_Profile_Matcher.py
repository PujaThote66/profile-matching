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
# 🔑 GEMINI API KEY GATE  (NEW)
# =================================================
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""

if not st.session_state.gemini_api_key:
    st.title("🔑 Gemini API Key Required")

    st.info(
        "Please enter your Gemini API key to continue.\n\n"
        "✅ The key is used only for this session.\n"
        "✅ It is not stored or logged."
    )

    api_key = st.text_input(
        "Enter Gemini API Key",
        type="password",
        placeholder="AIza..."
    )

    if st.button("Save & Continue"):
        if api_key.strip():
            st.session_state.gemini_api_key = api_key.strip()
            st.experimental_rerun()
        else:
            st.error("API key cannot be empty.")

    st.stop()

# ------------------------------------------------
# Common Headers (USED FOR ALL BACKEND CALLS)
# ------------------------------------------------
HEADERS = {
    "X-GEMINI-API-KEY": st.session_state.gemini_api_key
}

# =================================================
# MAIN APP STARTS HERE
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
# Candidate Count
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
# Match Button
# ------------------------------------------------
if st.button("🔍 Match Candidates"):

    if not jd.strip():
        st.error("❌ Job Description cannot be empty.")
        st.stop()

    elif len(empty_indices) == num_candidates:
        st.error("❌ Please enter at least one candidate profile.")
        st.stop()

    elif empty_indices:
        st.warning(
            f"⚠️ Profiles missing for candidates: {', '.join(map(str, empty_indices))}"
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
                headers=HEADERS,
                timeout=300
            )
        except Exception as e:
            st.error(f"Backend connection failed: {e}")
            st.stop()

    if response.status_code != 200:
        st.error(response.text)
        st.stop()

    data = response.json()
    df = pd.DataFrame(data["results"]).sort_values(
        "final_score", ascending=False
    )

    st.subheader("✅ Candidate Scores")
    st.dataframe(df.drop(columns=["matched_phrases"]), use_container_width=True)

# =================================================
# 📂 NEW BUTTON – FETCH ALL INTERVIEWS FROM DB
# =================================================
st.markdown("---")
st.subheader("📂 Stored Interviews")

if st.button("📥 Get All Interview Records"):
    with st.spinner("Fetching interview records..."):
        try:
            resp = requests.get(
                f"{API_BASE_URL}/interviews",
                headers=HEADERS,
                timeout=120
            )
        except Exception as e:
            st.error(f"Backend connection failed: {e}")
            st.stop()

    if resp.status_code != 200:
        st.error(resp.text)
        st.stop()

    interviews = resp.json()

    if not interviews:
        st.info("No interview records found.")
    else:
        df_interviews = pd.DataFrame(interviews)
        st.dataframe(df_interviews, use_container_width=True)