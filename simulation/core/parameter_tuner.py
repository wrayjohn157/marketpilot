#!/usr/bin/env python3
"""
Parameter Tuner for DCA Simulation
Optimizes DCA parameters using various algorithms
"""

import json
import logging
from itertools import product
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from .dca_simulator import DCASimulator

# === Logging ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class ParameterTuner:
    """Tunes DCA parameters using various optimization algorithms"""
    
    def __init__(self, simulator: Optional[DCASimulator] = None):
        self.simulator = simulator or DCASimulator()
        self.optimization_results = []
        
    def grid_search(self, 
                   symbol: str,
                   entry_time: int,
                   timeframe: str,
                   parameter_ranges: Dict[str, List[Any]],
                   simulation_days: int = 30,
                   max_combinations: int = 1000) -> List[Dict[str, Any]]:
        """
        Perform grid search optimization
        
        Args:
            symbol: Trading pair symbol
            entry_time: Entry timestamp
            timeframe: Data timeframe
            parameter_ranges: Dictionary of parameter ranges to test
            simulation_days: Days to simulate
            max_combinations: Maximum number of combinations to test
            
        Returns:
            List of results sorted by performance
        """
        try:
            logger.info(f"Starting grid search optimization for {symbol}")
            
            # Generate parameter combinations
            param_names = list(parameter_ranges.keys())
            param_values = list(parameter_ranges.values())
            
            # Limit combinations if too many
            total_combinations = np.prod([len(v) for v in param_values])
            if total_combinations > max_combinations:
                logger.warning(f"Too many combinations ({total_combinations}), limiting to {max_combinations}")
                # Sample combinations randomly
                combinations = self._sample_combinations(param_values, max_combinations)
            else:
                combinations = list(product(*param_values))
            
            logger.info(f"Testing {len(combinations)} parameter combinations")
            
            # Run simulations
            results = []
            for i, combination in enumerate(combinations):
                try:
                    # Create parameter dictionary
                    params = dict(zip(param_names, combination))
                    
                    # Run simulation
                    simulation_result = self.simulator.simulate(
                        symbol=symbol,
                        entry_time=entry_time,
                        timeframe=timeframe,
                        dca_params=params,
                        simulation_days=simulation_days
                    )
                    
                    # Extract performance metrics
                    performance = self._extract_performance_metrics(simulation_result)
                    performance['parameters'] = params
                    performance['combination_index'] = i
                    
                    results.append(performance)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Completed {i + 1}/{len(combinations)} simulations")
                        
                except Exception as e:
                    logger.warning(f"Error in simulation {i}: {e}")
                    continue
            
            # Sort by performance
            results.sort(key=lambda x: x.get('performance_score', 0), reverse=True)
            
            logger.info(f"Grid search completed: {len(results)} successful simulations")
            return results
            
        except Exception as e:
            logger.error(f"Error in grid search: {e}")
            return []
    
    def genetic_algorithm(self, 
                         symbol: str,
                         entry_time: int,
                         timeframe: str,
                         parameter_ranges: Dict[str, Tuple[float, float]],
                         population_size: int = 50,
                         generations: int = 20,
                         mutation_rate: float = 0.1,
                         simulation_days: int = 30) -> List[Dict[str, Any]]:
        """
        Perform genetic algorithm optimization
        
        Args:
            symbol: Trading pair symbol
            entry_time: Entry timestamp
            timeframe: Data timeframe
            parameter_ranges: Dictionary of parameter ranges (min, max)
            population_size: Size of each generation
            generations: Number of generations
            mutation_rate: Rate of mutation
            simulation_days: Days to simulate
            
        Returns:
            List of results sorted by performance
        """
        try:
            logger.info(f"Starting genetic algorithm optimization for {symbol}")
            
            # Initialize population
            population = self._initialize_population(parameter_ranges, population_size)
            
            all_results = []
            
            for generation in range(generations):
                logger.info(f"Generation {generation + 1}/{generations}")
                
                # Evaluate population
                generation_results = []
                for i, individual in enumerate(population):
                    try:
                        # Convert individual to parameters
                        params = self._individual_to_params(individual, parameter_ranges)
                        
                        # Run simulation
                        simulation_result = self.simulator.simulate(
                            symbol=symbol,
                            entry_time=entry_time,
                            timeframe=timeframe,
                            dca_params=params,
                            simulation_days=simulation_days
                        )
                        
                        # Extract performance
                        performance = self._extract_performance_metrics(simulation_result)
                        performance['parameters'] = params
                        performance['generation'] = generation
                        performance['individual'] = individual
                        
                        generation_results.append(performance)
                        
                    except Exception as e:
                        logger.warning(f"Error in generation {generation}, individual {i}: {e}")
                        continue
                
                # Sort by performance
                generation_results.sort(key=lambda x: x.get('performance_score', 0), reverse=True)
                all_results.extend(generation_results)
                
                # Create next generation
                if generation < generations - 1:
                    population = self._create_next_generation(generation_results, mutation_rate)
                
                logger.info(f"Generation {generation + 1} best score: {generation_results[0].get('performance_score', 0):.4f}")
            
            # Sort all results by performance
            all_results.sort(key=lambda x: x.get('performance_score', 0), reverse=True)
            
            logger.info(f"Genetic algorithm completed: {len(all_results)} total simulations")
            return all_results
            
        except Exception as e:
            logger.error(f"Error in genetic algorithm: {e}")
            return []
    
    def sensitivity_analysis(self, 
                           symbol: str,
                           entry_time: int,
                           timeframe: str,
                           base_parameters: Dict[str, Any],
                           sensitivity_ranges: Dict[str, List[Any]],
                           simulation_days: int = 30) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on parameters
        
        Args:
            symbol: Trading pair symbol
            entry_time: Entry timestamp
            timeframe: Data timeframe
            base_parameters: Base parameter set
            sensitivity_ranges: Parameters to vary and their ranges
            simulation_days: Days to simulate
            
        Returns:
            Sensitivity analysis results
        """
        try:
            logger.info(f"Starting sensitivity analysis for {symbol}")
            
            sensitivity_results = {}
            
            for param_name, param_values in sensitivity_ranges.items():
                logger.info(f"Analyzing sensitivity of {param_name}")
                
                param_results = []
                
                for value in param_values:
                    try:
                        # Create parameter set with varied parameter
                        test_params = base_parameters.copy()
                        test_params[param_name] = value
                        
                        # Run simulation
                        simulation_result = self.simulator.simulate(
                            symbol=symbol,
                            entry_time=entry_time,
                            timeframe=timeframe,
                            dca_params=test_params,
                            simulation_days=simulation_days
                        )
                        
                        # Extract performance
                        performance = self._extract_performance_metrics(simulation_result)
                        performance['parameter_value'] = value
                        
                        param_results.append(performance)
                        
                    except Exception as e:
                        logger.warning(f"Error in sensitivity analysis for {param_name}={value}: {e}")
                        continue
                
                # Sort by performance
                param_results.sort(key=lambda x: x.get('performance_score', 0), reverse=True)
                sensitivity_results[param_name] = param_results
                
                logger.info(f"Completed sensitivity analysis for {param_name}: {len(param_results)} tests")
            
            return sensitivity_results
            
        except Exception as e:
            logger.error(f"Error in sensitivity analysis: {e}")
            return {}
    
    def _sample_combinations(self, param_values: List[List[Any]], max_combinations: int) -> List[Tuple]:
        """Sample combinations randomly when there are too many"""
        try:
            # Generate all combinations
            all_combinations = list(product(*param_values))
            
            # Sample randomly
            if len(all_combinations) <= max_combinations:
                return all_combinations
            
            indices = np.random.choice(len(all_combinations), max_combinations, replace=False)
            return [all_combinations[i] for i in indices]
            
        except Exception as e:
            logger.warning(f"Error sampling combinations: {e}")
            return []
    
    def _initialize_population(self, parameter_ranges: Dict[str, Tuple[float, float]], population_size: int) -> List[List[float]]:
        """Initialize population for genetic algorithm"""
        try:
            population = []
            param_names = list(parameter_ranges.keys())
            
            for _ in range(population_size):
                individual = []
                for param_name in param_names:
                    min_val, max_val = parameter_ranges[param_name]
                    # Random value between min and max
                    value = np.random.uniform(min_val, max_val)
                    individual.append(value)
                population.append(individual)
            
            return population
            
        except Exception as e:
            logger.error(f"Error initializing population: {e}")
            return []
    
    def _individual_to_params(self, individual: List[float], parameter_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """Convert individual to parameter dictionary"""
        try:
            params = {}
            param_names = list(parameter_ranges.keys())
            
            for i, param_name in enumerate(param_names):
                value = individual[i]
                # Round to appropriate precision
                if param_name in ['confidence_threshold', 'rsi_oversold_threshold']:
                    value = round(value, 2)
                elif param_name in ['min_drawdown_pct', 'max_drawdown_pct']:
                    value = round(value, 1)
                else:
                    value = round(value, 0)
                
                params[param_name] = value
            
            return params
            
        except Exception as e:
            logger.error(f"Error converting individual to params: {e}")
            return {}
    
    def _create_next_generation(self, generation_results: List[Dict[str, Any]], mutation_rate: float) -> List[List[float]]:
        """Create next generation using selection, crossover, and mutation"""
        try:
            # Select top performers for reproduction
            elite_size = max(1, len(generation_results) // 4)
            elite = generation_results[:elite_size]
            
            new_population = []
            
            # Keep elite individuals
            for individual in elite:
                new_population.append(individual['individual'])
            
            # Generate offspring
            while len(new_population) < len(generation_results):
                # Select parents (tournament selection)
                parent1 = self._tournament_selection(generation_results)
                parent2 = self._tournament_selection(generation_results)
                
                # Create offspring
                offspring = self._crossover(parent1, parent2)
                
                # Apply mutation
                if np.random.random() < mutation_rate:
                    offspring = self._mutate(offspring)
                
                new_population.append(offspring)
            
            return new_population
            
        except Exception as e:
            logger.error(f"Error creating next generation: {e}")
            return []
    
    def _tournament_selection(self, generation_results: List[Dict[str, Any]], tournament_size: int = 3) -> List[float]:
        """Tournament selection for genetic algorithm"""
        try:
            # Randomly select tournament participants
            tournament = np.random.choice(len(generation_results), tournament_size, replace=False)
            tournament_results = [generation_results[i] for i in tournament]
            
            # Select best performer
            best = max(tournament_results, key=lambda x: x.get('performance_score', 0))
            return best['individual']
            
        except Exception as e:
            logger.warning(f"Error in tournament selection: {e}")
            return generation_results[0]['individual']
    
    def _crossover(self, parent1: List[float], parent2: List[float]) -> List[float]:
        """Crossover operation for genetic algorithm"""
        try:
            # Uniform crossover
            offspring = []
            for i in range(len(parent1)):
                if np.random.random() < 0.5:
                    offspring.append(parent1[i])
                else:
                    offspring.append(parent2[i])
            
            return offspring
            
        except Exception as e:
            logger.warning(f"Error in crossover: {e}")
            return parent1
    
    def _mutate(self, individual: List[float]) -> List[float]:
        """Mutation operation for genetic algorithm"""
        try:
            mutated = individual.copy()
            
            # Mutate each gene with small probability
            for i in range(len(mutated)):
                if np.random.random() < 0.1:  # 10% chance to mutate each gene
                    # Add small random change
                    mutation_strength = 0.1
                    change = np.random.normal(0, mutation_strength)
                    mutated[i] += change
            
            return mutated
            
        except Exception as e:
            logger.warning(f"Error in mutation: {e}")
            return individual
    
    def _extract_performance_metrics(self, simulation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance metrics from simulation result"""
        try:
            if not simulation_result:
                return {'performance_score': 0}
            
            dca_metrics = simulation_result.get('dca_metrics', {})
            performance_metrics = simulation_result.get('performance_metrics', {})
            
            # Calculate composite performance score
            final_pnl = performance_metrics.get('final_pnl_pct', 0)
            max_drawdown = abs(performance_metrics.get('max_drawdown', 0))
            dca_efficiency = dca_metrics.get('dca_efficiency', 0)
            risk_score = performance_metrics.get('risk_score', 0.5)
            
            # Weighted performance score
            performance_score = (
                final_pnl * 0.4 +  # 40% weight on final P&L
                dca_efficiency * 0.3 +  # 30% weight on DCA efficiency
                (100 - max_drawdown) * 0.2 +  # 20% weight on drawdown control
                (1 - risk_score) * 100 * 0.1  # 10% weight on risk management
            )
            
            return {
                'performance_score': performance_score,
                'final_pnl_pct': final_pnl,
                'max_drawdown': max_drawdown,
                'dca_efficiency': dca_efficiency,
                'risk_score': risk_score,
                'total_dca_count': dca_metrics.get('total_dca_count', 0),
                'total_spent': dca_metrics.get('total_spent', 0),
                'average_price': dca_metrics.get('average_price', 0)
            }
            
        except Exception as e:
            logger.warning(f"Error extracting performance metrics: {e}")
            return {'performance_score': 0}