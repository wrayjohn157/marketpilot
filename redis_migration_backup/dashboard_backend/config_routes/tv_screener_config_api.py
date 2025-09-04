# dashboard_backend/config_routes/tv_screener_config_api.py

from fastapi import APIRouter, HTTPException
from pathlib import Path
import yaml
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


router = APIRouter()
CONFIG_PATH = get_path("tv_screener_config")

# === Helpers ===
def load_config():
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="tv_screener_config.yaml not found")
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(data, f, sort_keys=False)

# === Routes ===

@router.get("/tv_screener")
def read_tv_config():
    return load_config()

@router.post("/tv_screener")
def update_tv_config(patch: dict):
    config = load_config()

    for key, val in patch.items():
        if key in config:
            config[key] = val
        else:
            raise HTTPException(status_code=400, detail=f"Invalid config key: {key}")

    save_config(config)
    return {"status": "success", "updated": patch}
