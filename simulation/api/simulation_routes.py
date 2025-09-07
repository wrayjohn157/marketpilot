#!/usr/bin/env python3

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from core.data_manager import HistoricalDataManager
from core.dca_simulator import DCASimulator
from core.parameter_tuner import ParameterTuner

"""
Simulation API Routes
FastAPI endpoints for DCA simulation functionality
"""

sys.path.append(str(Path(__file__).resolve().parent.parent))

# === Logging ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# === Router ===
router = APIRouter(prefix="/api/simulation", tags=["simulation"])


# === Pydantic Models ===
class SimulationRequest(BaseModel):
    symbol: str
    entry_time: int
    timeframe: str = "1h"
    dca_params: Dict[str, Any]
    simulation_days: int = 30


class OptimizationRequest(BaseModel):
    symbol: str
    entry_time: int
    timeframe: str = "1h"
    parameter_ranges: Dict[str, List[Any]]
    optimization_type: str = "grid_search"  # grid_search, genetic_algorithm
    simulation_days: int = 30
    max_combinations: int = 1000


class SensitivityRequest(BaseModel):
    symbol: str
    entry_time: int
    timeframe: str = "1h"
    base_parameters: Dict[str, Any]
    sensitivity_ranges: Dict[str, List[Any]]
    simulation_days: int = 30


class DataRequest(BaseModel):
    symbol: str
    timeframe: str
    start_time: int
    end_time: int


# === Initialize Services ===
simulator = DCASimulator()
tuner = ParameterTuner(simulator)
data_manager = HistoricalDataManager()

# === Simulation Endpoints ===


