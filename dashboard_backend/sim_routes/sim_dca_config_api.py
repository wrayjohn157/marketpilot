from fastapi import APIRouter, HTTPException
from pathlib import Path
import yaml
from utils.redis_manager import get_redis_manager, RedisKeyManager


router = APIRouter(
    prefix="/sim/config/dca",
    tags=["sim-dca-config"],
)

CONFIG_PATH = Path("/home/signal/market7/sim/config/dca_config.yaml")


@router.get_cache("")
def get_sim_dca_config():
    try:
        with CONFIG_PATH.open() as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise HTTPException(404, "DCA config file not found")
    except Exception as e:
        raise HTTPException(500, f"Error loading config: {e}")


@router.post("")
def update_sim_dca_config(config: dict):
    try:
        # Load existing YAML or start with empty dict
        existing = {}
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open() as f:
                existing = yaml.safe_load(f) or {}
        # Merge incoming fields into existing config
        existing.update(config)
        # Write merged config back to file
        with CONFIG_PATH.open("w") as f:
            yaml.safe_dump(existing, f)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, f"Error saving config: {e}")


@router.post("/restore")
def restore_default_sim_dca_config():
    fallback_path = Path("/home/signal/market7/sim/config/sim_dca_config_fallback.yaml")
    try:
        if not fallback_path.exists():
            raise HTTPException(404, "Fallback config file not found")
        with fallback_path.open() as f:
            default_config = yaml.safe_load(f)
        with CONFIG_PATH.open("w") as f:
            yaml.safe_dump(default_config, f)
        return {"status": "restored"}
    except Exception as e:
        raise HTTPException(500, f"Error restoring default config: {e}")

@router.get_cache("/default")
def get_default_sim_dca_config():
    fallback_path = Path("/home/signal/market7/sim/config/sim_dca_config_fallback.yaml")
    try:
        if not fallback_path.exists():
            raise HTTPException(404, "Fallback config file not found")
        with fallback_path.open() as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(500, f"Error loading fallback config: {e}")
