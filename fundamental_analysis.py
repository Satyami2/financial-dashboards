import yfinance as yf
import pandas as pd
import os

symbols_path = os.path.join(os.path.dirname(__file__), '../data/nifty50_symbols.csv')
symbols = pd.read_csv(symbols_path)['Symbol'].tolist()

fundamentals = []
for symbol in symbols:
    stock = yf.Ticker(symbol + ".NS")
    info = stock.info
    fundamentals.append({
        'Symbol': symbol,
        'Company': info.get('shortName'),
        'Market Cap (₹100 Cr)': round((info.get('marketCap', 0) or 0) / 1e10, 2),
        'P/E Ratio': info.get('trailingPE'),
        'Forward P/E': info.get('forwardPE'),
        'PEG Ratio': info.get('pegRatio'),
        'P/B Ratio': info.get('priceToBook'),
        'EPS': info.get('trailingEps'),
        'Forward EPS': info.get('forwardEps'),
        'Dividend Yield (%)': (info.get('dividendYield', 0) or 0) * 100,
        'ROE (%)': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') is not None else None,
        'ROA (%)': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') is not None else None,
        'Debt/Equity': info.get('debtToEquity'),
        'Current Ratio': info.get('currentRatio'),
        'Quick Ratio': info.get('quickRatio'),
        'Profit Margin (%)': info.get('profitMargins', 0) * 100 if info.get('profitMargins') is not None else None,
        'Operating Margin (%)': info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') is not None else None,
        'Sector': info.get('sector'),
        'Industry': info.get('industry'),
    })

fundamentals_path = os.path.join(os.path.dirname(__file__), '../data/nifty50_fundamentals.csv')
pd.DataFrame(fundamentals).to_csv(fundamentals_path, index=False)
print(f"Fundamental data saved to {fundamentals_path}") 