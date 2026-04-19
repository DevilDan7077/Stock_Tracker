"""
models.py - Data models for Stock Tracker App
Mini Project - Part A: Backend Implementation using Python
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Stock:
    """Represents a stock with real-time and historical data."""
    symbol: str
    name: str
    price: float
    change: float          # Absolute price change
    change_pct: float      # Percentage change
    volume: int
    market_cap: float
    pe_ratio: Optional[float]
    week_52_high: float
    week_52_low: float
    currency: str = "USD"
    exchange: str = "NASDAQ"
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "change": round(self.change, 2),
            "change_pct": round(self.change_pct, 4),
            "volume": self.volume,
            "market_cap": self.market_cap,
            "pe_ratio": self.pe_ratio,
            "week_52_high": self.week_52_high,
            "week_52_low": self.week_52_low,
            "currency": self.currency,
            "exchange": self.exchange,
            "last_updated": self.last_updated
        }


@dataclass
class HistoricalDataPoint:
    """Represents a single OHLCV data point."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }


@dataclass
class Portfolio:
    """Represents a user's stock portfolio."""
    holdings: dict = field(default_factory=dict)   # {symbol: quantity}

    def add_stock(self, symbol: str, quantity: int):
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity

    def remove_stock(self, symbol: str, quantity: int):
        if symbol not in self.holdings:
            raise ValueError(f"{symbol} not in portfolio")
        if self.holdings[symbol] < quantity:
            raise ValueError(f"Insufficient shares of {symbol}")
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]

    def to_dict(self) -> dict:
        return {"holdings": self.holdings}
