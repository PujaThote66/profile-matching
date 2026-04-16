
import streamlit as st
import pandas as pd
from utils.gemini_utils import generate_interview_questions

# ------------------------------------------------------
# Page Config & Title
# ------------------------------------------------------
st.set_page_config(page_title="Interview Panel", layout="wide")
st.title("🧑‍💼 Interview Panel")

# ------------------------------------------------------
# ✅ Global Guard: Ensure Page‑1 has been executed
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
# Load top candidates for selected algorithm
# ------------------------------------------------------
top_candidates = st.session_state["top_candidates"].get(algorithm_choice, [])

if not isinstance(top_candidates, list) or len(top_candidates) == 0:
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
# Fetch JD & Candidate Resume (Safe Access)
# ------------------------------------------------------
jd = st.session_state.get("jd", "").strip()
candidates = st.session_state.get("candidates", [])

if not jd:
    st.error("❌ Job Description data is missing.")
    st.stop()

try:
    candidate_index = int(selected_candidate.split()[-1]) - 1
    candidate_resume = candidates[candidate_index].strip()
except Exception:
    st.error(
        "❌ Unable to load candidate resume.\n\n"
        "Please re-run matching on the Profile Matcher page."
    )
    st.stop()

if not candidate_resume:
    st.warning("⚠️ Candidate resume is empty.")
    st.stop()

# ------------------------------------------------------
# Gemini Question Generation Section
# ------------------------------------------------------
st.subheader("🧠 Behavioral & L1 Technical Questions")

if st.button("Generate Interview Questions"):
    try:
        with st.spinner("Generating questions using Gemini..."):
            questions = generate_interview_questions(
                jd,
                candidate_resume
            )
        if not questions or not questions.strip():
            st.error("❌ Gemini returned an empty response.")
        else:
            st.session_state["generated_questions"] = questions
    except Exception as e:
        st.error(
            "❌ Failed to generate questions using Gemini.\n\n"
            "Possible reasons:\n"
            "- API key missing or invalid\n"
            "- Network issue\n"
            "- Free tier limit exceeded\n\n"
            f"Error: {str(e)}"
        )

# ------------------------------------------------------
# Display Generated Questions
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
# Score Sheet (Panel View)
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