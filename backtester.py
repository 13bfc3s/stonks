#!/usr/bin/env python3
# backtester.py

import datetime
from typing import Any, Dict, List

import pandas as pd

class Backtester:
    """
    Simulates long/short strategy performance on OHLC data.
    """

    def __init__(
        self,
        capital: float = 10000.0,
        order_size_pct: float = 20.0,
        tick_verify: float = 0.0,
        slippage: float = 0.0,
        margin: float = 100.0,
        max_day: int = 100,
        max_week: int = 500,
    ):
        self.capital = capital
        self.order_size_pct = order_size_pct
        self.tick_verify = tick_verify
        self.slippage = slippage
        self.margin = margin
        self.max_day = max_day
        self.max_week = max_week

    def run(
        self,
        data: pd.DataFrame,
        strat: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the backtest:
        - data: DataFrame with at least a 'Close' column and a DateTimeIndex
        - strat: instance of a Strategy subclass (must implement generate_signals)
        - params: dict of strategy parameters
        Returns a dict of performance metrics + equity curve.
        """
        cash = self.capital
        pos = 0.0
        entry_price = 0.0

        equity_curve: List[float] = []
        total_trades = wins = losses = 0
        gross_profit = gross_loss = 0.0

        day_count: Dict[datetime.date, int] = {}
        week_count: Dict[int, int] = {}

        max_equity = min_equity = cash
        max_pos = 0.0

        # Generate entry/exit signals: 1 for enter, -1 for exit, 0 hold
        signals = strat.generate_signals(data, params)

        for ts, price in data['Close'].items():
            date = ts.date()
            weeknum = date.isocalendar()[1]

            day_count.setdefault(date, 0)
            week_count.setdefault(weeknum, 0)

            sig = signals.get(ts, 0)

            # ENTRY: long if signal == 1
            if (
                sig == 1
                and pos == 0
                and day_count[date] < self.max_day
                and week_count[weeknum] < self.max_week
            ):
                # Determine position size
                order_cash = (self.order_size_pct / 100.0) * cash
                leverage = max(self.margin / 100.0, 1.0)
                size = order_cash / (price + self.tick_verify + self.slippage)
                size *= leverage

                entry_price = price + self.tick_verify + self.slippage
                pos = size
                cash -= size * entry_price

                total_trades += 1
                day_count[date] += 1
                week_count[weeknum] += 1

            # EXIT: close long if signal == -1
            elif sig == -1 and pos > 0:
                exit_price = price - self.tick_verify - self.slippage
                cash += pos * exit_price

                pnl = (exit_price - entry_price) * pos
                if pnl >= 0:
                    gross_profit += pnl
                    wins += 1
                else:
                    gross_loss += abs(pnl)
                    losses += 1

                pos = 0.0

            # Track equity and extremes
            equity = cash + pos * price
            equity_curve.append(equity)
            max_equity = max(max_equity, equity)
            min_equity = min(min_equity, equity)
            max_pos = max(max_pos, pos)

        # Close any open position at the end
        if pos > 0:
            last_price = data['Close'].iloc[-1]
            exit_price = last_price - self.tick_verify - self.slippage
            cash += pos * exit_price

            pnl = (exit_price - entry_price) * pos
            if pnl >= 0:
                gross_profit += pnl
                wins += 1
            else:
                gross_loss += abs(pnl)
                losses += 1

            equity_curve.append(cash)
            max_equity = max(max_equity, cash)
            min_equity = min(min_equity, cash)
            pos = 0.0

        # Compute summary metrics
        net_profit = cash - self.capital

        first_price = data['Close'].iloc[0]
        last_price = data['Close'].iloc[-1]
        buy_hold_val = (last_price - first_price) / first_price * self.capital
        buy_hold_pct = (last_price - first_price) / first_price * 100.0

        runup_val = max_equity - self.capital
        runup_pct = (runup_val / self.capital) * 100.0

        drawdown_val = self.capital - min_equity
        drawdown_pct = (drawdown_val / self.capital) * 100.0

        return {
            "net_profit": net_profit,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "buy_hold_val": buy_hold_val,
            "buy_hold_pct": buy_hold_pct,
            "max_runup_val": runup_val,
            "max_runup_pct": runup_pct,
            "max_drawdown_val": drawdown_val,
            "max_drawdown_pct": drawdown_pct,
            "total_trades": total_trades,
            "win_rate": (wins / total_trades * 100.0) if total_trades > 0 else 0.0,
            "loss_rate": (losses / total_trades * 100.0) if total_trades > 0 else 0.0,
            "max_trades_day": max(day_count.values()) if day_count else 0,
            "max_trades_week": max(week_count.values()) if week_count else 0,
            "max_contracts_held": max_pos,
            "equity_curve": equity_curve,
        }
