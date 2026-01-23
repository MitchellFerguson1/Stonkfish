import os
import random
from datetime import datetime

import discord
import pytz
from discord.ext import commands, tasks
from dotenv import load_dotenv

from market_utils import get_current_price, is_market_open
from portfolio import Portfolio
from trader import Trader, TradeResult

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_NAME = os.getenv('DISCORD_CHANNEL_NAME', 'Stonks')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize portfolio and trader
portfolio = Portfolio()
trader = Trader(portfolio)

# Track which events have been sent today to prevent duplicates
last_market_open_date = None
last_market_close_date = None


class FinanceBroPersonality:
    """Generate finance bro messages with daily mood variations"""

    MOODS = {
        'euphoric': {
            'emoji': '🚀🚀🚀',
            'vibe': 'ULTRA BULLISH',
        },
        'confident': {
            'emoji': '💪😤',
            'vibe': 'ALPHA MODE',
        },
        'chaotic': {
            'emoji': '🎲🎰',
            'vibe': 'YOLO ENERGY',
        },
        'technical': {
            'emoji': '📊📈',
            'vibe': 'CHART MASTER',
        },
        'aggressive': {
            'emoji': '🔥⚡',
            'vibe': 'ALL GAS NO BRAKES',
        },
        'grindset': {
            'emoji': '☕🏋️',
            'vibe': 'SIGMA GRINDSET',
        },
        'apex': {
            'emoji': '🦁👑',
            'vibe': 'APEX PREDATOR',
        },
    }

    @staticmethod
    def get_daily_mood() -> dict:
        """Get consistent mood for the day based on date"""
        today = datetime.now().date()
        mood_index = hash(str(today)) % len(FinanceBroPersonality.MOODS)
        mood_key = list(FinanceBroPersonality.MOODS.keys())[mood_index]
        return FinanceBroPersonality.MOODS[mood_key]

    @staticmethod
    def market_open_message(portfolio: Portfolio) -> str:
        """Generate market open message"""
        total_value = portfolio.get_total_value(get_current_price)
        pnl = total_value - 10000
        pnl_pct = (pnl / 10000) * 100
        mood = FinanceBroPersonality.get_daily_mood()

        intros = [
            f"LET'S GOOOOO! 🔔 {mood['emoji']}",
            f"RING THAT BELL BABY! 🔔 {mood['emoji']}",
            f"MARKETS ARE OPEN! 🚀 {mood['vibe']}!",
            f"TIME TO MAKE MONEY! 💰 {mood['vibe']}!",
            f"THE CASINO IS OPEN! 🎰 {mood['emoji']}",
            f"DING DING DING! 🔔 {mood['vibe']} ACTIVATED!",
            f"GOOD MORNING TRADERS! {mood['emoji']} READY TO DOMINATE!",
            f"WAKEY WAKEY! 🌅 {mood['vibe']} TIME!",
            f"IT'S GO TIME! ⏰ {mood['emoji']}",
            f"OPENING BELL! 🔔 {mood['vibe']} ENGAGED!",
            f"ANOTHER DAY ANOTHER DOLLAR! 💵 {mood['emoji']}",
            f"MARKET'S CALLING! 📞 {mood['vibe']} MODE ON!",
            f"STONK O'CLOCK! ⏰ {mood['emoji']}",
            f"CAPITALISM ACTIVATED! 🇺🇸 {mood['vibe']}!",
            f"TIME TO GET RICH! 💰 {mood['emoji']}",
            f"4AM WAKE UP PAID OFF! 🌅 {mood['emoji']} LET'S EAT!",
            f"COLD PLUNGE ✓ ESPRESSO ✓ MARKETS ✓ {mood['vibe']}!",
            f"3RD COFFEE AND WE'RE JUST GETTING STARTED! ☕ {mood['emoji']}",
            f"PRE-MARKET CARDIO DONE! 🏃 NOW THE REAL GAINS! {mood['emoji']}",
            f"BUILT DIFFERENT, INVEST DIFFERENT! 💪 {mood['vibe']}!",
            f"SCARED MONEY DON'T MAKE MONEY! {mood['emoji']} LET'S GO!",
            f"PATAGONIA VEST: ON. COFFEE: BLACK. GAINS: INCOMING. {mood['emoji']}",
        ]

        status_msgs = [
            f"Portfolio sitting at **${total_value:,.2f}**",
            f"We're holding **${total_value:,.2f}** right now",
            f"Currently at **${total_value:,.2f}**",
            f"Portfolio value: **${total_value:,.2f}**",
            f"The bag: **${total_value:,.2f}**",
            f"Net worth: **${total_value:,.2f}**",
            f"Stack size: **${total_value:,.2f}**",
            f"War chest: **${total_value:,.2f}**",
            f"Account balance: **${total_value:,.2f}**",
        ]

        pnl_msgs = []
        if pnl > 0:
            pnl_msgs = [
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 📈 GAINS BABY!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) WE'RE PRINTING MONEY!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 💎🙌 DIAMOND HANDS!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) TO THE MOON! 🚀",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 🤑 EASY MONEY!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 💰 STACKS ON STACKS!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 📈 WINNING!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 🔥 ON FIRE!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 💵 MONEY PRINTER GO BRRRR!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 🎯 CAN'T MISS!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 👑 KING MOVES!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 💪 UNSTOPPABLE!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 🔥 THEY CALLED US DUMB MONEY!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 📈 ANALYSTS IN SHAMBLES!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 💪 WHO SAID RETAIL CAN'T WIN?!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 🧊 COLD PLUNGE MENTALITY!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 😤 BEARS GET THE WOOD CHIPPER!",
                f"(+${pnl:,.2f} / +{pnl_pct:.1f}%) 🏆 MY SHARPE RATIO IS ELITE!",
            ]
        elif pnl < 0:
            pnl_msgs = [
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 📉 Just a dip bro!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) BUY THE DIP!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) It's called INVESTING!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) Temporary setback!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 📉 Building character!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🎢 What a ride!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 💪 Still standing!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🔮 Trust the process!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 📊 Temporary discount!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🎯 Comeback szn!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🌊 Riding the waves!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 💎 Pressure makes diamonds!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🧠 Tax loss harvesting baby!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 📈 Buffett didn't get rich in a day!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🏗️ Building generational wealth!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) ♟️ Playing 4D chess here!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🔴 RED MEANS BUY!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 💼 It's not a loss til you sell!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🎰 Scared money don't make money!",
                f"(-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🦁 Fortune favors the bold!",
            ]
        else:
            pnl_msgs = [
                "(±$0.00 / 0.0%) Perfectly balanced!",
                "(±$0.00 / 0.0%) Sideways trading baby!",
                "(±$0.00 / 0.0%) 📊 Theta gang!",
                "(±$0.00 / 0.0%) 🎯 Break even king!",
            ]

        cash_msgs = [
            f"Got **${portfolio.cash:,.2f}** cash ready to deploy!",
            f"**${portfolio.cash:,.2f}** in dry powder!",
            f"Sitting on **${portfolio.cash:,.2f}** cash!",
            f"**${portfolio.cash:,.2f}** burning a hole in my pocket!",
            f"**${portfolio.cash:,.2f}** locked and loaded!",
            f"Cash reserves: **${portfolio.cash:,.2f}**!",
            f"**${portfolio.cash:,.2f}** ready to YOLO!",
            f"Ammo: **${portfolio.cash:,.2f}**!",
            f"**${portfolio.cash:,.2f}** itching to be spent!",
            f"**${portfolio.cash:,.2f}** ready to risk it for the biscuit!",
            f"War chest: **${portfolio.cash:,.2f}**! Bears aren't ready!",
            f"**${portfolio.cash:,.2f}** cash - scared money stays home!",
        ]

        outros = [
            "Time to make some MOVES! 💪",
            "Let's GET IT! 🔥",
            "GAME TIME! 🎮",
            "SHOW ME THE MONEY! 💸",
            "LFG! 🚀",
            "NO DAYS OFF! 😤",
            "BUILT DIFFERENT! 💪",
            "Gym after close, gains all day! 🏋️",
            "Time to outperform these index fund cowards! 📈",
            "Warren Buffett wishes he had my alpha! 👴",
            "Not financial advice but... actually yes it is! 😤",
            "Few understand this! 🧠",
        ]

        return f"{random.choice(intros)}\n\n{random.choice(status_msgs)} {random.choice(pnl_msgs)}\n{random.choice(cash_msgs)}\n\n{random.choice(outros)}"

    @staticmethod
    def market_close_message(portfolio: Portfolio) -> str:
        """Generate market close message"""
        total_value = portfolio.get_total_value(get_current_price)
        pnl = total_value - 10000
        pnl_pct = (pnl / 10000) * 100
        mood = FinanceBroPersonality.get_daily_mood()

        todays_trades = portfolio.get_todays_trades()

        intros = [
            f"MARKET'S CLOSED! 🔔 {mood['emoji']}",
            f"BELL JUST RANG! 🔔 {mood['emoji']}",
            f"THAT'S A WRAP! 🎬 {mood['vibe']}!",
            f"AAAAND WE'RE DONE! ✅ {mood['emoji']}",
            f"CLOSING BELL BABY! 🔔 {mood['vibe']}!",
            f"DAY'S DONE! 🌆 {mood['emoji']}",
            f"MARKET CLOSED! 🚪 {mood['vibe']} COMPLETE!",
            f"THAT'S ALL FOLKS! 🎭 {mood['emoji']}",
            f"END OF DAY! ⏰ {mood['vibe']}!",
            f"LIGHTS OUT! 💡 {mood['emoji']}",
            f"BOOKS CLOSED! 📚 {mood['vibe']}!",
            f"SESSION COMPLETE! ✅ {mood['emoji']}",
            f"CASINO'S CLOSED! 🎰 TIME TO HIT THE GYM! {mood['emoji']}",
            f"FINAL BELL! 🔔 LEG DAY AWAITS! {mood['vibe']}!",
            f"DONE FOR TODAY! 💪 PROTEIN SHAKE TIME! {mood['emoji']}",
        ]

        # Trade summary
        buys = [t for t in todays_trades if t['action'] == 'BUY']
        sells = [t for t in todays_trades if t['action'] == 'SELL']

        trade_summary = f"Today's moves: **{len(buys)} buys**, **{len(sells)} sells**"

        # Recent trades (last 3)
        recent_trades = ""
        if todays_trades:
            recent_trades = "\n\n**Latest plays:**\n"
            for trade in todays_trades[-3:]:
                action = trade['action']
                ticker = trade['ticker']
                shares = trade['shares']
                price = trade['price']
                emoji = "📈" if action == "BUY" else "📉"
                recent_trades += f"{emoji} {action} {shares} shares of **${ticker}** @ ${price:.2f}\n"

        # Final status
        if pnl > 0:
            status_msgs = [
                f"Ending at **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 🚀\nWE'RE RICH!",
                f"Portfolio: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 💰\nCAN'T STOP WON'T STOP!",
                f"Closed at **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 📈\nSTONKS ONLY GO UP!",
                f"Final value: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 💎\nDIAMOND HANDS BABY!",
                f"EOD: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 🤑\nPRINTING MONEY!",
                f"Final tally: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 🔥\nCAN'T LOSE!",
                f"Day end: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 👑\nKING STATUS!",
                f"Close: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 💪\nTOO EASY!",
                f"Finishing: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 🎯\nNEVER IN DOUBT!",
                f"Done: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) ⚡\nBUILT DIFFERENT!",
                f"Final: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 😤\nTHEY CALLED US DUMB MONEY!",
                f"Closing: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 📉\nSHORTS ARE SWEATING!",
                f"EOD: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 🏆\nWHO NEEDS A FINANCE DEGREE?!",
                f"Done: **${total_value:,.2f}** (+${pnl:,.2f} / +{pnl_pct:.1f}%) 🦁\nFORTUNE FAVORED THE BOLD!",
            ]
        elif pnl < 0:
            status_msgs = [
                f"Ending at **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 📉\nJust a speed bump!",
                f"Portfolio: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🎢\nWhat goes down must go up!",
                f"Closed at **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 💼\nIt's called CHARACTER BUILDING!",
                f"Final value: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🎯\nTomorrow we MOON!",
                f"EOD: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 💪\nStill here baby!",
                f"Close: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🔮\nLong term play!",
                f"Finishing: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🌊\nRough seas!",
                f"Done: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🎲\nCan't win em all!",
                f"Day end: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 💎\nPressure makes diamonds!",
                f"Final: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🏋️\nGetting stronger!",
                f"EOD: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🧠\nTax loss harvesting SZN!",
                f"Close: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) ♟️\nPlaying 4D chess!",
                f"Final: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🏗️\nBuilding generational wealth!",
                f"Done: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 👴\nBuffett had red days too!",
                f"Ending: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 🔴\nRed means OPPORTUNITY!",
                f"EOD: **${total_value:,.2f}** (-${abs(pnl):,.2f} / {pnl_pct:.1f}%) 💼\nNot a loss til you sell!",
            ]
        else:
            status_msgs = [
                f"Ending at **${total_value:,.2f}** (±$0.00 / 0.0%) 📊\nSideways action!",
                f"Closed at **${total_value:,.2f}** (±$0.00 / 0.0%) ⚖️\nPerfectly balanced!",
                f"Final: **${total_value:,.2f}** (±$0.00 / 0.0%) 🎯\nFlat is the new up!",
            ]

        # S&P 500 comparison
        sp500_comparison = ""
        comparison = portfolio.get_sp500_comparison(get_current_price)
        if comparison:
            diff = comparison['difference']
            if comparison['beating_market']:
                sp500_msgs = [
                    f"\n\n📊 **vs S&P 500:** Me: +{pnl_pct:.1f}% | SPY: +{comparison['sp500_pnl_pct']:.1f}% | **CRUSHING IT by {diff:.1f}%!** 💪",
                    f"\n\n📊 **vs S&P 500:** Beating the market by **{diff:.1f}%**! Index funds are for COWARDS! 🚀",
                    f"\n\n📊 **vs S&P 500:** Up {diff:.1f}% vs the index! WHO NEEDS DIVERSIFICATION?! 🔥",
                    f"\n\n📊 **vs S&P 500:** Market +{comparison['sp500_pnl_pct']:.1f}%, me +{pnl_pct:.1f}%! **DIFFERENT BREED!** 💎",
                    f"\n\n📊 **vs S&P 500:** +{diff:.1f}% ALPHA! Warren Buffett wishes he had my returns! 👴",
                    f"\n\n📊 **vs S&P 500:** Outperforming by {diff:.1f}%! My Sharpe ratio is ELITE! 📈",
                    f"\n\n📊 **vs S&P 500:** SPY who?! Up {diff:.1f}% vs the boomers! 😤",
                ]
            elif diff < 0:
                sp500_msgs = [
                    f"\n\n📊 **vs S&P 500:** Me: {pnl_pct:+.1f}% | SPY: +{comparison['sp500_pnl_pct']:.1f}% | Down {abs(diff):.1f}% vs market... BUILDING CHARACTER! 💪",
                    f"\n\n📊 **vs S&P 500:** Trailing the market by {abs(diff):.1f}%... It's called TAKING RISKS! 🎲",
                    f"\n\n📊 **vs S&P 500:** Behind by {abs(diff):.1f}% but we're LEARNING! Index funds are boring anyway! 😤",
                    f"\n\n📊 **vs S&P 500:** SPY +{comparison['sp500_pnl_pct']:.1f}%, me {pnl_pct:+.1f}%... TEMPORARY SETBACK! 🔮",
                    f"\n\n📊 **vs S&P 500:** Down {abs(diff):.1f}% vs index... Playing 4D chess here! ♟️",
                    f"\n\n📊 **vs S&P 500:** -{abs(diff):.1f}% vs SPY... Tax loss harvesting is a STRATEGY! 🧠",
                    f"\n\n📊 **vs S&P 500:** Trailing by {abs(diff):.1f}%... Buffett had bad years too! 👴",
                ]
            else:
                sp500_msgs = [f"\n\n📊 **vs S&P 500:** Perfectly matched! Both at {pnl_pct:+.1f}%! ⚖️"]
            sp500_comparison = random.choice(sp500_msgs)

        outros = [
            "Same time tomorrow! 😤",
            "Rest up, we trade again tomorrow! 💪",
            "Time to hit the gym and count money! 💰",
            "See you at the opening bell! 🔔",
            "Back at it tomorrow! 🔥",
            "Sleep is for the weak! 😴 jk see ya!",
            "Time to review the tape! 📹",
            "Gotta prepare for tomorrow's plays! 🎯",
            "Off to the Lambo dealership! 🏎️",
            "Another day in paradise! 🌴",
            "Time to celebrate! 🍾 Or cry! Either way!",
            "Markets never sleep, but I do! 💤",
            "Leg day then steak dinner! 🥩🏋️",
            "Cold plunge and chill! 🧊",
            "Time to network at the golf course! ⛳",
            "Protein shake and chart analysis! 📊💪",
            "4AM alarm already set! NO DAYS OFF! ⏰",
            "Time to update the spreadsheet and hit legs! 📈🦵",
            "Off to tell people about my portfolio! 🗣️",
        ]

        return f"{random.choice(intros)}\n\n{trade_summary}{recent_trades}\n\n{random.choice(status_msgs)}{sp500_comparison}\n\n{random.choice(outros)}"

    @staticmethod
    def trade_message(result: TradeResult) -> str:
        """Generate message for a trade"""
        mood = FinanceBroPersonality.get_daily_mood()

        if not result.success or result.action == 'SKIP':
            skip_msgs = [
                f"Wanted to make a move but {result.reason.lower()}... 🤷 {mood['emoji']}",
                f"Had to skip this one - {result.reason.lower()} 😤",
                f"No action this hour - {result.reason.lower()} 💤",
                f"Sitting this one out - {result.reason.lower()} 🪑",
                f"Taking a breather - {result.reason.lower()} 😮‍💨",
                f"Patience is key - {result.reason.lower()} ⏰",
                f"Not this time - {result.reason.lower()} 🙅",
                f"Skipping - {result.reason.lower()} ⏭️",
                f"Even alphas rest sometimes - {result.reason.lower()} 🦁",
                f"Strategic pause - {result.reason.lower()} ♟️",
                f"Discipline over impulse - {result.reason.lower()} 🧠",
            ]
            return random.choice(skip_msgs)

        if result.action == 'LIQUIDATION':
            liquidation_msgs = [
                f"🚨 **EMERGENCY LIQUIDATION!** 🚨\nSOLD EVERYTHING! {result.ticker}!\nCashed out ${result.total:,.2f}!\nIT'S ALL CASH NOW BABY! 💵💵💵",
                f"🔥 **YOLO MOMENT!** 🔥\nGUT FEELING SAID SELL IT ALL!\n{result.ticker} LIQUIDATED!\n${result.total:,.2f} IN THE BANK! 🏦",
                f"⚡ **SPONTANEOUS DECISION!** ⚡\nDUMPED THE WHOLE PORTFOLIO!\n{result.ticker} → GONE!\n${result.total:,.2f} CASH SECURED! {mood['emoji']}",
                f"🎲 **CHAOS MODE ACTIVATED!** 🎲\nSOLD ABSOLUTELY EVERYTHING!\n{result.ticker} LIQUIDATED!\n${result.total:,.2f} TO PLAY WITH NOW! 💰",
                f"💣 **NUCLEAR OPTION!** 💣\nCLEARED THE ENTIRE PORTFOLIO!\n{result.ticker} → ALL CASH!\n${result.total:,.2f} READY TO DEPLOY! 🚀",
                f"🌪️ **TOTAL RESET!** 🌪️\nLIQUIDATED EVERYTHING ON A WHIM!\n{result.ticker} SOLD!\n${result.total:,.2f} BURNING A HOLE IN MY POCKET! {mood['emoji']}",
                f"🧊 **COLD PLUNGE CLARITY!** 🧊\nSAW THE LIGHT! SOLD IT ALL!\n{result.ticker} GONE!\n${result.total:,.2f} CASH! FEELING ALIVE! 💪",
                f"☕ **4TH ESPRESSO HIT DIFFERENT!** ☕\nLIQUIDATED THE WHOLE THING!\n{result.ticker} → CASH!\n${result.total:,.2f} READY FOR THE NEXT PLAY! {mood['emoji']}",
                f"🏋️ **POST-GYM ENERGY!** 🏋️\nFELT STRONG, SOLD EVERYTHING!\n{result.ticker} LIQUIDATED!\n${result.total:,.2f} CASH GANG! 💵",
            ]
            return random.choice(liquidation_msgs)

        if result.action == 'BUY':
            buy_msgs = [
                f"JUST BOUGHT {result.shares} SHARES OF **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 📈\nTO THE MOON! 🚀",
                f"LOADING UP! {result.shares} shares of **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 💰\nThis is gonna PRINT! 🖨️",
                f"YOLO'D ${result.total:,.2f} INTO **${result.ticker}**! {result.shares} shares @ ${result.price:.2f} 📈\nCAN'T LOSE! 💎🙌",
                f"BOUGHT THE DIP! {result.shares} shares of **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🎯\nEasy money! 💵",
                f"ALL IN! Well, ${result.total:,.2f} in **${result.ticker}**! {result.shares} shares @ ${result.price:.2f} 🚀\nLFG! 🔥",
                f"SCOOPED UP {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) {mood['emoji']}\n{mood['vibe']}! 💪",
                f"GOING LONG! {result.shares} shares **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 📈\nBULLISH! 🐂",
                f"ENTERED **${result.ticker}**! {result.shares} shares @ ${result.price:.2f}! (${result.total:,.2f}) 🎯\nPerfect entry! 👌",
                f"BIG MOVE! Grabbed {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) {mood['emoji']}\nThis one's special! ⭐",
                f"ACCUMULATING! {result.shares} shares of **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 💼\nBuilding a position! 🏗️",
                f"IN WE GO! {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🎢\nRide or die! 😤",
                f"DEPLOYED ${result.total:,.2f} INTO **${result.ticker}**! {result.shares} shares @ ${result.price:.2f} {mood['emoji']}\nStrategic buy! 🎯",
                f"SNAPPED UP {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) ⚡\nQuick trigger! 🔫",
                f"CONVICTION PLAY! {result.shares} shares **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 💪\nI believe! 🙏",
                f"COULDN'T RESIST! {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) {mood['emoji']}\nToo good to pass! 🤤",
                f"SCARED MONEY DON'T MAKE MONEY! {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🦁\nFortune favors the bold!",
                f"FEW UNDERSTAND THIS! {result.shares} shares **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🧠\nWe're so early!",
                f"RISK IT FOR THE BISCUIT! {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🎰\nNo risk no reward!",
                f"ALPHA MOVE! {result.shares} shares **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 😤\nBuilt different!",
            ]
            return random.choice(buy_msgs)
        else:  # SELL
            sell_msgs = [
                f"TOOK PROFITS! Sold {result.shares} shares of **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 💰\nCASH IS KING! 👑",
                f"DUMPED {result.shares} shares of **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 📉\nOn to the next one! 🎯",
                f"SECURED THE BAG! {result.shares} shares of **${result.ticker}** @ ${result.price:.2f} = ${result.total:,.2f}! 💼\nProfit is profit! 🤑",
                f"CASHED OUT! Sold {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🏦\nGotta lock in gains! 🔒",
                f"EXIT STRATEGY! {result.shares} shares of **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 📊\nLiving to trade another day! 😎",
                f"LIQUIDATED! {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) {mood['emoji']}\nCash gang! 💵",
                f"TRIMMED THE POSITION! Sold {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) ✂️\nTaking some off! 📉",
                f"PROFIT TAKING! {result.shares} shares **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 💸\nBank it! 🏦",
                f"OUT! Dumped {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) {mood['emoji']}\nMoving on! 🚀",
                f"SOLD! {result.shares} shares **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 💰\nRing the register! 🛎️",
                f"FLIPPED! {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🔄\nQuick flip! ⚡",
                f"TOOK THE WIN! Sold {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) {mood['emoji']}\nW in the books! ✅",
                f"CLOSED **${result.ticker}**! {result.shares} shares @ ${result.price:.2f}! (${result.total:,.2f}) 🚪\nPosition closed! 🔒",
                f"ESCAPED! {result.shares} shares **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🏃\nGot out! 😅",
                f"BANKED ${result.total:,.2f}! Sold {result.shares} **${result.ticker}** @ ${result.price:.2f} {mood['emoji']}\nCha-ching! 💵",
                f"REALIZED GAINS! {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🏆\nWinners take profits!",
                f"ROTATED OUT! Sold {result.shares} **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 🔄\nAlways moving!",
                f"BOOKING IT! {result.shares} shares **${result.ticker}** @ ${result.price:.2f}! (${result.total:,.2f}) 📚\nLocked and loaded for the next play!",
            ]
            return random.choice(sell_msgs)


