from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime



class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone: Optional[str] = None

class UserDisplay(BaseModel):
    id: int
    username: str
    email: str
    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    username: str
    password: str

class SendOTPSchema(BaseModel):
    phone: str

class VerifyOTPSchema(BaseModel):
    phone: str
    otp_code: str
    new_password: str



class StartInterviewSchema(BaseModel):
    role: str
    level: str
    api_key: str

class AnswerSchema(BaseModel):
    interview_id: int
    answer: str
    api_key: str

class EndInterviewSchema(BaseModel):
    interview_id: int
    api_key: str


class ResponseOut(BaseModel):
    id: int
    question: str
    answer: str
    score: Optional[float]
    feedback: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class ReportOut(BaseModel):
    id: int
    interview_id: int
    technical_score: float
    communication_score: float
    overall_score: float
    strengths: str
    weaknesses: str
    recommendations: str
    summary: str
    created_at: datetime
    class Config:
        from_attributes = True

class InterviewOut(BaseModel):
    id: int
    role: str
    level: str
    created_at: datetime
    ended_at: Optional[datetime]
    status: str
    class Config:
        from_attributes = True
