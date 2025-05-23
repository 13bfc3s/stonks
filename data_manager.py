import os, glob
import pandas as pd
import yfinance as yf

class DataManager:
    def __init__(self, folder: str): self.folder = folder
    def list_datasets(self): return glob.glob(os.path.join(self.folder, '*.csv'))
    def load_csv(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path, parse_dates=[0], index_col=0)
        df.columns = [c.strip().capitalize() for c in df.columns]
        for col in df.columns: df[col]=pd.to_numeric(df[col],errors='coerce')
        return df.dropna()
    def download_yfinance(self, sym: str, years: int, interval: str) -> str:
        df = yf.download(sym, period=f"{years}y", interval=interval)
        fn = f"{sym}_{years}Y_{interval}.csv"
        path = os.path.join(self.folder, fn)
        df.to_csv(path)
        return path