personality = FinanceBroPersonality()


async def get_stonks_channels():
    """
    Get ALL Stonks channels across all servers (case-insensitive)
    Matches any variation: Stonks, stonks, STONKS, StOnKs, etc.
    Returns a list of all matching channels across all guilds.
    """
    channels = []
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name.lower() == CHANNEL_NAME.lower():
                channels.append(channel)
    return channels


def is_stonks_channel(channel_name: str) -> bool:
    """
    Check if a channel name matches the Stonks channel (case-insensitive)
    """
    return channel_name.lower() == CHANNEL_NAME.lower()


@tasks.loop(minutes=1)
async def check_market_events():
    """Check for market open, close, and hourly trades"""
    global last_market_open_date, last_market_close_date

    try:
        et_tz = pytz.timezone('America/New_York')
        now_et = datetime.now(et_tz)
        current_time = now_et.time()
        today = now_et.date()

        # Get all stonks channels across all servers
        channels = await get_stonks_channels()
        if not channels:
            return

        # Check if it's a trading day (weekday, not holiday)
        # We need this separate check for market close messages
        if now_et.weekday() > 4:  # Weekend
            return

        from market_utils import get_nyse_holidays
        holidays = get_nyse_holidays(now_et.year)
        if today in holidays:
            return

        # Market open (9:30 AM) - SEND MESSAGE ONCE PER DAY
        if current_time.hour == 9 and current_time.minute == 30:
            if last_market_open_date != today:
                message = personality.market_open_message(portfolio)
                for channel in channels:
                    sent_message = await channel.send(message)
                    # Add reactions (50% chance each)
                    if random.random() < 0.5:
                        await sent_message.add_reaction('🚀')
                    if random.random() < 0.5:
                        await sent_message.add_reaction('💰')
                last_market_open_date = today

        # Market close (4:00 PM) - SEND MESSAGE ONCE PER DAY
        # Check this even if market is "closed" to avoid timing bug
        elif current_time.hour == 16 and current_time.minute == 0:
            if last_market_close_date != today:
                message = personality.market_close_message(portfolio)
                for channel in channels:
                    sent_message = await channel.send(message)
                    # Add reactions based on performance
                    total_value = portfolio.get_total_value(get_current_price)
                    pnl = total_value - 10000

                    if pnl > 0:
                        # Positive day
                        if random.random() < 0.6:
                            await sent_message.add_reaction('📈')
                        if random.random() < 0.4:
                            await sent_message.add_reaction('💎')
                    elif pnl < 0:
                        # Negative day
                        if random.random() < 0.6:
                            await sent_message.add_reaction('📉')
                        if random.random() < 0.4:
                            await sent_message.add_reaction('💪')
                    else:
                        # Flat day
                        if random.random() < 0.5:
                            await sent_message.add_reaction('⚖️')
                last_market_close_date = today

        # Hourly trades (on the hour, during market hours) - SILENT, NO MESSAGE
        # Only execute if market is actually open
        # EXCEPTION: Liquidation events are announced because they're CHAOS
        elif current_time.minute == 0 and 10 <= current_time.hour <= 15:
            if is_market_open():
                result = trader.execute_random_trade()
                # Announce LIQUIDATION events (rare chaos)
                if result.success and result.action == 'LIQUIDATION':
                    message = personality.trade_message(result)
                    for channel in channels:
                        sent_message = await channel.send(message)
                        # Add chaos emoji reactions
                        if random.random() < 0.8:  # 80% chance
                            await sent_message.add_reaction('🔥')
                        if random.random() < 0.8:
                            await sent_message.add_reaction('💀')
                        if random.random() < 0.8:
                            await sent_message.add_reaction('🎲')
                # All other trades are silent

    except Exception as e:
        print(f"Error in check_market_events: {e}")
        # Continue running - don't let one error stop the loop


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Looking for channel: {CHANNEL_NAME}')

    channels = await get_stonks_channels()
    if channels:
        print(f'Found {len(channels)} channel(s):')
        for channel in channels:
            print(f'  - {channel.name} in {channel.guild.name}')
    else:
        print(f'WARNING: Could not find any channels named "{CHANNEL_NAME}"')

    # Initialize S&P 500 baseline if not already set
    portfolio.initialize_sp500_baseline(get_current_price)

    # Start the market event checker
    if not check_market_events.is_running():
        check_market_events.start()


