import razorpay
import os
from dotenv import load_dotenv

load_dotenv()

def create_razorpay_payment_link(amount_in_paise: int, user_phone: str) -> str:
    """Creates a real Razorpay Payment Link and returns the short URL."""
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    
    # Fallback for dummy keys to prevent crashes during testing
    if not key_id or key_id == "rzp_test_dummy_id":
        print("[MOCK RAZORPAY] Generating fake payment link.")
        return "https://rzp.io/i/mock_payment_link_123"

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
        
        return payment_link['short_url']
    except Exception as e:
        print(f"Razorpay API Error: {e}")
        return "https://rzp.io/i/error_link"
