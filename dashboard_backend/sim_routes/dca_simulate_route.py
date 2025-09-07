import sys
from pathlib import Path

import simulate_dca_overlay
from fastapi import APIRouter
from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "sim" / "sandbox"))
router = APIRouter()


class DcaSimRequest(BaseModel):
    symbol: str
    entry_time: int
    tf: str = "1h"


@router.post("/dca/simulate")
def simulate_dca(request: DcaSimRequest):
    results = simulate_dca_overlay.run_dca_simulation(
        request.symbol, request.entry_time, request.tf
    )
    return {"result": results}
