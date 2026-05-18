import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.linear_model import LogisticRegression

st.set_page_config(layout="wide")

st.title("📈 Multi-Asset Trading Engine PRO")

# ==============================
# INPUT
# ==============================

tickers_input = st.text_input("Assets (Komma getrennt)", "SPY, QQQ, BTC-USD")
capital = st.number_input("Kapital ($)", value=10000)
context_score = st.slider("Context Score (Makro)", 0.0, 1.0, 0.5)

tickers = [t.strip() for t in tickers_input.split(",")]

# ==============================
# CACHE LAYER
# ==============================

@st.cache_data(ttl=3600)
def load_data(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", auto_adjust=True, progress=False)

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Open","High","Low","Close","Volume"]].copy()

        df = df.replace([np.inf, -np.inf], np.nan).dropna()

        if len(df) < 100:
            return None

        return df

    except:
        return None


@st.cache_data(ttl=3600)
def create_features(df):

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.copy()

    df["returns"] = df["Close"].pct_change()
    df["ma50"] = df["Close"].rolling(50).mean()
    df["ma200"] = df["Close"].rolling(200).mean()
    df["vol"] = df["returns"].rolling(20).std()

    df["trend"] = df["Close"] - df["ma50"]
    df["momentum"] = df["returns"].rolling(10).mean()

    df = df.replace([np.inf, -np.inf], np.nan).dropna()

    if len(df) < 50:
        return None, None, None

    X = df[["trend", "momentum", "vol"]]
    y = (df["returns"].shift(-1) > 0).astype(int)

    return X[:-1], y[:-1], df


@st.cache_resource
def train_model(X, y):
    model = LogisticRegression()
    model.fit(X, y)
    return model


@st.cache_data
def monte_carlo(returns, sims=500):

    last_price = 100
    results = []

    for _ in range(sims):
        price = last_price
        for r in returns[-100:]:
            price *= (1 + np.random.normal(r, returns.std()))
        results.append(price)

    return np.percentile(results, [5, 50, 95])


# ==============================
# ENGINE
# ==============================

results = []

for t in tickers:

    data = load_data(t)

    if data is None:
        st.warning(f"{t}: keine Daten")
        continue

    X, y, df = create_features(data)

    if X is None:
        st.warning(f"{t}: zu wenig Daten")
        continue

    model = train_model(X, y)

    latest = X.iloc[-1:]
    prob = model.predict_proba(latest)[0][1]

    vol = df["vol"].iloc[-1] * np.sqrt(252) * 100

    returns = df["returns"].dropna()

    mc_low, mc_mid, mc_high = monte_carlo(returns)

    signal = "NEUTRAL"

    if prob > 0.55 and context_score > 0.5:
        signal = "LONG"
    elif prob < 0.45 and context_score < 0.5:
        signal = "SHORT"

    results.append({
        "Asset": t,
        "Signal": signal,
        "ML Score": round(prob, 2),
        "Vol (%)": round(vol, 2),
        "MC Low": round(mc_low, 2),
        "MC Mid": round(mc_mid, 2),
        "MC High": round(mc_high, 2),
        "Data": df
    })


# ==============================
# OUTPUT TABLE
# ==============================

if len(results) > 0:

    df_results = pd.DataFrame(results)

    st.dataframe(df_results.drop(columns=["Data"]))

    # ==============================
    # CHARTS
    # ==============================

    for r in results:

        st.subheader(r["Asset"])

        df = r["Data"]

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"]
        ))

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["Close"].rolling(50).mean(),
            name="MA50"
        ))

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["Close"].rolling(200).mean(),
            name="MA200"
        ))

        fig.update_layout(
            height=400,
            yaxis=dict(
                range=[
                    df["Low"].min()*0.95,
                    df["High"].max()*1.05
                ]
            )
        )

        st.plotly_chart(fig, use_container_width=True)

# ==============================
# CACHE RESET
# ==============================

if st.sidebar.button("🔄 Cache leeren"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("Cache gelöscht")
