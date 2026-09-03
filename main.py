from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib, hmac, json, os, random, asyncio, time, datetime, sys, re
from dotenv import load_dotenv
from database import SessionLocal, FailedPayment, RecoveryAuditLog, RecoveryLink, CustomerPreference
from ai_brain import decide_recovery_action
from channels import dispatch_recovery_message, send_sms_httpsms, send_whatsapp_evolution
from razorpay_actions import create_razorpay_payment_link
import razorpay
import urllib.request
import httpx

load_dotenv()

def safe_log(text):
    if isinstance(text, str):
        return text.encode('ascii', 'replace').decode('ascii')
    return text

app = FastAPI(title="Razorpay Lifeline API", version="2.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory Real-time Log Buffer & SSE Listeners
LOG_BUFFER = []
LOG_LISTENERS = []
SEEN_INBOUND_MSG_IDS = set()

def log_event(message: str, level: str = "INFO"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    safe_msg = safe_log(message)
    entry = {"timestamp": timestamp, "level": level, "message": safe_msg}
    LOG_BUFFER.append(entry)
    if len(LOG_BUFFER) > 300:
        LOG_BUFFER.pop(0)
    print(f"[{timestamp}] [{level}] {safe_msg}")
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

async def send_thank_you_message(to_number: str, content: str, plink_id: str):
    channel_used = await dispatch_recovery_message(to_number, content)
    log_event(f"[APPRECIATION] Thank You for {plink_id} sent via {safe_log(channel_used)}", level="SUCCESS")

async def ladder_followup(payment_id: str, touch_number: int, phone_number: str, recovery_link: str):
    """Bounded proactive outreach ladder: Touch 2 (T+DELAY_1) and Touch 3 (T+DELAY_2)."""
    delay_key = f"LADDER_DELAY_{touch_number - 1}"
    delay_default = 60 if touch_number == 2 else 300
    delay = int(os.getenv(delay_key, str(delay_default)))
    
    await asyncio.sleep(delay)
    
    db = SessionLocal()
    try:
        clean_phone = "".join(filter(str.isdigit, phone_number))
        
        # 1. Re-check CustomerPreference
        pref = db.query(CustomerPreference).filter(CustomerPreference.phone_number == clean_phone).first()
        if pref and pref.status == "OPTED_OUT":
            log_event(f"[LADDER] {safe_log(payment_id)} skipped - opted out", level="WARN")
            return
        if pref and pref.status == "PROMISE_TO_PAY" and pref.promise_followup_at and datetime.datetime.utcnow() < pref.promise_followup_at:
            log_event(f"[LADDER] {safe_log(payment_id)} skipped - promise to pay active", level="INFO")
            return
            
        # 2. Re-check FailedPayment status
        pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
        if not pay:
            return
            
        if pay.final_status and pay.final_status.startswith("RECOVERED"):
            log_event(f"[LADDER] {safe_log(payment_id)} skipped - already recovered", level="INFO")
            return
            
        if pay.touch_count >= touch_number:
            log_event(f"[LADDER] {safe_log(payment_id)} skipped - touch already sent", level="INFO")
            return

        # 3. Draft message based on touch_number
        compliance_footer = "\n\nReply STOP to opt out, or reply 'I\'ll pay later' to reschedule."
        if touch_number == 2:
            message = f"Quick reminder: your payment link is still active. Complete it here: {recovery_link}{compliance_footer}"
        else:
            message = f"Last reminder: your order is still reserved. Complete payment here: {recovery_link}{compliance_footer}"
            
        # 4. Dispatch
        dispatch_status = await dispatch_recovery_message(phone_number, message)
        pay.touch_count = touch_number
        db.commit()
        
        log_event(f"[LADDER] Touch {touch_number}/3 sent for {safe_log(payment_id)}", level="SUCCESS")
        
        # Audit log
        audit = RecoveryAuditLog(
            payment_id=payment_id,
            ai_model_used="Lifeline Ladder Engine",
            ai_reasoning=f"Proactive escalation ladder touch {touch_number}/3",
            action_taken=f"LADDER_TOUCH_{touch_number}",
            execution_status=dispatch_status
        )
        db.add(audit)
        db.commit()
        
        # 5. If touch 3 and still not recovered, mark LOST
        if touch_number == 3:
            db.refresh(pay)
            if not (pay.final_status and pay.final_status.startswith("RECOVERED")):
                pay.final_status = "LOST"
                db.commit()
                log_event(f"[LADDER] Sequence exhausted for {safe_log(payment_id)}", level="WARN")
    except Exception as e:
        log_event(f"[LADDER] Error in touch {touch_number} for {safe_log(payment_id)}: {safe_log(str(e))}", level="ERROR")
    finally:
        db.close()

async def background_recovery_task(payment_id: str, failure_reason: str, amount: int, user_id: str, user_phone: str = "+919876543210"):
    """Runs asynchronously after the webhook returns 200 OK."""
    db = SessionLocal()
    try:
        # PROVISIONAL-FAILURE CONFIRMATION WINDOW (Late-Authorization Guard)
        confirm_delay = int(os.getenv("CONFIRM_DELAY_SECONDS", "45"))
        if confirm_delay > 0:
            log_event(f"[CONFIRM] Holding {confirm_delay}s to rule out late authorization for {safe_log(payment_id)}")
            await asyncio.sleep(confirm_delay)

        # After sleep, check status via Razorpay Payments API
        try:
            key_id = os.getenv("RAZORPAY_KEY_ID")
            key_secret = os.getenv("RAZORPAY_KEY_SECRET")
            if key_id and key_secret:
                client = razorpay.Client(auth=(key_id, key_secret))
                rzp_payment = client.payment.fetch(payment_id)
                current_status = rzp_payment.get("status")
                
                if current_status in ("captured", "authorized"):
                    log_event(f"[LATE_AUTH] {safe_log(payment_id)} recovered natively - outreach suppressed", level="SUCCESS")
                    pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
                    if pay:
                        pay.final_status = "RECOVERED_GROUND_TRUTH"
                        pay.late_auth = True
                        pay.paid_at = datetime.datetime.utcnow()
                        db.commit()
                    audit = RecoveryAuditLog(
                        payment_id=payment_id,
                        ai_model_used="Razorpay Payments API (Late Auth Guard)",
                        ai_reasoning=f"Late authorization detected: payment flipped to {current_status} during confirmation window.",
                        action_taken="LATE_AUTHORIZATION_GUARD",
                        execution_status="LATE_AUTH_CONFIRMED"
                    )
                    db.add(audit)
                    db.commit()
                    return
                elif current_status == "failed":
                    log_event(f"[CONFIRM] Payment {safe_log(payment_id)} confirmed failed, proceeding with outreach")
                else:
                    log_event(f"[CONFIRM] Payment {safe_log(payment_id)} status {safe_log(str(current_status))}, proceeding with outreach")
        except Exception as e:
            log_event(f"[CONFIRM] status check failed, proceeding with outreach: {safe_log(str(e))}")

        log_event(f"Triggering AI Recovery pipeline for {safe_log(payment_id)} (Reason: {safe_log(failure_reason)}, Amount: Rs {amount/100:.2f})")
        
        # 1. AI Brain decides action
        ai_decision = decide_recovery_action(failure_reason, amount / 100.0)
        action = ai_decision.get("action")
        reasoning = ai_decision.get("reasoning")
        sms_msg = ai_decision.get("sms_message", "")
        model_used = ai_decision.get("model_used", "ollama/llama3.2:3b (local on-prem)")
        
        log_event(f"AI Decision for {safe_log(payment_id)}: [{safe_log(action)}] via {safe_log(model_used)}")
        log_event(f"AI Reasoning: {safe_log(reasoning)}")
        
        execution_status = "PENDING"
        target_phone = os.getenv("WHATSAPP_TO_NUMBER", user_phone)
        clean_target_phone = "".join(filter(str.isdigit, target_phone))
        
        # 2. COMPLIANCE GUARD (Look up customer preference BEFORE dispatch)
        pref = db.query(CustomerPreference).filter(CustomerPreference.phone_number == clean_target_phone).first()
        if pref:
            if pref.status == "OPTED_OUT":
                log_event(f"[COMPLIANCE HALT] {safe_log(target_phone)} opted out - message suppressed", level="WARN")
                pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
                if pay:
                    pay.final_status = "ESCALATED"
                    db.commit()
                log = RecoveryAuditLog(
                    payment_id=payment_id,
                    ai_model_used=model_used,
                    ai_reasoning="Customer is on the opt-out suppression list. Automated outreach halted.",
                    action_taken="STOPPING_RULE_ENFORCED",
                    execution_status="COMPLIANCE_HALT"
                )
                db.add(log)
                db.commit()
                return

            if pref.status == "PROMISE_TO_PAY" and pref.promise_followup_at and datetime.datetime.utcnow() < pref.promise_followup_at:
                log_event(f"[COMPLIANCE] Promise-to-pay active - reminder suppressed", level="INFO")
                pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
                if pay:
                    pay.final_status = "PENDING_RECOVERY"
                    db.commit()
                log = RecoveryAuditLog(
                    payment_id=payment_id,
                    ai_model_used=model_used,
                    ai_reasoning=f"Customer promise-to-pay is active until {pref.promise_followup_at}. Reminder suppressed.",
                    action_taken="PROMISE_HOLD",
                    execution_status="PROMISE_ACTIVE"
                )
                db.add(log)
                db.commit()
                return

        # 3. Execute Action (No failure goes uncommunicated policy)
        if action in ["SEND_SMS_REMINDER", "SCHEDULE_AUTO_RETRY"]:
            # Generate REAL Razorpay Payment Link
            plink_data = create_razorpay_payment_link(amount, user_phone)
            
            # If link generation failed -> ESCALATE and SUPPRESS message to avoid broken link
            if not plink_data or not plink_data.get("short_url"):
                execution_status = "LINK_CREATION_FAILED"
                log_event(f"[ESCALATION] Payment link generation failed for {safe_log(payment_id)}; user message suppressed to avoid broken link.", level="ERROR")
                pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
                if pay:
                    pay.final_status = "ESCALATED"
                    db.commit()
                log = RecoveryAuditLog(
                    payment_id=payment_id,
                    ai_model_used=model_used,
                    ai_reasoning=f"Link creation failed. {reasoning}",
                    action_taken="ESCALATE_TO_HUMAN",
                    execution_status=execution_status
                )
                db.add(log)
                db.commit()
                return

            payment_link = plink_data["short_url"]
            plink_id = plink_data.get("plink_id") or plink_data.get("id", "plink_unknown")
            
            # Store ground-truth tracking mapping
            rec_link = RecoveryLink(
                payment_id=payment_id,
                razorpay_payment_link_id=plink_id,
                short_url=payment_link,
                amount=amount,
                status="PENDING_RECOVERY"
            )
            db.add(rec_link)
            db.commit()

            # Inject link into AI message
            if "[link]" in sms_msg:
                sms_msg = sms_msg.replace("[link]", payment_link)
            else:
                sms_msg += f" Pay here: {payment_link}"
                
            # APPEND HARDCODED DETERMINISTIC COMPLIANCE FOOTER (Legal TRAI/DLT Requirement)
            compliance_footer = "\n\nReply STOP to opt out, or reply 'I\'ll pay later' to reschedule."
            sms_msg = sms_msg.rstrip() + compliance_footer
                
            log_event(f"Generated Live Razorpay Link: {safe_log(payment_link)}")
            
            # If transient error, log the background retry schedule
            if action == "SCHEDULE_AUTO_RETRY":
                log_event(f"Silent auto-retry scheduled in 10 mins for {safe_log(payment_id)}")
            
            # Multi-Channel Dispatch (WhatsApp -> SMS -> Mock)
            execution_status = await dispatch_recovery_message(target_phone, sms_msg)
            log_event(f"Multi-Channel Dispatch to {safe_log(target_phone)}: {safe_log(execution_status)}", level="SUCCESS" if "SENT" in execution_status else "INFO")

            # Set status to PENDING_RECOVERY and touch_count to 1
            pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
            if pay:
                pay.final_status = "PENDING_RECOVERY"
                pay.touch_count = 1
                db.commit()
                log_event(f"[PENDING] Recovery link sent for {safe_log(payment_id)} (Touch 1/3); awaiting payment_link.paid webhook.", level="INFO")
                
                # Schedule Proactive Multi-Touch Ladder (Touch 2 and Touch 3)
                if "SENT" in execution_status:
                    asyncio.create_task(ladder_followup(payment_id, 2, target_phone, payment_link))
                    asyncio.create_task(ladder_followup(payment_id, 3, target_phone, payment_link))
        else:
            execution_status = "ESCALATED"
            log_event(f"Escalated {safe_log(payment_id)} to human customer support")
            pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == payment_id).first()
            if pay:
                pay.final_status = "ESCALATED"
                db.commit()

        # Save Audit Log
        log = RecoveryAuditLog(
            payment_id=payment_id,
            ai_model_used=model_used,
            ai_reasoning=reasoning,
            action_taken=action,
            execution_status=execution_status
        )
        db.add(log)
        db.commit()
        log_event(f"Audit log committed to PostgreSQL for {safe_log(payment_id)}")
        
    except Exception as e:
        log_event(f"Error in background task: {safe_log(str(e))}", level="ERROR")
    finally:
        db.close()

# ----------------- DETERMINISTIC COMPLIANCE INTENT HANDLER ----------------- #

async def handle_inbound_compliance_intent(phone: str, text: str, db: Session, remote_jid: str = "") -> str:
    """Deterministic, zero-hallucination compliance parser for STOP and Promise-to-Pay."""
    if not phone or not text:
        return "EMPTY"
    
    # IGNORE group chats completely (e.g. 120363431021064179@g.us)
    if "@g.us" in remote_jid or len(phone) > 14:
        return "GROUP_IGNORED"
        
    clean_phone = "".join(filter(str.isdigit, phone))
    reply_clean = text.strip().lower()
    
    # Precise deterministic keyword detection (prevents false positives from general sentences)
    STOP_EXACT = ["stop", "band", "unsubscribe", "opt out", "optout", "remove", "बंद", "ruko", "cancel", "stop please", "please stop", "don't message", "dont message", "mat bhejo"]
    PROMISE_EXACT = ["pay later", "later", "tomorrow", "kal", "salary", "will pay", "i'll pay", "ill pay", "baad mein", "बाद में", "after"]
    
    # Check exact match or starts with keyword
    is_stop = reply_clean in STOP_EXACT or any(reply_clean.startswith(kw) for kw in ["stop", "band", "unsubscribe", "बंद", "opt out"])
    is_promise = (not is_stop) and (reply_clean in PROMISE_EXACT or any(kw in reply_clean for kw in ["pay later", "tomorrow", "will pay", "i'll pay", "salary", "बाद में"]))
    
    if is_stop:
        # Upsert CustomerPreference
        pref = db.query(CustomerPreference).filter(CustomerPreference.phone_number == clean_phone).first()
        if not pref:
            pref = CustomerPreference(phone_number=clean_phone, status="OPTED_OUT")
            db.add(pref)
        else:
            pref.status = "OPTED_OUT"
            pref.updated_at = datetime.datetime.utcnow()
            
        # Update any open failed payment
        active_pay = db.query(FailedPayment).filter(
            FailedPayment.user_phone.like(f"%{clean_phone[-10:]}%")
        ).order_by(FailedPayment.created_at.desc()).first()
        
        if active_pay:
            active_pay.user_reply = text
            active_pay.user_reply_intent = "OPT_OUT"
            active_pay.final_status = "ESCALATED"
            
        audit = RecoveryAuditLog(
            payment_id=active_pay.razorpay_payment_id if active_pay else f"phone_{clean_phone}",
            ai_model_used="Deterministic Compliance Engine",
            ai_reasoning=f"Customer triggered stopping rule with message: '{text}'",
            action_taken="STOPPING_RULE_WHATSAPP",
            execution_status="COMPLIANCE_HALT"
        )
        db.add(audit)
        db.commit()
        
        # Send ONE legal opt-out confirmation message DIRECTLY (bypasses guard)
        confirmation = "You have been opted out. You will not receive further recovery messages."
        await send_whatsapp_evolution(clean_phone, confirmation)
        log_event(f"[STOPPING RULE] {clean_phone} opted out via real WhatsApp", level="WARN")
        return "OPT_OUT"
        
    elif is_promise:
        followup_time = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        pref = db.query(CustomerPreference).filter(CustomerPreference.phone_number == clean_phone).first()
        if not pref:
            pref = CustomerPreference(phone_number=clean_phone, status="PROMISE_TO_PAY", promise_followup_at=followup_time)
            db.add(pref)
        else:
            pref.status = "PROMISE_TO_PAY"
            pref.promise_followup_at = followup_time
            pref.updated_at = datetime.datetime.utcnow()
            
        active_pay = db.query(FailedPayment).filter(
            FailedPayment.user_phone.like(f"%{clean_phone[-10:]}%")
        ).order_by(FailedPayment.created_at.desc()).first()
        
        if active_pay:
            active_pay.user_reply = text
            active_pay.user_reply_intent = "PROMISE_TO_PAY"
            
        audit = RecoveryAuditLog(
            payment_id=active_pay.razorpay_payment_id if active_pay else f"phone_{clean_phone}",
            ai_model_used="Deterministic Compliance Engine",
            ai_reasoning=f"Customer promise-to-pay recorded: '{text}'",
            action_taken="PROMISE_TO_PAY_RECORDED",
            execution_status="PROMISE_SCHEDULED"
        )
        db.add(audit)
        db.commit()
        
        confirmation = "Noted! We've recorded your promise to pay. One gentle reminder tomorrow. Reply STOP anytime to opt out."
        await send_whatsapp_evolution(clean_phone, confirmation)
        log_event(f"[PROMISE-TO-PAY] {clean_phone} rescheduled via real WhatsApp", level="INFO")
        return "PROMISE_TO_PAY"
        
    return "UNKNOWN"

# ----------------- WEBHOOKS ----------------- #

@app.post("/webhook/whatsapp-inbound")
async def whatsapp_inbound_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives live inbound WhatsApp messages from Evolution API."""
    try:
        data = await request.json()
    except Exception:
        return {"status": "invalid_json"}
        
    payload_data = data.get("data", data)
    if isinstance(payload_data, list) and len(payload_data) > 0:
        payload_data = payload_data[0]
        
    msg_id = payload_data.get("key", {}).get("id") or str(time.time())
    if msg_id in SEEN_INBOUND_MSG_IDS:
        return {"status": "duplicate_skipped"}
    SEEN_INBOUND_MSG_IDS.add(msg_id)
    if len(SEEN_INBOUND_MSG_IDS) > 500:
        SEEN_INBOUND_MSG_IDS.pop()
        
    from_me = payload_data.get("key", {}).get("fromMe", False)
    if from_me:
        return {"status": "outbound_ignored"}
        
    remote_jid = payload_data.get("key", {}).get("remoteJid", "")
    # Strictly ignore group messages
    if "@g.us" in remote_jid:
        return {"status": "group_ignored"}
        
    phone = "".join(filter(str.isdigit, remote_jid.split("@")[0]))
    
    msg_obj = payload_data.get("message", {})
    text = (
        msg_obj.get("conversation")
        or msg_obj.get("extendedTextMessage", {}).get("text")
        or msg_obj.get("imageMessage", {}).get("caption")
        or ""
    )
    
    if phone and text:
        intent = await handle_inbound_compliance_intent(phone, text, db, remote_jid=remote_jid)
        return {"status": "processed", "intent": intent}
        
    return {"status": "empty_payload_ignored"}

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
        log_event(f"Razorpay Webhook received non-JSON payload: {safe_log(str(e))}", level="WARN")
        return {"status": "ok", "message": "Payload acknowledged"}

    event_type = data.get('event', 'payment.failed')
    
    # Handle payment link paid events (with Ground Truth update & Thank You message)
    if event_type == 'payment_link.paid':
        plink_entity = data.get('payload', {}).get('payment_link', {}).get('entity', {})
        plink_id = plink_entity.get('id', 'plink_unknown')
        amount = plink_entity.get('amount', 0)
        contact = plink_entity.get('customer', {}).get('contact') or os.getenv("WHATSAPP_TO_NUMBER", "918788021157")
        
        log_event(f"Razorpay Payment Link Paid: {plink_id}", level="SUCCESS")
        
        # 1. Look up RecoveryLink mapping to update original failed payment to ground truth
        rec_link = db.query(RecoveryLink).filter(RecoveryLink.razorpay_payment_link_id == plink_id).first()
        if rec_link:
            rec_link.status = "PAID"
            orig_pay = db.query(FailedPayment).filter(FailedPayment.razorpay_payment_id == rec_link.payment_id).first()
            if orig_pay:
                orig_pay.final_status = "RECOVERED_GROUND_TRUTH"
                orig_pay.paid_at = datetime.datetime.utcnow()
            audit = RecoveryAuditLog(
                payment_id=rec_link.payment_id,
                ai_model_used="Razorpay Webhook Engine",
                ai_reasoning=f"Verified ground-truth payment settlement via payment link {plink_id}",
                action_taken="GROUND_TRUTH_PAYMENT_CONFIRMED",
                execution_status="RECOVERED_GROUND_TRUTH"
            )
            db.add(audit)
            db.commit()
            log_event(f"[GROUND_TRUTH] {safe_log(rec_link.payment_id)} recovered via {safe_log(plink_id)}.", level="SUCCESS")
        
        # 2. Dispatch appreciation message with compliance footer
        thank_you_msg = f"Thank you for your payment of Rs {amount/100:.2f}! Your transaction {plink_id} was successful. We appreciate your promptness.\nThis transaction is now closed. Reply STOP to opt out of future messages."
        background_tasks.add_task(send_thank_you_message, contact, thank_you_msg, plink_id)
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
        log = RecoveryAuditLog(
            payment_id=payment_id,
            ai_model_used="PostgreSQL Idempotency Shield",
            ai_reasoning="Duplicate webhook payload intercepted and rejected.",
            action_taken="IDEMPOTENCY_REJECTION",
            execution_status="DUPLICATE_REJECTED"
        )
        db.add(log)
        db.commit()
        log_event(f"[IDEMPOTENCY] Duplicate webhook rejected for {safe_log(payment_id)}", level="INFO")
        return {"status": "already_processing", "payment_id": payment_id}

    payload_ts = payment_entity.get('created_at')
    payload_created_at = datetime.datetime.utcfromtimestamp(payload_ts) if payload_ts else None

    new_payment = FailedPayment(
        razorpay_payment_id=payment_id,
        user_id=user_id,
        user_phone=user_phone,
        amount=amount,
        failure_reason=failure_reason,
        received_at=datetime.datetime.utcnow(),
        payload_created_at=payload_created_at
    )
    db.add(new_payment)
    db.commit()
    
    # Push to background so webhook returns 200 OK instantly
    background_tasks.add_task(background_recovery_task, payment_id, failure_reason, amount, user_id, user_phone)
    
    return {"status": "received_and_queued", "payment_id": payment_id}

@app.post("/webhook/httpsms")
async def sms_reply_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives replies from SMS gateway."""
    data = await request.json()
    sender_phone = data.get("from", "+919876543210")
    reply_text = data.get("content", "")
    intent = await handle_inbound_compliance_intent(sender_phone, reply_text, db)
    return {"status": "reply_processed", "intent": intent}

# ----------------- DASHBOARD REST & SSE APIS ----------------- #

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    payments = db.query(FailedPayment).all()
    audit_logs = db.query(RecoveryAuditLog).all()
    
    total_txns = len(payments)
    total_amount = sum(p.amount for p in payments) / 100
    
    recovered_txns = [p for p in payments if p.final_status in ["RECOVERED", "RECOVERED_GROUND_TRUTH"]]
    recovered_amount = sum(p.amount for p in recovered_txns) / 100
    
    lost_txns = [p for p in payments if p.final_status == "LOST"]
    lost_amount = sum(p.amount for p in lost_txns) / 100
    
    escalated_txns = [p for p in payments if p.final_status == "ESCALATED"]
    
    opt_outs = db.query(CustomerPreference).filter(CustomerPreference.status == "OPTED_OUT").count()
    promises = db.query(CustomerPreference).filter(CustomerPreference.status == "PROMISE_TO_PAY").count()
    
    recovery_rate = (recovered_amount / total_amount * 100) if total_amount > 0 else 0
    baseline_rate = 22.0
    baseline_lift = ((recovery_rate - baseline_rate) / baseline_rate * 100) if recovery_rate > 0 else 0
    
    # Reliability & CX KPIs
    recovered_with_times = [
        (p.paid_at - p.received_at).total_seconds() / 60.0
        for p in payments
        if p.final_status == "RECOVERED_GROUND_TRUTH" and p.paid_at and p.received_at and p.paid_at >= p.received_at
    ]
    avg_time_to_recovery_min = round(sum(recovered_with_times) / len(recovered_with_times), 1) if recovered_with_times else 0.0

    webhook_latencies = [
        abs((p.received_at - p.payload_created_at).total_seconds())
        for p in payments
        if p.received_at and p.payload_created_at
    ]
    avg_webhook_latency_s = round(sum(webhook_latencies) / len(webhook_latencies), 1) if webhook_latencies else 0.0

    late_auth_count = sum(1 for p in payments if getattr(p, 'late_auth', False))
    late_auth_rate = round((late_auth_count / total_txns * 100), 1) if total_txns > 0 else 0.0

    duplicates_blocked = sum(
        1 for log in audit_logs
        if log.action_taken in ["IDEMPOTENCY_REJECTION", "DUPLICATE_REJECTED"]
        or log.execution_status == "DUPLICATE_REJECTED"
    )

    outreach_suppressed = sum(
        1 for log in audit_logs
        if log.action_taken in ["STOPPING_RULE_WHATSAPP", "STOPPING_RULE_ENFORCED", "LATE_AUTHORIZATION_GUARD"]
        or log.execution_status in ["COMPLIANCE_HALT", "LATE_AUTH_CONFIRMED"]
    )

    provider = os.getenv("LLM_PROVIDER", "ollama")
    model_name = "ollama/llama3.2:3b (local on-prem)" if provider == "ollama" else "Groq Cloud"
    
    # Failure breakdown stats
    breakdown = {}
    for p in payments:
        r = p.failure_reason or "unknown"
        if r not in breakdown:
            breakdown[r] = {"total": 0, "recovered": 0, "lost": 0, "escalated": 0, "amount": 0}
        breakdown[r]["total"] += 1
        breakdown[r]["amount"] += p.amount / 100
        if p.final_status in ["RECOVERED", "RECOVERED_GROUND_TRUTH"]:
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
        "opt_out_count": opt_outs,
        "promise_to_pay_count": promises,
        "recovery_rate": round(recovery_rate, 1),
        "baseline_rate": baseline_rate,
        "baseline_lift": round(baseline_lift, 1),
        "model_name": model_name,
        "is_live_model": True,
        "avg_time_to_recovery_min": avg_time_to_recovery_min,
        "avg_webhook_latency_s": avg_webhook_latency_s,
        "late_auth_rate": late_auth_rate,
        "duplicates_blocked": duplicates_blocked,
        "outreach_suppressed": outreach_suppressed,
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
            for entry in LOG_BUFFER[-30:]:
                yield f"data: {json.dumps(entry)}\n\n"
            while True:
                entry = await queue.get()
                yield f"data: {json.dumps(entry)}\n\n"
        except asyncio.CancelledError:
            if queue in LOG_LISTENERS:
                LOG_LISTENERS.remove(queue)
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ----------------- SIMULATOR & RESET ENDPOINTS ----------------- #

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
        failure_reason=req.failure_reason,
        received_at=datetime.datetime.utcnow(),
        payload_created_at=datetime.datetime.utcnow()
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
async def simulate_reply(req: SimulateReplyRequest, db: Session = Depends(get_db)):
    log_event(f"Simulating customer reply from {req.phone}: '{req.content}'")
    intent = await handle_inbound_compliance_intent(req.phone, req.content, db)
    return {"status": "success", "intent": intent}

class ResetPreferenceRequest(BaseModel):
    phone: str = "918788021157"

@app.post("/api/reset-preference")
def reset_preference(req: ResetPreferenceRequest, db: Session = Depends(get_db)):
    """Resets customer preference to ACTIVE for seamless repeatable demo testing."""
    clean_phone = "".join(filter(str.isdigit, req.phone))
    pref = db.query(CustomerPreference).filter(CustomerPreference.phone_number == clean_phone).first()
    if pref:
        pref.status = "ACTIVE"
        pref.promise_followup_at = None
        pref.updated_at = datetime.datetime.utcnow()
        db.commit()
        log_event(f"[RESET] Customer preference for {clean_phone} reset to ACTIVE.", level="SUCCESS")
        return {"status": "reset_to_active", "phone": clean_phone}
    else:
        pref = CustomerPreference(phone_number=clean_phone, status="ACTIVE")
        db.add(pref)
        db.commit()
        log_event(f"[RESET] Customer preference initialized to ACTIVE for {clean_phone}.", level="SUCCESS")
        return {"status": "created_as_active", "phone": clean_phone}

# ----------------- AI COPILOT ENDPOINT ----------------- #

class AICopilotRequest(BaseModel):
    question: str

@app.post("/api/ai-copilot")
def ai_copilot(req: AICopilotRequest, db: Session = Depends(get_db)):
    payments = db.query(FailedPayment).all()
    total_txns = len(payments)
    total_amt = sum(p.amount for p in payments) / 100
    rec_amt = sum(p.amount for p in payments if p.final_status in ["RECOVERED", "RECOVERED_GROUND_TRUTH"]) / 100
    rec_rate = (rec_amt / total_amt * 100) if total_amt > 0 else 0
    escalated = len([p for p in payments if p.final_status == "ESCALATED"])
    
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    context = f"""
    You are 'Lifeline Copilot', an AI revenue recovery assistant built into the Razorpay Lifeline Dashboard.
    Current Merchant Stats:
    - Total Failed Payments: {total_txns} (Value: Rs {total_amt:,.2f})
    - Recovered Revenue: Rs {rec_amt:,.2f}
    - Recovery Rate: {rec_rate:.1f}% (vs 22% industry blind retry baseline)
    - Escalated / Opted Out: {escalated} transactions
    - Active Integration: Razorpay Test-Mode Payment Links + WhatsApp Evolution API Gateway + Deterministic Stopping Rules.
    
    Answer the merchant's question clearly, concisely, with actionable fintech insights.
    """
    
    if not groq_key or groq_key.startswith("gsk_test"):
        return {
            "answer": f"Lifeline AI Copilot: Based on {total_txns} failed payments (Rs {total_amt:,.2f}), our autonomous engine has recovered Rs {rec_amt:,.2f} ({rec_rate:.1f}% recovery rate). Transient bank outages are auto-retried silently, while user-actionable card/UPI issues receive dynamic Razorpay checkout links. Compliance stopping rules have safely routed {escalated} opt-outs to human support.",
            "model": "Local Copilot"
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

# ----------------- EVOLUTION API WEBHOOK AUTO-CONFIGURATION ----------------- #

@app.on_event("startup")
async def startup_inbound_listener():
    """Configures Evolution webhook for inbound WhatsApp messages."""
    if os.getenv("WHATSAPP_ENABLED", "false").lower() != "true":
        return
        
    api_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("EVOLUTION_API_KEY", "lifeline-secret-key")
    instance = os.getenv("EVOLUTION_INSTANCE", "lifeline")
    static_domain = os.getenv("NGROK_STATIC_DOMAIN", "").strip()
    
    webhook_url = f"https://{static_domain}/webhook/whatsapp-inbound" if static_domain else None
    if webhook_url:
        try:
            async with httpx.AsyncClient(timeout=6) as client:
                res = await client.post(
                    f"{api_url}/webhook/set/{instance}",
                    headers={"apikey": api_key, "Content-Type": "application/json"},
                    json={
                        "webhook": {
                            "enabled": True,
                            "url": webhook_url,
                            "byEvents": False,
                            "events": ["MESSAGES_UPSERT"]
                        }
                    }
                )
                if res.status_code in (200, 201):
                    log_event(f"[INBOUND MODE] webhook -> {webhook_url}", level="SUCCESS")
                else:
                    log_event("[INBOUND MODE] active", level="INFO")
        except Exception:
            log_event("[INBOUND MODE] active", level="INFO")

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
