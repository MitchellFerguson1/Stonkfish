import yfinance as yf
import random
import requests
import csv
import os
from datetime import datetime, time, date
from typing import Optional, List
import pytz


def get_nyse_holidays(year: int) -> List[date]:
    """
    Get NYSE holidays for a given year
    Based on official NYSE holiday schedule
    """
    holidays = []

    # New Year's Day (observed)
    ny_day = date(year, 1, 1)
    if ny_day.weekday() == 5:  # Saturday
        holidays.append(date(year, 1, 3))  # Observed Monday
    elif ny_day.weekday() == 6:  # Sunday
        holidays.append(date(year, 1, 2))  # Observed Monday
    else:
        holidays.append(ny_day)

    # Martin Luther King Jr. Day (3rd Monday in January)
    jan_1 = date(year, 1, 1)
    # Find first Monday: if Jan 1 is Monday (0), first Monday is Jan 1
    # Otherwise, find next Monday
    days_until_monday = (7 - jan_1.weekday()) % 7
    if days_until_monday == 0:
        first_monday = jan_1
    else:
        first_monday = date(year, 1, 1 + days_until_monday)
    # 3rd Monday is first Monday + 14 days
    mlk_day = date(year, 1, first_monday.day + 14)
    holidays.append(mlk_day)

    # Presidents Day (3rd Monday in February)
    feb_1 = date(year, 2, 1)
    days_until_monday = (7 - feb_1.weekday()) % 7
    if days_until_monday == 0:
        first_monday = feb_1
    else:
        first_monday = date(year, 2, 1 + days_until_monday)
    # 3rd Monday is first Monday + 14 days
    presidents_day = date(year, 2, first_monday.day + 14)
    holidays.append(presidents_day)

    # Good Friday (Friday before Easter - approximate)
    # Using fixed dates for major years, can be enhanced with proper Easter calculation
    good_friday_dates = {
        2024: date(2024, 3, 29),
        2025: date(2025, 4, 18),
        2026: date(2026, 4, 3),
        2027: date(2027, 3, 26),
        2028: date(2028, 4, 14),
        2029: date(2029, 3, 30),
        2030: date(2030, 4, 19),
    }
    if year in good_friday_dates:
        holidays.append(good_friday_dates[year])

    # Memorial Day (Last Monday in May)
    # Find last Monday by starting from May 31 and going backwards
    may_31 = date(year, 5, 31)
    days_back = (may_31.weekday() - 0) % 7  # Days back to Monday
    memorial_day = date(year, 5, 31 - days_back)
    holidays.append(memorial_day)

    # Juneteenth (June 19, observed)
    juneteenth = date(year, 6, 19)
    if juneteenth.weekday() == 5:  # Saturday
        holidays.append(date(year, 6, 18))  # Observed Friday
    elif juneteenth.weekday() == 6:  # Sunday
        holidays.append(date(year, 6, 20))  # Observed Monday
    else:
        holidays.append(juneteenth)

    # Independence Day (July 4, observed)
    july_4 = date(year, 7, 4)
    if july_4.weekday() == 5:  # Saturday
        holidays.append(date(year, 7, 3))  # Observed Friday
    elif july_4.weekday() == 6:  # Sunday
        holidays.append(date(year, 7, 5))  # Observed Monday
    else:
        holidays.append(july_4)

    # Labor Day (1st Monday in September)
    sep_1 = date(year, 9, 1)
    # If Sept 1 is Monday, that's Labor Day. Otherwise find the next Monday.
    if sep_1.weekday() == 0:  # Monday
        labor_day = sep_1
    else:
        days_until_monday = (7 - sep_1.weekday()) % 7
        labor_day = date(year, 9, 1 + days_until_monday)
    holidays.append(labor_day)

    # Thanksgiving (4th Thursday in November)
    nov_1 = date(year, 11, 1)
    # Find first Thursday
    if nov_1.weekday() == 3:  # Thursday
        first_thursday = nov_1
    elif nov_1.weekday() < 3:  # Before Thursday
        days_until_thursday = 3 - nov_1.weekday()
        first_thursday = date(year, 11, 1 + days_until_thursday)
    else:  # After Thursday (Fri, Sat, Sun)
        days_until_thursday = 7 - nov_1.weekday() + 3
        first_thursday = date(year, 11, 1 + days_until_thursday)
    # 4th Thursday is first Thursday + 21 days
    thanksgiving = date(year, 11, first_thursday.day + 21)
    holidays.append(thanksgiving)

    # Christmas (December 25, observed)
    xmas = date(year, 12, 25)
    if xmas.weekday() == 5:  # Saturday
        holidays.append(date(year, 12, 24))  # Observed Friday
    elif xmas.weekday() == 6:  # Sunday
        holidays.append(date(year, 12, 26))  # Observed Monday
    else:
        holidays.append(xmas)

    return holidays


