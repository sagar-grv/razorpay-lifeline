import razorpay
import os
import time
from dotenv import load_dotenv

load_dotenv()

def create_razorpay_payment_link(amount_in_paise: int, user_phone: str) -> dict | None:
    """Creates a real Razorpay Payment Link and returns dict with short_url & plink_id, or None on failure."""
    if os.getenv("RAZORPAY_DEMO_MODE", "false").lower() == "true":
        print("[DEMO MODE] Skipping Razorpay Payment Link creation - returning dummy link")
        demo_id = f"plink_DEMO_{int(time.time()*1000)%10000000}"
        return {
            "id": demo_id,
            "plink_id": demo_id,
            "short_url": "https://razorpay.com/demo"
        }

    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    
    # Fallback for dummy keys in offline local dev
    if not key_id or key_id == "rzp_test_dummy_id":
        print("[MOCK RAZORPAY] Generating offline test payment link.")
        return {
            "short_url": "https://rzp.io/rzp/mock_demo_link",
            "plink_id": "plink_mock_demo_123"
        }

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        
        # We disable Razorpay's native SMS/Email notifications because OUR AI handles the messaging
        payment_link = client.payment_link.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": "Recovery for your recent failed transaction",
            "customer": {
                "name": "Valued Customer",
                "contact": user_phone,
                "email": "customer@example.com"
            },
            "notify": {
                "sms": False,
                "email": False
            },
            "reminder_enable": False
        })
        
        return {
            "short_url": payment_link.get("short_url"),
            "plink_id": payment_link.get("id")
        }
    except Exception as e:
        # Log clean error without exposing secrets
        err_msg = str(e)
        print(f"[RAZORPAY API NOTICE] Link generation error: {err_msg}")
        return None
