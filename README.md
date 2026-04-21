# trade_b0t_mk1

A paper trading bot built from scratch using ML techniques from Georgia Tech's CS 7646 (Machine Learning for Trading). Runs two parallel strategies on Alpaca paper money across NVDA, MSFT, and SPY — one executes real trades, one runs in shadow mode for comparison.

---

## Strategies

### Manual Strategy (executes real trades)
A 2-of-3 indicator voting system using Bollinger Band %B (20-day), 14-day Momentum, and 14-day RSI. Each indicator votes +1 (oversold/long), -1 (overbought/short), or 0. A position is only taken when at least 2 of 3 agree. Proven to generalize out-of-sample in the original ML4T report.

### Strategy Learner (shadow mode — no real orders)
A BagLearner of 20 Random Trees trained on the same three indicators. Labels are generated from 5-day forward returns with market impact cost baked in. Signals are logged to Supabase daily alongside the Manual Strategy for long-term comparison. Retrains every 2 months on a rolling 2-year window.

---

## Architecture

```
Mac (launchd, 3:50 PM ET Mon–Fri)
│
├── Fetch closing prices       ← Alpaca Historical API
├── Compute BB%B, Momentum, RSI
├── Manual Strategy → signal   → place orders (Alpaca Paper)
├── Strategy Learner → signal  → log only (shadow)
├── Log everything             → Supabase
└── Send daily email           → Gmail SMTP
│
Supabase (PostgreSQL)          Vercel (Next.js Dashboard)
└── signals                    └── dashboard-nine-virid-85.vercel.app
└── trades
└── portfolio_snapshots
└── daily_performance
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Bot runtime | Python 3.10, conda env `trade_b0t` |
| Trading API | `alpaca-py` (paper trading) |
| Historical data | Alpaca Historical API |
| ML model | Custom BagLearner + RTLearner (ported from ML4T) |
| Scheduler | macOS `launchd` + `pmset` scheduled wake |
| Database | Supabase (PostgreSQL) |
| Email | Gmail SMTP (App Password) |
| Dashboard | Next.js 16, deployed on Vercel |

---

## Project Structure

```
trade_b0t_mk1/
├── bot/
│   ├── learners/
│   │   ├── RTLearner.py         # Random tree (ported from ML4T)
│   │   └── BagLearner.py        # 20-bag ensemble
│   ├── indicators.py            # BB%B, Momentum, RSI
│   ├── manual_strategy.py       # 2/3 voting → ±1/0 signal
│   ├── strategy_learner.py      # BagLearner train + predict per symbol
│   ├── data_feed.py             # Alpaca historical OHLCV fetcher
│   ├── portfolio.py             # Position sizing, order placement
│   ├── executor.py              # Daily trade cycle entry point
│   ├── trainer.py               # Bimonthly retraining entry point
│   ├── reporter.py              # Daily HTML email via Gmail SMTP
│   ├── db.py                    # Supabase insert helpers
│   └── scheduler.py             # APScheduler (alternative to launchd)
├── models/
│   ├── NVDA_model.pkl
│   ├── MSFT_model.pkl
│   └── SPY_model.pkl
├── dashboard/                   # Next.js dashboard (Vercel)
│   ├── app/
│   │   ├── page.tsx             # Overview: portfolio value, positions, signals
│   │   ├── signals/page.tsx     # Full indicator history by day
│   │   ├── race/page.tsx        # Manual vs ML strategy comparison chart
│   │   └── trades/page.tsx      # Trade log
│   ├── components/
│   │   ├── PortfolioChart.tsx
│   │   ├── StrategyRaceChart.tsx
│   │   ├── SignalBadge.tsx
│   │   ├── StatTile.tsx
│   │   └── Card.tsx
│   └── lib/
│       └── supabase.ts
├── logs/
│   ├── daily.log                # stdout from each daily run
│   └── daily_error.log          # stderr (errors)
├── .env                         # API keys (never commit this)
├── .env.example                 # Template for new setups
└── requirements.txt
```

---

## Setup

### 1. Prerequisites
- macOS (for launchd + pmset scheduling)
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- [Alpaca paper trading account](https://alpaca.markets)
- [Supabase account](https://supabase.com)
- Gmail account with 2FA enabled

### 2. Clone and create conda env
```bash
git clone <your-repo-url>
cd trade_b0t_mk1
conda create -n trade_b0t python=3.10
conda activate trade_b0t
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Fill in all values in .env — see .env.example for reference
```

Required variables:
| Variable | Where to find it |
|----------|-----------------|
| `ALPACA_API_KEY` | Alpaca dashboard → Paper Trading → API Keys |
| `ALPACA_SECRET_KEY` | Same — shown once on generation |
| `SUPABASE_URL` | Supabase → Project Settings → API |
| `SUPABASE_KEY` | Supabase → Project Settings → API (anon/public key) |
| `EMAIL_SENDER` | Your Gmail address |
| `EMAIL_RECIPIENT` | Where to send daily reports |
| `EMAIL_APP_PASSWORD` | myaccount.google.com/apppasswords |
| `DASHBOARD_URL` | Your Vercel deployment URL |

### 4. Create Supabase tables
Paste the contents of the SQL block below into the Supabase SQL Editor and run it:

```sql
create table signals (
  id bigserial primary key, date date not null, symbol text not null,
  bb_pct_b numeric, momentum numeric, rsi numeric,
  manual_signal integer, ml_signal integer,
  created_at timestamptz default now(), unique (date, symbol)
);
create table trades (
  id bigserial primary key, date date not null, symbol text not null,
  action text not null, shares numeric, dollar_amount numeric,
  price numeric, strategy text default 'manual',
  created_at timestamptz default now()
);
create table portfolio_snapshots (
  id bigserial primary key, date date not null unique,
  total_value numeric, cash numeric, positions jsonb,
  created_at timestamptz default now()
);
create table daily_performance (
  id bigserial primary key, date date not null, symbol text not null,
  daily_pnl numeric, cumulative_return_pct numeric,
  created_at timestamptz default now(), unique (date, symbol)
);
alter table signals             disable row level security;
alter table trades              disable row level security;
alter table portfolio_snapshots disable row level security;
alter table daily_performance   disable row level security;
```

### 5. Train initial models
```bash
conda activate trade_b0t
cd trade_b0t_mk1
python -m bot.trainer
```

### 6. Set up launchd (runs bot automatically, no terminal needed)
```bash
# Load both jobs
launchctl load ~/Library/LaunchAgents/com.tradeb0t.daily.plist
launchctl load ~/Library/LaunchAgents/com.tradeb0t.retrain.plist

