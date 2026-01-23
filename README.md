# Stonkfish 🐟📈

A Discord bot that makes random stock trades throughout the day with the personality of an ecstatic, ironic finance bro. Stonkfish starts with $10,000 and makes chaotic moves every hour during market hours.

## Features

- **Simulated Trading**: Tracks a $10,000 portfolio trading real NYSE stocks (2,400+ available)
- **Hourly Random Trades**: Every hour during market hours (9:30 AM - 4:00 PM ET), makes random buy/sell decisions
- **Market Announcements**:
  - 9:30 AM: Opens with portfolio status and emoji reactions
  - 4:00 PM: Closes with daily recap, P&L, and S&P 500 comparison
- **S&P 500 Comparison**: See if random trading beats just buying the index (spoiler: probably not)
- **Best/Worst Trade Tracking**: Hall of Fame/Shame for your greatest wins and most spectacular losses
- **Chaos Mode**: 0.5% chance per hour to spontaneously liquidate the ENTIRE portfolio
- **Multi-Server Support**: Works across multiple Discord servers simultaneously
- **Dynamic Personality**: Over-the-top finance bro with daily mood variations and 100+ unique message combinations
- **Portfolio Tracking**: Persistent portfolio with holdings, trade history, and accurate cost basis tracking
- **Detailed Analytics**: View individual stock performance, P&L per position, winners/losers breakdown

## Commands

In the #Stonks channel:

| Command | Description |
|---------|-------------|
| `!portfolio` | Quick portfolio overview (total value, P&L, top holdings) |
| `!stonks` | Detailed breakdown of every position with cost basis and P&L |
| `!history` | Recent trade history + Hall of Fame/Shame (best/worst trades ever) |
| `!reset` | Reset portfolio back to $10,000 |

## Setup

### 1. Prerequisites

- Python 3.8+
- Discord Bot Token (see Discord Bot Setup below)
- Discord server with a channel named "Stonks"

### 2. Installation

```bash
# Clone or download this repository
cd Stonkfish

# Install dependencies
pip install -r requirements.txt
```

### 3. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "Stonkfish")
3. Go to the "Bot" section and click "Add Bot"
4. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
5. Click "Reset Token" and copy your bot token
6. Go to OAuth2 > URL Generator
7. Select scopes: `bot`
8. Select bot permissions:
   - Send Messages
   - Read Message History
   - Read Messages/View Channels
   - Add Reactions
9. Copy the generated URL and open it in your browser to invite the bot to your server

### 4. Configuration

```bash
# Copy the template
cp .env.template .env

# Edit .env and add your Discord bot token
# Your .env file should look like:
DISCORD_BOT_TOKEN=your_actual_token_here
DISCORD_CHANNEL_NAME=Stonks
```

### 5. Create the Discord Channel

In your Discord server, create a text channel named `Stonks` (or whatever you set in `.env`).

**Note:** The channel name is **case-insensitive** - `Stonks`, `stonks`, `STONKS`, or any other variation will work!

### 6. Run the Bot

```bash
python bot.py
```

You should see:
```
Stonkfish#1234 has connected to Discord!
Looking for channel: Stonks
Found 2 channel(s):
  - Stonks in My Server
  - stonks in Another Server
S&P 500 baseline initialized: 21.43 shares of SPY @ $466.72
```

## Docker Setup (Alternative)

If you prefer to run Stonkfish in Docker:

### Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose (comes with Docker Desktop)
- Discord Bot Token (follow Discord Bot Setup above)

### Quick Start with Docker

**1. Configuration:**
```bash
# Copy the template
cp .env.template .env

# Edit .env and add your Discord bot token
nano .env
```

**2. Build and run:**
```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### Docker Commands

```bash
# Start the bot (detached mode)
docker-compose up -d

# View logs (real-time)
docker-compose logs -f stonkfish

# Stop the bot
docker-compose down

# Restart the bot
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build

# View bot status
docker-compose ps
```

### Portfolio Data Persistence

Portfolio data is automatically persisted in `portfolio_data.json` on your host machine. Even if you restart or rebuild the container, your trading history is preserved.

### Updating the Bot

```bash
# Pull latest code changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Troubleshooting Docker

**Container won't start:**
```bash
# Check logs
docker-compose logs

# Check if .env file exists
ls -la .env
```

**Reset portfolio:**
```bash
# Delete portfolio data
rm portfolio_data.json

# Restart bot
docker-compose restart
```

**Timezone issues:**
The container is set to `America/New_York` timezone. If you need a different timezone, edit `docker-compose.yml` and change the `TZ` environment variable.

## Usage

### Automatic Features

The bot automatically:
- **Posts at 9:30 AM ET** when markets open with portfolio status (with emoji reactions)
- **Executes random trades silently every hour** (10 AM, 11 AM, 12 PM, 1 PM, 2 PM, 3 PM)
- **Posts at 4:00 PM ET** when markets close with daily recap, P&L, and S&P 500 comparison
- **Only operates on NYSE trading days** (Mon-Fri during market hours, excluding all NYSE holidays)
- **Announces CHAOS events** when the rare liquidation triggers

**Only 2 messages per day** (plus rare chaos events) to avoid spam! Use commands anytime to check status.

### S&P 500 Comparison

