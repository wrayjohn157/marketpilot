#!/usr/bin/env python3
"""
Simulation Integration Routes
Integrates the simulation system with the main dashboard backend
"""

import sys
from pathlib import Path
from fastapi import APIRouter

# Add simulation paths
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "simulation"))

from api.simulation_routes import router as simulation_router

# Create integrated router
router = APIRouter()

# Include simulation routes
router.include_router(simulation_router, prefix="/simulation")

# Additional integration endpoints
@router.get("/simulation/health")
async def simulation_health():
    """Health check for simulation system"""
    return {
        "status": "healthy",
        "system": "simulation",
        "version": "1.0.0"
    }