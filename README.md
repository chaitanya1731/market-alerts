# Market alerts (SPY / QQQ)

A tiny, **free**, no-server-needed watcher that runs on **GitHub Actions** and
sends **Telegram** notifications:

- 🔻 **Drop alerts** — every time SPY or QQQ crosses a new *5% down* level on the
  day (−5%, −10%, −15%, …), measured against the previous close.
- 📊 **Daily trend** — one message after the close saying whether each symbol was
  **UP / DOWN / SIDEWAYS** today.

Everything is configurable and runs entirely on GitHub's free scheduled runners.

---

## One-time setup (~5 minutes)

### 1. Create a Telegram bot and get your chat ID

1. In Telegram, message **@BotFather**, send `/newbot`, follow the prompts.
   Copy the **bot token** it gives you (looks like `123456:ABC-DEF...`).
2. **Send any message to your new bot** (e.g. "hi") — this is required so it can
   message you back.
3. Get your chat ID: open this URL in a browser (paste your token):
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Look for `"chat":{"id":<NUMBER>` — that number is your **chat ID**.

### 2. Add them as GitHub repo secrets

In the repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name          | Value              |
| -------------------- | ------------------ |
| `TELEGRAM_BOT_TOKEN` | your bot token     |
| `TELEGRAM_CHAT_ID`   | your chat ID       |

### 3. Enable the workflow

Go to the **Actions** tab and enable workflows if prompted. Use **Run workflow**
on "Market alerts" to test it immediately (outside market hours it will just say
"nothing to do" — that's expected).

That's it. It now runs itself every 5 minutes during US market hours.

---

## Tuning

Edit the `env:` block in `.github/workflows/market-alerts.yml`:

- `SYMBOLS` — comma-separated tickers (default `SPY,QQQ`).
- `DROP_STEP_PCT` — alert on every N% of drop (default `5`). A 5% single-day drop
  is rare; set to `2` or `1` for more frequent alerts.
- `SIDEWAYS_PCT` — move smaller than this (%) counts as "sideways" (default `0.5`).

## Good to know

- **GitHub cron isn't exact** — scheduled runs can be delayed 5–20 min (rarely
  skipped) during high load. Fine for this; not real-time precision.
- **Free**: on a **public** repo, Actions minutes are unlimited. Data comes from
  Yahoo Finance via `yfinance` (no API key).
- **State** is kept in `state.json`, committed back only when something actually
  fires — so no commit spam.
