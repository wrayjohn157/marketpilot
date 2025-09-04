# sim_dca_strategies.py

from fastapi import APIRouter, HTTPException
from pathlib import Path
import yaml

router = APIRouter()

STRATEGY_DIR = Path("sim/strategies/dca")
DEFAULT_CONFIG_PATH = Path("config/dca_config.yaml_fallback_real")

# Ensure strategy directory exists
STRATEGY_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/sim/dca/strategies")
def list_strategies():
    return [f.stem for f in STRATEGY_DIR.glob("*.yaml")]


@router.get("/sim/dca/strategies/{name}")
def load_strategy(name: str):
    path = STRATEGY_DIR / f"{name}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Strategy not found")
    with open(path) as f:
        return yaml.safe_load(f)


@router.post("/sim/dca/strategies/{name}")
def save_strategy(name: str, config: dict):
    path = STRATEGY_DIR / f"{name}.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)
    return {"status": "saved", "name": name}


@router.delete("/sim/dca/strategies/{name}")
def delete_strategy(name: str):
    path = STRATEGY_DIR / f"{name}.yaml"
    if path.exists():
        path.unlink()
        return {"status": "deleted", "name": name}
    raise HTTPException(status_code=404, detail="Strategy not found")


@router.get("/sim/dca/default")
def get_default_config():
    if not DEFAULT_CONFIG_PATH.exists():
        raise HTTPException(status_code=500, detail="Default config not found")
    with open(DEFAULT_CONFIG_PATH) as f:
        return yaml.safe_load(f)
