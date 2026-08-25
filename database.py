from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FailedPayment(Base):
    __tablename__ = "failed_payments"
    id = Column(Integer, primary_key=True, index=True)
    razorpay_payment_id = Column(String, unique=True, index=True)
    user_id = Column(String)
    user_phone = Column(String, default="+919876543210")
    user_reply = Column(String, nullable=True)
    user_reply_intent = Column(String, nullable=True)  # OPT_OUT, PROMISE_TO_PAY, UNKNOWN
    amount = Column(Integer)
    failure_reason = Column(String)
    status = Column(String, default="PENDING_RECOVERY")
    final_status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

class RecoveryAuditLog(Base):
    __tablename__ = "recovery_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String)
    ai_model_used = Column(String)
    ai_reasoning = Column(Text)
    action_taken = Column(String)
    execution_status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
