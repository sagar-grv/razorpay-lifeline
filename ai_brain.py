import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def decide_recovery_action(failure_reason: str, user_history: str = "Standard user") -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    
    # Graceful fallback if no real API key is provided
    if not api_key or api_key.startswith("gsk_test"):
        print("[MOCK AI] Simulating decision for:", failure_reason)
        r = failure_reason.lower()
        if "bank" in r:
            return {"action": "SCHEDULE_AUTO_RETRY", "reasoning": "Bank server down = transient issue. Silent auto-retry in 10 mins, no user disturbance.", "sms_message": ""}
        if "card" in r:
            return {"action": "SEND_SMS_REMINDER", "reasoning": "Card expired = user must manually update card details before retry can work.", "sms_message": "Hi! Aapka card expire ho gaya, isliye payment fail hui. Please card update karke pay karein: [link]"}
        if "upi" in r:
            return {"action": "SEND_SMS_REMINDER", "reasoning": "UPI PIN blocked = user must reset PIN or switch UPI app.", "sms_message": "UPI PIN blocked tha. Dobara try karein ya dusra UPI app use karein: [link]"}
        return {"action": "SEND_SMS_REMINDER", "reasoning": "Insufficient funds = retrying now will fail again. Polite nudge, suggest later time.", "sms_message": "Bhai, balance kam tha. Salary ke baad is link se pay kar dena: [link]"}

    client = Groq(api_key=api_key)
    prompt = f"""
    You are an AI recovery agent for a fintech company. A payment failed.
    Failure Reason: {failure_reason}
    User History: {user_history}
    
    Decide the best recovery action. Choose ONLY ONE action: 
    "SEND_SMS_REMINDER", "SCHEDULE_AUTO_RETRY", "ESCALATE_TO_HUMAN".
    
    If action is SEND_SMS_REMINDER, write a polite, short SMS message in Hinglish/English.
    Return ONLY valid JSON with keys: "action", "reasoning", "sms_message" (if applicable).
    """
    
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Error: {e}")
        return {"action": "ESCALATE_TO_HUMAN", "reasoning": f"AI failed: {str(e)}", "sms_message": ""}
