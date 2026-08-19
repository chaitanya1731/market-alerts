# Market alerts (SPY / QQQ)

A tiny, **free**, no-server-needed watcher that runs on **GitHub Actions** and
sends **Telegram** notifications:

- 🔻 **Drop alerts** — every time SPY or QQQ crosses a new *2% down* level on the
  day (−2%, −4%, −6%, …), measured against the previous close.
- 🌅 **Morning AI summary** — ~15 minutes after the open, an AI-written 3–4
  sentence read on the day's early trend and likely drivers (via Google Gemini's
  free tier). Optional — skipped automatically if you don't add a key.
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

### 3. (Optional) Enable the morning AI summary

1. Go to **https://aistudio.google.com/apikey**, sign in, and click
   **Create API key** — it's free (Gemini free tier).
2. Add it as one more repo secret:

   | Secret name      | Value                |
   | ---------------- | -------------------- |
   | `GEMINI_API_KEY` | your Gemini API key  |

If you skip this, everything else still works — the morning summary is just
silently skipped. To change the model, set a `GEMINI_MODEL` env var in the
workflow (default `gemini-flash-latest`).

### 4. Enable the workflow

Go to the **Actions** tab and enable workflows if prompted. Use **Run workflow**
on "Market alerts" to test it immediately (outside market hours it will just say
"nothing to do" — that's expected).

That's it. It now runs itself every 15 minutes during US market hours. Note this
is just the *check* interval — you only get a message when a new drop level is
crossed (or the once-daily summary / trend), never a message every run.

---

## Tuning

Edit the `env:` block in `.github/workflows/market-alerts.yml`:

- `SYMBOLS` — comma-separated tickers (default `SPY,QQQ`).
- `DROP_STEP_PCT` — alert on every N% of drop (currently set to `2`, so −2%, −4%,
  …). A 5% single-day drop is rare; `2` or `1` gives more frequent alerts.
- `SIDEWAYS_PCT` — move smaller than this (%) counts as "sideways" (default `0.5`).
- `GEMINI_MODEL` — Gemini model for the morning summary (default `gemini-flash-latest`).

## Good to know

- **GitHub cron isn't exact** — scheduled runs can be delayed 5–20 min (rarely
  skipped) during high load. Fine for this; not real-time precision.
- **Free**: on a **public** repo, Actions minutes are unlimited. Data comes from
  Yahoo Finance via `yfinance` (no API key).
- **State** is kept in `state.json`, committed back only when something actually
  fires — so no commit spam.
