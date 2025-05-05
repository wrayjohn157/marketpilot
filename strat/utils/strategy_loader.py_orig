import yaml
from pathlib import Path

def load_strategy_config(name="confidence_safeguard"):
    path = Path(f"./strategies/{name}.yaml")
    if not path.exists():
        raise FileNotFoundError(f"Strategy config not found: {path}")
    
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    return data
