import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")

st.title("🚀 AI Trading Dashboard")

ticker = st.text_input("Ticker eingeben (z.B. AAPL, TSLA, BTC-USD)", "AAPL")

data = yf.download(ticker, period="1y")

st.line_chart(data["Close"])

st.write("Letzte Daten:")
st.dataframe(data.tail())
