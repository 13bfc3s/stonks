import pandas as pd

class Strategy:
    def generate_signals(self, data: pd.DataFrame, params: dict) -> pd.Series:
        raise NotImplementedError

class MACDStrategy(Strategy):
    def generate_signals(self, data, params):
        fast = int(params['Fast EMA Period'])
        slow = int(params['Slow EMA Period'])
        sig  = int(params['MACD Signal Smoothing'])
        e1 = data['Close'].ewm(span=fast).mean()
        e2 = data['Close'].ewm(span=slow).mean()
        mac = e1 - e2
        sigl = mac.ewm(span=sig).mean()
        buy = (mac>sigl) & (mac.shift(1)<=sigl.shift(1))
        sell= (mac<sigl) & (mac.shift(1)>=sigl.shift(1))
        s = pd.Series(0, index=data.index)
        s[buy]=1; s[sell]=-1
        return s

class RSIStrategy(Strategy):
    def generate_signals(self, data, params):
        length = int(params['RSI Period'])
        ob = params['RSI Overbought']; os_ = params['RSI Oversold']
        d = data['Close'].diff(); g=d.where(d>0,0); l=-d.where(d<0,0)
        ag = g.ewm(alpha=1/length).mean(); al=l.ewm(alpha=1/length).mean()
        rsi = 100 - (100/(1+ag/al))
        s=pd.Series(0,index=data.index); s[rsi<os_]=1; s[rsi>ob]=-1
        return s
