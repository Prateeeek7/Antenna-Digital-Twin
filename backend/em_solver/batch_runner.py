"""Batch EM simulation runner with parallel execution."""

import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
import uuid

from backend.em_solver.interface import EMSolverInterface
from backend.core.models.schemas import AntennaParameters, EMSimulationResult
from backend.core.config import settings
from backend.core.exceptions import EMSolverError


class BatchRunner:
    """Run multiple EM simulations in parallel."""
    
    def __init__(
        self,
        solver: EMSolverInterface,
        max_workers: Optional[int] = None,
        use_processes: bool = False
    ):
        """
        Initialize batch runner.
        
        Args:
            solver: EM solver instance
            max_workers: Maximum parallel workers (default: from config)
            use_processes: Use ProcessPoolExecutor instead of ThreadPoolExecutor
        """
        self.solver = solver
        self.max_workers = max_workers or settings.EM_SOLVER_MAX_WORKERS
        self.use_processes = use_processes
        self.executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    
    def run_batch(
        self,
        parameters_list: List[AntennaParameters],
        base_output_dir: Path,
        progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None
    ) -> List[EMSimulationResult]:
        """
        Run batch of simulations.
        
        Args:
            parameters_list: List of antenna parameter sets
            base_output_dir: Base directory for simulation outputs
            progress_callback: Optional callback(completed, total, result_dict)
            
        Returns:
            List of simulation results
        """
        base_output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        completed = 0
        total = len(parameters_list)
        
        def run_single(params: AntennaParameters, index: int) -> Dict[str, Any]:
            """Run single simulation."""
            sim_id = str(uuid.uuid4())
            output_dir = base_output_dir / f"sim_{index:04d}_{sim_id[:8]}"
            
            try:
                result = self.solver.simulate(
                    params,
                    output_dir,
                    timeout=settings.EM_SOLVER_TIMEOUT
                )
                return {
                    "success": True,
                    "result": result,
                    "index": index,
                    "sim_id": sim_id
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "index": index,
                    "sim_id": sim_id
                }
        
        # Run simulations in parallel
        with self.executor_class(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(run_single, params, i)
                for i, params in enumerate(parameters_list)
            ]
            
            for future in futures:
                outcome = future.result()
                completed += 1
                
                if outcome["success"]:
                    results.append(outcome["result"])
                else:
                    # Log error but continue
                    print(f"Simulation {outcome['index']} failed: {outcome['error']}")
                
                if progress_callback:
                    progress_callback(completed, total, outcome)
        
        return results
    
    async def run_batch_async(
        self,
        parameters_list: List[AntennaParameters],
        base_output_dir: Path,
        progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None
    ) -> List[EMSimulationResult]:
        """
        Run batch of simulations asynchronously.
        
        Args:
            parameters_list: List of antenna parameter sets
            base_output_dir: Base directory for simulation outputs
            progress_callback: Optional callback(completed, total, result_dict)
            
        Returns:
            List of simulation results
        """
        base_output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        completed = 0
        total = len(parameters_list)
        
        async def run_single_async(params: AntennaParameters, index: int) -> Dict[str, Any]:
            """Run single simulation asynchronously."""
            loop = asyncio.get_event_loop()
            sim_id = str(uuid.uuid4())
            output_dir = base_output_dir / f"sim_{index:04d}_{sim_id[:8]}"
            
            try:
                # Run solver in thread pool to avoid blocking
                result = await loop.run_in_executor(
                    None,
                    lambda: self.solver.simulate(
                        params,
                        output_dir,
                        timeout=settings.EM_SOLVER_TIMEOUT
                    )
                )
                return {
                    "success": True,
                    "result": result,
                    "index": index,
                    "sim_id": sim_id
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "index": index,
                    "sim_id": sim_id
                }
        
        # Create tasks
        tasks = [
            run_single_async(params, i)
            for i, params in enumerate(parameters_list)
        ]
        
        # Run with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def run_with_semaphore(task):
            async with semaphore:
                return await task
        
        # Execute all tasks
        outcomes = await asyncio.gather(*[run_with_semaphore(task) for task in tasks])
        
        for outcome in outcomes:
            if outcome["success"]:
                results.append(outcome["result"])
            else:
                print(f"Simulation {outcome['index']} failed: {outcome['error']}")
            
            completed += 1
            if progress_callback:
                progress_callback(completed, total, outcome)
        
        return results



















