import textwrap
import json
import requests

class AIAdvisor:
    def __init__(self, api_url: str, model: str):
        self.api_url = api_url.rstrip('/')
        self.model = model

    def _print_wrapped(self, label: str, msg: str):
        print(f"[{label}]")
        for line in textwrap.wrap(msg, width=80): print(line)

    def suggest_parameters(self, prompt_data: dict, n: int=3) -> list:
        sys = ("You are an AI trading strategy expert. Analyze the dataset summary "
               "and suggest optimal parameter sets as JSON.")
        user = json.dumps({**prompt_data, "n_suggestions": n})
        self._print_wrapped("AI System", sys)
        self._print_wrapped("AI User", user)
        payload = {"model": self.model,
                   "messages": [{"role":"system","content":sys},
                                {"role":"user","content":user}]}
        r = requests.post(f"{self.api_url}/v1/chat/completions", json=payload)
        r.raise_for_status()
        resp = r.json()["choices"][0]["message"]["content"]
        self._print_wrapped("AI Response", resp)
        try: return json.loads(resp)
        except: return []

    def generate_pine_script(self, prompt: str) -> str:
        sys = "Generate Pine Script v5 strategy code..."
        self._print_wrapped("AI System", sys)
        self._print_wrapped("AI User", prompt)
        payload = {"model":self.model,
                   "messages":[{"role":"system","content":sys},
                               {"role":"user","content":prompt}]}
        r = requests.post(f"{self.api_url}/v1/chat/completions", json=payload)
        r.raise_for_status()
        script = r.json()["choices"][0]["message"]["content"]
        self._print_wrapped("AI Script", script)
        return script

    def validate_pine(self, script: str) -> bool:
        sys = "Validate Pine Script v5 syntax: respond 'Valid' or list errors."
        self._print_wrapped("AI System", sys)
        self._print_wrapped("AI User", script)
        payload = {"model":self.model,
                   "messages":[{"role":"system","content":sys},
                               {"role":"user","content":f"```pine\n{script}\n```"}]}
        r = requests.post(f"{self.api_url}/v1/chat/completions", json=payload)
        r.raise_for_status()
        res = r.json()["choices"][0]["message"]["content"]
        self._print_wrapped("AI Validation", res)
        return "valid" in res.lower()
