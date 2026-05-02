import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_lightweight_charts import renderLightweightCharts

# 1. Page Configuration
st.set_page_config(page_title="ICT Smart Money AI", layout="wide")
st.title("ICT Smart Money AI (TradingView Style)")

# Sidebar
assets = ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC"]
ticker = st.sidebar.selectbox("Asset", assets)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "1d"])

# 2. Data Fetching
# 5 ደቂቃ ከሆነ የ2 ቀን፣ ሌላ ከሆነ የ5 ቀን ዳታ
period = "2d" if timeframe == "5m" else "5d"
data = yf.download(ticker, period=period, interval=timeframe)

if data.empty:
    st.error("ዳታ ማግኘት አልተቻለም።")
    st.stop()

# 3. Data Cleaning (Crucial for image_c039bd.png)
df = data.reset_index()
# የኮለም ስሞችን ማስተካከል (Multi-index ችግርን ለመከላከል)
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# የጊዜ አወቃቀር - የግድ ወደ Unix Timestamp (integer) መቀየር አለበት
time_col = 'datetime' if 'datetime' in df.columns else 'date'
df['time'] = df[time_col].apply(lambda x: int(x.timestamp()))

# ICT Logic (PDH/PDL)
df['pdh'] = df['high'].shift(1).rolling(window=24, min_periods=1).max()
df['pdl'] = df['low'].shift(1).rolling(window=24, min_periods=1).min()

# **መፍትሄ**: ሁሉንም NaN (ባዶ) ዳታዎች ማስወገድ። renderLightweightCharts NaN ዳታ ካገኘ TypeError ይወረውራል።
df = df.dropna(subset=['time', 'open', 'high', 'low', 'close', 'pdh', 'pdl']).copy()

# 4. Preparing Data for Chart
# ዳታው የግድ Dictionary ዝርዝር መሆን አለበት
chart_candles = []
for _, row in df.iterrows():
    chart_candles.append({
        "time": int(row['time']),
        "open": float(row['open']),
        "high": float(row['high']),
        "low": float(row['low']),
        "close": float(row['close'])
    })

chart_options = {
    "layout": {"background_color": "#0e1117", "textColor": "#d1d4dc"},
    "grid": {"vertLines": {"color": "#242733"}, "horzLines": {"color": "#242733"}},
    "timeScale": {"timeVisible": True, "secondsVisible": False}
}

# 5. UI Layout
col1, col2 = st.columns([3, 1])

with col1:
    if chart_candles:
        # እዚህ ጋር ነው image_c039bd.png ላይ የታየው ስህተት ይፈጠር የነበረው
        series = [
            {
                "type": "Candlestick",
                "data": chart_candles,
                "options": {
                    "upColor": "#26a69a", 
                    "downColor": "#ef5350", 
                    "borderVisible": False,
                    "wickUpColor": "#26a69a",
                    "wickDownColor": "#ef5350"
                }
            }
        ]
        renderLightweightCharts(data=series, options=chart_options, height=600)
    else:
        st.warning("ለቻርቱ የሚሆን በቂ ዳታ የለም።")

with col2:
    last_row = df.iloc[-1]
    c_price = float(last_row['close'])
    pdh_val = float(last_row['pdh'])
    pdl_val = float(last_row['pdl'])

    # Simple ICT Signal
    status = "🔎 SCANNING..."
    color = "white"
    
    if c_price > pdl_val and float(df.iloc[-2]['low']) < pdl_val:
        status = "🔥 ICT BUY SIGNAL"
        color = "#26a69a"
    elif c_price < pdh_val and float(df.iloc[-2]['high']) > pdh_val:
        status = "⚠️ ICT SELL SIGNAL"
        color = "#ef5350"

    st.markdown(f"### <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
    st.metric("Price", f"{c_price:,.5f}")
    
    if status != "🔎 SCANNING...":
        st.success(f"Setup Detected at {c_price:,.5f}")
        st.balloons()
    
    st.write("---")
    st.write(f"**PDH (Prev Day High):** {pdh_val:,.5f}")
    st.write(f"**PDL (Prev Day Low):** {pdl_val:,.5f}")
