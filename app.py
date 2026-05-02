import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_lightweight_charts import renderLightweightCharts

# 1. ገጽታ
st.set_page_config(page_title="ICT Smart Money AI", layout="wide")
st.title("ICT Smart Money AI (TradingView Style)")

# Sidebar
assets = ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC"]
ticker = st.sidebar.selectbox("Asset", assets)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "1d"])

# 2. ዳታ ማውረድ
data = yf.download(ticker, period="3d", interval=timeframe)

if data.empty:
    st.error("ዳታ መጫን አልተቻለም። እባክህ ኢንተርኔትህን አረጋግጥ።")
    st.stop()

# 3. ዳታውን ማጽዳት (TypeError ለመከላከል)
df = data.reset_index()
# የኮለም ስሞችን ማስተካከል (Multi-index ችግርን ይፈታል)
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# ማንኛውንም ባዶ (NaN) ዳታ ማጽዳት
df = df.dropna(subset=['open', 'high', 'low', 'close']).copy()

# የጊዜ አወቃቀር - ወደ Unix timestamp መቀየር
if 'datetime' in df.columns:
    df['time'] = df['datetime'].apply(lambda x: int(x.timestamp()))
elif 'date' in df.columns:
    df['time'] = df['date'].apply(lambda x: int(x.timestamp()))

# 4. ICT Logic (PDH, PDL)
df['pdh'] = df['high'].shift(1).rolling(window=24, min_periods=1).max()
df['pdl'] = df['low'].shift(1).rolling(window=24, min_periods=1).min()

# እንደገና ማጽዳት (ስሌቱ NaN ሊፈጥር ስለሚችል)
df = df.dropna().copy()

last_row = df.iloc[-1]
c_price = float(last_row['close'])
pdh_val = float(last_row['pdh'])
pdl_val = float(last_row['pdl'])

# Entry Logic
entry, sl, tp = 0, 0, 0
status = "🔎 Looking for ICT Setup..."
color = "white"

if c_price > pdl_val and float(df.iloc[-2]['low']) < pdl_val:
    status = "🔥 ICT BUY SIGNAL (PDL Sweep)"
    color = "#26a69a"
    entry = c_price
    sl = pdl_val * 0.999
    tp = entry + (entry - sl) * 2
elif c_price < pdh_val and float(df.iloc[-2]['high']) > pdh_val:
    status = "⚠️ ICT SELL SIGNAL (PDH Sweep)"
    color = "#ef5350"
    entry = c_price
    sl = pdh_val * 1.001
    tp = entry - (sl - entry) * 2

# 5. ለቻርቱ ዳታውን ማዘጋጀት (TypeError እንዳይመጣ ቁጥሮቹን ማረጋገጥ)
chart_data = []
for _, row in df.iterrows():
    chart_data.append({
        "time": int(row['time']),
        "open": float(row['open']),
        "high": float(row['high']),
        "low": float(row['low']),
        "close": float(row['close'])
    })

chart_options = {
    "layout": {"background_color": "#0e1117", "textColor": "#d1d4dc"},
    "grid": {"vertLines": {"color": "#242733"}, "horzLines": {"color": "#242733"}},
    "timeScale": {"timeVisible": True}
}

series = [
    {
        "type": "Candlestick",
        "data": chart_data,
        "options": {"upColor": "#26a69a", "downColor": "#ef5350"}
    }
]

# 6. ውጤቱን ማሳየት
col1, col2 = st.columns([3, 1])

with col1:
    if chart_data:
        renderLightweightCharts(data=series, options=chart_options, height=600)
    else:
        st.warning("ቻርቱን ለማሳየት በቂ ዳታ የለም።")

with col2:
    st.markdown(f"### <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
    st.metric("አሁኑ ዋጋ", f"{c_price:,.2f}")
    
    if entry != 0:
        st.info(f"**Target TP:** {tp:,.2f}")
        st.error(f"**Stop Loss:** {sl:,.2f}")
        st.balloons()
    
    st.write(f"**PDH (High):** {pdh_val:,.2f}")
    st.write(f"**PDL (Low):** {pdl_val:,.2f}")
