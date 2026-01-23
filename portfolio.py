import json
import os
from datetime import datetime

import pytz


class Portfolio:
    """Manages the trading portfolio with persistence"""

    def __init__(self, data_file: str = "portfolio_data.json"):
        self.data_file = data_file
        self.cash: float = 10000.0
        self.holdings: dict[str, int] = {}  # ticker: num_shares (int, not float)
        self.cost_basis: dict[str, float] = {}  # ticker: total cost basis
        self.trade_history: list = []
        self.best_trade: dict | None = None  # Best trade by % return
        self.worst_trade: dict | None = None  # Worst trade by % return
        self.sp500_baseline: float | None = None  # S&P 500 price at start
        self.sp500_shares: float | None = None  # How many SPY shares $10k would buy
        self.load()

    def load(self):
        """Load portfolio from disk"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file) as f:
                    data = json.load(f)
                    self.cash = data.get('cash', 10000.0)
                    # Convert holdings to int
                    self.holdings = {k: int(v) for k, v in data.get('holdings', {}).items()}
                    self.cost_basis = data.get('cost_basis', {})
                    self.trade_history = data.get('trade_history', [])
                    self.best_trade = data.get('best_trade')
                    self.worst_trade = data.get('worst_trade')
                    self.sp500_baseline = data.get('sp500_baseline')
                    self.sp500_shares = data.get('sp500_shares')

                    # Migrate old data: if cost_basis is missing, calculate from trade history
                    if not self.cost_basis and self.holdings:
                        self._recalculate_cost_basis_from_history()
            except Exception as e:
                print(f"Error loading portfolio: {e}")
                self._initialize_fresh()
        else:
            self._initialize_fresh()

    def _initialize_fresh(self):
        """Initialize a fresh portfolio"""
        self.cash = 10000.0
        self.holdings = {}
        self.cost_basis = {}
        self.trade_history = []
        self.best_trade = None
        self.worst_trade = None
        self.sp500_baseline = None
        self.sp500_shares = None
        self.save()

    def save(self):
        """Save portfolio to disk with atomic write"""
        data = {
            'cash': self.cash,
            'holdings': self.holdings,
            'cost_basis': self.cost_basis,
            'trade_history': self.trade_history,
            'best_trade': self.best_trade,
            'worst_trade': self.worst_trade,
            'sp500_baseline': self.sp500_baseline,
            'sp500_shares': self.sp500_shares
        }
        # Atomic write: write to temp file, then rename
        temp_file = self.data_file + '.tmp'
        try:
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            # Atomic rename (safe even if crash happens)
            os.replace(temp_file, self.data_file)
        except Exception as e:
            print(f"Error saving portfolio: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def buy(self, ticker: str, shares: int, price: float) -> bool:
        """
        Buy shares of a stock
        Returns True if successful, False if insufficient funds
        """
        cost = shares * price
        if cost > self.cash:
            return False

        self.cash -= cost
        self.holdings[ticker] = self.holdings.get(ticker, 0) + shares
        self.cost_basis[ticker] = self.cost_basis.get(ticker, 0.0) + cost

        self._record_trade('BUY', ticker, shares, price, cost)
        self.save()
        return True

    def sell(self, ticker: str, shares: int, price: float) -> bool:
        """
        Sell shares of a stock
        Returns True if successful, False if insufficient shares
        """
        current_shares = self.holdings.get(ticker, 0)
        if shares > current_shares:
            return False

        proceeds = shares * price
        self.cash += proceeds

        # Calculate P&L for this trade
        cost_per_share = 0
        if current_shares > 0 and ticker in self.cost_basis:
            cost_per_share = self.cost_basis[ticker] / current_shares
            trade_cost = cost_per_share * shares
            trade_pnl = proceeds - trade_cost
            trade_pnl_pct = (trade_pnl / trade_cost * 100) if trade_cost > 0 else 0

            # Track best/worst trades
            self._update_best_worst_trade(ticker, shares, cost_per_share, price, trade_pnl_pct)

            # Reduce cost basis proportionally
            self.cost_basis[ticker] -= cost_per_share * shares

        self.holdings[ticker] = current_shares - shares

        # Remove ticker if no shares left
        if self.holdings[ticker] == 0:
            del self.holdings[ticker]
            if ticker in self.cost_basis:
                del self.cost_basis[ticker]

        self._record_trade('SELL', ticker, shares, price, proceeds)
        self.save()
        return True

    def _record_trade(self, action: str, ticker: str, shares: int, price: float, total: float):
        """Record a trade in history"""
        et_tz = pytz.timezone('America/New_York')
        trade = {
            'timestamp': datetime.now(et_tz).isoformat(),
            'action': action,
            'ticker': ticker,
            'shares': shares,
            'price': price,
            'total': total
        }
        self.trade_history.append(trade)

        # Keep only last 100 trades to avoid bloat
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]

    def get_total_value(self, get_price_func) -> float:
        """
        Calculate total portfolio value (cash + holdings value)
        get_price_func: function that takes ticker and returns current price
        """
        holdings_value = 0
        for ticker, shares in self.holdings.items():
            try:
                price = get_price_func(ticker)
                if price:
                    holdings_value += shares * price
            except Exception:
                pass  # Skip if can't get price

        return self.cash + holdings_value

    def get_holdings_summary(self, get_price_func) -> list:
        """Get list of holdings with current values"""
        summary = []
        for ticker, shares in self.holdings.items():
            try:
                price = get_price_func(ticker)
                if price:
                    value = shares * price
                    summary.append({
                        'ticker': ticker,
                        'shares': shares,
                        'price': price,
                        'value': value
                    })
            except Exception:
                pass

        return sorted(summary, key=lambda x: x['value'], reverse=True)

    def get_todays_trades(self) -> list:
        """Get trades from today (using ET timezone)"""
        et_tz = pytz.timezone('America/New_York')
        today = datetime.now(et_tz).date()
        todays_trades = []

        for trade in reversed(self.trade_history):
            # Parse timestamp and convert to ET
            trade_dt = datetime.fromisoformat(trade['timestamp'])
            # If timestamp is naive, assume it's ET
            if trade_dt.tzinfo is None:
                trade_dt = et_tz.localize(trade_dt)
            else:
                trade_dt = trade_dt.astimezone(et_tz)

            trade_date = trade_dt.date()
            if trade_date == today:
                todays_trades.append(trade)
            elif trade_date < today:
                break  # Stop when we hit yesterday

        return list(reversed(todays_trades))

    def get_position_details(self, get_price_func) -> list:
        """
        Get detailed position info including cost basis and P&L
        Returns list of dicts with ticker, shares, current price, cost basis, P&L, etc.
        """
        positions = []

        for ticker, shares in self.holdings.items():
            # Get cost basis from tracked data
            cost_basis = self.cost_basis.get(ticker, 0.0)
            avg_cost = cost_basis / shares if shares > 0 else 0

            # Get current price
            try:
                current_price = get_price_func(ticker)
                if current_price:
                    current_value = shares * current_price
                    pnl = current_value - cost_basis
                    pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0

                    positions.append({
                        'ticker': ticker,
                        'shares': shares,
                        'avg_cost': avg_cost,
                        'current_price': current_price,
                        'cost_basis': cost_basis,
                        'current_value': current_value,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
            except Exception:
                pass

        return sorted(positions, key=lambda x: abs(x['pnl']), reverse=True)

    def _recalculate_cost_basis_from_history(self):
        """Recalculate cost basis from trade history (for migration)"""
        self.cost_basis = {}
        temp_holdings = {}

        for trade in self.trade_history:
            ticker = trade['ticker']
            shares = trade['shares']
            action = trade['action']
            total = trade['total']

            if action == 'BUY':
                temp_holdings[ticker] = temp_holdings.get(ticker, 0) + shares
                self.cost_basis[ticker] = self.cost_basis.get(ticker, 0.0) + total
            elif action == 'SELL':
                current = temp_holdings.get(ticker, 0)
                if current > 0 and ticker in self.cost_basis:
                    cost_per_share = self.cost_basis[ticker] / current
                    self.cost_basis[ticker] -= cost_per_share * shares
                    temp_holdings[ticker] = current - shares
                    if temp_holdings[ticker] == 0:
                        del self.cost_basis[ticker]

    def _update_best_worst_trade(self, ticker: str, shares: int, cost_per_share: float,
                                   sell_price: float, pnl_pct: float):
        """Update best and worst trade records"""
        trade_info = {
            'ticker': ticker,
            'shares': shares,
            'buy_price': cost_per_share,
            'sell_price': sell_price,
            'pnl_pct': pnl_pct,
            'timestamp': datetime.now(pytz.timezone('America/New_York')).isoformat()
        }

        # Update best trade
        if self.best_trade is None or pnl_pct > self.best_trade.get('pnl_pct', float('-inf')):
            self.best_trade = trade_info

        # Update worst trade
        if self.worst_trade is None or pnl_pct < self.worst_trade.get('pnl_pct', float('inf')):
            self.worst_trade = trade_info

    def initialize_sp500_baseline(self, get_price_func):
        """Initialize S&P 500 baseline for comparison (call once at start)"""
        if self.sp500_baseline is None:
            spy_price = get_price_func('SPY')
            if spy_price:
                self.sp500_baseline = spy_price
                self.sp500_shares = 10000.0 / spy_price
                self.save()
                print(f"S&P 500 baseline initialized: {self.sp500_shares:.2f} shares of SPY @ ${spy_price:.2f}")

    def get_sp500_comparison(self, get_price_func) -> dict | None:
        """Get comparison vs S&P 500"""
        if self.sp500_baseline is None or self.sp500_shares is None:
            return None

        current_spy_price = get_price_func('SPY')
        if not current_spy_price:
            return None

        sp500_value = self.sp500_shares * current_spy_price
        sp500_pnl = sp500_value - 10000
        sp500_pnl_pct = (sp500_pnl / 10000) * 100

        portfolio_value = self.get_total_value(get_price_func)
        portfolio_pnl = portfolio_value - 10000
        portfolio_pnl_pct = (portfolio_pnl / 10000) * 100

        difference = portfolio_pnl_pct - sp500_pnl_pct

        return {
            'sp500_value': sp500_value,
            'sp500_pnl': sp500_pnl,
            'sp500_pnl_pct': sp500_pnl_pct,
            'portfolio_value': portfolio_value,
            'portfolio_pnl': portfolio_pnl,
            'portfolio_pnl_pct': portfolio_pnl_pct,
            'difference': difference,
            'beating_market': difference > 0
        }

    def reset(self):
        """Reset portfolio to starting state"""
        self._initialize_fresh()
