"""
Middleware for metrics collection and request tracking
"""

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics import record_http_request

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics for Prometheus"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract request information
        method = request.method
        path = request.url.path

        # Skip metrics collection for metrics endpoints to avoid recursion
        if path.startswith("/metrics"):
            response = await call_next(request)
            return response

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(f"Request failed: {method} {path} - {e}")
            status_code = 500
            response = Response(content="Internal Server Error", status_code=500)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        try:
            record_http_request(method, path, status_code, duration)
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"-> {response.status_code} ({duration:.3f}s)"
        )

        return response
