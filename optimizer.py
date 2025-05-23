# optimizer.py
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from typing import Any, Dict, List, Tuple

class Optimizer:
    """
    Runs a parallel, progress-bar-wrapped random search over parameter bounds.
    """

    def __init__(
        self,
        backtester,            # an instance of Backtester
        data,                  # your OHLC DataFrame
        strategy,              # a Strategy subclass instance
        bounds: Dict[str, Tuple[float, float]],  # {param: (min, max)}
        workers: int = None    # number of parallel processes
    ):
        self.bt = backtester
        self.data = data
        self.strat = strategy
        self.bounds = bounds
        self.workers = workers or None  # defaults to os.cpu_count()

    def random_search(
        self,
        samples: int = 1_000_000
    ) -> List[Tuple[Dict[str, float], Dict[str, Any]]]:
        """
        samples parameter sets uniformly within bounds,
        runs backtest in parallel, returns list of (params, metrics).
        """
        # Pre-generate all parameter sets
        param_sets = [
            {k: random.uniform(lo, hi) for k, (lo, hi) in self.bounds.items()}
            for _ in range(samples)
        ]

        results: List[Tuple[Dict[str, float], Dict[str, Any]]] = []
        with ProcessPoolExecutor(max_workers=self.workers) as exec:
            futures = {
                exec.submit(self.bt.run, self.data, self.strat, ps): ps
                for ps in param_sets
            }
            for fut in tqdm(as_completed(futures),
                            total=len(futures),
                            desc="Random search",
                            unit="jobs"):
                ps = futures[fut]
                metrics = fut.result()
                results.append((ps, metrics))

        return results
