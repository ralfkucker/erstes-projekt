import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(layout="wide")

# ==============================
# ASSET UNIVERSE
# ==============================

ASSETS = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL",
    "META","TSLA","NFLX",
    "SPY","QQQ",
    "GLD","SLV","USO",
    "EURUSD=X","GBPUSD=X",
    "BTC-USD","ETH-USD"
]

# ==============================
# DATA
# ==============================

@st.cache_data
def load_data(symbol):
    df = yf.download(symbol, period="2y", interval="1d")

    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.dropna()

# ==============================
# FEATURES
# ==============================

def create_features(df):

    df = df.copy()

    if isinstance(df["Close"], pd.DataFrame):
        df["Close"] = df["Close"].iloc[:, 0]

    df["returns"] = df["Close"].pct_change()
    df["ma50"] = df["Close"].rolling(50).mean()
    df["momentum"] = df["Close"] - df["Close"].shift(10)
    df["volatility"] = df["returns"].rolling(20).std()
    df["trend"] = df["Close"] - df["ma50"]

    return df.dropna()

# ==============================
# SIGNAL SCORE
# ==============================

def generate_score(df):

    row = df.iloc[-1]
    score = 0

    if row["momentum"] > 0:
        score += 1
    if row["trend"] > 0:
        score += 1
    if row["volatility"] < df["volatility"].mean():
        score += 1

    return score

# ==============================
# SCANNER
# ==============================

def scan_markets():

    results = []

    for asset in ASSETS:

        df = load_data(asset)
        if df is None:
            continue

        df = create_features(df)
        if len(df) < 200:
            continue

        score = generate_score(df)

        results.append({
            "Asset": asset,
            "Score": score,
            "Price": round(df["Close"].iloc[-1], 2)
        })

    return pd.DataFrame(results)

# ==============================
# BACKTEST
# ==============================

def simulate_trade(df, i, rr=2, sl=0.01):

    entry = df["Close"].iloc[i]
    tp = entry * (1 + rr * sl)
    stop = entry * (1 - sl)

    for j in range(i+1, len(df)):
        if df["Low"].iloc[j] <= stop:
            return -1
        if df["High"].iloc[j] >= tp:
            return rr

    return 0


def backtest(df):

    results = []

    for i in range(200, len(df)-10):

        sub = df.iloc[:i]

        if generate_score(sub) >= 2:
            results.append(simulate_trade(df, i))

    return results


def evaluate(results):

    if not results:
        return {"Winrate":0,"EV":0,"Trades":0}

    wins = [r for r in results if r > 0]
    losses = [r for r in results if r < 0]

    winrate = len(wins)/len(results)
    ev = winrate*np.mean(wins) - (1-winrate)*abs(np.mean(losses))

    return {
        "Winrate": round(winrate,2),
        "EV": round(ev,2),
        "Trades": len(results)
    }

# ==============================
# UI
# ==============================

st.title("🤖 AI Hedge Fund – PRO SCANNER")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Backtest",
    "🔎 Scanner",
    "🏆 Top Trades",
    "💼 Portfolio"
])

# ==============================
# TAB 1 BACKTEST
# ==============================

with tab1:

    if st.button("Run Backtest"):

        data = []

        for asset in ASSETS:
            df = load_data(asset)
            if df is None:
                continue

            df = create_features(df)
            if len(df) < 300:
                continue

            stats = evaluate(backtest(df))

            stats["Asset"] = asset
            data.append(stats)

        st.dataframe(pd.DataFrame(data))


# ==============================
# TAB 2 SCANNER
# ==============================

with tab2:

    if st.button("Scan Markets"):

        df = scan_markets()
        st.dataframe(df.sort_values("Score", ascending=False))


# ==============================
# TAB 3 TOP TRADES
# ==============================

with tab3:

    if st.button("Get Top Trades"):

        df = scan_markets()

        top = df.sort_values("Score", ascending=False).head(5)

        for _, row in top.iterrows():
            st.subheader(row["Asset"])
            st.write("Score:", row["Score"])
            st.write("Price:", row["Price"])
            st.markdown("---")


# ==============================
# TAB 4 PORTFOLIO
# ==============================

with tab4:

    if st.button("Build Portfolio"):

        df = scan_markets()

        top = df.sort_values("Score", ascending=False).head(5)

        capital = 10000
        allocation = capital / len(top)

        portfolio = []

        for _, row in top.iterrows():
            portfolio.append({
                "Asset": row["Asset"],
                "Allocation ($)": round(allocation,2),
                "Score": row["Score"]
            })

        st.dataframe(pd.DataFrame(portfolio))
