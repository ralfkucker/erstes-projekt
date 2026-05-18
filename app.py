import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm

st.set_page_config(layout="wide")

st.title("🚀 AI Trading Terminal PRO")

# =========================
# DATA
# =========================
ticker = st.sidebar.text_input("Ticker", "SPY")
data = yf.download(ticker, period="6mo")

if data.empty:
    st.error("Keine Daten geladen")
    st.stop()

# =========================
# CLEAN DATA
# =========================
data = data.dropna()

# Preise runden
data = data.round(2)

# =========================
# VOLATILITY ENGINE (FIXED)
# =========================
returns = np.log(data["Close"] / data["Close"].shift(1))
returns = returns.dropna()

vol = returns.rolling(20).std()

# ABSICHERUNG gegen leere Series
if len(vol.dropna()) == 0:
    current_vol = 0
    avg_vol = 0
else:
    vol_clean = vol.dropna()
    current_vol = float(vol_clean.iloc[-1])
    avg_vol = float(vol_clean.mean())

# Annualisieren + in %
current_vol_annual = current_vol * np.sqrt(252) * 100
avg_vol_annual = avg_vol * np.sqrt(252) * 100

# =========================
# MARKET REGIME
# =========================
regime = "Risk On" if current_vol < avg_vol else "Risk Off"

st.subheader("🧠 Market Regime")

col1, col2, col3 = st.columns(3)

col1.metric("Aktuelle Volatilität", f"{current_vol_annual:.2f}%")
col2.metric("Durchschnitt", f"{avg_vol_annual:.2f}%")
col3.metric("Phase", regime)

# =========================
# CHART (FIXED SCALE)
# =========================
st.subheader("📈 Chart")

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close']
))

# Auto-scale fix (kein 0 mehr)
min_price = data["Low"].min()
max_price = data["High"].max()

fig.update_layout(
    yaxis=dict(range=[min_price * 0.98, max_price * 1.02]),
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# SIGNAL ENGINE
# =========================
st.subheader("📊 Signal")

if regime == "Risk On":
    st.success("➡️ Risk-On Strategien")
    st.write("- Long Calls")
    st.write("- Trend Following")
    st.write("- Momentum")
else:
    st.error("➡️ Risk-Off Strategien")
    st.write("- Long Puts")
    st.write("- Hedging")
    st.write("- Cash / Defensive")

# =========================
# OPTIONS ENGINE (LEVEL 3)
# =========================
st.subheader("🧮 Options Engine")

S = float(data["Close"].iloc[-1])  # aktueller Preis
K = st.number_input("Strike", value=round(S, 0))
T = st.slider("Laufzeit (Jahre)", 0.01, 2.0, 0.5)
r = 0.01
sigma = current_vol * np.sqrt(252)

def black_scholes_call(S, K, T, r, sigma):
    if sigma == 0 or T == 0:
        return 0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2)*T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)

def black_scholes_put(S, K, T, r, sigma):
    if sigma == 0 or T == 0:
        return 0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2)*T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return K * np.exp(-r*T) * norm.cdf(-d2) - S * norm.cdf(-d1)

call_price = black_scholes_call(S, K, T, r, sigma)
put_price = black_scholes_put(S, K, T, r, sigma)

col1, col2 = st.columns(2)
col1.metric("Call Preis", f"{call_price:.2f}")
col2.metric("Put Preis", f"{put_price:.2f}")

# =========================
# LEVEL 4 – AI SIGNAL SCORE
# =========================
st.subheader("🤖 AI Score")

momentum = data["Close"].pct_change(20).iloc[-1]
vol_score = 1 if current_vol < avg_vol else -1
trend_score = 1 if data["Close"].iloc[-1] > data["Close"].rolling(50).mean().iloc[-1] else -1

score = momentum * 5 + vol_score * 2 + trend_score * 3

if score > 3:
    st.success(f"BULLISH ({score:.2f})")
elif score < -3:
    st.error(f"BEARISH ({score:.2f})")
else:
    st.warning(f"NEUTRAL ({score:.2f})")

# =========================
# RAW DATA
# =========================
with st.expander("📋 Rohdaten anzeigen"):
    st.dataframe(data.tail())
