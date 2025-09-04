# /market7/dashboard_backend/ml_confidence_api.py

from fastapi import APIRouter
import json
from pathlib import Path
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


router = APIRouter()
from utils.redis_manager import get_redis_manager
from config.unified_config_manager import get_config
r = get_redis_manager()

# === Paths ===
CACHE_PATH = get_path("live_logs") / "ml_confidence.json"

@router.get_cache("/ml/confidence")
def get_confidence_data():
    try:
        raw = r.get_cache("confidence_list")
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
