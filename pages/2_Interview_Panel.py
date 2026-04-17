import streamlit as st
import pandas as pd
import requests

API_BASE_URL = "https://profile-matching-api.onrender.com"

# ------------------------------------------------------
# Page Config & Title
# ------------------------------------------------------
st.set_page_config(page_title="Interview Panel", layout="wide")
st.title("🧑‍💼 Interview Panel")

# ======================================================
# 🔑 GEMINI API KEY GATE (NEW)
# ======================================================
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""

if not st.session_state.gemini_api_key:
    st.info(
        "🔑 Please enter your Gemini API key to continue.\n\n"
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

HEADERS = {
    "X-GEMINI-API-KEY": st.session_state.gemini_api_key
}

# ------------------------------------------------------
# ✅ Global Guard: Ensure Profile Matcher ran first
# ------------------------------------------------------
required_keys = ["jd", "candidates", "top_candidates"]
missing_keys = [k for k in required_keys if k not in st.session_state]

if missing_keys:
    st.warning(
        "⚠️ Required data is missing.\n\n"
        "Please complete candidate matching on the **Profile Matcher** page first."
    )
    st.stop()

# ------------------------------------------------------
# Algorithm Selection
# ------------------------------------------------------
st.subheader("⚙️ Select Matching Algorithm")

algorithm_choice = st.radio(
    "Choose algorithm:",
    [
        "Semantic Only",
        "BM25 Only",
        "Keyword / Skill Match Only"
    ]
)

# ------------------------------------------------------
# Load Top Candidates
# ------------------------------------------------------
top_candidates = st.session_state["top_candidates"].get(algorithm_choice, [])

if not top_candidates:
    st.info(
        f"No top candidates available for **{algorithm_choice}**.\n\n"
        "Run matching using this algorithm on the Profile Matcher page."
    )
    st.stop()

# ------------------------------------------------------
# Candidate Selection
# ------------------------------------------------------
st.subheader("👤 Select Candidate for Interview")

selected_candidate = st.selectbox(
    "Top candidates:",
    top_candidates
)

# ------------------------------------------------------
# Fetch JD & Candidate Resume
# ------------------------------------------------------
jd = st.session_state.get("jd", "").strip()
candidates = st.session_state.get("candidates", [])

try:
    candidate_index = int(selected_candidate.split()[-1]) - 1
    candidate_resume = candidates[candidate_index].strip()
except Exception:
    st.error(
        "❌ Unable to load candidate resume.\n\n"
        "Please re-run matching on the Profile Matcher page."
    )
    st.stop()

# ------------------------------------------------------
# Interview Question Generation (🔑 Gemini via Backend)
# ------------------------------------------------------
st.subheader("🧠 Behavioral & L1 Technical Questions")

if st.button("Generate Interview Questions"):
    payload = {
        "job_description": jd,
        "candidate_resume": candidate_resume
    }

    with st.spinner("Generating questions using Gemini..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/interview-questions",
                json=payload,
                headers=HEADERS,
                timeout=300
            )
        except Exception as e:
            st.error(f"❌ Failed to connect to backend: {e}")
            st.stop()

    if response.status_code != 200:
        st.error(response.text)
        st.stop()

    questions = response.json().get("questions", "")

    if questions.strip():
        st.session_state["generated_questions"] = questions
    else:
        st.error("❌ Gemini returned an empty response.")

# ------------------------------------------------------
# Display Questions
# ------------------------------------------------------
if "generated_questions" in st.session_state:
    st.markdown("### 📋 Interview Questions")
    st.markdown(st.session_state["generated_questions"])

# ------------------------------------------------------
# Panel Notes
# ------------------------------------------------------
st.subheader("📝 Panel Notes")

panel_notes = st.text_area(
    "Enter interviewer notes:",
    height=150,
    placeholder="Strengths, weaknesses, examples discussed..."
)

# ------------------------------------------------------
# Score Input
# ------------------------------------------------------
st.subheader("⭐ Interview Score")

score = st.slider(
    "Overall interview score (0–10)",
    min_value=0,
    max_value=10,
    value=5
)

# ------------------------------------------------------
# Save Interview Evaluation
# ------------------------------------------------------
if "interview_scores" not in st.session_state:
    st.session_state["interview_scores"] = {}

if st.button("💾 Save Interview Evaluation"):
    st.session_state["interview_scores"][selected_candidate] = {
        "algorithm": algorithm_choice,
        "score": score,
        "notes": panel_notes
    }
    st.success("✅ Interview evaluation saved successfully")

# ------------------------------------------------------
# Score Sheet
# ------------------------------------------------------
st.subheader("📊 Interview Score Sheet")

if st.session_state["interview_scores"]:
    score_df = pd.DataFrame.from_dict(
        st.session_state["interview_scores"],
        orient="index"
    )
    st.dataframe(score_df)
else:
    st.info("No interview evaluations recorded yet.")