from sqlalchemy.orm import Session
from backend.schemas import UserCreate, LoginSchema, SendOTPSchema, VerifyOTPSchema
from backend.model import User, OTPRecord
from backend.hash import Hash
from fastapi import HTTPException, status, Request
import jwt, os, random
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

from twilio.rest import Client as TwilioClient

def _make_token(email: str) -> str:
    exp = datetime.utcnow() + timedelta(hours=8)
    return jwt.encode({"id": email, "exp": exp}, os.getenv("SECRET_KEY", "dev-secret"), os.getenv("ALGORITHM", "HS256"))

def get_current_user(db: Session, request: Request):
    auth = request.headers.get("authorization", "")
    if not auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth.split(" ")[-1]
    try:
        data = jwt.decode(token, os.getenv("SECRET_KEY", "dev-secret"), algorithms=[os.getenv("ALGORITHM", "HS256")])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == data.get("id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def create_user(db: Session, req: UserCreate):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    u = User(username=req.username, email=req.email, password=Hash.bcrypt(req.password), phone=req.phone)
    db.add(u); db.commit(); db.refresh(u)
    return u

def login_user(db: Session, req: LoginSchema):
    u = db.query(User).filter(User.username == req.username).first()
    if not u or not Hash.verify(req.password, u.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"token": _make_token(u.email), "username": u.username, "user_id": u.id}

def send_otp(db: Session, req: SendOTPSchema):
    u = db.query(User).filter(User.phone == req.phone).first()
    if not u:
        raise HTTPException(status_code=404, detail="No account with this phone number")
    otp = str(random.randint(100000, 999999))
    db.query(OTPRecord).filter(OTPRecord.phone == req.phone, OTPRecord.is_used == False).update({"is_used": True})
    db.add(OTPRecord(phone=req.phone, otp_code=otp))
    db.commit()
    try:
        client = TwilioClient(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        client.messages.create(body=f"Your InterviewAI OTP: {otp}. Valid 10 mins.", from_=os.getenv("TWILIO_PHONE_NUMBER"), to=req.phone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMS error: {e}")
    return {"message": "OTP sent"}

def verify_otp_reset(db: Session, req: VerifyOTPSchema):
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    rec = db.query(OTPRecord).filter(OTPRecord.phone==req.phone, OTPRecord.otp_code==req.otp_code, OTPRecord.is_used==False, OTPRecord.created_at>=cutoff).first()
    if not rec:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    u = db.query(User).filter(User.phone == req.phone).first()
    u.password = Hash.bcrypt(req.new_password)
    rec.is_used = True
    db.commit()
    return {"message": "Password reset successful"}