@bot.command(name='portfolio')
async def show_portfolio(ctx):
    """Show current portfolio"""
    if not is_stonks_channel(ctx.channel.name):
        return

    try:
        total_value = portfolio.get_total_value(get_current_price)
        pnl = total_value - 10000
        pnl_pct = (pnl / 10000) * 100

        message = "**💼 PORTFOLIO STATUS 💼**\n\n"
        message += f"Total Value: **${total_value:,.2f}**\n"
        message += f"P&L: **${pnl:+,.2f}** ({pnl_pct:+.2f}%)\n"
        message += f"Cash: **${portfolio.cash:,.2f}**\n\n"

        if portfolio.holdings:
            message += "**Holdings:**\n"
            holdings = portfolio.get_holdings_summary(get_current_price)
            for holding in holdings[:10]:  # Top 10
                message += f"• **{holding['ticker']}**: {holding['shares']} shares @ ${holding['price']:.2f} = ${holding['value']:,.2f}\n"
        else:
            message += "No holdings - ALL CASH BABY! 💵\n"

        await ctx.send(message)
    except Exception as e:
        print(f"Error in portfolio command: {e}")
        await ctx.send("Error fetching portfolio data. Try again later! 📊")


@bot.command(name='stonks')
async def show_detailed_stonks(ctx):
    """Show detailed stock-by-stock breakdown with P&L"""
    if not is_stonks_channel(ctx.channel.name):
        return

    try:
        mood = FinanceBroPersonality.get_daily_mood()
        positions = portfolio.get_position_details(get_current_price)

        if not positions:
            await ctx.send(f"No positions! 💸 ALL CASH BABY! {mood['emoji']}")
            return

        total_value = portfolio.get_total_value(get_current_price)
        total_invested = sum(p['cost_basis'] for p in positions)
        total_pnl = sum(p['pnl'] for p in positions)

        message = "**📊 DETAILED STONKS BREAKDOWN 📊**\n"
        message += f"**{mood['vibe']}** vibes today! {mood['emoji']}\n\n"

        # Winners and losers
        winners = [p for p in positions if p['pnl'] > 0]
        losers = [p for p in positions if p['pnl'] < 0]
        flat = [p for p in positions if p['pnl'] == 0]

        message += f"**Summary:** {len(winners)}W / {len(losers)}L / {len(flat)}⚖️\n"
        message += f"**Total Invested:** ${total_invested:,.2f}\n"
        message += f"**Current Value:** ${total_value:,.2f}\n"
        message += f"**Overall P&L:** ${total_pnl:+,.2f}\n\n"

        # Show top positions (up to 15)
        message += "**Positions:**\n"
        for pos in positions[:15]:
            ticker = pos['ticker']
            shares = pos['shares']
            avg_cost = pos['avg_cost']
            current = pos['current_price']
            pnl = pos['pnl']
            pnl_pct = pos['pnl_pct']

            # Emoji based on P&L
            if pnl > 0:
                emoji = "📈" if pnl_pct > 10 else "✅"
                vibe = random.choice(["WINNER!", "GAINS!", "UP!", "MOON!", "🚀"])
            elif pnl < 0:
                emoji = "📉" if pnl_pct < -10 else "❌"
                vibe = random.choice(["DIP!", "HODL!", "DOWN!", "BUY MORE!", "💎🙌"])
            else:
                emoji = "⚖️"
                vibe = "FLAT!"

            message += f"{emoji} **{ticker}**: {shares} @ ${avg_cost:.2f} → ${current:.2f} | "
            message += f"${pnl:+,.2f} ({pnl_pct:+.1f}%) {vibe}\n"

        if len(positions) > 15:
            message += f"\n...and {len(positions) - 15} more positions!"

        # Add some personality
        if total_pnl > 100:
            message += f"\n\n💰 **PORTFOLIO IS PRINTING!** {mood['emoji']}"
        elif total_pnl < -100:
            message += f"\n\n💎 **DIAMOND HANDS ACTIVATED!** {mood['emoji']}"
        else:
            message += f"\n\n📊 **STABLE GENIUS!** {mood['emoji']}"

        await ctx.send(message)
    except Exception as e:
        print(f"Error in stonks command: {e}")
        await ctx.send("Error fetching detailed stonks data. Try again later! 📉")


