import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['SMA20'] = df['close'].rolling(window=20).mean()
    df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['RSI14'] = rsi(df['close'], 14)

    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df


def support_resistance(df: pd.DataFrame, lookback: int = 30) -> pd.Series:
    recent = df.tail(lookback)
    support = recent['close'].min()
    resistance = recent['close'].max()
    return pd.Series({'support': support, 'resistance': resistance})
