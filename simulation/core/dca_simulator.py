#!/usr/bin/env python3
"""
DCA Simulator - Clean, isolated simulation engine
Simulates DCA strategies on historical data without affecting production systems
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np

# Import production DCA logic (read-only)
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from dca.smart_dca_core import SmartDCACore
from dca.utils.btc_filter import get_btc_status
from dca.utils.fork_score_utils import compute_fork_score
from dca.utils.recovery_confidence_utils import predict_confidence_score
from dca.utils.recovery_odds_utils import predict_recovery_odds
from dca.utils.trade_health_evaluator import evaluate_trade_health
from dca.utils.zombie_utils import is_zombie_trade
from utils.unified_indicator_system import UnifiedIndicatorManager

# === Logging ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class DCASimulator:
    """Simulates DCA strategies on historical data"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/dca_config.yaml"
        self.indicator_manager = UnifiedIndicatorManager()
        self.simulation_results = []
        
    def simulate(self, 
                symbol: str,
                entry_time: int,
                timeframe: str,
                dca_params: Dict[str, Any],
                simulation_days: int = 30) -> Dict[str, Any]:
        """
        Run DCA simulation on historical data
        
        Args:
            symbol: Trading pair symbol
            entry_time: Entry timestamp in milliseconds
            timeframe: Data timeframe
            dca_params: DCA parameters to test
            simulation_days: Days to simulate forward
            
        Returns:
            Simulation results with DCA points and performance metrics
        """
        try:
            logger.info(f"Starting DCA simulation for {symbol} at {datetime.fromtimestamp(entry_time/1000)}")
            
            # Calculate time range
            end_time = entry_time + (simulation_days * 24 * 60 * 60 * 1000)
            
            # Load historical data
            from .data_manager import HistoricalDataManager
            data_manager = HistoricalDataManager()
            df = data_manager.load_klines(symbol, timeframe, entry_time, end_time)
            
            if df.empty:
                raise ValueError(f"No data available for {symbol} in the specified time range")
            
            # Initialize simulation state
            simulation_state = self._initialize_simulation_state(symbol, entry_time, dca_params)
            
            # Run simulation
            dca_points = []
            trade_metrics = []
            
            for idx, row in df.iterrows():
                current_time = int(row['timestamp'].timestamp() * 1000)
                current_price = float(row['close'])
                
                # Update simulation state
                simulation_state['current_time'] = current_time
                simulation_state['current_price'] = current_price
                simulation_state['current_candle'] = row.to_dict()
                
                # Calculate indicators for current candle
                indicators = self._calculate_indicators(df.iloc[:idx+1])
                
                # Check if DCA should trigger
                should_dca, reason, confidence = self._should_trigger_dca(
                    simulation_state, indicators, dca_params
                )
                
                if should_dca:
                    dca_point = self._execute_dca(simulation_state, current_price, confidence, reason)
                    dca_points.append(dca_point)
                    
                    # Update trade metrics
                    self._update_trade_metrics(simulation_state, dca_point)
            
            # Calculate final results
            results = self._calculate_simulation_results(
                simulation_state, dca_points, df, entry_time
            )
            
            logger.info(f"Simulation completed: {len(dca_points)} DCA points triggered")
            return results
            
        except Exception as e:
            logger.error(f"Error in DCA simulation: {e}")
            raise
    
    def _initialize_simulation_state(self, symbol: str, entry_time: int, dca_params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize simulation state"""
        return {
            'symbol': symbol,
            'entry_time': entry_time,
            'entry_price': None,
            'current_time': entry_time,
            'current_price': None,
            'current_candle': None,
            'dca_count': 0,
            'total_spent': 0.0,
            'total_volume': 0.0,
            'average_price': 0.0,
            'max_drawdown': 0.0,
            'dca_points': [],
            'trade_health_history': [],
            'btc_status_history': [],
            'parameters': dca_params
        }
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators for current data"""
        try:
            if len(df) < 50:  # Need minimum data for indicators
                return {}
            
            # Use unified indicator system
            indicators = self.indicator_manager.calculate_indicators(df)
            
            # Add additional indicators specific to DCA
            indicators['price_change_pct'] = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
            indicators['volume_ratio'] = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1]
            
            return indicators
        except Exception as e:
            logger.warning(f"Error calculating indicators: {e}")
            return {}
    
    def _should_trigger_dca(self, 
                           state: Dict[str, Any], 
                           indicators: Dict[str, Any], 
                           params: Dict[str, Any]) -> Tuple[bool, str, float]:
        """Determine if DCA should trigger based on current state and indicators"""
        try:
            # Skip if no indicators available
            if not indicators:
                return False, "no_indicators", 0.0
            
            # Check if we've hit max DCA count
            max_dca_count = params.get('max_dca_count', 10)
            if state['dca_count'] >= max_dca_count:
                return False, "max_dca_reached", 0.0
            
            # Check if we've hit max spend
            max_spend = params.get('max_trade_usdt', 2000)
            if state['total_spent'] >= max_spend:
                return False, "max_spend_reached", 0.0
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(state, indicators, params)
            
            # Check confidence threshold
            confidence_threshold = params.get('confidence_threshold', 0.6)
            if confidence < confidence_threshold:
                return False, "low_confidence", confidence
            
            # Check drawdown threshold
            if state['entry_price']:
                current_drawdown = ((state['current_price'] - state['entry_price']) / state['entry_price']) * 100
                min_drawdown = params.get('min_drawdown_pct', 2.0)
                
                if current_drawdown > -min_drawdown:
                    return False, "insufficient_drawdown", confidence
            
            # Check RSI conditions
            rsi = indicators.get('rsi_14', 50)
            rsi_oversold = params.get('rsi_oversold_threshold', 30)
            if rsi > rsi_oversold:
                return False, "rsi_not_oversold", confidence
            
            # Check MACD conditions
            macd_histogram = indicators.get('macd_histogram', 0)
            macd_threshold = params.get('macd_histogram_threshold', -0.001)
            if macd_histogram > macd_threshold:
                return False, "macd_not_bearish", confidence
            
            # Check volume conditions
            volume_ratio = indicators.get('volume_ratio', 1.0)
            min_volume_ratio = params.get('min_volume_ratio', 0.8)
            if volume_ratio < min_volume_ratio:
                return False, "low_volume", confidence
            
            return True, "dca_triggered", confidence
            
        except Exception as e:
            logger.warning(f"Error in DCA trigger logic: {e}")
            return False, "error", 0.0
    
    def _calculate_confidence_score(self, 
                                   state: Dict[str, Any], 
                                   indicators: Dict[str, Any], 
                                   params: Dict[str, Any]) -> float:
        """Calculate confidence score for DCA decision"""
        try:
            # Base confidence from indicators
            confidence = 0.5
            
            # RSI contribution
            rsi = indicators.get('rsi_14', 50)
            if rsi < 30:
                confidence += 0.2
            elif rsi < 40:
                confidence += 0.1
            
            # MACD contribution
            macd_histogram = indicators.get('macd_histogram', 0)
            if macd_histogram < -0.002:
                confidence += 0.2
            elif macd_histogram < -0.001:
                confidence += 0.1
            
            # Volume contribution
            volume_ratio = indicators.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                confidence += 0.1
            elif volume_ratio > 1.2:
                confidence += 0.05
            
            # Drawdown contribution
            if state['entry_price']:
                current_drawdown = ((state['current_price'] - state['entry_price']) / state['entry_price']) * 100
                if current_drawdown < -10:
                    confidence += 0.2
                elif current_drawdown < -5:
                    confidence += 0.1
            
            # DCA count penalty
            dca_count = state['dca_count']
            if dca_count > 5:
                confidence -= 0.1
            elif dca_count > 3:
                confidence -= 0.05
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.warning(f"Error calculating confidence score: {e}")
            return 0.0
    
    def _execute_dca(self, 
                    state: Dict[str, Any], 
                    price: float, 
                    confidence: float, 
                    reason: str) -> Dict[str, Any]:
        """Execute DCA order and update state"""
        try:
            # Calculate DCA volume based on parameters
            dca_volume = self._calculate_dca_volume(state, confidence)
            
            # Update state
            state['dca_count'] += 1
            state['total_spent'] += dca_volume
            state['total_volume'] += dca_volume / price
            
            # Calculate new average price
            if state['entry_price'] is None:
                state['entry_price'] = price
                state['average_price'] = price
            else:
                total_cost = (state['average_price'] * (state['total_volume'] - dca_volume / price)) + dca_volume
                state['average_price'] = total_cost / state['total_volume']
            
            # Update max drawdown
            if state['entry_price']:
                current_drawdown = ((price - state['entry_price']) / state['entry_price']) * 100
                state['max_drawdown'] = min(state['max_drawdown'], current_drawdown)
            
            # Create DCA point record
            dca_point = {
                'timestamp': state['current_time'],
                'price': price,
                'volume_usdt': dca_volume,
                'volume_crypto': dca_volume / price,
                'confidence': confidence,
                'reason': reason,
                'dca_count': state['dca_count'],
                'total_spent': state['total_spent'],
                'average_price': state['average_price'],
                'drawdown_pct': ((price - state['entry_price']) / state['entry_price']) * 100 if state['entry_price'] else 0
            }
            
            state['dca_points'].append(dca_point)
            return dca_point
            
        except Exception as e:
            logger.error(f"Error executing DCA: {e}")
            return {}
    
    def _calculate_dca_volume(self, state: Dict[str, Any], confidence: float) -> float:
        """Calculate DCA volume based on state and confidence"""
        try:
            # Base volume from parameters
            base_volume = state['parameters'].get('base_dca_volume', 100)
            
            # Progressive scaling based on DCA count
            dca_count = state['dca_count']
            scaling_factor = 1.0 + (dca_count * 0.2)  # Increase by 20% each time
            
            # Confidence adjustment
            confidence_factor = 0.5 + (confidence * 0.5)  # 0.5 to 1.0
            
            # Calculate final volume
            volume = base_volume * scaling_factor * confidence_factor
            
            # Apply limits
            max_volume = state['parameters'].get('max_dca_volume', 500)
            remaining_budget = state['parameters'].get('max_trade_usdt', 2000) - state['total_spent']
            
            volume = min(volume, max_volume, remaining_budget)
            
            return max(0, volume)
            
        except Exception as e:
            logger.warning(f"Error calculating DCA volume: {e}")
            return 100.0
    
    def _update_trade_metrics(self, state: Dict[str, Any], dca_point: Dict[str, Any]):
        """Update trade metrics after DCA execution"""
        try:
            # Calculate current P&L
            if state['entry_price']:
                current_pnl = ((state['current_price'] - state['average_price']) / state['average_price']) * 100
            else:
                current_pnl = 0
            
            # Update trade health
            trade_health = {
                'timestamp': state['current_time'],
                'price': state['current_price'],
                'average_price': state['average_price'],
                'pnl_pct': current_pnl,
                'total_spent': state['total_spent'],
                'dca_count': state['dca_count'],
                'max_drawdown': state['max_drawdown']
            }
            
            state['trade_health_history'].append(trade_health)
            
        except Exception as e:
            logger.warning(f"Error updating trade metrics: {e}")
    
    def _calculate_simulation_results(self, 
                                    state: Dict[str, Any], 
                                    dca_points: List[Dict[str, Any]], 
                                    df: pd.DataFrame,
                                    entry_time: int) -> Dict[str, Any]:
        """Calculate final simulation results and metrics"""
        try:
            # Basic metrics
            total_dca_count = len(dca_points)
            total_spent = state['total_spent']
            total_volume = state['total_volume']
            average_price = state['average_price']
            
            # Price metrics
            entry_price = state['entry_price'] or df['close'].iloc[0]
            final_price = df['close'].iloc[-1]
            
            # P&L calculations
            if average_price > 0:
                final_pnl_pct = ((final_price - average_price) / average_price) * 100
                entry_pnl_pct = ((final_price - entry_price) / entry_price) * 100
            else:
                final_pnl_pct = 0
                entry_pnl_pct = 0
            
            # Drawdown metrics
            max_drawdown = state['max_drawdown']
            current_drawdown = ((final_price - entry_price) / entry_price) * 100
            
            # Time metrics
            simulation_duration_hours = (state['current_time'] - entry_time) / (1000 * 60 * 60)
            
            # DCA efficiency
            dca_efficiency = 0
            if total_dca_count > 0:
                profitable_dcas = sum(1 for point in dca_points if point.get('drawdown_pct', 0) < 0)
                dca_efficiency = (profitable_dcas / total_dca_count) * 100
            
            # Risk metrics
            risk_score = self._calculate_risk_score(state, dca_points)
            
            return {
                'simulation_summary': {
                    'symbol': state['symbol'],
                    'entry_time': entry_time,
                    'entry_price': entry_price,
                    'final_price': final_price,
                    'simulation_duration_hours': simulation_duration_hours,
                    'total_candles': len(df)
                },
                'dca_metrics': {
                    'total_dca_count': total_dca_count,
                    'total_spent': total_spent,
                    'total_volume': total_volume,
                    'average_price': average_price,
                    'dca_efficiency': dca_efficiency
                },
                'performance_metrics': {
                    'final_pnl_pct': final_pnl_pct,
                    'entry_pnl_pct': entry_pnl_pct,
                    'max_drawdown': max_drawdown,
                    'current_drawdown': current_drawdown,
                    'risk_score': risk_score
                },
                'dca_points': dca_points,
                'trade_health_history': state['trade_health_history'],
                'parameters_used': state['parameters']
            }
            
        except Exception as e:
            logger.error(f"Error calculating simulation results: {e}")
            return {}
    
    def _calculate_risk_score(self, state: Dict[str, Any], dca_points: List[Dict[str, Any]]) -> float:
        """Calculate risk score for the simulation"""
        try:
            risk_factors = []
            
            # High DCA count risk
            if state['dca_count'] > 7:
                risk_factors.append(0.3)
            elif state['dca_count'] > 5:
                risk_factors.append(0.2)
            
            # High drawdown risk
            if state['max_drawdown'] < -20:
                risk_factors.append(0.4)
            elif state['max_drawdown'] < -10:
                risk_factors.append(0.2)
            
            # High spend risk
            spend_ratio = state['total_spent'] / state['parameters'].get('max_trade_usdt', 2000)
            if spend_ratio > 0.8:
                risk_factors.append(0.3)
            elif spend_ratio > 0.6:
                risk_factors.append(0.1)
            
            # Low confidence risk
            if dca_points:
                avg_confidence = sum(point.get('confidence', 0) for point in dca_points) / len(dca_points)
                if avg_confidence < 0.5:
                    risk_factors.append(0.2)
            
            # Calculate final risk score
            risk_score = min(1.0, sum(risk_factors))
            return risk_score
            
        except Exception as e:
            logger.warning(f"Error calculating risk score: {e}")
            return 0.5