# /dashboard_backend/eval_routes/dca_eval_api.py

from fastapi import APIRouter
from utils.log_reader import load_latest_dca_logs
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dca.utils.entry_utils import get_live_3c_trades

router = APIRouter()

@router.get("/dca-evals")
def get_dca_evaluations():
    """
    Returns only active DCA evaluations (based on live deal_ids).
    """
    today = datetime.now().strftime("%Y-%m-%d")
    evaluations = load_latest_dca_logs(today)
    live_deals = {trade["id"] for trade in get_live_3c_trades()}
    filtered = [e for e in evaluations if e.get("deal_id") in live_deals]
    return {"evaluations": filtered}