@router.post("/simulate")
async def run_simulation(request: SimulationRequest) -> Dict[str, Any]:
    """Run a single DCA simulation"""
    try:
        logger.info(
            f"Running simulation for {request.symbol} at {datetime.fromtimestamp(request.entry_time/1000)}"
        )

        result = simulator.simulate(
            symbol=request.symbol,
            entry_time=request.entry_time,
            timeframe=request.timeframe,
            dca_params=request.dca_params,
            simulation_days=request.simulation_days,
        )

        if not result:
            raise HTTPException(status_code=500, detail="Simulation failed")

        return {
            "success": True,
            "result": result,
            "metadata": {
                "symbol": request.symbol,
                "entry_time": request.entry_time,
                "timeframe": request.timeframe,
                "simulation_days": request.simulation_days,
                "parameters": request.dca_params,
            },
        }

    except Exception as e:
        logger.error(f"Error in simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def run_optimization(request: OptimizationRequest) -> Dict[str, Any]:
    """Run parameter optimization"""
    try:
        logger.info(
            f"Running {request.optimization_type} optimization for {request.symbol}"
        )

        if request.optimization_type == "grid_search":
            results = tuner.grid_search(
                symbol=request.symbol,
                entry_time=request.entry_time,
                timeframe=request.timeframe,
                parameter_ranges=request.parameter_ranges,
                simulation_days=request.simulation_days,
                max_combinations=request.max_combinations,
            )
        elif request.optimization_type == "genetic_algorithm":
            # Convert parameter ranges to (min, max) tuples for GA
            ga_ranges = {}
            for param, values in request.parameter_ranges.items():
                if isinstance(values[0], (int, float)):
                    ga_ranges[param] = (min(values), max(values))
                else:
                    # Skip non-numeric parameters for GA
                    continue

            results = tuner.genetic_algorithm(
                symbol=request.symbol,
                entry_time=request.entry_time,
                timeframe=request.timeframe,
                parameter_ranges=ga_ranges,
                simulation_days=request.simulation_days,
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid optimization type")

        return {
            "success": True,
            "results": results,
            "best_result": results[0] if results else None,
            "metadata": {
                "symbol": request.symbol,
                "entry_time": request.entry_time,
                "timeframe": request.timeframe,
                "optimization_type": request.optimization_type,
                "total_tests": len(results),
            },
        }

    except Exception as e:
        logger.error(f"Error in optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sensitivity")
async def run_sensitivity_analysis(request: SensitivityRequest) -> Dict[str, Any]:
    """Run sensitivity analysis"""
    try:
        logger.info(f"Running sensitivity analysis for {request.symbol}")

        results = tuner.sensitivity_analysis(
            symbol=request.symbol,
            entry_time=request.entry_time,
            timeframe=request.timeframe,
            base_parameters=request.base_parameters,
            sensitivity_ranges=request.sensitivity_ranges,
            simulation_days=request.simulation_days,
        )

        return {
            "success": True,
            "results": results,
            "metadata": {
                "symbol": request.symbol,
                "entry_time": request.entry_time,
                "timeframe": request.timeframe,
                "parameters_analyzed": list(results.keys()),
            },
        }

    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Data Endpoints ===


@router.post("/data/load")
async def load_historical_data(request: DataRequest) -> Dict[str, Any]:
    """Load historical data for simulation"""
    try:
        logger.info(f"Loading historical data for {request.symbol} {request.timeframe}")

        df = data_manager.load_klines(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_time=request.start_time,
            end_time=request.end_time,
        )

        if df.empty:
            raise HTTPException(
                status_code=404, detail="No data available for the specified parameters"
            )

        # Convert DataFrame to JSON-serializable format
        data = {
            "candles": df.to_dict("records"),
            "summary": {
                "total_candles": len(df),
                "start_time": df["timestamp"].min().isoformat(),
                "end_time": df["timestamp"].max().isoformat(),
                "price_range": {"min": df["low"].min(), "max": df["high"].max()},
            },
        }

        return {"success": True, "data": data}

    except Exception as e:
        logger.error(f"Error loading historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/symbols")
async def get_available_symbols() -> Dict[str, Any]:
    """Get list of available trading symbols"""
    try:
        symbols = data_manager.get_available_symbols()
        return {"success": True, "symbols": symbols, "total": len(symbols)}
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/timeframes")
async def get_available_timeframes() -> Dict[str, Any]:
    """Get list of available timeframes"""
    try:
        timeframes = data_manager.get_available_timeframes()
        return {"success": True, "timeframes": timeframes}
    except Exception as e:
        logger.error(f"Error getting available timeframes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/validate")
async def validate_data_quality(request: DataRequest) -> Dict[str, Any]:
    """Validate data quality for simulation"""
    try:
        logger.info(f"Validating data quality for {request.symbol} {request.timeframe}")

        df = data_manager.load_klines(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start_time=request.start_time,
            end_time=request.end_time,
        )

        quality_report = data_manager.validate_data_quality(df)

        return {"success": True, "quality_report": quality_report}

    except Exception as e:
        logger.error(f"Error validating data quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Utility Endpoints ===


@router.get("/status")
async def get_simulation_status() -> Dict[str, Any]:
    """Get simulation system status"""
    try:
        return {
            "success": True,
            "status": "operational",
            "services": {
                "simulator": "ready",
                "tuner": "ready",
                "data_manager": "ready",
            },
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parameters/default")
async def get_default_parameters() -> Dict[str, Any]:
    """Get default DCA parameters for simulation"""
    try:
        default_params = {
            "confidence_threshold": 0.6,
            "min_drawdown_pct": 2.0,
            "rsi_oversold_threshold": 30,
            "macd_histogram_threshold": -0.001,
            "min_volume_ratio": 0.8,
            "base_dca_volume": 100,
            "max_dca_volume": 500,
            "max_dca_count": 10,
            "max_trade_usdt": 2000,
        }

        return {"success": True, "default_parameters": default_params}
    except Exception as e:
        logger.error(f"Error getting default parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parameters/ranges")
async def get_parameter_ranges() -> Dict[str, Any]:
    """Get recommended parameter ranges for optimization"""
    try:
        parameter_ranges = {
            "confidence_threshold": [0.4, 0.5, 0.6, 0.7, 0.8],
            "min_drawdown_pct": [1.0, 2.0, 3.0, 5.0, 7.0],
            "rsi_oversold_threshold": [20, 25, 30, 35, 40],
            "macd_histogram_threshold": [-0.005, -0.003, -0.001, -0.0005],
            "min_volume_ratio": [0.5, 0.7, 0.8, 1.0, 1.2],
            "base_dca_volume": [50, 100, 150, 200, 250],
            "max_dca_volume": [200, 300, 500, 750, 1000],
            "max_dca_count": [5, 7, 10, 12, 15],
            "max_trade_usdt": [1000, 1500, 2000, 3000, 5000],
        }

        return {"success": True, "parameter_ranges": parameter_ranges}
    except Exception as e:
        logger.error(f"Error getting parameter ranges: {e}")
        raise HTTPException(status_code=500, detail=str(e))
