# /dashboard_backend/config_routes/fork_score_config_api.py

from fastapi import APIRouter, HTTPException
from pathlib import Path
import yaml
import os

CONFIG_PATH = Path("/home/signal/market7/config/fork_score_config.yaml")

router = APIRouter()

# === Helpers ===
def load_config():
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="fork_score_config.yaml not found")
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(data, f, sort_keys=False)

# === Routes ===

@router.get("/config/fork_score")
def read_fork_score_config():
    return load_config()

@router.post("/config/fork_score")
def update_fork_score_config(patch: dict):
    config = load_config()

    for key, val in patch.items():
        if key in config:
            if isinstance(val, dict) and isinstance(config[key], dict):
                config[key].update(val)
            else:
                config[key] = val
        else:
            raise HTTPException(status_code=400, detail=f"Invalid config key: {key}")

    save_config(config)
    return {"status": "success", "updated": patch}
