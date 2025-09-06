"""
Scan Review API endpoints
"""
from fastapi import APIRouter
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter()

@router.get("/api/scan/results")
def get_scan_results() -> Dict[str, Any]:
    """Get scan review results"""
    # Mock scan results for now
    scan_results = {
        "scans": [
            {
                "id": 1,
                "symbol": "BTC",
                "price": 110880.0,
                "score": 0.75,
                "volume": 1250000.0,
                "change_24h": 2.5,
                "indicators": {
                    "rsi": 65.2,
                    "macd": 0.0012,
                    "adx": 45.8
                },
                "notes": "Strong bullish momentum",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "id": 2,
                "symbol": "ETH",
                "price": 3450.0,
                "score": 0.68,
                "volume": 890000.0,
                "change_24h": 1.8,
                "indicators": {
                    "rsi": 58.4,
                    "macd": 0.0008,
                    "adx": 42.1
                },
                "notes": "Moderate bullish signal",
                "timestamp": datetime.utcnow().isoformat()
            }
        ],
        "stats": {
            "total_scans": 2,
            "avg_score": 0.715,
            "success_rate": 0.85,
            "last_updated": datetime.utcnow().isoformat()
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return scan_results

@router.get("/api/scan/stats")
def get_scan_stats() -> Dict[str, Any]:
    """Get scan statistics"""
    return {
        "total_scans": 2,
        "avg_score": 0.715,
        "success_rate": 0.85,
        "last_updated": datetime.utcnow().isoformat()
    }
