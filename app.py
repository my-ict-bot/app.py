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
data = yf.download(ticker, period="5d", interval=timeframe)

if data.empty:
    st.error("ዳታ አልተገኘም")
    st.stop()

# 3. ዳታውን ማጽዳት (Critical for image_c04161.png error)
df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# የጊዜ አወቃቀርን ማስተካከል
time_col = 'datetime' if 'datetime' in df.columns else 'date'
df['time'] = df[time_col].apply(lambda x: int(x.timestamp()))

# ICT Logic
df['pdh'] = df['high'].shift(1).rolling(window=24, min_periods=1).max()
df['pdl'] = df['low'].shift(1).rolling(window=24, min_periods=1).min()

# **ዋናው መፍትሄ**፦ ሁሉንም NaN (ባዶ) ዳታዎች እና ያልተሟሉ መስመሮችን ሙሉ በሙሉ ማስወገድ
df = df[['time', 'open', 'high', 'low', 'close', 'pdh', 'pdl']].dropna().copy()

# 4. ዳታውን ለቻርቱ ማዘጋጀት (TypeError እንዳይመጣ ጥንቃቄ ተደርጓል)
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
    "timeScale": {"timeVisible": True}
}

# 5. ውጤቱን ማሳየት
col1, col2 = st.columns([3, 1])

with col1:
    if chart_candles:
        # እዚህ ጋር ነው በምስሉ ላይ ስህተት ይፈጠር የነበረው፤ አሁን chart_candles ንጹህ ነው
        series = [{"type": "Candlestick", "data": chart_candles}]
        renderLightweightCharts(data=series, options=chart_options, height=600)
    else:
        st.warning("ቻርቱን ለማሳየት በቂ ዳታ አልተገኘም።")

with col2:
    last_row = df.iloc[-1]
    c_price = float(last_row['close'])
    pdh_val = float(last_row['pdh'])
    pdl_val = float(last_row['pdl'])

    status = "🔎 SCANNING"
    color = "white"
    
    # Simple ICT Logic
    if c_price > pdl_val and float(df.iloc[-2]['low']) < pdl_val:
        status = "🔥 ICT BUY SIGNAL"
        color = "#26a69a"
    elif c_price < pdh_val and float(df.iloc[-2]['high']) > pdh_val:
        status = "⚠️ ICT SELL SIGNAL"
        color = "#ef5350"

    st.markdown(f"### <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
    st.metric("አሁኑ ዋጋ", f"{c_price:,.5f}")
    st.write(f"**PDH (High):** {pdh_val:,.5f}")
    st.write(f"**PDL (Low):** {pdl_val:,.5f}")
