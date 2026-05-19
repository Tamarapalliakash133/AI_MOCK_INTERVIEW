from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.data import Base


class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email    = Column(String, unique=True, index=True)
    password = Column(String)
    phone    = Column(String, nullable=True)
    interviews = relationship("Interview", back_populates="user")


class OTPRecord(Base):
    __tablename__ = "otp_records"
    id         = Column(Integer, primary_key=True, index=True)
    phone      = Column(String, index=True)
    otp_code   = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_used    = Column(Boolean, default=False)


class Interview(Base):
    __tablename__ = "interviews"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    role       = Column(String)
    level      = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at   = Column(DateTime, nullable=True)
    status     = Column(String, default="active")   # active | ended
    user       = relationship("User", back_populates="interviews")
    responses  = relationship("Response", back_populates="interview")
    report     = relationship("Report", back_populates="interview", uselist=False)


class Response(Base):
    __tablename__ = "responses"
    id           = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    question     = Column(Text)
    answer       = Column(Text)
    score        = Column(Float, nullable=True)
    feedback     = Column(Text, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    interview    = relationship("Interview", back_populates="responses")


class Report(Base):
    __tablename__ = "reports"
    id                  = Column(Integer, primary_key=True, index=True)
    interview_id        = Column(Integer, ForeignKey("interviews.id"), unique=True)
    technical_score     = Column(Float)
    communication_score = Column(Float)
    overall_score       = Column(Float)
    strengths           = Column(Text)
    weaknesses          = Column(Text)
    recommendations     = Column(Text)
    summary             = Column(Text)
    created_at          = Column(DateTime, default=datetime.utcnow)
    interview           = relationship("Interview", back_populates="report")
