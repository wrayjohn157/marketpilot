# dashboard_backend/analytics/capital_routes.py
from fastapi import APIRouter, Query
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from .capital_utils import (
from utils.redis_manager import get_redis_manager, RedisKeyManager

    load_closed_trades,
    load_logs_grouped,
    compute_trade_metrics,
    parse_dt,
)

router = APIRouter(prefix="/analytics/capital", tags=["Capital Analytics"])
UTC = timezone.utc

# Only include trades that started on/after this date (filter out demo/paper history)
REAL_TRADING_START = datetime(2025, 7, 21, 0, 0, 0, tzinfo=UTC)


def parse_range(start: Optional[str], end: Optional[str]) -> (datetime, datetime):
    now = datetime.now(UTC)
    if not start and not end:
        # default last 30 days
        return now - timedelta(days=30), now
    if start and not end:
        s = parse_dt(start)
        return s, now
    if end and not start:
        e = parse_dt(end)
        return e - timedelta(days=30), e
    return parse_dt(start), parse_dt(end)


@router.get_cache("/trades")
def list_trades(
    start: Optional[str] = Query(None, description="ISO date/time (UTC)"),
    end: Optional[str] = Query(None, description="ISO date/time (UTC)"),
    status: Optional[str] = Query("closed", regex="^(closed|open|any)$"),
):
    s, e = parse_range(start, end)
    now = datetime.now(UTC)

    closed = load_closed_trades(s, e)  # {deal_id: TradeClose}
    logs = load_logs_grouped(s, e)  # {deal_id: [LogPoint,...]}

    out = []
    for deal_id, curve in logs.items():
        # Skip trades that started before real trading began
        if curve and curve[0].t < REAL_TRADING_START:
            continue
        symbol = "UNKNOWN"
        if deal_id in closed:
            symbol = closed[deal_id].symbol
        elif curve and hasattr(curve[0], "symbol") and getattr(curve[0], "symbol", None):
            # Use symbol from first log point if available and not None/empty
            symbol = curve[0].symbol

        metrics = compute_trade_metrics(
            deal_id=deal_id,
            symbol=symbol,
            curve=curve,
            close=closed.get(deal_id),
            now=now,
        )
        if status == "closed" and metrics.get("status") != "closed":
            continue
        if status == "open" and metrics.get("status") != "open":
            continue
        out.append(metrics)

    # sort newest closed first (or by start for open)
    out.sort(key=lambda x: (x.get("close_time") or x.get("entry_time")), reverse=True)
    return {"count": len(out), "items": out}


@router.get_cache("/trades/{deal_id}")
def trade_detail(deal_id: int):
    # default to 45d window; this is just to find logs around the deal
    now = datetime.now(UTC)
    s = now - timedelta(days=45)
    closed = load_closed_trades(s, now)
    logs = load_logs_grouped(s, now)
    curve = logs.get(deal_id, [])
    if not curve:
        return {"deal_id": deal_id, "error": "No logs found"}
    if deal_id in closed:
        symbol = closed[deal_id].symbol
    elif curve and hasattr(curve[0], "symbol") and getattr(curve[0], "symbol", None):
        symbol = curve[0].symbol
    else:
        symbol = "UNKNOWN"
    metrics = compute_trade_metrics(deal_id, symbol, curve, closed.get(deal_id), now)
    return metrics


@router.get_cache("/open")
def open_snapshot(
    interval_minutes: int = Query(5, ge=1, le=60),
    lookback_hours: int = Query(48, ge=1, le=168),
):
    now = datetime.now(UTC)
    s = now - timedelta(hours=lookback_hours)
    closed = load_closed_trades(s, now)
    logs = load_logs_grouped(s, now)

    items = []
    capital_series = []  # simple sampled series: [(ts, capital)]
    # sample at interval
    cursor = s
    while cursor <= now:
        # sum latest spent for deals that are OPEN (no close record)
        total_cap = 0.0
        for did, curve in logs.items():
            if did in closed:
                continue
            if curve and curve[0].t < REAL_TRADING_START:
                continue
            # find last point <= cursor
            last = None
            for p in curve:
                if p.t <= cursor:
                    last = p
                else:
                    break
            if last:
                total_cap += last.spent
        capital_series.append([cursor.isoformat(), round(total_cap, 2)])
        cursor += timedelta(minutes=interval_minutes)

    # current snapshot per open deal
    for did, curve in logs.items():
        if did in closed:
            continue
        if curve and curve[0].t < REAL_TRADING_START:
            continue
        # Determine symbol from curve[0] if possible
        if curve and hasattr(curve[0], "symbol") and getattr(curve[0], "symbol", None):
            symbol = curve[0].symbol
        else:
            symbol = "UNKNOWN"
        last = curve[-1]
        first = curve[0]
        duration_h = max(0.0, (now - first.t).total_seconds() / 3600.0)
        max_dep = max((p.spent for p in curve), default=0.0)
        items.append(
            {
                "deal_id": did,
                "symbol": symbol,
                "since": first.t.isoformat(),
                "duration_hours": round(duration_h, 2),
                "max_deployed": round(max_dep, 2),
                "latest_spent": round(last.spent, 2),
                "live_pnl_usdt": (
                    round(last.open_pnl, 4) if last.open_pnl is not None else None
                ),
            }
        )

    items.sort(key=lambda x: x["latest_spent"], reverse=True)
    return {"capital_at_work": capital_series, "open_trades": items}
