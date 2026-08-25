import requests, hmac, hashlib, json, random, time

secret = b'whsec_test_secret_12345'
reasons = ["bank_server_down", "insufficient_funds", "card_expired", "upi_pin_blocked"]

print("Firing 50 simulated webhooks...")
for i in range(50):
    payment_id = f"pay_BATCH_{i:03d}"
    reason = random.choice(reasons)
    amount = random.randint(10000, 500000) 
    
    payload = json.dumps({
        'payload': {'payment': {'entity': {
            'id': payment_id, 
            'amount': amount, 
            'error_description': reason,
            'customer_id': f'user_{random.randint(1, 100)}'
        }}}
    }).encode()
    
    sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    headers = {'Content-Type': 'application/json', 'X-Razorpay-Signature': sig}
    
    requests.post('http://127.0.0.1:8000/webhook/razorpay', data=payload, headers=headers)
    time.sleep(0.1) 
    
print("Batch of 50 test payments sent! Check your dashboard.")
