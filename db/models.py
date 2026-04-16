# db/models.py

from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from datetime import datetime

from db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False)
    candidate_name = Column(String(100))
    resume_text = Column(Text, nullable=False)


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False)
    candidate_id = Column(Integer, nullable=False)
    algorithm_used = Column(String(50))
    match_score = Column(Float)


class InterviewFeedback(Base):
    __tablename__ = "interview_feedback"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, nullable=False)
    panel_feedback = Column(Text)
    panel_rating = Column(Float)
    decision = Column(String(20))  # PASS / HOLD / REJECT
    created_at = Column(DateTime, default=datetime.utcnow)