@bot.command(name='history')
async def show_history(ctx):
    """Show recent trade history"""
    if not is_stonks_channel(ctx.channel.name):
        return

    try:
        mood = FinanceBroPersonality.get_daily_mood()
        trades = portfolio.trade_history[-10:]  # Last 10 trades

        if not trades:
            await ctx.send(f"No trades yet! Still waiting for the perfect entry! 😤 {mood['emoji']}")
            return

        message = "**📜 RECENT TRADE HISTORY 📜**\n"
        message += f"**{mood['vibe']}** energy! {mood['emoji']}\n\n"

        for trade in reversed(trades):
            action = trade['action']
            ticker = trade['ticker']
            shares = trade['shares']
            price = trade['price']
            total = trade['total']
            timestamp = datetime.fromisoformat(trade['timestamp'])
            time_str = timestamp.strftime("%m/%d %I:%M %p")

            emoji = "📈" if action == "BUY" else "📉"
            message += f"{emoji} **{time_str}** - {action} {shares} **{ticker}** @ ${price:.2f} (${total:,.2f})\n"

        # Best/Worst trades
        if portfolio.best_trade or portfolio.worst_trade:
            message += "\n**🏆 HALL OF FAME/SHAME 🏆**\n"

            if portfolio.best_trade:
                bt = portfolio.best_trade
                message += f"✅ **BEST:** {bt['shares']} {bt['ticker']} @ ${bt['buy_price']:.2f} → ${bt['sell_price']:.2f} "
                message += f"(**+{bt['pnl_pct']:.1f}%**) 🚀\n"

            if portfolio.worst_trade:
                wt = portfolio.worst_trade
                message += f"❌ **WORST:** {wt['shares']} {wt['ticker']} @ ${wt['buy_price']:.2f} → ${wt['sell_price']:.2f} "
                message += f"(**{wt['pnl_pct']:.1f}%**) 💀\n"

        await ctx.send(message)
    except Exception as e:
        print(f"Error in history command: {e}")
        await ctx.send("Error fetching trade history. Try again later! 📜")


