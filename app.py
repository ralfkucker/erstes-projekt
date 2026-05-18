import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm

st.set_page_config(layout="wide")
st.title("🚀 AI Trading Terminal PRO – FINAL")

# =========================
# USER INPUT
# =========================
st.sidebar.header("⚙️ Settings")

tickers = st.sidebar.text_input("Watchlist (comma separated)", "SPY,QQQ,DIA,GLD,TLT,VIX").split(",")

capital = st.sidebar.number_input("Kapital (€)", value=100000)

risk_profile = st.sidebar.selectbox("Risk Profile", ["Konservativ", "Moderat", "Aggressiv"])

st.sidebar.subheader("🎛️ Factor Weights")

w_trend = st.sidebar.slider("Trend", 0, 100, 20)
w_mom = st.sidebar.slider("Momentum", 0, 100, 15)
w_vol = st.sidebar.slider("Volatility", 0, 100, 15)
w_macro = st.sidebar.slider("Macro/VIX", 0, 100, 15)
w_corr = st.sidebar.slider("Correlation", 0, 100, 10)
w_flow = st.sidebar.slider("Options Flow", 0, 100, 15)

weights = np.array([w_trend, w_mom, w_vol, w_macro, w_corr, w_flow])
weights = weights / weights.sum()

# =========================
# FUNCTIONS
# =========================
def load_data(ticker):
    data = yf.download(ticker, period="6mo")
    return data.dropna()

def calc_scores(data):
    returns = np.log(data["Close"]/data["Close"].shift(1)).dropna()
    vol = returns.rolling(20).std().dropna()

    current_vol = vol.iloc[-1] if len(vol)>0 else 0
    vol_score = -1 if current_vol > vol.mean() else 1

    ma50 = data["Close"].rolling(50).mean().iloc[-1]
    trend_score = 1 if data["Close"].iloc[-1] > ma50 else -1

    momentum = data["Close"].pct_change(20).iloc[-1]
    mom_score = 1 if momentum > 0 else -1

    macro_score = 0  # placeholder
    corr_score = 0
    flow_score = 0

    factors = np.array([trend_score, mom_score, vol_score, macro_score, corr_score, flow_score])
    score = np.dot(weights, factors) * 100

    return score, current_vol

def get_strategy(score, vol):
    if score > 60 and vol < 0.2:
        return "Long Calls / Bull Spread"
    elif score > 60:
        return "Short Puts"
    elif score < -60:
        return "Long Puts / Bear Spread"
    else:
        return "Iron Condor"

# =========================
# MAIN LOOP
# =========================
results = []

for t in tickers:
    data = load_data(t.strip())

    if data.empty:
        continue

    score, vol = calc_scores(data)

    strategy = get_strategy(score, vol)

    results.append({
        "Ticker": t,
        "Score": round(score,2),
        "Vol": round(vol*100,2),
        "Strategy": strategy
    })

df = pd.DataFrame(results)

# =========================
# DASHBOARD
# =========================
st.subheader("📊 Signal Board")
st.dataframe(df)

# =========================
# BEST TRADE
# =========================
if not df.empty:
    best = df.sort_values("Score", ascending=False).iloc[0]

    st.subheader("🏆 Best Trade")

    st.write(best)

# =========================
# PORTFOLIO ALLOCATION
# =========================
st.subheader("💼 Portfolio Allocation")

if not df.empty:
    df["Weight"] = df["Score"].clip(lower=0)
    df["Weight"] = df["Weight"] / df["Weight"].sum()

    df["Capital (€)"] = df["Weight"] * capital

    st.dataframe(df)

# =========================
# CHART
# =========================
st.subheader("📈 Chart")

ticker_chart = st.selectbox("Chart auswählen", df["Ticker"] if not df.empty else [])

if ticker_chart:
    data = load_data(ticker_chart)

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    ))

    st.plotly_chart(fig, use_container_width=True)

# =========================
# OPTIONS ENGINE
# =========================
st.subheader("📊 Options Engine")

if ticker_chart:
    S = data["Close"].iloc[-1]
    K = st.number_input("Strike", value=float(round(S)))
    T = st.slider("Laufzeit", 0.1, 2.0, 0.5)
    r = 0.02
    sigma = 0.2

    def bs_call(S,K,T,r,sigma):
        d1=(np.log(S/K)+(r+sigma**2/2)*T)/(sigma*np.sqrt(T))
        d2=d1-sigma*np.sqrt(T)
        return S*norm.cdf(d1)-K*np.exp(-r*T)*norm.cdf(d2)

    def bs_put(S,K,T,r,sigma):
        d1=(np.log(S/K)+(r+sigma**2/2)*T)/(sigma*np.sqrt(T))
        d2=d1-sigma*np.sqrt(T)
        return K*np.exp(-r*T)*norm.cdf(-d2)-S*norm.cdf(-d1)

    st.write("Call:", round(bs_call(S,K,T,r,sigma),2))
    st.write("Put:", round(bs_put(S,K,T,r,sigma),2))
