# Stonks Backtester

## Project Layout
stonks/
├── ai_utils.py          # AIAdvisor: chat, prompt, Pine script generation/validation
├── data_manager.py      # DataManager: listing, loading, downloading data
├── strategies.py        # Strategy base, MACDStrategy, RSIStrategy
├── backtester.py        # Backtester class: long/short simulation
├── optimizer.py         # Optimizer class: parallel random_search
├── pine_injector.py     # inject_pine helper
├── cli.py               # CLI entrypoint: prompt_user, create/refine workflows
├── requirements.txt
├── README.md
├──── data/
└──── strategies/

## Setup
pip install -r requirements.txt
## Usage
python cli.py
