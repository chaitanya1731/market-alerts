#!/usr/bin/env python3
"""Notify on intraday drops in SPY/QQQ and report the daily trend.

Designed to run on GitHub Actions on a schedule. Each invocation:
  * while the US market is open, checks whether each symbol has crossed a
    new N% drop step vs the previous close and sends a Telegram alert for
    each newly-crossed step (default step = 5%, so -5%, -10%, ...)
  * once, after the market closes, sends a daily up/down/sideways trend

State is kept in state.json so each alert fires at most once per day.
"""
import json
import os
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yfinance as yf

ET = ZoneInfo("America/New_York")
STATE_FILE = Path(__file__).with_name("state.json")

SYMBOLS = [s.strip().upper() for s in os.getenv("SYMBOLS", "SPY,QQQ").split(",") if s.strip()]
DROP_STEP_PCT = float(os.getenv("DROP_STEP_PCT", "5"))   # alert every N% of drop
SIDEWAYS_PCT = float(os.getenv("SIDEWAYS_PCT", "0.5"))   # |move| below this = sideways
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)


def send(text: str) -> None:
    """Send a Telegram message."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=30,
    )
    resp.raise_for_status()


def load_state(today: str) -> dict:
    """Load today's state, or a fresh one if it's a new day / missing."""
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        if state.get("date") == today:
            return state
    return {"date": today, "steps": {}, "trend_sent": False}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def get_quote(sym: str, today):
    """Return (last_price, prev_close) if sym actually trades today, else None.

    Returning None naturally handles weekends, holidays and the pre-open
    window, because there is no intraday data stamped with today's date.
    """
    t = yf.Ticker(sym)
    intraday = t.history(period="1d", interval="1m")
    if intraday.empty:
        return None
    ts = intraday.index[-1]
    ts = ts.tz_convert(ET) if ts.tzinfo else ts
    if ts.date() != today:
        return None  # latest data is from a previous session -> not trading today
    last = float(intraday["Close"].iloc[-1])

    daily = t.history(period="5d", interval="1d")
    if len(daily) < 2:
        return None
    prev_close = float(daily["Close"].iloc[-2])
    return last, prev_close


def main() -> None:
    now = datetime.now(ET)
    today = now.date()
    state = load_state(today.isoformat())

    quotes = {}
    for sym in SYMBOLS:
        q = get_quote(sym, today)
        if q is not None:
            quotes[sym] = q

    if not quotes:
        print("No trading data for today (weekend/holiday/pre-open) - nothing to do.")
        return

    changed = False

    # --- intraday drop alerts (only while the market is open) ---
    if MARKET_OPEN <= now.time() < MARKET_CLOSE:
        for sym, (last, prev) in quotes.items():
            pct = (last - prev) / prev * 100.0
            drop = -pct  # positive when the symbol is down on the day
            step = int(drop // DROP_STEP_PCT)  # 0, 1, 2, ...  each = DROP_STEP_PCT%
            if step > state["steps"].get(sym, 0):
                send(
                    f"\U0001F53B <b>{sym} down {drop:.1f}%</b> today\n"
                    f"Price ${last:,.2f} (prev close ${prev:,.2f})\n"
                    f"Crossed the -{step * DROP_STEP_PCT:.0f}% level."
                )
                state["steps"][sym] = step
                changed = True

    # --- daily trend, sent once after the close ---
    if now.time() >= MARKET_CLOSE and not state["trend_sent"]:
        lines = ["\U0001F4CA <b>Daily trend</b>"]
        for sym, (last, prev) in quotes.items():
            pct = (last - prev) / prev * 100.0
            if pct > SIDEWAYS_PCT:
                arrow, word = "\U0001F7E2", "UP"
            elif pct < -SIDEWAYS_PCT:
                arrow, word = "\U0001F534", "DOWN"
            else:
                arrow, word = "⚪", "SIDEWAYS"
            lines.append(f"{arrow} {sym}: {word} ({pct:+.2f}%)  ${last:,.2f}")
        send("\n".join(lines))
        state["trend_sent"] = True
        changed = True

    if changed:
        save_state(state)
        print("State updated.")
    else:
        print("No new alerts.")


if __name__ == "__main__":
    main()
