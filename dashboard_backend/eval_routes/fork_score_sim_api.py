# /dashboard_backend/eval_routes/fork_score_sim_api.py
from fastapi import APIRouter, Request
from market7.data.fork_score_simulator import simulate_fork_score #from data.fork_score_simulator import simulate_fork_score

router = APIRouter()

@router.post("/simulate/fork_score")
async def simulate_fork_score_route(request: Request):
    payload = await request.json()
    symbol = payload.get("symbol")
    interval = payload.get("interval", "1h")
    weights = payload.get("weights", {})
    threshold = payload.get("threshold", 0.85)

    scores = simulate_fork_score(symbol, interval, weights, threshold)
    return {"symbol": symbol, "interval": interval, "results": scores}
