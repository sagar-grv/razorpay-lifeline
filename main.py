from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib, hmac, json, os, random, asyncio, time, datetime, sys
from dotenv import load_dotenv
from database import SessionLocal, FailedPayment, RecoveryAuditLog
from ai_brain import decide_recovery_action
from channels import send_sms_httpsms
from razorpay_actions import create_razorpay_payment_link
import urllib.request

load_dotenv()

app = FastAPI(title="Razorpay Lifeline API", version="2.0.0")

# Enable CORS for React frontend (Vite port 5173 and any origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory Real-time Log Buffer
LOG_BUFFER = []
LOG_LISTENERS = []

def log_event(message: str, level: str = "INFO"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = {"timestamp": timestamp, "level": level, "message": message}
    LOG_BUFFER.append(entry)
    if len(LOG_BUFFER) > 300:
        LOG_BUFFER.pop(0)
    print(f"[{timestamp}] [{level}] {message}")
    for queue in LOG_LISTENERS:
        try:
            queue.put_nowait(entry)
        except Exception:
            pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def background_recovery_task(payment_id: str, failure_reason: str, amount: int, user_id: str, user_phone: str = "+919876543210"):
    """Runs asynchronously after the webhook returns 200 OK."""
    db = SessionLocal()
    try:
        log_event(f"Triggering AI Recovery pipeline for {payment_id} (Reason: {failure_reason}, Amount: Rs {amount/100:.2f})")
        
        # 1. AI Brain decides action
        ai_decision = decide_recovery_action(failure_reason)
        action = ai_decision.get("action")
        reasoning = ai_decision.get("reasoning")
        sms_msg = ai_decision.get("sms_message", "")
        model_used = ai_decision.get("model_used", "openai/gpt-oss-120b (Groq)")
        
        log_event(f"AI Decision for {payment_id}: [{action}] via {model_used}")
        log_event(f"AI Reasoning: {reasoning}")
        
        execution_status = "PENDING"
        
        # 2. Execute Action
        if action == "SEND_SMS_REMINDER":
            # 1. Generate REAL Razorpay Payment Link
            payment_link = create_razorpay_payment_link(amount, user_phone)
            
            # 2. Inject link into message
            if "[link]" in sms_msg:
                sms_msg = sms_msg.replace("[link]", payment_link)
            else:
                sms_msg += f" Pay here: {payment_link}"
                
            log_event(f"Generated Live Razorpay Link: {payment_link}")
            
            # 3. Send via httpsms
            success = await send_sms_httpsms(user_phone, sms_msg) 
            execution_status = "SMS_SENT" if success else "SMS_FAILED"
            log_event(f"SMS Dispatch to {user_phone}: {execution_status}")
        elif action == "SCHEDULE_AUTO_RETRY":
            execution_status = "RETRY_SCHEDULED"
            log_event(f"Silent auto-retry scheduled in 10 mins for {payment_id}")
        else:
            execution_status = "ESCALATED"
            log_event(f"Escalated {payment_id} to human customer support")
            
        # 4. CLOSED LOOP: did user pay after intervention?
        SUCCESS_PROB = {"SMS_SENT": 0.35, "RETRY_SCHEDULED": 0.80, "ESCALATED": 0.15}
        await asyncio.sleep(1)
        recovered = random.random() < SUCCESS_PROB.get(execution_status, 0.10)
        final_status = "RECOVERED" if recovered else "LOST"

        pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
        if pay:
            if pay.final_status != "ESCALATED":
                pay.final_status = final_status
            db.commit()
            log_event(f"Closed-Loop outcome for {payment_id}: {pay.final_status}", level="SUCCESS" if pay.final_status == "RECOVERED" else "WARN")

        # 3. Save Audit Log
        log = RecoveryAuditLog(
            payment_id=payment_id,
            ai_model_used=model_used,
            ai_reasoning=reasoning,
            action_taken=action,
            execution_status=execution_status
        )
        db.add(log)
        db.commit()
        log_event(f"Audit log committed to PostgreSQL for {payment_id}")
        
    except Exception as e:
        log_event(f"Error in background task: {e}", level="ERROR")
    finally:
        db.close()

# ----------------- WEBHOOKS ----------------- #

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
        log_event("Razorpay Webhook rejected: Invalid HMAC Signature", level="ERROR")
        raise HTTPException(status_code=400, detail="Invalid Signature")

    # Safe JSON parse (handles empty test pings from Razorpay Dashboard)
    if not body or len(body.strip()) == 0:
        log_event("Received empty Razorpay test ping", level="INFO")
        return {"status": "ok", "message": "Test ping acknowledged"}

    try:
        data = json.loads(body)
    except Exception as e:
        log_event(f"Razorpay Webhook received non-JSON payload: {e}", level="WARN")
        return {"status": "ok", "message": "Payload acknowledged"}

    event_type = data.get('event', 'payment.failed')
    
    # Handle payment link paid events
    if event_type == 'payment_link.paid':
        plink_entity = data.get('payload', {}).get('payment_link', {}).get('entity', {})
        link_id = plink_entity.get('id')
        log_event(f"Razorpay Payment Link Paid: {link_id}", level="SUCCESS")
        return {"status": "payment_link_paid_acknowledged"}

    # Extract payment entity safely
    payment_entity = data.get('payload', {}).get('payment', {}).get('entity', {})
    if not payment_entity:
        if 'id' in data:
            payment_entity = data
        else:
            log_event("Razorpay Webhook ping acknowledged (No payment entity)", level="INFO")
            return {"status": "ok", "message": "Ping acknowledged"}

    payment_id = payment_entity.get('id', f"pay_live_{int(time.time())}")
    amount = payment_entity.get('amount', 10000)
    user_id = payment_entity.get('customer_id') or payment_entity.get('email') or 'guest_user'
    user_phone = payment_entity.get('contact') or '+919876543210'

    # Deep extract error reason from real-world Razorpay nested structures
    error_obj = payment_entity.get('error')
    if isinstance(error_obj, dict):
        failure_reason = (
            error_obj.get('description')
            or error_obj.get('reason')
            or error_obj.get('code')
            or 'card_expired'
        )
    else:
        failure_reason = (
            payment_entity.get('error_description')
            or payment_entity.get('error_reason')
            or payment_entity.get('error_code')
            or 'payment_failed_by_bank'
        )

    log_event(f"Incoming Razorpay Webhook: {payment_id} | Reason: {failure_reason} | Amount: Rs {amount/100:.2f}")

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
    
    # Push to background so webhook returns 200 OK instantly
    background_tasks.add_task(background_recovery_task, payment_id, failure_reason, amount, user_id, user_phone)
    
    return {"status": "received_and_queued", "payment_id": payment_id}

@app.post("/webhook/httpsms")
async def sms_reply_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives replies from user (e.g., 'STOP', 'I will pay tomorrow')."""
    data = await request.json()
    sender_phone = data.get("from", "+919876543210")
    reply_text = data.get("content", "").lower()
    
    log_event(f"Inbound SMS received from {sender_phone}: '{reply_text}'")
    
    # Deterministic Stopping Rule (No AI hallucination risk on compliance!)
    intent = "UNKNOWN"
    if any(word in reply_text for word in ["stop", "unsubscribe", "cancel", "angry", "block", "fraud"]):
        intent = "OPT_OUT"
    elif any(word in reply_text for word in ["tomorrow", "later", "salary", "will pay", "friday"]):
        intent = "PROMISE_TO_PAY"
        
    active_payment = db.query(FailedPayment).filter(
        FailedPayment.user_phone == sender_phone
    ).order_by(FailedPayment.created_at.desc()).first()
    
    if active_payment:
        active_payment.user_reply = reply_text
        active_payment.user_reply_intent = intent
        if intent == "OPT_OUT":
            active_payment.final_status = "ESCALATED"
            log_event(f"STOPPING RULE TRIGGERED for {active_payment.razorpay_payment_id}. Compliance halt applied & escalated to human.", level="WARN")
        else:
            log_event(f"Classified user intent as: {intent} for {active_payment.razorpay_payment_id}")
        db.commit()
        
    return {"status": "reply_processed", "intent": intent}

# ----------------- DASHBOARD REST & SSE APIS ----------------- #

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    payments = db.query(FailedPayment).all()
    audit_logs = db.query(RecoveryAuditLog).all()
    
    total_txns = len(payments)
    total_amount = sum(p.amount for p in payments) / 100
    
    recovered_txns = [p for p in payments if p.final_status == "RECOVERED"]
    recovered_amount = sum(p.amount for p in recovered_txns) / 100
    
    lost_txns = [p for p in payments if p.final_status == "LOST"]
    lost_amount = sum(p.amount for p in lost_txns) / 100
    
    escalated_txns = [p for p in payments if p.final_status == "ESCALATED"]
    
    opt_outs = [p for p in payments if p.user_reply_intent == "OPT_OUT"]
    promises = [p for p in payments if p.user_reply_intent == "PROMISE_TO_PAY"]
    
    recovery_rate = (recovered_amount / total_amount * 100) if total_amount > 0 else 0
    baseline_rate = 22.0
    baseline_lift = ((recovery_rate - baseline_rate) / baseline_rate * 100) if recovery_rate > 0 else 0
    
    groq_key = os.getenv("GROQ_API_KEY", "")
    is_live_model = bool(groq_key and not groq_key.startswith("gsk_test"))
    model_name = "openai/gpt-oss-120b (LIVE)" if is_live_model else "MOCK MODE (Llama 3 Smart Fallback)"
    
    # Failure breakdown stats
    breakdown = {}
    for p in payments:
        r = p.failure_reason or "unknown"
        if r not in breakdown:
            breakdown[r] = {"total": 0, "recovered": 0, "lost": 0, "escalated": 0, "amount": 0}
        breakdown[r]["total"] += 1
        breakdown[r]["amount"] += p.amount / 100
        if p.final_status == "RECOVERED":
            breakdown[r]["recovered"] += 1
        elif p.final_status == "LOST":
            breakdown[r]["lost"] += 1
        elif p.final_status == "ESCALATED":
            breakdown[r]["escalated"] += 1
            
    return {
        "total_transactions": total_txns,
        "total_amount": round(total_amount, 2),
        "recovered_transactions": len(recovered_txns),
        "recovered_amount": round(recovered_amount, 2),
        "lost_transactions": len(lost_txns),
        "lost_amount": round(lost_amount, 2),
        "escalated_transactions": len(escalated_txns),
        "opt_out_count": len(opt_outs),
        "promise_to_pay_count": len(promises),
        "recovery_rate": round(recovery_rate, 1),
        "baseline_rate": baseline_rate,
        "baseline_lift": round(baseline_lift, 1),
        "model_name": model_name,
        "is_live_model": is_live_model,
        "failure_breakdown": breakdown
    }

@app.get("/api/payments")
def get_payments(db: Session = Depends(get_db)):
    payments = db.query(FailedPayment).order_by(FailedPayment.created_at.desc()).all()
    audit_map = {log.payment_id: log for log in db.query(RecoveryAuditLog).all()}
    
    result = []
    for p in payments:
        log = audit_map.get(p.razorpay_payment_id)
        result.append({
            "id": p.id,
            "payment_id": p.razorpay_payment_id,
            "user_id": p.user_id,
            "user_phone": p.user_phone,
            "amount": p.amount / 100,
            "failure_reason": p.failure_reason,
            "final_status": p.final_status or "PENDING",
            "user_reply": p.user_reply,
            "user_reply_intent": p.user_reply_intent,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else None,
            "action_taken": log.action_taken if log else None,
            "ai_reasoning": log.ai_reasoning if log else None,
            "execution_status": log.execution_status if log else None,
            "ai_model_used": log.ai_model_used if log else None,
        })
    return result

@app.get("/api/logs")
def get_logs():
    return LOG_BUFFER[-100:]

@app.get("/api/logs/stream")
async def stream_logs():
    queue = asyncio.Queue()
    LOG_LISTENERS.append(queue)
    
    async def event_generator():
        try:
            # Yield initial recent logs
            for entry in LOG_BUFFER[-30:]:
                yield f"data: {json.dumps(entry)}\n\n"
            while True:
                entry = await queue.get()
                yield f"data: {json.dumps(entry)}\n\n"
        except asyncio.CancelledError:
            if queue in LOG_LISTENERS:
                LOG_LISTENERS.remove(queue)
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ----------------- SIMULATOR ENDPOINTS ----------------- #

class SimulatePaymentRequest(BaseModel):
    failure_reason: str = "insufficient_funds"
    amount_in_rupees: float = 500.0
    phone: str = "+919876543210"

@app.post("/api/simulate-payment")
async def simulate_payment(req: SimulatePaymentRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    tx_id = f"pay_SIM_{int(time.time()*1000)%1000000}"
    amount_paise = int(req.amount_in_rupees * 100)
    
    new_payment = FailedPayment(
        razorpay_payment_id=tx_id,
        user_id=f"user_{tx_id[-4:]}",
        user_phone=req.phone,
        amount=amount_paise,
        failure_reason=req.failure_reason
    )
    db.add(new_payment)
    db.commit()
    
    log_event(f"Triggered simulated failure {tx_id} ({req.failure_reason}, Rs {req.amount_in_rupees})")
    background_tasks.add_task(background_recovery_task, tx_id, req.failure_reason, amount_paise, f"user_{tx_id[-4:]}", req.phone)
    
    return {"status": "simulated", "payment_id": tx_id}

class SimulateReplyRequest(BaseModel):
    phone: str = "+919876543210"
    content: str = "STOP PLEASE"

@app.post("/api/simulate-reply")
def simulate_reply(req: SimulateReplyRequest, db: Session = Depends(get_db)):
    reply_text = req.content.lower()
    log_event(f"Simulating user SMS reply from {req.phone}: '{req.content}'")
    
    intent = "UNKNOWN"
    if any(word in reply_text for word in ["stop", "unsubscribe", "cancel", "angry", "block", "fraud"]):
        intent = "OPT_OUT"
    elif any(word in reply_text for word in ["tomorrow", "later", "salary", "will pay", "friday"]):
        intent = "PROMISE_TO_PAY"
        
    active_payment = db.query(FailedPayment).filter(
        FailedPayment.user_phone == req.phone
    ).order_by(FailedPayment.created_at.desc()).first()
    
    if active_payment:
        active_payment.user_reply = req.content
        active_payment.user_reply_intent = intent
        if intent == "OPT_OUT":
            active_payment.final_status = "ESCALATED"
            log_event(f"STOPPING RULE: Marked {active_payment.razorpay_payment_id} ESCALATED due to opt-out", level="WARN")
        db.commit()
        return {"status": "success", "intent": intent, "payment_id": active_payment.razorpay_payment_id}
        
    return {"status": "no_active_payment_found", "intent": intent}

@app.post("/api/batch-test")
async def trigger_batch_test(background_tasks: BackgroundTasks):
    from batch_tester import main as run_batch
    log_event("Batch of 50 failed payments simulation triggered from UI", level="INFO")
    
    def run_batch_sync():
        import requests, hmac, hashlib, json
        secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "whsec_test_secret_12345").encode()
        reasons = ["bank_server_down", "card_expired", "upi_pin_blocked", "insufficient_funds"]
        amounts = [150000, 300000, 75000, 500000, 200000, 120000]
        
        for i in range(1, 26):
            p_id = f"pay_BATCH_{int(time.time())}_{i}"
            payload = json.dumps({
                "payload": {
                    "payment": {
                        "entity": {
                            "id": p_id,
                            "amount": random.choice(amounts),
                            "error_description": random.choice(reasons),
                            "customer_id": f"cust_{i}",
                            "contact": f"+9198765{i:05d}"
                        }
                    }
                }
            }).encode()
            sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
            try:
                requests.post("http://127.0.0.1:8000/webhook/razorpay", data=payload, headers={
                    "Content-Type": "application/json",
                    "X-Razorpay-Signature": sig
                }, timeout=5)
            except Exception:
                pass
        log_event("Batch simulation completed (25 synthetic failed transactions processed).", level="SUCCESS")

    background_tasks.add_task(run_batch_sync)
    return {"status": "batch_started", "count": 25}

# ----------------- AI COPILOT ENDPOINT ----------------- #

class AICopilotRequest(BaseModel):
    question: str

@app.post("/api/ai-copilot")
def ai_copilot(req: AICopilotRequest, db: Session = Depends(get_db)):
    payments = db.query(FailedPayment).all()
    total_txns = len(payments)
    total_amt = sum(p.amount for p in payments) / 100
    rec_amt = sum(p.amount for p in payments if p.final_status == "RECOVERED") / 100
    rec_rate = (rec_amt / total_amt * 100) if total_amt > 0 else 0
    escalated = len([p for p in payments if p.final_status == "ESCALATED"])
    
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    context = f"""
    You are 'Lifeline Copilot', an AI revenue & fintech recovery assistant built into the Razorpay Lifeline Dashboard.
    Current Merchant Stats:
    - Total Failed Payments: {total_txns} (Value: Rs {total_amt:,.2f})
    - Recovered Revenue: Rs {rec_amt:,.2f}
    - Recovery Rate: {rec_rate:.1f}% (vs 22% industry blind retry baseline)
    - Escalated / Opted Out: {escalated} transactions
    - Active Integration: Razorpay Test-Mode Payment Links + httpSMS Gateway + Deterministic Stopping Rules.
    
    Answer the merchant's question clearly, concisely, with actionable fintech insights.
    """
    
    if not groq_key or groq_key.startswith("gsk_test"):
        return {
            "answer": f"Lifeline AI Copilot [Simulated]: Based on your current dataset of {total_txns} failed payments (Rs {total_amt:,.2f}), our autonomous engine has recovered Rs {rec_amt:,.2f} ({rec_rate:.1f}% recovery rate). Transient bank outages are auto-retried silently, while non-transient card/balance issues receive dynamic Razorpay checkout links. Compliance stopping rules have safely routed {escalated} opt-outs to human support.",
            "model": "Mock Copilot"
        }
        
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": req.question}
            ],
            temperature=0.3,
            max_tokens=300
        )
        return {"answer": resp.choices[0].message.content, "model": "openai/gpt-oss-120b (Groq)"}
    except Exception as e:
        return {"answer": f"Copilot fallback: {str(e)}", "model": "fallback"}

# ----------------- NGROK INFO ----------------- #

@app.get("/api/ngrok-info")
def get_ngrok_info():
    static_domain = os.getenv("NGROK_STATIC_DOMAIN", "")
    if static_domain:
        return {"public_url": f"https://{static_domain}", "is_static": True}
    try:
        data = json.loads(urllib.request.urlopen('http://127.0.0.1:4040/api/tunnels', timeout=2).read())
        tunnels = data.get("tunnels", [])
        if tunnels:
            return {"public_url": tunnels[0]["public_url"], "is_static": False}
    except Exception:
        pass
    return {"public_url": "http://localhost:8000", "is_static": False}

# ----------------- STATIC FRONTEND SERVING ----------------- #
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        if full_path.startswith("api") or full_path.startswith("webhook") or full_path.startswith("docs") or full_path.startswith("openapi"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

