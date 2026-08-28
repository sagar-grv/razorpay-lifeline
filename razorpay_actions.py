import razorpay
import os
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

def create_razorpay_payment_link(amount_in_paise: int, user_phone: str) -> Optional[Dict[str, str]]:
    """
    Creates a real Razorpay Payment Link or Invoice and returns dict with 'id' and 'short_url'.
    Never returns fake/broken error URLs. Returns None on failure so caller can escalate safely.
    """
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    
    if not key_id or not key_secret or key_id.startswith("rzp_test_dummy"):
        print("[MOCK RAZORPAY] Dummy credentials detected. Link creation skipped.")
        return None

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        
        # Primary Strategy: Standard Razorpay Payment Link
        try:
            payment_link = client.payment_link.create({
                "amount": amount_in_paise,
                "currency": "INR",
                "accept_partial": False,
                "description": "Recovery for your recent transaction",
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
            if payment_link and payment_link.get("short_url"):
                return {
                    "id": payment_link.get("id"),
                    "short_url": payment_link.get("short_url")
                }
        except Exception as pl_err:
            # Secondary Strategy: Razorpay Invoice Link (generates genuine rzp.io checkout URL if payment_link quota reached)
            try:
                inv = client.invoice.create({
                    "type": "invoice",
                    "description": "Autonomous Payment Recovery",
                    "customer": {
                        "name": "Valued Customer",
                        "contact": user_phone,
                        "email": "customer@example.com"
                    },
                    "line_items": [{
                        "name": "Payment Recovery",
                        "amount": amount_in_paise,
                        "currency": "INR",
                        "quantity": 1
                    }],
                    "sms_notify": 0,
                    "email_notify": 0
                })
                if inv and inv.get("short_url"):
                    return {
                        "id": inv.get("id"),
                        "short_url": inv.get("short_url")
                    }
            except Exception as inv_err:
                print(f"[RAZORPAY ERROR] Link & Invoice creation failed: {pl_err} | {inv_err}")
                return None

    except Exception as e:
        print(f"[RAZORPAY CLIENT ERROR] {e}")
        return None

    return None
