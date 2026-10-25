import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "sample_data"
SETTINGS_FILE = BASE_DIR / "settings.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default configuration settings
DEFAULT_CONFIG = {
    "gemini_api_key": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", ""),
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    "preferred_llm": "gemini",  # 'gemini' or 'claude'
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "ocr_engine": "paddleocr",
    "enable_offline_fallback": True,
    "top_k_recommendations": 6,
    "top_k_search": 8
}

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(saved)
                # Environment variables take precedence if set and file has empty
                if not config.get("gemini_api_key") and (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
                    config["gemini_api_key"] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if not config.get("anthropic_api_key") and os.getenv("ANTHROPIC_API_KEY"):
                    config["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
                return config
        except Exception as e:
            print(f"Error loading settings: {e}")
    return DEFAULT_CONFIG.copy()

def save_settings(new_settings: dict):
    current = load_settings()
    current.update(new_settings)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return current
