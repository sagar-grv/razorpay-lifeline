import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def send_sms_httpsms(to_number: str, content: str) -> bool:
    """Sends SMS via httpsms Android gateway."""
    api_key = os.getenv("HTTPSMS_API_KEY", "test_key")
    from_number = os.getenv("HTTPSMS_FROM_NUMBER", "+1234567890")
    
    # Mock API call if keys are dummy
    if api_key == "test_key":
        print(f"[MOCK SMS SENT] To: {to_number} | Msg: {content}")
        return True

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
