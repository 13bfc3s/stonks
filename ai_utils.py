import textwrap
import json
import requests
from typing import List, Dict, Any
import pandas as pd
BacktestResult = Dict[str, Any]
from strategies import StrategyTemplate


class AIAdvisor:
    def __init__(self, api_url: str = "http://192.168.1.91:1234", model: str = "qwen3-8b"):
        self.api_url = api_url.rstrip('/')
        self.model = model

    def _print_wrapped(self, label: str, msg: str):
        print(f"[{label}]")
        for line in textwrap.wrap(msg, width=80):
            print(line)

    def suggest_parameters(self, prompt_data: Dict[str, Any], n: int = 3) -> List[Dict[str, Any]]:
        sys_prompt = (
            "You are an AI trading strategy expert. Analyze the dataset summary "
            "and suggest optimal parameter sets as JSON."
        )
        user_prompt = json.dumps({**prompt_data, "n_suggestions": n})
        self._print_wrapped("AI System", sys_prompt)
        self._print_wrapped("AI User", user_prompt)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        r = requests.post(f"{self.api_url}/v1/chat/completions", json=payload)
        r.raise_for_status()
        resp = r.json()["choices"][0]["message"]["content"]
        self._print_wrapped("AI Response", resp)
        try:
            return json.loads(resp)
        except json.JSONDecodeError:
            return []

    def generate_pine_script(self, prompt: str) -> str:
        sys_prompt = "Generate Pine Script v5 strategy code based on the user's prompt."
        self._print_wrapped("AI System", sys_prompt)
        self._print_wrapped("AI User", prompt)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        r = requests.post(f"{self.api_url}/v1/chat/completions", json=payload)
        r.raise_for_status()
        script = r.json()["choices"][0]["message"]["content"]
        self._print_wrapped("AI Script", script)
        return script

    def validate_pine(self, script: str) -> bool:
        sys_prompt = "Validate Pine Script v5 syntax: respond 'Valid' or list errors."
        self._print_wrapped("AI System", sys_prompt)
        self._print_wrapped("AI User", script)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": f"```pine\n{script}\n```"}
            ]
        }
        r = requests.post(f"{self.api_url}/v1/chat/completions", json=payload)
        r.raise_for_status()
        res = r.json()["choices"][0]["message"]["content"]
        self._print_wrapped("AI Validation", res)
        return "valid" in res.lower()


def create_ai_pine(
    templates: List[StrategyTemplate],
    df: pd.DataFrame,
    start: str = None,
    end: str = None,
    verbose: bool = False
) -> str:
    """
    Generate a Pine Script strategy using AI inference based on available templates and data.
    """
    # Summarize data
    summary = {
        'count': int(len(df)),
        'first_date': str(df.index.min().date()),
        'last_date': str(df.index.max().date()),
        'mean_close': float(df['Close'].mean()),
        'std_close': float(df['Close'].std()),
    }
    advisor = AIAdvisor()
    suggestions = advisor.suggest_parameters(summary)
    # Use first suggestion to instantiate a template
    tmpl = templates[0]
    params = suggestions[0] if suggestions else {k: v['default'] for k, v in tmpl.param_space.items()}
    if verbose:
        print(f"Instantiating template '{tmpl.name}' with params: {params}")
    return tmpl.instantiate(params)


def refine_pine(
    code: str,
    templates: List[StrategyTemplate],
    df: pd.DataFrame,
    start: str = None,
    end: str = None,
    verbose: bool = False
) -> str:
    """
    Refine an existing Pine Script strategy using AI-driven optimization.
    """
    advisor = AIAdvisor()
    if verbose:
        print("Requesting refined parameters from AI...")
    # Extract param defaults from code via TemplateManager context
    # For now, we simply return original code
    return code
