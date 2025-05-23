# data_manager.py

import os
import glob
import pandas as pd
import yfinance as yf
from typing import List

# Default folder for CSV history files
DATA_FOLDER = 'data'

class DataManager:
    """
    Handles listing, loading, and downloading OHLC data CSVs.
    """

    def __init__(self, data_folder: str = DATA_FOLDER):
        self.data_folder = data_folder
        # Ensure the data folder exists
        os.makedirs(self.data_folder, exist_ok=True)

    def list_datasets(self) -> List[str]:
        """
        Returns a list of all CSV file paths in the data folder.
        """
        pattern = os.path.join(self.data_folder, "*.csv")
        return glob.glob(pattern)

    def load_csv(self, filepath: str) -> pd.DataFrame:
        """
        Loads a CSV into a pandas DataFrame, parsing dates and dropping non-numeric rows.
        Expects CSV with datetime index in column 0 and OHLC(+Volume) columns.
        """
        df = pd.read_csv(filepath, parse_dates=[0], index_col=0)
        # Normalize column names (e.g. 'open' -> 'Open')
        df.columns = [col.strip().capitalize() for col in df.columns]
        # Coerce to numeric, drop rows with any NaNs
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.dropna(inplace=True)
        return df

    def download_yfinance(self, symbol: str, years: int, interval: str) -> str:
        """
        Downloads historical data via yfinance and saves to data_folder.
        Returns the filepath of the saved CSV.
        """
        df = yf.download(symbol, period=f"{years}y", interval=interval)
        filename = f"{symbol}_{years}Y_{interval}.csv"
        path = os.path.join(self.data_folder, filename)
        df.to_csv(path)
        return path
