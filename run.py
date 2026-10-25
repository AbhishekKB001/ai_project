import os
import sys
import socket
import webbrowser
import time
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root and parent to path so it can run standalone or as a package
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR.parent))

# Ensure OneDrive and Pydantic don't conflict
os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"

def find_available_port(start_port=8000):
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
            port += 1
    return start_port

def main():
    import uvicorn
    env_port = os.environ.get("PORT")
    port = int(env_port) if env_port else find_available_port(8000)
    host = "0.0.0.0" if env_port else "127.0.0.1"
    url = f"http://127.0.0.1:{port}"

    print("=" * 70)
    print("   AI-POWERED SMART NOTICE MANAGEMENT & RECOMMENDATION SYSTEM   ")
    print("=" * 70)
    print(f"[*] Starting Server on {host}:{port}")
    print("[-] Integrated AI Tools:")
    print("    * PaddleOCR: Scanned circular text & layout detection")
    print("    * Sentence Transformers: 384-dimensional dense semantic embeddings")
    print("    * FAISS: Sub-millisecond vector similarity search")
    print("    * Google Gemini: Live executive summarization & NoticeBot Q&A")
    print("    * Anthropic Claude: Comparative drafting & deep circular reasoning")
    print("=" * 70)
    print(f"[>] Access Website at: {url}")
    print("=" * 70)

    # Automatically open browser in background
    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Determine uvicorn import string based on execution context
    try:
        import backend.app
        app_module = "backend.app:app"
    except ImportError:
        app_module = "smart_notice_system.backend.app:app"

    # Run Uvicorn server
    uvicorn.run(app_module, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
