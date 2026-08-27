import httpx
import os
import sys
import base64
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

def connect_whatsapp():
    base_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("EVOLUTION_API_KEY", "lifeline-secret-key")
    instance = os.getenv("EVOLUTION_INSTANCE", "lifeline")
    headers = {"apikey": api_key, "Content-Type": "application/json"}

    print(f"[*] Connecting to Evolution API at {base_url}...")
    
    with httpx.Client(timeout=20) as client:
        # 1. Fetch QR Code
        print(f"[*] Requesting pairing QR code for instance '{instance}'...")
        try:
            r = client.get(f"{base_url}/instance/connect/{instance}", headers=headers)
            data = r.json()
            b64 = data.get("base64")
            
            if b64:
                clean_b64 = b64.split(",")[-1]
                img_data = base64.b64decode(clean_b64)
                qr_path = os.path.abspath("whatsapp_qr.png")
                with open(qr_path, "wb") as f:
                    f.write(img_data)
                print("\n" + "="*65)
                print(" [SUCCESS] Pairing QR Code saved to 'whatsapp_qr.png'")
                print(f" File Path: {qr_path}")
                print(" Instructions:")
                print(" 1. Open WhatsApp on your spare phone")
                print(" 2. Tap Settings -> Linked Devices -> Link a Device")
                print(" 3. Point camera at 'whatsapp_qr.png'")
                print("="*65 + "\n")
                return True
            else:
                print(f"[*] Response status: {r.status_code}, data: {data}")
        except Exception as e:
            print(f"[-] Error fetching QR code: {e}")

    return False

if __name__ == "__main__":
    connect_whatsapp()