@bot.command(name='reset')
async def reset_portfolio(ctx):
    """Reset portfolio to starting state (admin only)"""
    if not is_stonks_channel(ctx.channel.name):
        return

    try:
        portfolio.reset()
        await ctx.send("Portfolio reset to $10,000! LET'S RUN IT BACK! 🔄")
    except Exception as e:
        print(f"Error in reset command: {e}")
        await ctx.send("Error resetting portfolio. Something went wrong! ❌")


# Remove default help command to use our custom one
bot.remove_command('help')


@bot.command(name='help')
async def show_help(ctx):
    """Show available commands"""
    if not is_stonks_channel(ctx.channel.name):
        return

    mood = FinanceBroPersonality.get_daily_mood()

    message = f"**📈 STONKFISH COMMANDS 📈** {mood['emoji']}\n\n"
    message += "**!portfolio** - View total portfolio value, P&L, and holdings summary\n"
    message += "**!stonks** - Detailed breakdown of every position with individual P&L\n"
    message += "**!history** - Recent trade history + best/worst trades\n"
    message += "**!reset** - Reset portfolio to $10,000 starting cash\n"
    message += "**!help** - Show this message\n\n"
    message += f"**{mood['vibe']}!** LET'S GET THIS BREAD! 🍞💰"

    await ctx.send(message)




if __name__ == '__main__':
    if not TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN not found in .env file!")
        exit(1)

    bot.run(TOKEN)
