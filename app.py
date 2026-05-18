import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# ==============================
# CONFIG
# ==============================

ASSETS = ["AAPL", "MSFT", "TSLA", "SPY", "BTC-USD"]

# ==============================
# DATA LAYER
# ==============================

@st.cache_data
def load_data(symbol):
    df = yf.download(symbol, period="2y", interval="1d")

    if df is None or df.empty:
        return None

    df = df.dropna()

    return df

# ==============================
# FEATURE ENGINEERING
# ==============================

def create_features(df):

    df["returns"] = df["Close"].pct_change()

    df["ma50"] = df["Close"].rolling(50).mean()
    df["ma200"] = df["Close"].rolling(200).mean()

    df["momentum"] = df["Close"] - df["Close"].shift(10)

    df["volatility"] = df["returns"].rolling(20).std()

    df["trend"] = df["Close"] - df["ma50"]

    df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

    df = df.dropna()

    return df

# ==============================
# SIGNAL AI
# ==============================

def generate_signal(df):

    row = df.iloc[-1]

    score = 0

    if row["momentum"] > 0:
        score += 1

    if row["trend"] > 0:
        score += 1

    if row["volatility"] < df["volatility"].mean():
        score += 1

    return score >= 2

# ==============================
# TRADE SIMULATION
# ==============================

def simulate_trade(df, entry_idx, rr=2, sl=0.01):

    entry = df["Close"].iloc[entry_idx]

    tp = entry * (1 + rr * sl)
    stop = entry * (1 - sl)

    for i in range(entry_idx+1, len(df)):

        high = df["High"].iloc[i]
        low = df["Low"].iloc[i]

        if low <= stop:
            return -1

        if high >= tp:
            return rr

    return 0

# ==============================
# BACKTEST
# ==============================

def backtest(df):

    results = []

    for i in range(200, len(df)-10):

        sub_df = df.iloc[:i]

        if generate_signal(sub_df):

            result = simulate_trade(df, i)

            results.append(result)

    return results

# ==============================
# METRICS
# ==============================

def evaluate(results):

    if len(results) == 0:
        return {"winrate": 0, "ev": 0, "trades": 0}

    wins = [r for r in results if r > 0]
    losses = [r for r in results if r < 0]

    winrate = len(wins) / len(results)

    avg_win = np.mean(wins) if wins else 0
    avg_loss = abs(np.mean(losses)) if losses else 0

    ev = winrate * avg_win - (1 - winrate) * avg_loss

    return {
        "winrate": round(winrate, 2),
        "ev": round(ev, 2),
        "trades": len(results)
    }

# ==============================
# WALK FORWARD
# ==============================

def walk_forward(df):

    chunk = int(len(df) / 5)

    scores = []

    for i in range(2, 5):

        test = df[i*chunk:(i+1)*chunk]

        results = backtest(test)

        stats = evaluate(results)

        scores.append(stats)

    return scores

# ==============================
# AI HEDGE FUND CORE (SIMPLIFIED)
# ==============================

def run_ai_fund():

    all_results = []

    for asset in ASSETS:

        df = load_data(asset)

        if df is None:
            continue

        df = create_features(df)

        results = backtest(df)

        stats = evaluate(results)

        wf = walk_forward(df)

        all_results.append({
            "asset": asset,
            "stats": stats,
            "wf": wf
        })

    return all_results

# ==============================
# UI
# ==============================

st.set_page_config(layout="wide")
st.title("🤖 AI Hedge Fund – Test Mode")

if st.button("Run Full System Test"):

    results = run_ai_fund()

    for r in results:

        st.subheader(r["asset"])

        st.write("Winrate:", r["stats"]["winrate"])
        st.write("Expected Value:", r["stats"]["ev"])
        st.write("Trades:", r["stats"]["trades"])

        st.write("Walk Forward:")

        for wf in r["wf"]:
            st.write(wf)

        st.markdown("---")
