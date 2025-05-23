#!/usr/bin/env python3
import sys

from ai_utils      import AIAdvisor
from data_manager  import DataManager
from strategies    import MACDStrategy, RSIStrategy
from backtester    import Backtester
from optimizer     import Optimizer
from pine_injector import inject_pine_script

def create_workflow():
    dm = DataManager()
    use_existing = input("Use existing data? (y/N): ").strip().lower() == 'y'
    if use_existing:
        files = dm.list_datasets()
        if not files:
            print("No CSVs in data/. Please download first.")
            return
        for i, f in enumerate(files, 1):
            print(f"  {i}) {f}")
        idx = int(input("Select dataset: ").strip()) - 1
        data = dm.load_csv(files[idx])
        sym = files[idx].split('_')[0]
    else:
        sym = input("Symbol (e.g. AAPL): ").strip().upper() or 'AAPL'
        yrs = int(input("Years of data (default 2): ").strip() or 2)
        iv  = input("Interval (1d/60m default 1d): ").strip() or '1d'
        path = dm.download_yfinance(sym, yrs, iv)
        data = dm.load_csv(path)

    summary = {
        'symbol':     sym,
        'count':      len(data),
        'first_close': float(data['Close'].iloc[0]),
        'last_close':  float(data['Close'].iloc[-1]),
        'mean_close':  float(data['Close'].mean()),
        'std_close':   float(data['Close'].std())
    }
    prompt = (
        f"Generate a Pine Script v5 strategy for {sym} with inputs based on summary:\n"
        f"{summary}"
    )
    ai = AIAdvisor()
    script = ai.generate_pine_script(prompt)
    if ai.validate_pine(script):
        print("✅ Script syntax valid")
    out = f"strategies/{sym}_ai_{int(__import__('time').time())}.pine"
    with open(out, 'w') as fh:
        fh.write(script)
    print(f"Saved AI script to {out}")

def refine_workflow():
    files = [f for f in DataManager().list_datasets()]  # wrong list? Sorry, strategies:
    pine = __import__('glob').glob("strategies/*.pine")
    if not pine:
        print("No Pine scripts found in strategies/")
        return
    for i, f in enumerate(pine, 1):
        print(f"  {i}) {f}")
    idx = int(input("Select script to refine: ").strip()) - 1
    path = pine[idx]
    text = open(path).read()
    # extract input.int/float
    params = {}
    for m in __import__('re').finditer(
        r"input\.(?:int|float)\(\s*([\d\.]+)\s*,\s*['\"]([^'\"]+)['\"]", text
    ):
        params[m.group(2)] = float(m.group(1))
    if not params:
        print("No parameters found.")
        return
    print("Found parameters:", params)

    # load a dataset
    files = DataManager().list_datasets()
    for i, f in enumerate(files, 1):
        print(f"  {i}) {f}")
    idx = int(input("Select data for backtest: ").strip()) - 1
    data = DataManager().load_csv(files[idx])

    # multi-level refine (simplified – plug in your Optimizer logic)
    bt = Backtester()
    strat = MACDStrategy()  # or choose based on script contents
    bounds = {k: (v*0.1, v*10) for k, v in params.items()}
    opt = Optimizer(bt, data, strat, bounds)
    print("Running 1M-sample random search…")
    results = opt.random_search(samples=1_000_000)
    top = sorted(results, key=lambda x: x[1]['net_profit'], reverse=True)[:3]
    print("Top 3 parameter sets:")
    for ps, metrics in top:
        print(ps, "| Profit:", metrics['net_profit'], "Win %:", metrics['win_rate'])

    # inject best into Pine and save
    best_params = top[0][0]
    new_script = inject_pine_script(text, best_params)
    out = path.replace(".pine", f"_refined_{int(__import__('time').time())}.pine")
    open(path + ".bak", "w").write(text)
    with open(out, "w") as fh:
        fh.write(new_script)
    print(f"Backup saved to {path}.bak, refined script to {out}")

def prompt_user():
    while True:
        print("\nOptions:")
        print("  1) Create AI Pine Script")
        print("  2) Refine existing Pine script")
        print("  3) Exit")
        c = input("Choice: ").strip()
        if c == '1':
            create_workflow()
        elif c == '2':
            refine_workflow()
        elif c == '3':
            print("Goodbye.")
            sys.exit(0)
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    prompt_user()
