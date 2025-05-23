import os
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import concurrent.futures
import pandas as pd

from data_manager import load_templates, load_data
from ai_utils import create_ai_pine, refine_pine
from backtester import Backtester

console = Console()


def _print_user(question: str):
    console.print(f"❯ {question}", style="bold cyan")


def _print_ai(response: str):
    console.print(response, style="bold yellow")


@click.group()
def cli():
    """STONKS Backtesting Suite CLI"""
    pass


@cli.command('create-ai')
@click.option('--templates-dir', default='templates', help='Directory of Pine Script templates')
@click.option('--symbol', required=True, help='Stock symbol to backtest')
@click.option('--start', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end', default=None, help='End date (YYYY-MM-DD)')
@click.option('--verboseAI', is_flag=True, default=False, help='Show AI reasoning logs')
def create_ai(templates_dir, symbol, start, end, verboseai):
    """
    Create a new Pine Script strategy using AI and available templates.
    """
    _print_user(f"create-ai --symbol {symbol} --start {start} --end {end}")

    templates = load_templates(templates_dir)
    if not templates:
        console.print(f"No templates found in {templates_dir}", style="bold red")
        return

    data = load_data()
    symbol = symbol.upper()
    if symbol not in data:
        console.print(f"Data for symbol {symbol} not found.", style="bold red")
        return
    df = data[symbol]

    if not verboseai:
        with Progress(SpinnerColumn(), TextColumn("[green]Thinking..."), transient=True) as progress:
            progress.add_task("ai", total=None)
            code = create_ai_pine(templates, df, start, end)
    else:
        code = create_ai_pine(templates, df, start, end, verbose=True)

    _print_ai(code)

    output_path = os.path.join('strategies', f'{symbol}_ai_generated.pine')
    os.makedirs('strategies', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(code)

    console.print(f"AI Pine Script generated and saved to {output_path}", style="bold green")


@cli.command('refine-ai')
@click.option('--templates-dir', default='templates', help='Directory of Pine Script templates')
@click.option('--input-script', required=True, type=click.Path(exists=True), help='Existing Pine Script file to refine')
@click.option('--symbol', required=True, help='Stock symbol to backtest refinement')
@click.option('--start', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end', default=None, help='End date (YYYY-MM-DD)')
@click.option('--verboseAI', is_flag=True, default=False, help='Show AI reasoning logs')
def refine_ai(templates_dir, input_script, symbol, start, end, verboseai):
    """
    Refine an existing Pine Script strategy using AI-based optimization.
    """
    _print_user(f"refine-ai --input-script {input_script} --symbol {symbol} --start {start} --end {end}")

    templates = load_templates(templates_dir)

    with open(input_script, 'r') as f:
        code = f.read()

    data = load_data()
    symbol = symbol.upper()
    if symbol not in data:
        console.print(f"Data for symbol {symbol} not found.", style="bold red")
        return
    df = data[symbol]

    if not verboseai:
        with Progress(SpinnerColumn(), TextColumn("[green]Thinking..."), transient=True) as progress:
            progress.add_task("ai", total=None)
            refined = refine_pine(code, templates, df, start, end)
    else:
        refined = refine_pine(code, templates, df, start, end, verbose=True)

    _print_ai(refined)

    base = os.path.splitext(os.path.basename(input_script))[0]
    output_path = os.path.join('strategies', f'{base}_refined.pine')
    os.makedirs('strategies', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(refined)

    console.print(f"Refined Pine Script saved to {output_path}", style="bold green")


@cli.command('scan')
@click.option('--symbols', required=True, help='Comma-separated list of stock symbols')
@click.option('--periods', required=True, help='Comma-separated date ranges (start:end, YYYY-MM-DD:YYYY-MM-DD)')
@click.option('--templates-dir', default='templates', help='Directory of Pine Script templates')
@click.option('--workers', default=4, help='Number of parallel workers')
def scan(symbols, periods, templates_dir, workers):
    """
    Scan multiple symbols and periods with all templates in parallel.
    """
    _print_user(f"scan --symbols {symbols} --periods {periods}")

    # Parse inputs
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    period_list = []
    for p in periods.split(','):
        start, end = p.split(':')
        period_list.append((start, end))

    # Load data and templates
    data = load_data()
    templates = load_templates(templates_dir)
    if not templates:
        console.print(f"No templates found in {templates_dir}", style="bold red")
        return

    # Prepare tasks
    tasks = []
    for sym in symbol_list:
        if sym not in data:
            console.print(f"Data for symbol {sym} not found, skipping.", style="bold yellow")
            continue
        df_full = data[sym]
        for (start, end) in period_list:
            df = df_full.loc[start:end]
            for tmpl in templates:
                tasks.append((sym, start, end, tmpl))

    results = []

    def _run_backtest(task):
        sym, start, end, tmpl = task
        df = data[sym].loc[start:end]
        bt = Backtester(df)
        code = tmpl.instantiate({k: v['default'] for k, v in tmpl.param_space.items()})
        res = bt.run(code)
        return {
            'symbol': sym,
            'start': start,
            'end': end,
            'template': tmpl.name,
            'net_profit': res.net_profit,
            'win_rate': res.win_rate
        }

    # Execute in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for r in executor.map(_run_backtest, tasks):
            results.append(r)

    # Aggregate and save
    df_res = pd.DataFrame(results)
    out_csv = 'scan_results.csv'
    df_res.to_csv(out_csv, index=False)

    console.print(f"Scan complete. Results saved to {out_csv}", style="bold green")


if __name__ == '__main__':
    cli()
