import os
import pandas as pd
from nsepython import nsefetch
import yfinance as yf

# Ensure data directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), '../data'), exist_ok=True)

# Fetch Nifty 50 symbols
nifty50_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
data = nsefetch(nifty50_url)
symbols = [item['symbol'] for item in data['data']]

symbols_path = os.path.join(os.path.dirname(__file__), '../data/nifty50_symbols.csv')
pd.DataFrame(symbols, columns=['Symbol']).to_csv(symbols_path, index=False)
print(f"Nifty 50 symbols saved to {symbols_path}")

# Fetch historical data for all symbols using yfinance (6 months)
symbols_yf = [s + ".NS" for s in symbols]
hist_data = yf.download(symbols_yf, period="6mo", interval="1d", group_by='ticker', auto_adjust=True)
hist_data.to_csv(os.path.join(os.path.dirname(__file__), '../data/nifty50_data.csv'))
print("Nifty 50 historical data saved to data/nifty50_data.csv") 