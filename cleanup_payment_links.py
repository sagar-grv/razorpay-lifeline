from dotenv import load_dotenv
import os
import razorpay

load_dotenv()

client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

res = client.payment_link.all({"count": 100})
links = res.get("payment_links", [])
print(f"Found {len(links)} total links on account.")

cancelled = 0
skipped = 0

for l in links:
    pid = l.get("id")
    status = l.get("status")
    if status in ["created", "issued"]:
        try:
            client.payment_link.cancel(pid)
            print(f"  [CANCELLED] {pid}")
            cancelled += 1
        except Exception as e:
            print(f"  [ERROR] Could not cancel {pid}: {e}")
    else:
        skipped += 1

print(f"\nDone! Cancelled: {cancelled}, Skipped (Paid/Expired/Cancelled): {skipped}")
