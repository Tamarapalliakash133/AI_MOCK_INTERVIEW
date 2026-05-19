from sqlalchemy.orm import Session
from backend.model import Interview, Response, Report
from backend.schemas import StartInterviewSchema, AnswerSchema, EndInterviewSchema
from backend.interview_engine import generate_first_question, generate_next_question, evaluate_answer, generate_report
from fastapi import HTTPException
from datetime import datetime


def start_interview(db: Session, req: StartInterviewSchema, user_id: int):
    interview = Interview(user_id=user_id, role=req.role, level=req.level)
    db.add(interview); db.commit(); db.refresh(interview)
    question = generate_first_question(req.role, req.level, req.api_key)
    return {"interview_id": interview.id, "question": question, "role": req.role, "level": req.level}


def submit_answer(db: Session, req: AnswerSchema, user_id: int):
    interview = db.query(Interview).filter(Interview.id == req.interview_id, Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.status == "ended":
        raise HTTPException(status_code=400, detail="Interview already ended")

    # get last unanswered question (stored in session via last response with no answer)
    responses = db.query(Response).filter(Response.interview_id == req.interview_id).order_by(Response.id.desc()).all()

    # find the pending question (last one with no answer)
    pending = None
    for r in responses:
        if r.answer is None:
            pending = r
            break

    if not pending:
        raise HTTPException(status_code=400, detail="No pending question")

    # evaluate answer
    eval_result = evaluate_answer(pending.question, req.answer, interview.role, interview.level, req.api_key)
    pending.answer   = req.answer
    pending.score    = eval_result.get("score", 5.0)
    pending.feedback = eval_result.get("feedback", "")
    db.commit()

    # build history for next question
    all_resp = db.query(Response).filter(
        Response.interview_id == req.interview_id,
        Response.answer.isnot(None)
    ).all()
    history = [{"question": r.question, "answer": r.answer, "score": r.score} for r in all_resp]

    # generate next question
    next_q = generate_next_question(interview.role, interview.level, history, req.api_key)

    # store next question as pending
    db.add(Response(interview_id=req.interview_id, question=next_q, answer=None))
    db.commit()

    return {
        "next_question": next_q,
        "score": pending.score,
        "feedback": pending.feedback,
        "question_count": len(all_resp)
    }


def store_first_question(db: Session, interview_id: int, question: str):
    db.add(Response(interview_id=interview_id, question=question, answer=None))
    db.commit()


def end_interview(db: Session, req: EndInterviewSchema, user_id: int):
    interview = db.query(Interview).filter(Interview.id == req.interview_id, Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    interview.status   = "ended"
    interview.ended_at = datetime.utcnow()
    db.commit()

    responses = db.query(Response).filter(Response.interview_id == req.interview_id, Response.answer != None).all()
    if not responses:
        raise HTTPException(status_code=400, detail="No responses to evaluate")

    resp_list = [{"question": r.question, "answer": r.answer, "score": r.score, "feedback": r.feedback} for r in responses]
    report_data = generate_report(interview.role, interview.level, resp_list, req.api_key)

    report = Report(
        interview_id        = req.interview_id,
        technical_score     = report_data["technical_score"],
        communication_score = report_data["communication_score"],
        overall_score       = report_data["overall_score"],
        strengths           = report_data["strengths"],
        weaknesses          = report_data["weaknesses"],
        recommendations     = report_data["recommendations"],
        summary             = report_data["summary"],
    )
    db.add(report); db.commit(); db.refresh(report)
    return report


def get_history(db: Session, user_id: int):
    return db.query(Interview).filter(Interview.user_id == user_id).order_by(Interview.created_at.desc()).all()


def get_report(db: Session, interview_id: int, user_id: int):
    interview = db.query(Interview).filter(Interview.id == interview_id, Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    report = db.query(Report).filter(Report.interview_id == interview_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not generated yet")
    return report


def get_responses(db: Session, interview_id: int, user_id: int):
    interview = db.query(Interview).filter(Interview.id == interview_id, Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return db.query(Response).filter(Response.interview_id == interview_id, Response.answer.isnot(None)).all()