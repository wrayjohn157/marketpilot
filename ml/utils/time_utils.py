from datetime import datetime, timezone, timedelta

def parse_iso(ts: str) -> datetime:
    try:
        # With fractional seconds (e.g., 2025-05-01T20:43:22.594Z)
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    except ValueError:
        # Fallback to second-only precision
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def normalize_trade_date(dt: datetime) -> datetime:
    if not isinstance(dt, datetime):
        raise TypeError(f"normalize_trade_date expects datetime, got {type(dt)}")

    if dt.hour < 3:
        return (dt - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)
