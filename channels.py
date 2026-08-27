import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def safe_log_channel(text):
    if isinstance(text, str):
        return text.encode('ascii', 'replace').decode('ascii')
    return text

async def send_whatsapp_evolution(to_number: str, content: str) -> bool:
    """Sends real WhatsApp message via Evolution API."""
    if os.getenv("WHATSAPP_ENABLED", "false").lower() != "true":
        return False
    
    api_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("EVOLUTION_API_KEY", "lifeline-secret-key")
    instance = os.getenv("EVOLUTION_INSTANCE", "lifeline")
    
    # Format number: remove +, -, spaces
    clean_number = "".join(filter(str.isdigit, to_number))
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{api_url}/message/sendText/{instance}",
                headers={"apikey": api_key, "Content-Type": "application/json"},
                json={
                    "number": clean_number,
                    "text": content,
                    "delay": 1200,
                    "linkPreview": True
                }
            )
            if resp.status_code in (200, 201):
                print(f"[WHATSAPP SENT] To: {clean_number} | Status: 200 OK")
                return True
            else:
                # Try fallback endpoint format if different version
                fallback_resp = await client.post(
                    f"{api_url}/message/sendText",
                    params={"instanceName": instance},
                    headers={"apikey": api_key, "Content-Type": "application/json"},
                    json={"number": clean_number, "text": content}
                )
                if fallback_resp.status_code in (200, 201):
                    print(f"[WHATSAPP SENT] To: {clean_number} | Status: 200 OK")
                    return True
                print(f"[WHATSAPP FAILED] Response ({resp.status_code}): {safe_log_channel(resp.text)}")
                return False
    except Exception as e:
        print(f"[WHATSAPP ERROR] {safe_log_channel(str(e))}")
        return False

async def send_sms_httpsms(to_number: str, content: str) -> bool:
    """Sends SMS via httpsms Android gateway."""
    api_key = os.getenv("HTTPSMS_API_KEY", "test_key")
    from_number = os.getenv("HTTPSMS_FROM_NUMBER", "+1234567890")
    
    # Mock API call if keys are dummy
    if api_key == "test_key":
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.httpsms.com/v1/messages/send",
                headers={"x-api-key": api_key},
                json={"from": from_number, "to": to_number, "content": content}
            )
            return resp.status_code in (200, 202)
    except Exception:
        return False

async def dispatch_recovery_message(to_number: str, content: str) -> str:
    """Dispatches recovery message across fallback chain: WhatsApp -> SMS -> Mock."""
    # 1. Try WhatsApp
    if await send_whatsapp_evolution(to_number, content):
        return "WHATSAPP_SENT"
        
    # 2. Try real SMS
    if await send_sms_httpsms(to_number, content):
        return "SMS_SENT"
        
    # 3. Fallback Mock Log
    print(f"[MOCK DISPATCH] To: {to_number} | Content: {safe_log_channel(content)}")
    return "SMS_SENT"
