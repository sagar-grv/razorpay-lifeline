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

def check_docker_services():
    print("[1/4] Ensuring PostgreSQL & Evolution API Docker Services are Running...")
    try:
        # Check Docker CLI availability
        dock_check = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if dock_check.returncode != 0:
            print("  ⚠️  Docker Desktop is not running. Please start Docker Desktop to enable PostgreSQL and WhatsApp containers.")
            return

        # 1. PostgreSQL check & auto-start
        res_pg = subprocess.run(["docker", "ps", "-a", "--filter", "name=lifeline_db", "--format", "{{.Status}}"], capture_output=True, text=True)
        if "Up" in res_pg.stdout:
            print("  -> PostgreSQL Container (lifeline_db) is ALIVE on port 5432.")
        elif res_pg.stdout.strip():
            print("  -> Starting existing PostgreSQL Container (lifeline_db)...")
            subprocess.run(["docker", "start", "lifeline_db"], capture_output=True)
            time.sleep(2)
            print("  -> PostgreSQL Container (lifeline_db) started successfully.")
        else:
            print("  -> Creating and starting new PostgreSQL Container (lifeline_db)...")
            subprocess.run([
                "docker", "run", "-d",
                "--name", "lifeline_db",
                "-e", "POSTGRES_PASSWORD=password",
                "-p", "5432:5432",
                "postgres"
            ], capture_output=True)
            time.sleep(3)
            print("  -> PostgreSQL Container (lifeline_db) created and started on port 5432.")
            
        # 2. Evolution API check & auto-start
        if os.getenv("WHATSAPP_ENABLED", "false").lower() == "true":
            res_evo = subprocess.run(["docker", "ps", "-a", "--filter", "name=evolution-api", "--format", "{{.Status}}"], capture_output=True, text=True)
            if "Up" in res_evo.stdout:
                print("  -> Evolution API Container (evolution-api) is ALIVE on port 8080.")
            elif res_evo.stdout.strip():
                print("  -> Starting existing Evolution API Container (evolution-api)...")
                subprocess.run(["docker", "start", "evolution-api"], capture_output=True)
                time.sleep(2)
                print("  -> Evolution API Container (evolution-api) started successfully.")
            else:
                print("  -> Creating and starting new Evolution API Container (evolution-api)...")
                subprocess.run([
                    "docker", "run", "-d",
                    "--name", "evolution-api",
                    "-p", "8080:8080",
                    "-e", "AUTHENTICATION_API_KEY=lifeline-secret-key",
                    "-e", "DATABASE_ENABLED=true",
                    "-e", "DATABASE_PROVIDER=postgresql",
                    "-e", "DATABASE_CONNECTION_URI=postgresql://postgres:password@host.docker.internal:5432/evolution_db",
                    "-e", "CACHE_REDIS_ENABLED=false",
                    "evoapicloud/evolution-api:latest"
                ], capture_output=True)
                time.sleep(4)
                print("  -> Evolution API Container (evolution-api) created and started on port 8080.")
    except Exception as e:
        print(f"  -> Docker check notice: {e}")

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
    raw_domain = os.getenv("NGROK_STATIC_DOMAIN", "").strip()
    clean_domain = raw_domain.replace("https://", "").replace("http://", "").strip("/")
    
    if clean_domain:
        print(f"  -> Using Permanent Static Ngrok Domain: https://{clean_domain}")
        cmd = ["ngrok", "http", f"--domain={clean_domain}", "8000", "--log=stdout"]
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
    check_docker_services()
    
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
