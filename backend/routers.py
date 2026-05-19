from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from backend.data import get_db
import backend.auth as auth_service
import backend.interview as interview_service
from backend.schemas import (
    UserCreate, UserDisplay, LoginSchema, SendOTPSchema, VerifyOTPSchema,
    StartInterviewSchema, AnswerSchema, EndInterviewSchema,
    InterviewOut, ReportOut, ResponseOut
)
from typing import List

# ── Auth Router ───────────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/register", response_model=UserDisplay)
def register(req: UserCreate, db: Session = Depends(get_db)):
    return auth_service.create_user(db, req)

@auth_router.post("/login")
def login(req: LoginSchema, db: Session = Depends(get_db)):
    return auth_service.login_user(db, req)

@auth_router.post("/forgot-password/send-otp")
def send_otp(req: SendOTPSchema, db: Session = Depends(get_db)):
    return auth_service.send_otp(db, req)

@auth_router.post("/forgot-password/verify-otp")
def verify_otp(req: VerifyOTPSchema, db: Session = Depends(get_db)):
    return auth_service.verify_otp_reset(db, req)

@auth_router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = auth_service.get_current_user(db, request)
    return {"id": user.id, "username": user.username, "email": user.email}


# ── Interview Router ──────────────────────────────────────────────────────────
interview_router = APIRouter(prefix="/interview", tags=["Interview"])

@interview_router.post("/start")
def start(req: StartInterviewSchema, request: Request, db: Session = Depends(get_db)):
    user = auth_service.get_current_user(db, request)
    result = interview_service.start_interview(db, req, user.id)
    # store the first question as pending
    interview_service.store_first_question(db, result["interview_id"], result["question"])
    return result

@interview_router.post("/answer")
def answer(req: AnswerSchema, request: Request, db: Session = Depends(get_db)):
    user = auth_service.get_current_user(db, request)
    return interview_service.submit_answer(db, req, user.id)

@interview_router.post("/end")
def end(req: EndInterviewSchema, request: Request, db: Session = Depends(get_db)):
    user = auth_service.get_current_user(db, request)
    return interview_service.end_interview(db, req, user.id)

@interview_router.get("/history", response_model=List[InterviewOut])
def history(request: Request, db: Session = Depends(get_db)):
    user = auth_service.get_current_user(db, request)
    return interview_service.get_history(db, user.id)

@interview_router.get("/report/{interview_id}", response_model=ReportOut)
def report(interview_id: int, request: Request, db: Session = Depends(get_db)):
    user = auth_service.get_current_user(db, request)
    return interview_service.get_report(db, interview_id, user.id)

@interview_router.get("/responses/{interview_id}", response_model=List[ResponseOut])
def responses(interview_id: int, request: Request, db: Session = Depends(get_db)):
    user = auth_service.get_current_user(db, request)
    return interview_service.get_responses(db, interview_id, user.id)
