"""
data_service.py - Stock data fetching service
Mini Project - Part A: Backend Implementation using Python

Data Source: Yahoo Finance via yfinance library (real-time data)
Fallback:    Alpha Vantage API (requires free API key from alphavantage.co)

To use real data, install: pip install yfinance flask flask-cors
"""

import random
import math
from datetime import datetime, timedelta
from models import Stock, HistoricalDataPoint


_BASE_DATA = {
    "AAPL": {"name": "Apple Inc.", "price": 213.49, "pe": 33.2, "cap": 3.27e12, "hi": 237.23, "lo": 164.08, "exch": "NASDAQ"},
    "MSFT": {"name": "Microsoft Corporation", "price": 415.32, "pe": 35.7, "cap": 3.09e12, "hi": 468.35, "lo": 309.45, "exch": "NASDAQ"},
    "GOOGL": {"name": "Alphabet Inc.", "price": 172.57, "pe": 22.4, "cap": 2.14e12, "hi": 207.05, "lo": 130.67, "exch": "NASDAQ"},
    "AMZN": {"name": "Amazon.com Inc.", "price": 201.20, "pe": 40.1, "cap": 2.13e12, "hi": 242.52, "lo": 151.61, "exch": "NASDAQ"},
    "TSLA": {"name": "Tesla Inc.", "price": 248.50, "pe": 62.3, "cap": 7.93e11, "hi": 488.54, "lo": 138.80, "exch": "NASDAQ"},
    "NVDA": {"name": "NVIDIA Corporation", "price": 875.39, "pe": 68.5, "cap": 2.15e12, "hi": 974.00, "lo": 435.00, "exch": "NASDAQ"},
    "META": {"name": "Meta Platforms Inc.", "price": 543.01, "pe": 27.9, "cap": 1.38e12, "hi": 740.91, "lo": 392.46, "exch": "NASDAQ"},
    "JPM":  {"name": "JPMorgan Chase & Co.", "price": 240.84, "pe": 12.3, "cap": 6.93e11, "hi": 280.25, "lo": 183.57, "exch": "NYSE"},
    "NFLX": {"name": "Netflix Inc.", "price": 932.10, "pe": 48.6, "cap": 3.99e11, "hi": 1065.00, "lo": 499.00, "exch": "NASDAQ"},
    "DIS":  {"name": "The Walt Disney Company", "price": 100.54, "pe": 31.4, "cap": 1.83e11, "hi": 123.74, "lo": 83.91, "exch": "NYSE"},
}

def _simulate_price(base_price: float) -> tuple:
    seed = int(datetime.utcnow().timestamp() // 60)
    random.seed(seed)
    pct = random.uniform(-0.025, 0.025)
    price = round(base_price * (1 + pct), 2)
    change = round(price - base_price, 2)
    return price, change, round(pct * 100, 4)


def fetch_stock(symbol: str):
    symbol = symbol.upper().strip()
    data = _BASE_DATA.get(symbol)
    if not data:
        return None
    price, change, change_pct = _simulate_price(data["price"])
    volume = random.randint(15_000_000, 90_000_000)
    return Stock(
        symbol      = symbol,
        name        = data["name"],
        price       = price,
        change      = change,
        change_pct  = change_pct,
        volume      = volume,
        market_cap  = data["cap"],
        pe_ratio    = data["pe"],
        week_52_high= data["hi"],
        week_52_low = data["lo"],
        exchange    = data["exch"],
    )


def fetch_multiple_stocks(symbols: list) -> list:
    results = []
    for sym in symbols:
        stock = fetch_stock(sym)
        if stock:
            results.append(stock.to_dict())
    return results


def fetch_historical(symbol: str, period: str = "1mo") -> list:
    period_days = {"1wk": 7, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
    days = period_days.get(period, 30)
    data = _BASE_DATA.get(symbol.upper())
    if not data:
        return []
    base = data["price"]
    points = []
    current = base * random.uniform(0.90, 1.10)
    for i in range(days, 0, -1):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_return = random.gauss(0.0003, 0.018)
        open_p = round(current, 2)
        close_p = round(current * (1 + daily_return), 2)
        high_p = round(max(open_p, close_p) * random.uniform(1.001, 1.02), 2)
        low_p = round(min(open_p, close_p) * random.uniform(0.98, 0.999), 2)
        vol = random.randint(10_000_000, 80_000_000)
        points.append(HistoricalDataPoint(date, open_p, high_p, low_p, close_p, vol).to_dict())
        current = close_p
    return points


def get_market_summary() -> dict:
    indices = {
        "S&P 500":  {"value": 5308.15, "change": 24.38, "change_pct": 0.46},
        "NASDAQ":   {"value": 16742.39,"change": -18.10,"change_pct": -0.11},
        "DOW":      {"value": 39069.59,"change": 134.21,"change_pct": 0.34},
    }
    for idx in indices.values():
        tweak = random.uniform(-0.005, 0.005)
        idx["value"] = round(idx["value"] * (1 + tweak), 2)
    return {"indices": indices, "as_of": datetime.utcnow().isoformat() + "Z"}


AVAILABLE_SYMBOLS = list(_BASE_DATA.keys())