def is_market_open() -> bool:
    """
    Check if NYSE is currently open
    Checks: weekends, holidays, and market hours (9:30 AM - 4:00 PM ET)
    """
    et_tz = pytz.timezone('America/New_York')
    now_et = datetime.now(et_tz)
    today = now_et.date()

    # Check if it's a weekday (Monday=0, Sunday=6)
    if now_et.weekday() > 4:  # Saturday or Sunday
        return False

    # Check if today is a NYSE holiday
    holidays = get_nyse_holidays(now_et.year)
    if today in holidays:
        return False

    # Market hours: 9:30 AM - 4:00 PM ET
    market_open = time(9, 30)
    market_close = time(16, 0)
    current_time = now_et.time()

    return market_open <= current_time <= market_close


def get_current_price(ticker: str) -> Optional[float]:
    """Get current price for a ticker"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return None
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None


# Cache for loaded stocks to avoid repeated file reads
_STOCK_CACHE = None


def _load_stocks_from_csv(csv_path: str = "nyse_stocks.csv") -> List[str]:
    """Load stock tickers from CSV file"""
    stocks = []

    # Try to find the CSV file in the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, csv_path)

    try:
        with open(full_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Support both old format (ticker) and new format (ACT Symbol)
                ticker = row.get('ACT Symbol', row.get('ticker', '')).strip()

                if ticker:
                    # Filter out warrants, units, preferred stocks, and other derivatives
                    # Keep only common stocks (no dots, dollar signs, or other special chars)
                    if '.' not in ticker and '$' not in ticker and '^' not in ticker:
                        stocks.append(ticker)

        print(f"Loaded {len(stocks)} stocks from {csv_path}")
        return stocks

    except FileNotFoundError:
        print(f"Warning: {csv_path} not found at {full_path}, using fallback list")
        return _get_fallback_stocks()
    except Exception as e:
        print(f"Error loading stocks from CSV: {e}, using fallback list")
        return _get_fallback_stocks()


def _get_fallback_stocks() -> List[str]:
    """Fallback list of major NYSE stocks if CSV fails to load"""
    return [
        'BAC', 'WFC', 'JPM', 'C', 'GS', 'MS', 'BLK',
        'XOM', 'CVX', 'COP', 'SLB', 'OXY',
        'PFE', 'JNJ', 'UNH', 'CVS', 'ABBV', 'BMY', 'LLY',
        'T', 'VZ', 'DIS', 'CMCSA',
        'BA', 'CAT', 'GE', 'MMM', 'HON', 'RTX', 'LMT',
        'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW',
        'KO', 'PEP', 'PM', 'MO', 'PG',
        'GM', 'F', 'DOW', 'DD', 'LYB',
        'NEE', 'DUK', 'SO', 'D',
        'AMT', 'PLD', 'SPG', 'PSA',
        'BRK.B', 'BX', 'KKR',
        'UPS', 'FDX', 'DAL', 'UAL', 'AAL',
        'MAR', 'HLT', 'V', 'MA', 'AXP',
    ]


def get_nyse_stocks() -> List[str]:
    """
    Get a list of NYSE stocks. Loads from nyse_stocks.csv if available,
    otherwise uses a fallback list of major stocks.
    """
    global _STOCK_CACHE

    if _STOCK_CACHE is None:
        _STOCK_CACHE = _load_stocks_from_csv()

    return _STOCK_CACHE


def get_random_stock() -> str:
    """Get a random NYSE stock ticker"""
    stocks = get_nyse_stocks()
    return random.choice(stocks)


def get_random_trade_amount(cash_balance: float, max_percent: float = 0.3) -> float:
    """
    Get a random dollar amount for trading
    Returns amount between $100 and max_percent of cash balance
    """
    min_trade = min(100, cash_balance)
    max_trade = cash_balance * max_percent

    if min_trade >= max_trade:
        return min_trade

    # Use power distribution to favor smaller trades
    amount = random.uniform(min_trade, max_trade)
    return round(amount, 2)
