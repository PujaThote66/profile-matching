# api/main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

# Reuse existing core logic
from matcher import score_candidates
from utils.gemini_utils import generate_interview_questions

# DB imports
from db.database import SessionLocal
from db import models


# -----------------------------------------------------
# FastAPI App Initialization
# -----------------------------------------------------
app = FastAPI(
    title="Profile Matching & Interview API",
    description="Public API for candidate matching, interview question generation, and interview feedback storage",
    version="1.0.0"
)


# -----------------------------------------------------
# DB Session Dependency
# -----------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------
# Health Check
# -----------------------------------------------------
@app.get("/")
def health_check():
    return {"status": "API is running"}


# -----------------------------------------------------
# Request / Response Models
# -----------------------------------------------------
class MatchRequest(BaseModel):
    job_description: str
    candidates: List[str]
    algorithm: str


class InterviewQuestionRequest(BaseModel):
    job_description: str
    candidate_resume: str


class InterviewFeedbackRequest(BaseModel):
    job_description: str
    candidate_name: str
    candidate_resume: str
    algorithm_used: str
    match_score: float
    interview_questions: str
    panel_feedback: str
    panel_rating: float
    decision: str  # PASS / HOLD / REJECT


class InterviewResponse(BaseModel):
    interview_id: int
    job_description: str
    candidate_name: str
    algorithm_used: str
    match_score: float
    panel_rating: float | None
    decision: str | None
    created_at: str


# -----------------------------------------------------
# Candidate Matching API
# -----------------------------------------------------
@app.post("/match")
def match_candidates(request: MatchRequest):
    try:
        allowed_algorithms = [
            "Semantic Only",
            "BM25 Only",
            "Keyword / Skill Match Only"
        ]

        if request.algorithm not in allowed_algorithms:
            raise ValueError(
                f"Invalid algorithm '{request.algorithm}'. "
                f"Allowed values: {allowed_algorithms}"
            )

        results, extracted_keywords = score_candidates(
            request.job_description,
            request.candidates,
            request.algorithm
        )

        return {
            "algorithm": request.algorithm,
            "results": results,
            "extracted_keywords": extracted_keywords
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Matcher internal error: {str(e)}"
        )


# -----------------------------------------------------
# Interview Question Generation API
# -----------------------------------------------------
@app.post("/interview-questions")
def interview_questions(request: InterviewQuestionRequest):
    try:
        questions = generate_interview_questions(
            request.job_description,
            request.candidate_resume
        )

        return {"questions": questions}

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Interview question generation failed: {str(e)}"
        )


# -----------------------------------------------------
# Save Interview Feedback API
# -----------------------------------------------------
@app.post("/save-interview-feedback")
def save_interview_feedback(
    request: InterviewFeedbackRequest,
    db: Session = Depends(get_db)
):
    try:
        # Save Job
        job = models.Job(job_description=request.job_description)
        db.add(job)
        db.commit()
        db.refresh(job)

        # Save Candidate
        candidate = models.Candidate(
            job_id=job.id,
            candidate_name=request.candidate_name,
            resume_text=request.candidate_resume
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        # Save Interview
        interview = models.Interview(
            job_id=job.id,
            candidate_id=candidate.id,
            algorithm_used=request.algorithm_used,
            match_score=request.match_score
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)

        # Save Feedback
        feedback = models.InterviewFeedback(
            interview_id=interview.id,
            panel_feedback=request.panel_feedback,
            panel_rating=request.panel_rating,
            decision=request.decision
        )
        db.add(feedback)
        db.commit()

        return {
            "status": "success",
            "message": "Interview feedback saved successfully",
            "interview_id": interview.id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save interview feedback: {str(e)}"
        )


# -----------------------------------------------------
# ✅ GET ALL INTERVIEWS API (UPDATED WITH EXCEPTION HANDLING)
# -----------------------------------------------------
@app.get("/interviews", response_model=List[InterviewResponse])
def get_all_interviews(db: Session = Depends(get_db)):
    try:
        results = (
            db.query(
                models.Interview.id,
                models.Job.job_description,
                models.Candidate.candidate_name,
                models.Interview.algorithm_used,
                models.Interview.match_score,
                models.InterviewFeedback.panel_rating,
                models.InterviewFeedback.decision,
                models.InterviewFeedback.created_at
            )
            .join(models.Job, models.Interview.job_id == models.Job.id)
            .join(models.Candidate, models.Interview.candidate_id == models.Candidate.id)
            .join(
                models.InterviewFeedback,
                models.Interview.id == models.InterviewFeedback.interview_id,
                isouter=True
            )
            .order_by(models.Interview.id.desc())
            .all()
        )

        return [
            InterviewResponse(
                interview_id=row[0],
                job_description=row[1],
                candidate_name=row[2],
                algorithm_used=row[3],
                match_score=float(row[4]),
                panel_rating=float(row[5]) if row[5] is not None else None,
                decision=row[6],
                created_at=row[7].isoformat() if row[7] else ""
            )
            for row in results
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve interviews: {str(e)}"
        )