At market close, Stonkfish compares its performance against the S&P 500:
- Tracks how many SPY shares $10k would have bought at start
- Shows if random trading is beating or trailing the market
- Personality-driven responses ("CRUSHING IT!" or "It's called TAKING RISKS!")

### Chaos Mode (Rare Event)

There's a **0.5% chance per hour** (~1 in 200 trades) that Stonkfish will spontaneously liquidate the ENTIRE portfolio. When this happens:
- All positions are sold immediately
- A dramatic announcement is posted
- Bot reacts with chaos emojis (🔥💀🎲)
- Starts fresh with all cash

This adds unpredictable excitement to the simulation!

### Emoji Reactions

The bot reacts to its own messages:
- **Market Open**: 🚀 and 💰 (50% chance each)
- **Market Close**:
  - Green day: 📈 and 💎
  - Red day: 📉 and 💪
  - Flat day: ⚖️
- **Liquidation Events**: 🔥💀🎲

### Holiday Awareness

The bot automatically detects and respects all 10 NYSE holidays including New Year's Day, MLK Day, Presidents Day, Good Friday, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving, and Christmas (with proper observance rules for weekends).

## How It Works

### Trading Logic

Every hour during market hours:
1. **0.5% chance**: Liquidate everything (CHAOS MODE)
2. Otherwise, randomly decides to BUY or SELL (50/50)
3. Picks a random NYSE stock from `nyse_stocks.csv`
4. If buying: Spends a random dollar amount (up to 30% of cash)
5. If selling: Sells a random percentage (10-100%) of a random holding
6. Skips if insufficient funds or no holdings

### Stock Universe

Stonkfish trades from a comprehensive list of 500+ NYSE stocks stored in `nyse_stocks.csv`. The list includes:
- Large-cap blue chips (AAPL, MSFT, JPM, etc.)
- Mid-cap growth stocks
- Dividend aristocrats
- All major sectors (Tech, Finance, Healthcare, Energy, etc.)

**Customizing the stock list:**
- Edit `nyse_stocks.csv` to add or remove stocks
- Format: `ticker,name,sector` (keep the header row)
- If the CSV is missing or invalid, the bot falls back to a smaller curated list

### Portfolio Management

- Starts with $10,000 cash
- Tracks all holdings with share counts
- **Accurate cost basis tracking** - properly handles partial sells and re-buys
- Records full trade history (last 100 trades)
- Tracks best and worst trades ever (by % return)
- Compares performance vs S&P 500
- Persists to `portfolio_data.json` with atomic writes (crash-safe)
- Skips buy orders if balance is $0

### Personality

Stonkfish talks like an over-enthusiastic finance bro with **daily mood variations**:
- EXCESSIVE CAPS
- Rocket emojis 🚀
- "Diamond hands" 💎🙌
- "To the moon!"
- Always ecstatic, even when losing money

**Daily Moods** (changes each day for variety):
- 🚀🚀🚀 **ULTRA BULLISH** - Maximum optimism mode
- 💪😤 **ALPHA MODE** - Confident and aggressive
- 🎲🎰 **YOLO ENERGY** - Chaotic gambling vibes
- 📊📈 **CHART MASTER** - Technical analysis focus
- 🔥⚡ **ALL GAS NO BRAKES** - Pure adrenaline

Each day has a consistent mood that flavors all messages, giving personality variation without being random.

## Files

- `bot.py` - Main Discord bot with personality and scheduling
- `portfolio.py` - Portfolio management with cost basis and S&P tracking
- `trader.py` - Trading logic (random buy/sell/liquidation)
- `market_utils.py` - Stock data fetching and market hours/holiday checking
- `nyse_stocks.csv` - List of 500+ tradeable NYSE stocks (editable)
- `requirements.txt` - Python dependencies
- `.env` - Configuration (not committed to git)
- `portfolio_data.json` - Portfolio state (auto-generated, crash-safe)

## Troubleshooting

**Bot doesn't respond:**
- Verify bot token in `.env` is correct
- Check bot has permission to read/send messages in #Stonks channel
- Ensure "Message Content Intent" is enabled in Discord Developer Portal

**"Could not find channel" warning:**
- Create a channel with the name matching your `DISCORD_CHANNEL_NAME` in `.env` (default: "Stonks")
- Channel name matching is case-insensitive (Stonks = stonks = STONKS)
- Make sure there are no extra spaces or special characters in the channel name

**Trade errors:**
- Bot needs internet connection to fetch stock prices
- yfinance API may occasionally fail - trades will be skipped

**Bot not trading:**
- Only trades during market hours (9:30 AM - 4:00 PM ET)
- Only trades on NYSE trading days (Mon-Fri, excluding holidays)
- Check your system timezone is correct
- Respects all NYSE holidays:
  - New Year's Day
  - Martin Luther King Jr. Day
  - Presidents Day
  - Good Friday
  - Memorial Day
  - Juneteenth
  - Independence Day
  - Labor Day
  - Thanksgiving
  - Christmas

**Messages only appearing in one server:**
- This was a bug in earlier versions - now fixed!
- Bot broadcasts to ALL servers with a matching channel name

## Disclaimer

This is a **SIMULATION BOT** for entertainment purposes. It does not execute real trades or connect to any brokerage. All trades are fictional. This is not financial advice. Please don't actually trade like Stonkfish (random stock picking is a terrible strategy).

## License

MIT - Do whatever you want with it!
