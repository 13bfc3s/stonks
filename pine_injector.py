import re
from typing import Dict, Any

def inject_pine_script(script: str, params: Dict[str, Any]) -> str:
    """
    Given a Pine Script v5 strategy as a string and a dict of parameter names → new values,
    replace the default values in input.int(...) and input.float(...) calls with those new values.
    Returns the modified script.
    """
    # Matches input.int(default, "Name"... ) or input.float(default, "Name"... )
    pattern = re.compile(
        r"(input\.(?P<type>int|float)\(\s*)(?P<default>[-\d\.]+)(\s*,\s*['\"](?P<name>[^'\"]+)['\"])",
        flags=re.IGNORECASE
    )

    def repl(match: re.Match) -> str:
        prefix = match.group(1)      # e.g. "input.int("
        val_type = match.group('type')  # "int" or "float"
        name = match.group('name')   # parameter name
        suffix = match.group(4)      # e.g. ", \"Name\""
        if name in params:
            new_val = params[name]
            # Format according to type
            if val_type.lower() == 'int':
                new_default = str(int(round(new_val)))
            else:
                new_default = str(float(new_val))
            return f"{prefix}{new_default}{suffix}"
        # No replacement if param not in dict
        return match.group(0)

    return pattern.sub(repl, script)
