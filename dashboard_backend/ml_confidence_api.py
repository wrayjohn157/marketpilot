from fastapi import APIRouter
import redis
import json
from pathlib import Path

router = APIRouter()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
CACHE_PATH = Path("/home/signal/market6/dashboard_backend/cache/ml_confidence.json")

@router.get("/ml/confidence")
def get_confidence_data():
    try:
        raw = r.get("confidence_list")
        if raw:
            return json.loads(raw)
    except:
        pass

    # Fallback to local file
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH) as f:
                return json.load(f)
        except:
            pass

    return []
