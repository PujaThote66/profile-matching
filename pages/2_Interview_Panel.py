import streamlit as st
import pandas as pd
import requests

API_BASE_URL = "https://profile-matching-api.onrender.com"

# ------------------------------------------------------
# Page Config & Title
# ------------------------------------------------------
st.set_page_config(page_title="Interview Panel", layout="wide")
st.title("🧑‍💼 Interview Panel")
# 🔑 GEMINI API KEY INPUT
# ======================================================
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""

if not st.session_state.gemini_api_key:
    st.info(
        "🔑 Please enter your Gemini API key to continue.\n\n"
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

HEADERS = {
    "X-GEMINI-API-KEY": st.session_state.gemini_api_key
}

# ------------------------------------------------------
# ✅ Ensure Profile Matcher ran first
# ------------------------------------------------------
required_keys = ["jd", "candidates", "top_candidates", "algorithm_results"]
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
st.subheader("👤 Select Candidate")

selected_candidate = st.selectbox("Top candidates:", top_candidates)

# ------------------------------------------------------
# Fetch JD & Resume
# ------------------------------------------------------
jd = st.session_state["jd"]
candidates = st.session_state["candidates"]

try:
    candidate_index = int(selected_candidate.split()[-1]) - 1
    candidate_resume = candidates[candidate_index]
except Exception:
    st.error("❌ Unable to load candidate resume.")
    st.stop()

# ------------------------------------------------------
# Interview Question Generation
# ------------------------------------------------------
st.subheader("🧠 Behavioral & L1 Technical Questions")

if st.button("Generate Interview Questions"):
    payload = {
        "job_description": jd,
        "candidate_resume": candidate_resume
    }

    with st.spinner("Generating interview questions..."):
        response = requests.post(
            f"{API_BASE_URL}/interview-questions",
            json=payload,
            headers=HEADERS,
            timeout=300
        )

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
# ✅ Save Interview Feedback to DATABASE (NO DECISION UI)
# ------------------------------------------------------
st.subheader("💾 Save Interview Feedback")

if st.button("Save Interview Feedback to Database"):

    if "generated_questions" not in st.session_state:
        st.error("Please generate interview questions first.")
        st.stop()

    # Get match score from previous results
    result_df = st.session_state["algorithm_results"][algorithm_choice]
    match_score = float(
        result_df[result_df["candidate"] == selected_candidate]["final_score"].iloc[0]
    )

    payload = {
        "job_description": jd,
        "candidate_name": selected_candidate,
        "candidate_resume": candidate_resume,
        "algorithm_used": algorithm_choice,
        "match_score": match_score,
        "interview_questions": st.session_state["generated_questions"],
        "panel_feedback": panel_notes,
        "panel_rating": score,
        "decision": "HOLD"   # ✅ DEFAULT (no UI)
    }

    with st.spinner("Saving interview feedback..."):
        response = requests.post(
            f"{API_BASE_URL}/save-interview-feedback",
            json=payload,
            headers=HEADERS,
            timeout=150
        )

    if response.status_code != 200:
        st.error(response.text)
    else:
        st.success("✅ Interview feedback saved successfully")

# ======================================================
# ✅ GET ALL INTERVIEW HISTORY
# ======================================================
st.markdown("---")
st.subheader("📂 Interview History (Database)")

if st.button("📥 Get All Interview History"):
    with st.spinner("Fetching interview history..."):
        resp = requests.get(
            f"{API_BASE_URL}/interviews",
            headers=HEADERS,
            timeout=120
        )

    if resp.status_code != 200:
        st.error(resp.text)
        st.stop()

    interviews = resp.json()

    if not interviews:
        st.info("No interview history found.")
    else:
        df_history = pd.DataFrame(interviews)
        st.dataframe(df_history, use_container_width=True)


