from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, text
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
    received_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    late_auth = Column(Boolean, default=False)
    touch_count = Column(Integer, default=0)
    payload_created_at = Column(DateTime, nullable=True)
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

class RecoveryLink(Base):
    __tablename__ = "recovery_links"
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, index=True)
    razorpay_payment_link_id = Column(String, unique=True, index=True)
    short_url = Column(String)
    amount = Column(Integer)
    status = Column(String, default="PENDING_RECOVERY")
    created_at = Column(DateTime, default=datetime.utcnow)

class CustomerPreference(Base):
    __tablename__ = "customer_preferences"
    phone_number = Column(String, primary_key=True)
    status = Column(String, default="ACTIVE")  # ACTIVE | OPTED_OUT | PROMISE_TO_PAY
    promise_followup_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Auto-migration for new columns in PostgreSQL
try:
    with engine.connect() as conn:
        for col_name, col_type in [
            ("received_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("paid_at", "TIMESTAMP"),
            ("late_auth", "BOOLEAN DEFAULT FALSE"),
            ("touch_count", "INTEGER DEFAULT 0"),
            ("payload_created_at", "TIMESTAMP"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE failed_payments ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass
except Exception:
    pass
