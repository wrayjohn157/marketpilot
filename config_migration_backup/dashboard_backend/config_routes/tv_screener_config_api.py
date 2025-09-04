# dashboard_backend/config_routes/tv_screener_config_api.py

from config.config_loader import PATHS
from fastapi import APIRouter, HTTPException
from pathlib import Path
import yaml

router = APIRouter()
CONFIG_PATH = PATHS["tv_screener_config"]

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
