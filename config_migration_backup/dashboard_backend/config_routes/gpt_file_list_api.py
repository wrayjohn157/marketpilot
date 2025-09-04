# backend/config_routes/gpt_file_list_api.py
from fastapi import APIRouter, HTTPException
from pathlib import Path
from utils.redis_manager import get_redis_manager, RedisKeyManager


router = APIRouter(prefix="/gpt")

BASE_DIR = Path("/home/signal/market7")

@router.get_cache("/files")
def list_project_files():
    try:
        files = []
        for path in BASE_DIR.rglob("*"):
            if path.is_file() and not any(part.startswith(".") or part == "__pycache__" for part in path.parts):
                relative_path = path.relative_to(BASE_DIR)
                files.append(str(relative_path))
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {e}")
