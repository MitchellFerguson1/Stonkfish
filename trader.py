import random
from typing import Optional, Dict
from portfolio import Portfolio
from market_utils import get_random_stock, get_current_price, get_random_trade_amount


class TradeResult:
    """Result of a trade attempt"""

    def __init__(self, success: bool, action: str, ticker: str, shares: int = 0,
                 price: float = 0, total: float = 0, reason: str = ""):
        self.success = success
        self.action = action  # 'BUY', 'SELL', or 'SKIP'
        self.ticker = ticker
        self.shares = shares  # Always int, never float
        self.price = price
        self.total = total
        self.reason = reason


class Trader:
    """Handles trading logic"""

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def execute_random_trade(self) -> TradeResult:
        """
        Execute a random trade:
        - Pick random stock
        - Pick random buy or sell
        - Pick random dollar amount
        - 0.5% chance to liquidate EVERYTHING (chaos mode)
        """
        # RARE CHAOS EVENT: 0.5% chance to liquidate entire portfolio
        if random.random() < 0.005 and self.portfolio.holdings:
            return self._execute_liquidation()

        # Decide buy or sell (50/50)
        action = random.choice(['BUY', 'SELL'])

        if action == 'BUY':
            return self._execute_buy()
        else:
            return self._execute_sell()

    def _execute_buy(self) -> TradeResult:
        """Execute a random buy order"""
        # Skip if no cash
        if self.portfolio.cash <= 0:
            return TradeResult(
                success=False,
                action='SKIP',
                ticker='N/A',
                reason='No cash available'
            )

        # Get random stock
        ticker = get_random_stock()

        # Get current price
        price = get_current_price(ticker)
        if price is None:
            return TradeResult(
                success=False,
                action='SKIP',
                ticker=ticker,
                reason='Could not fetch price'
            )

        # Get random trade amount
        trade_amount = get_random_trade_amount(self.portfolio.cash)

        # Calculate shares (rounded down to avoid fractional shares)
        shares = int(trade_amount / price)

        if shares == 0:
            return TradeResult(
                success=False,
                action='SKIP',
                ticker=ticker,
                reason='Insufficient funds for even 1 share'
            )

        # Execute buy
        actual_cost = shares * price
        success = self.portfolio.buy(ticker, shares, price)

        if success:
            return TradeResult(
                success=True,
                action='BUY',
                ticker=ticker,
                shares=shares,
                price=price,
                total=actual_cost
            )
        else:
            return TradeResult(
                success=False,
                action='SKIP',
                ticker=ticker,
                reason='Failed to execute buy'
            )

    def _execute_sell(self) -> TradeResult:
        """Execute a random sell order"""
        # Skip if no holdings
        if not self.portfolio.holdings:
            return TradeResult(
                success=False,
                action='SKIP',
                ticker='N/A',
                reason='No holdings to sell'
            )

        # Pick random stock from holdings
        ticker = random.choice(list(self.portfolio.holdings.keys()))
        shares_owned = self.portfolio.holdings[ticker]

        # Get current price
        price = get_current_price(ticker)
        if price is None:
            return TradeResult(
                success=False,
                action='SKIP',
                ticker=ticker,
                reason='Could not fetch price'
            )

        # Decide how many shares to sell (random percentage)
        sell_percent = random.uniform(0.1, 1.0)  # Sell 10% to 100%
        shares_to_sell = max(1, int(shares_owned * sell_percent))

        # Execute sell
        success = self.portfolio.sell(ticker, shares_to_sell, price)

        if success:
            total = shares_to_sell * price
            return TradeResult(
                success=True,
                action='SELL',
                ticker=ticker,
                shares=shares_to_sell,
                price=price,
                total=total
            )
        else:
            return TradeResult(
                success=False,
                action='SKIP',
                ticker=ticker,
                reason='Failed to execute sell'
            )

    def _execute_liquidation(self) -> TradeResult:
        """CHAOS MODE: Sell EVERYTHING in the portfolio"""
        if not self.portfolio.holdings:
            return TradeResult(
                success=False,
                action='SKIP',
                ticker='N/A',
                reason='No holdings to liquidate'
            )

        total_proceeds = 0
        positions_sold = 0
        tickers_sold = []

        # Sell all positions
        holdings_copy = list(self.portfolio.holdings.items())
        for ticker, shares in holdings_copy:
            price = get_current_price(ticker)
            if price:
                if self.portfolio.sell(ticker, shares, price):
                    total_proceeds += shares * price
                    positions_sold += 1
                    tickers_sold.append(ticker)

        if positions_sold > 0:
            return TradeResult(
                success=True,
                action='LIQUIDATION',
                ticker=f"{positions_sold} positions",
                shares=0,
                price=0,
                total=total_proceeds,
                reason=f"Liquidated {', '.join(tickers_sold[:3])}{'...' if len(tickers_sold) > 3 else ''}"
            )
        else:
            return TradeResult(
                success=False,
                action='SKIP',
                ticker='N/A',
                reason='Liquidation failed'
            )
