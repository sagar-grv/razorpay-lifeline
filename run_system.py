import subprocess
import os
import sys
import time
import json
import urllib.request
import threading
from dotenv import load_dotenv

load_dotenv()

def print_banner():
    banner = r"""
  ========================================================================
   🚑  RAZORPAY LIFELINE v2.0 — AUTONOMOUS AI PAYMENT RECOVERY SUITE
  ========================================================================
   * Engine: FastAPI + PostgreSQL + Groq (Llama 3 / GPT-OSS)
   * Handlers: Real Razorpay Payment Links API + httpSMS Gateway
   * Compliance: Deterministic Opt-Out Stopping Rules
   * Frontend: Animated React & Tailwind Dashboard + Live AI Copilot
  ========================================================================
    """
    print(banner)

def check_postgres_docker():
    print("[1/4] Checking PostgreSQL Docker Container (lifeline_db)...")
    try:
        res = subprocess.run(["docker", "ps", "-a", "--filter", "name=lifeline_db", "--format", "{{.Status}}"], capture_output=True, text=True)
        if "Up" in res.stdout:
            print("  -> PostgreSQL Container is ALIVE and RUNNING on port 5432.")
        else:
            print("  -> Starting PostgreSQL Container (lifeline_db)...")
            subprocess.run(["docker", "start", "lifeline_db"], capture_output=True)
            time.sleep(2)
            print("  -> PostgreSQL Container started.")
    except Exception as e:
        print(f"  -> Docker check warning: {e}. Ensure PostgreSQL is accessible on localhost:5432.")

def start_backend():
    print("[2/4] Starting FastAPI Uvicorn Server on http://localhost:8000...")
    venv_python = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable
    
    cmd = [venv_python, "-m", "uvicorn", "main:app", "--port", "8000", "--reload"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    
    def stream_uvicorn_logs():
        for line in proc.stdout:
            sys.stdout.write(f"  [BACKEND] {line}")
            sys.stdout.flush()
            
    threading.Thread(target=stream_uvicorn_logs, daemon=True).start()
    time.sleep(3)
    return proc

def start_ngrok():
    print("[3/4] Starting Ngrok Public Tunnel...")
    static_domain = os.getenv("NGROK_STATIC_DOMAIN", "").strip()
    
    if static_domain:
        print(f"  -> Using Permanent Static Ngrok Domain: https://{static_domain}")
        cmd = ["ngrok", "http", f"--domain={static_domain}", "8000", "--log=stdout"]
    else:
        print("  -> Using Dynamic Ngrok Tunnel (Add NGROK_STATIC_DOMAIN to .env for a permanent URL)")
        cmd = ["ngrok", "http", "8000", "--log=stdout"]
        
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    time.sleep(3)
    
    # Query tunnel URL
    public_url = None
    for _ in range(10):
        try:
            data = json.loads(urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2).read())
            tunnels = data.get("tunnels", [])
            if tunnels:
                public_url = tunnels[0]["public_url"]
                break
        except Exception:
            pass
        time.sleep(1)
        
    if public_url:
        print(f"\n  ================================================================")
        print(f"  🔗 LIVE RAZORPAY WEBHOOK URL:")
        print(f"     {public_url}/webhook/razorpay")
        print(f"  * Secret: whsec_test_secret_12345")
        print(f"  * Events: payment.failed, payment_link.paid")
        print(f"  ================================================================\n")
    else:
        print("  -> Ngrok tunnel initiated. View active endpoint at http://127.0.0.1:4040")
        
    return proc

def start_frontend():
    print("[4/4] Launching React Development Server on http://localhost:5173...")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    cmd = ["npm.cmd", "run", "dev"] if sys.platform == "win32" else ["npm", "run", "dev"]
    proc = subprocess.Popen(cmd, cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    
    def stream_vite_logs():
        for line in proc.stdout:
            if "ready in" in line or "Local:" in line:
                print(f"  [FRONTEND] {line.strip()}")
                
    threading.Thread(target=stream_vite_logs, daemon=True).start()
    time.sleep(2)
    return proc

def main():
    print_banner()
    check_postgres_docker()
    
    backend_proc = start_backend()
    ngrok_proc = start_ngrok()
    frontend_proc = start_frontend()
    
    print("\n" + "="*70)
    print(" 🚀 RAZORPAY LIFELINE SYSTEM IS LIVE!")
    print(" -> React Animated Dashboard:  http://localhost:5173")
    print(" -> Production Static Bundle:  http://localhost:8000")
    print(" -> Live Log Stream:           http://localhost:8000/api/logs/stream")
    print(" -> API Swagger Documentation: http://localhost:8000/docs")
    print("="*70)
    print(" Press Ctrl+C to terminate all services safely.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all services...")
        backend_proc.terminate()
        ngrok_proc.terminate()
        frontend_proc.terminate()
        print("All processes closed cleanly.")

if __name__ == "__main__":
    main()
