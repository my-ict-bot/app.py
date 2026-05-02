import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_lightweight_charts import renderLightweightCharts

# 1. ገጽታ
st.set_page_config(page_title="ICT TradingView AI", layout="wide")
st.title("ICT Smart Money AI (TradingView Style)")

# Sidebar
assets = ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC"]
ticker = st.sidebar.selectbox("Asset", assets)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "1d"])

# 2. ዳታ ማውረድ
data = yf.download(ticker, period="2d" if timeframe == "5m" else "5d", interval=timeframe)

if data.empty:
    st.error("ዳታ የለም")
    st.stop()

# ዳታውን ለቻርቱ ማዘጋጀት
df = data.reset_index()
df.columns = [c.lower() for c in df.columns]
df['time'] = df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')

# 3. ICT Logic (PDH, PDL, FVG)
df['pdh'] = df['high'].shift(1).rolling(window=24).max()
df['pdl'] = df['low'].shift(1).rolling(window=24).min()

last_row = df.iloc[-1]
c_price = float(last_row['close'])
pdh_val = float(last_row['pdh'])
pdl_val = float(last_row['pdl'])

# Entry Logic
entry, sl, tp = 0, 0, 0
status = "🔎 Waiting for Setup..."
color = "white"

if c_price > pdl_val and float(df.iloc[-2]['low']) < pdl_val:
    status = "🔥 ICT BUY SIGNAL"
    color = "green"
    entry = c_price
    sl = pdl_val * 0.9995
    tp = entry + (entry - sl) * 3
elif c_price < pdh_val and float(df.iloc[-2]['high']) > pdh_val:
    status = "⚠️ ICT SELL SIGNAL"
    color = "red"
    entry = c_price
    sl = pdh_val * 1.0005
    tp = entry - (sl - entry) * 3

# 4. TradingView Style Chart Configuration
chart_options = {
    "layout": {"background_color": "#0e1117", "text_color": "#d1d4dc"},
    "grid": {"vertLines": {"color": "#242733"}, "horzLines": {"color": "#242733"}},
    "crosshair": {"mode": 0},
    "priceScale": {"borderVisible": False},
    "timeScale": {"borderVisible": False, "timeVisible": True, "secondsVisible": False},
}

candles = [
    {
        "type": "Candlestick",
        "data": df[['time', 'open', 'high', 'low', 'close']].to_dict(orient='records'),
        "options": {"upColor": "#26a69a", "downColor": "#ef5350", "borderVisible": False, "wickUpColor": "#26a69a", "wickDownColor": "#ef5350"}
    }
]

# 5. ውጤቱን ማሳየት
col1, col2 = st.columns([3, 1])

with col1:
    renderLightweightCharts(data=candles, options=chart_options, height=600)

with col2:
    st.markdown(f"### Status: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
    if entry != 0:
        st.success(f"**ENTRY:** {entry:.5f}\n\n**SL:** {sl:.5f}\n\n**TP:** {tp:.5f}")
        st.balloons()
    
    st.metric("አሁኑ ዋጋ", f"{c_price:.5f}")
    st.write(f"**PDH:** {pdh_val:.5f}")
    st.write(f"**PDL:** {pdl_val:.5f}")

st.dataframe(df.tail(10))
