
import os
from dotenv import load_dotenv
import google.generativeai as genai


# ------------------------------------------------------
# Load environment variables
# ------------------------------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found. Please set it in .env or environment variables."
    )


# ------------------------------------------------------
# Configure Gemini
# ------------------------------------------------------
genai.configure(api_key=GEMINI_API_KEY)


# ------------------------------------------------------
# ✅ Auto‑select a compatible model (IMPORTANT FIX)
# ------------------------------------------------------
def get_compatible_model():
    """
    Dynamically selects the first model that supports text generation.
    Works across ALL google-generativeai SDK versions.
    """

    print("gen ai model list : ",genai.list_models())
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print("selected model is : ",genai.GenerativeModel(m.name))
            return genai.GenerativeModel(m.name)

    raise RuntimeError("No compatible Gemini model found for generateContent.")


# Initialize model safely
model = get_compatible_model()

# ------------------------------------------------------
# Interview Question Generator
# ------------------------------------------------------
def generate_interview_questions(jd: str, resume: str) -> str:
    if not jd.strip():
        raise ValueError("Job Description is empty.")

    if not resume.strip():
        raise ValueError("Candidate resume is empty.")

    prompt = f"""
You are a senior technical interviewer.

Job Description:
{jd}

Candidate Resume:
{resume}

Generate:
1. 5 Behavioral interview questions
2. 5 L1 Technical interview questions

Rules:
- Do NOT include answers
- Avoid advanced system design questions
- Keep questions clear and practical
- Use EXACTLY this format:

Behavioral Questions:
1.
2.
3.
4.
5.

L1 Technical Questions:
1.
2.
3.
4.
5.
"""

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {str(e)}")

    if not response or not hasattr(response, "text"):
        raise RuntimeError("Gemini returned an invalid response.")

    if not response.text.strip():
        raise RuntimeError("Gemini returned an empty response.")

    return response.text.strip()
