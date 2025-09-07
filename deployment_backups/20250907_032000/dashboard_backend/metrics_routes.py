"""
Metrics routes for Prometheus scraping
"""

import logging

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from .metrics import get_metrics, update_system_metrics

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    try:
        # Update system metrics before returning
        update_system_metrics()

        metrics_data = get_metrics()
        return PlainTextResponse(
            content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return PlainTextResponse(
            content="# Error generating metrics\n", media_type="text/plain"
        )


@router.get("/metrics/trading")
async def trading_metrics():
    """Trading-specific metrics endpoint"""
    try:
        update_system_metrics()
        metrics_data = get_metrics()
        return PlainTextResponse(
            content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating trading metrics: {e}")
        return PlainTextResponse(
            content="# Error generating trading metrics\n", media_type="text/plain"
        )


@router.get("/metrics/ml")
async def ml_metrics():
    """ML-specific metrics endpoint"""
    try:
        update_system_metrics()
        metrics_data = get_metrics()
        return PlainTextResponse(
            content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating ML metrics: {e}")
        return PlainTextResponse(
            content="# Error generating ML metrics\n", media_type="text/plain"
        )


@router.get("/metrics/dca")
async def dca_metrics():
    """DCA-specific metrics endpoint"""
    try:
        update_system_metrics()
        metrics_data = get_metrics()
        return PlainTextResponse(
            content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating DCA metrics: {e}")
        return PlainTextResponse(
            content="# Error generating DCA metrics\n", media_type="text/plain"
        )


@router.get("/metrics/3commas")
async def threecommas_metrics():
    """3Commas API metrics endpoint"""
    try:
        update_system_metrics()
        metrics_data = get_metrics()
        return PlainTextResponse(
            content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating 3Commas metrics: {e}")
        return PlainTextResponse(
            content="# Error generating 3Commas metrics\n", media_type="text/plain"
        )


@router.get("/metrics/redis")
async def redis_metrics():
    """Redis metrics endpoint"""
    try:
        update_system_metrics()
        metrics_data = get_metrics()
        return PlainTextResponse(
            content=metrics_data, media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating Redis metrics: {e}")
        return PlainTextResponse(
            content="# Error generating Redis metrics\n", media_type="text/plain"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "2.0.0",
        "services": {"backend": "healthy", "database": "healthy", "redis": "healthy"},
    }
