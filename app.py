import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# ======================
# HEADER
# ======================
st.title("🚀 AI Trading Terminal PRO")

# ======================
# SIDEBAR
# ======================
st.sidebar.header("Settings")

ticker = st.sidebar.text_input("Ticker", "AAPL")
period = st.sidebar.selectbox("Zeitraum", ["6mo", "1y", "2y"])

# ======================
# DATA LOAD (SAFE)
# ======================
@st.cache_data
def load_data(ticker, period):
    try:
        data = yf.download(ticker, period=period)
        return data
    except:
        return pd.DataFrame()

data = load_data(ticker, period)

# ======================
# CHECK DATA
# ======================
if data.empty:
    st.error("Keine Daten gefunden. Bitte anderen Ticker eingeben.")
    st.stop()

# ======================
# CHART
# ======================
st.subheader("📈 Preisverlauf")
st.line_chart(data["Close"])

# ======================
# INDICATORS
# ======================
data["Returns"] = data["Close"].pct_change()

# Volatility (rolling)
volatility = data["Returns"].rolling(20).std()

# CLEAN values
volatility = volatility.dropna()

if len(volatility) == 0:
    st.warning("Nicht genug Daten für Volatilität.")
    st.stop()

current_vol = float(volatility.iloc[-1])
avg_vol = float(volatility.mean())

# ======================
# AI MARKET STATE
# ======================
st.subheader("🧠 Market Regime")

if current_vol > avg_vol:
    regime = "⚠️ Risk Off"
else:
    regime = "✅ Risk On"

st.write("Aktuelle Volatilität:", round(current_vol, 4))
st.write("Durchschnitt:", round(avg_vol, 4))
st.write("Marktphase:", regime)

# ======================
# SIGNAL ENGINE
# ======================
st.subheader("📊 Signal")

if regime == "⚠️ Risk Off":
    st.error("➡️ Defensive Strategien empfohlen")
    st.write("- Long Puts")
    st.write("- Short Calls")
    st.write("- Hedging")
else:
    st.success("➡️ Risk-On Strategien")
    st.write("- Long Calls")
    st.write("- Short Puts")
    st.write("- Trend Following")

# ======================
# DATA TABLE
# ======================
with st.expander("📋 Rohdaten anzeigen"):
    st.dataframe(data.tail(50))
