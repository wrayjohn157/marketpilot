#!/usr/bin/env python3
"""
Custom decorators for the dashboard backend
"""

from functools import wraps

from fastapi import APIRouter


def get_cache(router: APIRouter, path: str):
    """
    Decorator to add caching to FastAPI routes
    This is a placeholder implementation - in a real system you'd want
    proper caching with Redis or similar
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Add the route to the router
        router.add_api_route(path, wrapper, methods=["GET"])
        return wrapper

    return decorator


# Monkey patch APIRouter to add get_cache method
def _get_cache(self, path: str):
    return get_cache(self, path)


APIRouter.get_cache = _get_cache
