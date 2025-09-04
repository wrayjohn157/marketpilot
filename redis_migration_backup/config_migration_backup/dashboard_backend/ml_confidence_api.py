# /market7/dashboard_backend/ml_confidence_api.py

from fastapi import APIRouter
import redis
import json
from pathlib import Path
from config.config_loader import PATHS

router = APIRouter()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# === Paths ===
CACHE_PATH = PATHS["live_logs"] / "ml_confidence.json"

@router.get("/ml/confidence")
def get_confidence_data():
    try:
        raw = r.get("confidence_list")
        if raw:
            return json.loads(raw)
    except Exception:
        pass

    # Fallback to local file
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH) as f:
                return json.load(f)
        except Exception:
            pass

    return []
