import os
import json
import httpx
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def decide_recovery_action(failure_reason: str, amount_in_rupees: float = 0.0) -> dict:
    """Decides autonomous recovery action with zero-PII leakage and 'no failure goes uncommunicated' policy."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    prompt = f"""You are an autonomous fintech recovery intelligence agent for Razorpay Lifeline. A payment failed.
Failure Reason: {failure_reason}
Amount: Rs {amount_in_rupees:.2f}

Operational Rules:
1. "SEND_SMS_REMINDER" for user-actionable errors (e.g. card expired, insufficient funds, incorrect PIN, declined by bank, wallet limit). Tone: Direct, helpful, urgent.
2. "SCHEDULE_AUTO_RETRY" for transient infrastructure errors (e.g. temporary issue, network glitch, gateway timeout, bank server downtime). Tone: Soft, reassuring.
3. "ESCALATE_TO_HUMAN" for high risk / fraud anomalies.

CRITICAL POLICY — NO FAILURE GOES UNCOMMUNICATED:
Every decision MUST include an "sms_message" containing the exact token "[link]".
- For user-actionable errors: Ask user to retry/update details using [link].
- For transient bank errors: Inform user that an automatic retry is scheduled in 10 minutes, but they can pay immediately via [link].

Return ONLY a JSON object with:
{{
  "action": "SEND_SMS_REMINDER" | "SCHEDULE_AUTO_RETRY" | "ESCALATE_TO_HUMAN",
  "reasoning": "1-2 sentence justification",
  "sms_message": "Friendly message text containing [link]"
}}"""

    # 1. On-Premises Local LLM Inference (Ollama) — Zero Data Leakage
    if provider == "ollama":
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        try:
            with httpx.Client(timeout=18) as client:
                res = client.post(
                    f"{ollama_url}/api/chat",
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": "You are a fintech AI recovery engine. Return valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "format": "json",
                        "stream": False,
                        "options": {"temperature": 0.2}
                    }
                )
                if res.status_code == 200:
                    resp_json = res.json()
                    content = resp_json.get("message", {}).get("content", "{}")
                    decision = json.loads(content)
                    decision["model_used"] = f"ollama/{model_name} (local on-prem)"
                    
                    # Ensure [link] token is present
                    if "[link]" not in decision.get("sms_message", ""):
                        decision["sms_message"] = (decision.get("sms_message", "") + " Pay here: [link]").strip()
                    return decision
        except Exception as e:
            print(f"[*] Local Ollama fallback triggered: {e}")

    # 2. Cloud LLM Inference (Groq)
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key and not groq_api_key.startswith("gsk_test"):
        try:
            client = Groq(api_key=groq_api_key)
            models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
            for model_name in models_to_try:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                        temperature=0.2
                    )
                    decision = json.loads(response.choices[0].message.content)
                    decision["model_used"] = f"{model_name} (Groq Cloud)"
                    if "[link]" not in decision.get("sms_message", ""):
                        decision["sms_message"] = (decision.get("sms_message", "") + " Pay here: [link]").strip()
                    return decision
                except Exception:
                    continue
        except Exception as e:
            print(f"[*] Groq inference notice: {e}")

    # 3. Deterministic Edge Fallback
    r = failure_reason.lower()
    if any(k in r for k in ["bank", "temporary", "timeout", "server", "gateway"]):
        return {
            "action": "SCHEDULE_AUTO_RETRY",
            "reasoning": "Transient network/bank issue detected. Scheduled auto-retry in 10 mins with optional instant pay link.",
            "sms_message": "Hi! We noticed a temporary bank outage during your payment. An automatic retry is scheduled in 10 mins. To pay instantly without waiting, use this link: [link]",
            "model_used": "Deterministic Rule Engine (On-Prem)"
        }
    elif "card" in r:
        return {
            "action": "SEND_SMS_REMINDER",
            "reasoning": "Card expired or invalid. Customer must update payment details.",
            "sms_message": "Hi! Your payment failed because your card expired. Please update details and complete payment here: [link]",
            "model_used": "Deterministic Rule Engine (On-Prem)"
        }
    elif "upi" in r:
        return {
            "action": "SEND_SMS_REMINDER",
            "reasoning": "UPI PIN blocked or limit exceeded. Recommend switching apps.",
            "sms_message": "UPI payment failed. Please retry using another UPI app or card: [link]",
            "model_used": "Deterministic Rule Engine (On-Prem)"
        }
    else:
        return {
            "action": "SEND_SMS_REMINDER",
            "reasoning": "Insufficient funds or account limit. Polite reminder sent with direct payment link.",
            "sms_message": "Payment could not be completed due to account balance. You can retry anytime using this link: [link]",
            "model_used": "Deterministic Rule Engine (On-Prem)"
        }
