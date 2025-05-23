import os
import re
from typing import Dict, List, Any

from strategies import StrategyTemplate


class TemplateManager:
    """
    Scans a directory of Pine Script (.pine) template files,
    parses input declarations, and builds StrategyTemplate objects.
    """
    INPUT_PATTERN = re.compile(r"input\.(?P<type>int|float|bool|string)\s*\(\s*title\s*=\s*['\"](?P<title>[^'\"]+)['\"]\s*(?:,\s*defval\s*=\s*(?P<defval>[^,\)]+))?(?:,\s*minval\s*=\s*(?P<min>[^,\)]+))?(?:,\s*maxval\s*=\s*(?P<max>[^,\)]+))?(?:,\s*step\s*=\s*(?P<step>[^,\)]+))?\s*\)")

    def __init__(self, templates_dir: str = 'templates'):
        self.templates_dir = templates_dir
        self.templates: List[StrategyTemplate] = []
        self._load_all()

    def _load_all(self):
        if not os.path.isdir(self.templates_dir):
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")

        for fname in os.listdir(self.templates_dir):
            if fname.lower().endswith('.pine'):
                path = os.path.join(self.templates_dir, fname)
                try:
                    tmpl = self._load_one(path)
                    self.templates.append(tmpl)
                except Exception as e:
                    print(f"Warning: failed to load template {fname}: {e}")

    def _load_one(self, filepath: str) -> StrategyTemplate:
        name = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()

        param_space: Dict[str, Dict[str, Any]] = {}
        for match in self.INPUT_PATTERN.finditer(code):
            ptype = match.group('type')
            title = match.group('title')
            defval = match.group('defval')
            minval = match.group('min')
            maxval = match.group('max')
            step = match.group('step')

            # convert values
            def _to_num(val: str):
                try:
                    return int(val)
                except ValueError:
                    return float(val)

            default = None
            if defval is not None:
                default = _to_num(defval.strip())
            bounds = None
            if minval is not None and maxval is not None:
                low = _to_num(minval.strip())
                high = _to_num(maxval.strip())
                bounds = (low, high)

            param_space[title] = {
                'type': ptype,
                'default': default,
                'bounds': bounds,
                'step': _to_num(step.strip()) if step else None
            }

        return StrategyTemplate(
            name=name,
            code_template=code,
            param_space=param_space
        )

    def get_templates(self) -> List[StrategyTemplate]:
        """Returns the loaded StrategyTemplate objects."""
        return self.templates
