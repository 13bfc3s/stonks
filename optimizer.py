import random
from typing import Any, Dict, List, Tuple

from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args

from backtester import Backtester, BacktestResult
from strategies import StrategyTemplate


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
            # Randomly choose parameters from the template's defined param_space
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
        # Build skopt search spaces
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
            # Instantiate and backtest strategy
            script = template.instantiate(params)
            result: BacktestResult = self.backtester.run(script)
            score = getattr(result, self.metric)
            # We minimize objective -> return negative profit
            return -float(score)

        # Run Bayesian optimization
        result = gp_minimize(
            func=objective,
            dimensions=dimensions,
            n_initial_points=n_initial,
            n_calls=n_calls,
            random_state=42
        )

        # Extract best parameters and score
        best_params = {dim.name: val for dim, val in zip(dimensions, result.x)}
        best_score = -result.fun
        return best_params, best_score


# Example usage within optimizer module
if __name__ == '__main__':
    # Placeholder: load strategy templates and data
    from data_manager import load_templates, load_data

    templates = load_templates('/strategies')
    data = load_data('/data')

    backtester = Backtester(data)
    sampler = EnsembleSampler(templates, num_strategies=5)
    variants = sampler.sample()
    print("Sampled Ensemble Variants:")
    for name, script, params in variants:
        print(f"{name}: params={params}")

    # Optimize the first template as a demo
    optimizer = BayesianOptimizer(backtester)
    best_params, best_score = optimizer.optimize(templates[0], n_initial=15, n_calls=60)
    print(f"Best params: {best_params}, Best score: {best_score}")
