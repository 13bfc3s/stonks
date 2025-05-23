#!/usr/bin/env python3
"""
Interactive entry point for STONKS Backtesting Suite.
Provides a guided CLI with menus, prompts, loading bars, and ETAs.
"""
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from datetime import datetime
import time

from cli import create_ai, refine_ai, scan, optimize
from data_manager import load_templates, load_data

console = Console()

OPTIONS = {
    "1": "Create AI Pine Script",
    "2": "Refine Pine Script",
    "3": "Scan Symbols",
    "4": "Optimize Strategies",
    "5": "Exit"
}


def main():
    console.clear()
    console.rule("[bold green]STONKS Backtesting Concierge[/]")
    while True:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="dim", width=6)
        table.add_column("Description")
        for key, desc in OPTIONS.items():
            table.add_row(key, desc)
        console.print(table)

        choice = Prompt.ask("Select an option", choices=list(OPTIONS.keys()), default="1")
        if choice == "5":
            console.print("Goodbye!", style="bold green")
            break

        # Common prompts
        templates_dir = Prompt.ask("Templates directory", default="templates")
        data = load_data()

        if choice == "1":  # Create AI
            symbol = Prompt.ask("Symbol (e.g. AAPL)").upper()
            start = Prompt.ask("Start date (YYYY-MM-DD)", default="2000-01-01")
            end = Prompt.ask("End date (YYYY-MM-DD)", default=datetime.today().strftime("%Y-%m-%d"))
            verbose = Prompt.ask("Show AI reasoning?", choices=["y","n"], default="n") == "y"

            console.print(f"Generating AI script for [bold]{symbol}[/]...")
            with Progress(
                "[progress.description]{task.description}",
                BarColumn(), TimeElapsedColumn(), TimeRemainingColumn(),
                transient=True
            ) as progress:
                task = progress.add_task("AI Generation", total=100)
                for i in range(20):
                    time.sleep(0.05)
                    progress.advance(task, 5)
                # call actual function
                create_ai.callback(templates_dir, symbol, start, end, verbose)

        elif choice == "2":  # Refine
            script = Prompt.ask("Path to existing .pine script")
            symbol = Prompt.ask("Symbol for refinement").upper()
            start = Prompt.ask("Start date (YYYY-MM-DD)", default="2000-01-01")
            end = Prompt.ask("End date (YYYY-MM-DD)", default=datetime.today().strftime("%Y-%m-%d"))
            verbose = Prompt.ask("Show AI reasoning?", choices=["y","n"], default="n") == "y"

            console.print(f"Refining Pine script [bold]{script}[/]...")
            with Progress(
                "[progress.description]{task.description}",
                BarColumn(), TimeElapsedColumn(), TimeRemainingColumn(),
                transient=True
            ) as progress:
                task = progress.add_task("AI Refinement", total=100)
                for i in range(20):
                    time.sleep(0.05)
                    progress.advance(task, 5)
                refine_ai.callback(templates_dir, script, symbol, start, end, verbose)

        elif choice == "3":  # Scan
            symbols = Prompt.ask("Symbols (comma-separated)")
            periods = Prompt.ask("Periods (start:end, comma-separated)")
            workers = IntPrompt.ask("Parallel workers", default=4)

            console.print("Starting multi-symbol scan...")
            scan.callback(symbols, periods, templates_dir, workers)

        elif choice == "4":  # Optimize
            symbols = Prompt.ask("Symbols (comma-separated)")
            periods = Prompt.ask("Periods (start:end, comma-separated)")
            workers = IntPrompt.ask("Parallel workers", default=4)
            n_initial = IntPrompt.ask("Bayes initial samples", default=10)
            n_calls = IntPrompt.ask("Bayes optimization calls", default=50)

            console.print("Starting Bayesian optimization...")
            optimize.callback(symbols, periods, templates_dir, workers, n_initial, n_calls)

        console.print("\n")


if __name__ == '__main__':
    main()