# Schedule Mac to wake at 3:45 PM weekdays so it's awake when the job fires
sudo pmset repeat wake MTWRF 15:45:00

# Verify both registered
launchctl list | grep tradeb0t

# Verify wake schedule
pmset -g sched
```

The bot fires at **3:50 PM ET Monday–Friday**. The Mac wakes itself at 3:45 PM, runs the job (~2 minutes), and can sleep again. No terminal needs to stay open.

---

## Running manually (testing)
```bash
conda activate trade_b0t
cd trade_b0t_mk1

# Run one daily cycle immediately
python -m bot.executor

# Retrain models immediately
python -m bot.trainer

# Check logs
cat logs/daily.log
cat logs/daily_error.log
```

---

## Dashboard

Live at: `https://dashboard-nine-virid-85.vercel.app`

| Page | URL | Content |
|------|-----|---------|
| Overview | `/` | Portfolio value, open positions, today's signals |
| Signals | `/signals` | Full indicator history by day |
| Strategy Race | `/race` | Manual vs ML vs $1,700 baseline chart |
| Trade Log | `/trades` | Every order placed |

### Deploying dashboard changes
Currently deployed via Vercel CLI. To redeploy after changes:
```bash
cd dashboard
npx vercel --prod
```

**Recommended:** Link the repo to Vercel on GitHub for automatic deploys on every push:
1. Push this repo to GitHub
2. Go to vercel.com → your project → Settings → Git → Connect Repository
3. From then on, every push to `main` auto-deploys the dashboard

---

## Position Sizing

Starting capital: **$1,700** (~$567 per stock)

| Signal | Action |
|--------|--------|
| +1 Long | Buy $567 worth — fractional shares via Alpaca notional order |
| 0 Flat | Close any open position |
| -1 Short | Short `floor($567 / price)` whole shares (Alpaca requires whole shares for shorts) |

> **Note:** SPY at ~$710/share exceeds the $567 allocation for shorting. Short signals on SPY are skipped; long signals work fine via fractional shares.

---

## Retraining Schedule

Models retrain on the **1st of every odd month** (January, March, May, July, September, November) at 7:00 AM via a separate launchd job. Each model trains on a rolling 2-year window of daily OHLCV data pulled from the Alpaca Historical API.

---

## Key Design Decisions

- **Manual Strategy executes real trades** — it demonstrated out-of-sample generalization in the original ML4T report. The Strategy Learner overfit to 2008–09 crisis dynamics and went negative out-of-sample, so it runs in shadow mode until it earns trust over time.
- **Virtual $1,700 accounting** — Alpaca paper accounts start at $100k. The bot tracks a virtual portfolio (`$1,700 + unrealized P&L`) for apples-to-apples comparison with a real Robinhood account.
- **Alpaca for both training data and execution** — eliminates price discrepancy between what the model trained on and what it actually trades.
- **No cloud hosting for the bot** — API keys stay local. Only the dashboard (read-only, no secrets) is publicly hosted.

---

## Academic Context

Strategies ported from Georgia Tech CS 7646 — Machine Learning for Trading (Spring 2026).  
Original report: *Strategy Evaluation* — Rayyan Jamil.
