import httpx
import os
import sys
import base64
import time
import qrcode
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

def pair_live_whatsapp():
    base_url = os.getenv("EVOLUTION_API_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("EVOLUTION_API_KEY", "lifeline-secret-key")
    instance = os.getenv("EVOLUTION_INSTANCE", "lifeline")
    headers = {"apikey": api_key, "Content-Type": "application/json"}

    print("\n" + "="*65)
    print(" 🚑 WHATSAPP LIVE PAIRING ASSISTANT")
    print("="*65)
    
    with httpx.Client(timeout=15) as client:
        # Check if already connected
        try:
            r = client.get(f"{base_url}/instance/connectionState/{instance}", headers=headers)
            if r.status_code == 200 and r.json().get("instance", {}).get("state") == "open":
                print("\n ✅ WhatsApp is ALREADY CONNECTED and ACTIVE on instance 'lifeline'!\n")
                return True
        except Exception:
            pass

        # Reset instance connection state
        try:
            client.delete(f"{base_url}/instance/logout/{instance}", headers=headers)
            time.sleep(1)
        except Exception:
            pass

        print("\n[*] Waiting for fresh WhatsApp QR code from Evolution API...")
        
        for attempt in range(1, 20):
            try:
                # Request fresh QR
                r = client.get(f"{base_url}/instance/connect/{instance}", headers=headers)
                data = r.json()
                raw_code = data.get("code")
                b64 = data.get("base64")
                
                # Check if connected while waiting
                state_r = client.get(f"{base_url}/instance/connectionState/{instance}", headers=headers)
                if state_r.status_code == 200 and state_r.json().get("instance", {}).get("state") == "open":
                    print("\n" + "="*65)
                    print(" 🎉 SUCCESS! WHATSAPP DEVICE PAIRED SUCCESSFULLY!")
                    print(" Your autonomous recovery engine can now send real WhatsApp messages.")
                    print("="*65 + "\n")
                    return True
                
                if b64 or raw_code:
                    # Save image
                    if b64:
                        clean_b64 = b64.split(",")[-1]
                        img_data = base64.b64decode(clean_b64)
                        with open("whatsapp_qr.png", "wb") as f:
                            f.write(img_data)
                    
                    print(f"\n--- [FRESH QR CODE GENERATED: Cycle {attempt}] ---")
                    print("Scan this QR code with WhatsApp -> Linked Devices:\n")
                    
                    # Print ASCII QR code in terminal
                    qr_str = raw_code if raw_code else b64
                    qr = qrcode.QRCode(border=1)
                    qr.add_data(qr_str)
                    qr.make(fit=True)
                    qr.print_ascii(invert=True)
                    
                    print(f"\n📂 Saved fresh image to: {os.path.abspath('whatsapp_qr.png')}")
                    print("⏳ Point camera now (Refreshes automatically every 20s)...")
                    
                time.sleep(12)
            except Exception as e:
                print(f"[*] Connecting... ({e})")
                time.sleep(3)
                
    return False

if __name__ == "__main__":
    pair_live_whatsapp()
