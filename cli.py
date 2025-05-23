# cli.py
import os
import click

from data_manager import load_templates, load_data
from ai_utils import create_ai_pine, refine_pine
from backtester import Backtester


@click.group()
def cli():
    """STONKS Backtesting Suite CLI"""
    pass


@cli.command('create-ai')
@click.option('--templates-dir', default='templates', help='Directory of Pine Script templates')
@click.option('--symbol', required=True, help='Stock symbol to backtest')
@click.option('--start', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end', default=None, help='End date (YYYY-MM-DD)')
def create_ai(templates_dir, symbol, start, end):
    """
    Create a new Pine Script strategy using AI and available templates.
    """
    # Load templates
    templates = load_templates(templates_dir)
    if not templates:
        click.echo('No templates found in ' + templates_dir)
        return

    # Load data
    data = load_data()
    if symbol.upper() not in data:
        click.echo(f"Data for symbol {symbol} not found.")
        return
    df = data[symbol.upper()]

    # Generate AI Pine Script
    code = create_ai_pine(templates, df, start, end)
    output_path = os.path.join('strategies', f'{symbol}_ai_generated.pine')
    os.makedirs('strategies', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(code)

    click.echo(f"AI Pine Script generated and saved to {output_path}")


@cli.command('refine-ai')
@click.option('--templates-dir', default='templates', help='Directory of Pine Script templates')
@click.option('--input-script', required=True, type=click.Path(exists=True), help='Existing Pine Script file to refine')
@click.option('--symbol', required=True, help='Stock symbol to backtest refinement')
@click.option('--start', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end', default=None, help='End date (YYYY-MM-DD)')
def refine_ai(templates_dir, input_script, symbol, start, end):
    """
    Refine an existing Pine Script strategy using AI-based optimization.
    """
    # Load templates (for context)
    templates = load_templates(templates_dir)

    # Read existing script
    with open(input_script, 'r') as f:
        code = f.read()

    # Load data
    data = load_data()
    if symbol.upper() not in data:
        click.echo(f"Data for symbol {symbol} not found.")
        return
    df = data[symbol.upper()]

    # Refine Pine Script
    refined_code = refine_pine(code, templates, df, start, end)
    base_name = os.path.splitext(os.path.basename(input_script))[0]
    output_path = os.path.join('strategies', f'{base_name}_refined.pine')
    os.makedirs('strategies', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(refined_code)

    click.echo(f"Refined Pine Script saved to {output_path}")


if __name__ == '__main__':
    cli()
