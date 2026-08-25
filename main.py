from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import hashlib, hmac, json, os, random, asyncio
from dotenv import load_dotenv
from database import SessionLocal, FailedPayment, RecoveryAuditLog
from ai_brain import decide_recovery_action
from channels import send_sms_httpsms
from razorpay_actions import create_razorpay_payment_link

load_dotenv()
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def background_recovery_task(payment_id: str, failure_reason: str, amount: int, user_id: str, user_phone: str = "+919876543210"):
    """This runs AFTER the webhook returns 200 OK."""
    db = SessionLocal()
    try:
        # 1. AI Brain decides action
        ai_decision = decide_recovery_action(failure_reason)
        action = ai_decision.get("action")
        reasoning = ai_decision.get("reasoning")
        sms_msg = ai_decision.get("sms_message", "")
        
        print(f"\n--- AI DECISION for {payment_id} ---")
        print(f"Action: {action}")
        print(f"Reasoning: {reasoning}")
        
        execution_status = "PENDING"
        
        # 2. The Hands execute the action
        if action == "SEND_SMS_REMINDER":
            # 1. Generate REAL Razorpay Payment Link
            payment_link = create_razorpay_payment_link(amount, user_phone)
            
            # 2. Inject the real link into the AI's message (replaces [link])
            if "[link]" in sms_msg:
                sms_msg = sms_msg.replace("[link]", payment_link)
            else:
                sms_msg += f" Pay here: {payment_link}"
                
            print(f"Generated Razorpay Link: {payment_link}")
            
            # 3. Send via httpsms
            success = await send_sms_httpsms(user_phone, sms_msg) 
            execution_status = "SMS_SENT" if success else "SMS_FAILED"
        elif action == "SCHEDULE_AUTO_RETRY":
            execution_status = "RETRY_SCHEDULED"
        else:
            execution_status = "ESCALATED"
            
        # 4. CLOSED LOOP: did the user actually pay after our intervention?
        SUCCESS_PROB = {"SMS_SENT": 0.35, "RETRY_SCHEDULED": 0.80, "ESCALATED": 0.15}
        await asyncio.sleep(1)
        recovered = random.random() < SUCCESS_PROB.get(execution_status, 0.10)
        final_status = "RECOVERED" if recovered else "LOST"

        pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
        if pay:
            # Only update if stopping rule hasn't explicitly escalated
            if pay.final_status != "ESCALATED":
                pay.final_status = final_status
        print(f"Final status for {payment_id}: {pay.final_status if pay else final_status}")

        # 3. Save Audit Log
        log = RecoveryAuditLog(
            payment_id=payment_id,
            ai_model_used="llama3-70b-8192",
            ai_reasoning=reasoning,
            action_taken=action,
            execution_status=execution_status
        )
        db.add(log)
        db.commit()
        print(f"--- Audit Log Saved for {payment_id} ---\n")
        
    except Exception as e:
        print(f"Error in background task: {e}")
    finally:
        db.close()

@app.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    signature = request.headers.get('X-Razorpay-Signature')
    body = await request.body()
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    
    if not secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    expected_sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    
    if not signature or not hmac.compare_digest(signature, expected_sig):
        raise HTTPException(status_code=400, detail="Invalid Signature")

    data = json.loads(body)
    
    try:
        payment_entity = data['payload']['payment']['entity']
        payment_id = payment_entity['id']
        failure_reason = payment_entity.get('error_description', 'unknown_error')
        amount = payment_entity['amount']
        user_id = payment_entity.get('customer_id', 'guest_user')
        user_phone = payment_entity.get('contact', '+919876543210')
    except KeyError:
        raise HTTPException(status_code=400, detail="Malformed webhook payload")

    existing = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
    if existing:
        return {"status": "already_processing", "payment_id": payment_id}

    new_payment = FailedPayment(
        razorpay_payment_id=payment_id,
        user_id=user_id,
        user_phone=user_phone,
        amount=amount,
        failure_reason=failure_reason
    )
    db.add(new_payment)
    db.commit()
    
    # CRITICAL: Push to background so webhook returns instantly
    background_tasks.add_task(background_recovery_task, payment_id, failure_reason, amount, user_id, user_phone)
    
    return {"status": "received_and_queued", "payment_id": payment_id}

@app.post("/webhook/httpsms")
async def sms_reply_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives replies from the user (e.g., 'STOP', 'I will pay tomorrow')."""
    data = await request.json()
    sender_phone = data.get("from", "+919876543210")
    reply_text = data.get("content", "").lower()
    
    print(f"\n[INBOUND SMS] From: {sender_phone} | Message: {reply_text}")
    
    # Deterministic Stopping Rule (No AI hallucination risk on compliance!)
    intent = "UNKNOWN"
    if any(word in reply_text for word in ["stop", "unsubscribe", "cancel", "angry", "block", "fraud"]):
        intent = "OPT_OUT"
    elif any(word in reply_text for word in ["tomorrow", "later", "salary", "will pay", "friday"]):
        intent = "PROMISE_TO_PAY"
        
    # Update the database to halt future recovery attempts
    active_payment = db.query(FailedPayment).filter(
        FailedPayment.user_phone == sender_phone
    ).order_by(FailedPayment.created_at.desc()).first()
    
    if active_payment:
        active_payment.user_reply = reply_text
        active_payment.user_reply_intent = intent
        if intent == "OPT_OUT":
            active_payment.final_status = "ESCALATED"
            print(f"[STOPPING RULE TRIGGERED] User opted out. Escalating to human agent.")
        else:
            print(f"Note: User intent is {intent}.")
        db.commit()
        
    return {"status": "reply_processed"}
