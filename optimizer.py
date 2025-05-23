import random
from typing import Any, Dict, List, Tuple
import concurrent.futures
import pandas as pd

from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args

from backtester import Backtester, BacktestResult
from strategies import StrategyTemplate
from data_manager import load_data, load_templates


class EnsembleSampler:
    """
    Samples a set of strategy templates and generates randomized variants for ensemble testing.
    """
    def __init__(self, templates: List[StrategyTemplate], num_strategies: int):
        self.templates = templates
        self.num_strategies = num_strategies

    def sample(self) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Returns a list of tuples: (strategy_name, pine_script_code, params)
        """
        selected = random.sample(self.templates, self.num_strategies)
        variants: List[Tuple[str, str, Dict[str, Any]]] = []
        for tmpl in selected:
            params = {}
            for name, space in tmpl.param_space.items():
                if space['type'] == 'int':
                    params[name] = random.randint(space['bounds'][0], space['bounds'][1])
                elif space['type'] == 'float':
                    low, high = space['bounds']
                    params[name] = random.uniform(low, high)
                elif space['type'] == 'categorical':
                    params[name] = random.choice(space['bounds'])
                else:
                    raise ValueError(f"Unsupported parameter type: {space['type']}")

            script = tmpl.instantiate(params)
            variants.append((tmpl.name, script, params))
        return variants


class BayesianOptimizer:
    """
    Performs Bayesian optimization over a StrategyTemplate's parameters to maximize net profit.
    """
    def __init__(
        self,
        backtester: Backtester,
        metric: str = 'net_profit',
        win_rate_metric: str = 'win_rate'
    ):
        self.backtester = backtester
        self.metric = metric
        self.win_rate_metric = win_rate_metric

    def optimize(
        self,
        template: StrategyTemplate,
        n_initial: int = 10,
        n_calls: int = 50
    ) -> Tuple[Dict[str, Any], float]:
        """
        Runs Bayesian optimization on the given strategy template.

        Returns:
            best_params: dict of parameter name to optimal value
            best_score: achieved metric value
        """
        dimensions = []
        for name, space in template.param_space.items():
            if space['type'] == 'int':
                dimensions.append(Integer(space['bounds'][0], space['bounds'][1], name=name))
            elif space['type'] == 'float':
                dimensions.append(Real(space['bounds'][0], space['bounds'][1], name=name))
            elif space['type'] == 'categorical':
                dimensions.append(Categorical(space['bounds'], name=name))
            else:
                raise ValueError(f"Unsupported parameter type: {space['type']}")

        @use_named_args(dimensions)
        def objective(**params) -> float:
            script = template.instantiate(params)
            result: BacktestResult = self.backtester.run(script)
            score = getattr(result, self.metric)
            return -float(score)

        result = gp_minimize(
            func=objective,
            dimensions=dimensions,
            n_initial_points=n_initial,
            n_calls=n_calls,
            random_state=42
        )

        best_params = {dim.name: val for dim, val in zip(dimensions, result.x)}
        best_score = -result.fun
        return best_params, best_score


def scan_optimize(
    symbols: List[str],
    periods: List[Tuple[str, str]],
    templates_dir: str = 'templates',
    workers: int = 4,
    n_initial: int = 10,
    n_calls: int = 50
) -> pd.DataFrame:
    """
    Runs Bayesian optimization across multiple symbols and periods in parallel.

    Returns a DataFrame of results: symbol, start, end, template, best_params, best_score.
    """
    # Load data and templates
    data = load_data()
    templates = load_templates(templates_dir)

    tasks = []
    for sym in symbols:
        sym_u = sym.upper()
        if sym_u not in data:
            continue
        for start, end in periods:
            bt_data = data[sym_u].loc[start:end]
            for tmpl in templates:
                tasks.append((sym_u, start, end, tmpl))

    def _opt_task(task):
        sym, start, end, tmpl = task
        df = data[sym].loc[start:end]
        bt = Backtester(df)
        optimizer = BayesianOptimizer(bt)
        best_params, best_score = optimizer.optimize(tmpl, n_initial=n_initial, n_calls=n_calls)
        return {
            'symbol': sym,
            'start': start,
            'end': end,
            'template': tmpl.name,
            'best_params': best_params,
            'best_score': best_score
        }

    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for res in executor.map(_opt_task, tasks):
            results.append(res)

    df_res = pd.DataFrame(results)
    return df_res


# Example usage
if __name__ == '__main__':
    # Example symbols and periods
    symbols = ['AAPL', 'MSFT']  # or parse from CLI
    periods = [('2010-01-01', '2015-12-31'), ('2016-01-01', '2020-12-31')]
    df_results = scan_optimize(symbols, periods, workers=4, n_initial=15, n_calls=60)
    df_results.to_csv('opt_results.csv', index=False)
    print("Optimization scan complete, results saved to opt_results.csv")
