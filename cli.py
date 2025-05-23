import os
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from data_manager import load_templates, load_data
from ai_utils import create_ai_pine, refine_pine
from backtester import Backtester

console = Console()

@click.group()
def cli():
    """STONKS Backtesting Suite CLI"""
    pass


def _print_user(question: str):
    console.print(f"❯ {question}", style="bold cyan")


def _print_ai(response: str):
    console.print(response, style="bold yellow")


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
    # Print user prompt
    _print_user(f"create-ai --symbol {symbol} --start {start} --end {end}")

    # Load templates
    templates = load_templates(templates_dir)
    if not templates:
        console.print(f"No templates found in {templates_dir}", style="bold red")
        return

    # Load data
    data = load_data()
    symbol = symbol.upper()
    if symbol not in data:
        console.print(f"Data for symbol {symbol} not found.", style="bold red")
        return
    df = data[symbol]

    # AI generation with spinner
    if not verboseai:
        with Progress(SpinnerColumn(), TextColumn("[green]Thinking..."), transient=True) as progress:
            progress.add_task("ai", total=None)
            code = create_ai_pine(templates, df, start, end)
    else:
        code = create_ai_pine(templates, df, start, end, verbose=True)

    # Print AI response
    _print_ai(code)

    # Save file
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
    # Print user prompt
    _print_user(f"refine-ai --input-script {input_script} --symbol {symbol} --start {start} --end {end}")

    # Load templates
    templates = load_templates(templates_dir)

    # Read existing script
    with open(input_script, 'r') as f:
        code = f.read()

    # Load data
    data = load_data()
    symbol = symbol.upper()
    if symbol not in data:
        console.print(f"Data for symbol {symbol} not found.", style="bold red")
        return
    df = data[symbol]

    # AI refinement with spinner
    if not verboseai:
        with Progress(SpinnerColumn(), TextColumn("[green]Thinking..."), transient=True) as progress:
            progress.add_task("ai", total=None)
            refined = refine_pine(code, templates, df, start, end)
    else:
        refined = refine_pine(code, templates, df, start, end, verbose=True)

    # Print AI response
    _print_ai(refined)

    # Save file
    base = os.path.splitext(os.path.basename(input_script))[0]
    output_path = os.path.join('strategies', f'{base}_refined.pine')
    os.makedirs('strategies', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(refined)

    console.print(f"Refined Pine Script saved to {output_path}", style="bold green")


if __name__ == '__main__':
    cli()
