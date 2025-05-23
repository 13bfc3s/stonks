import datetime
from typing import Dict, Any
import pandas as pd

class Backtester:
    def __init__(self, capital=10000, pct=20, tick=0, slip=0, margin=100, md=100, mw=500):
        self.capital, self.pct, self.tick, self.slip = capital,pct,tick,slip
        self.margin, self.max_day, self.max_week = margin, md, mw

    def run(self, data: pd.DataFrame, strat, params: Dict[str,Any]) -> Dict[str,Any]:
        cash=self.capital;pos=0;entry=0;equity=[]
        # simulate trades...
        return {"net_profit":0.0}
