import re

def inject_pine(script: str, params: dict) -> str:
    def repl(m):
        name=m.group('name')
        if name in params:
            return re.sub(r"defval=\d+","defval="+str(params[name]),m.group(0))
        return m.group(0)
    return re.sub(r"input\.\w+\(.*?title=['\"](?P<name>[^'\"]+)['\"].*?\)",repl,script,flags=re.DOTALL)
