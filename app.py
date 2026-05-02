import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. ገጽታ
st.set_page_config(page_title="ICT Smart Money AI", layout="wide")
st.title("ICT Smart Money AI (Plotly Version)")

# Sidebar
assets = ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC"]
ticker = st.sidebar.selectbox("Asset", assets)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "1d"])

# 2. ዳታ ማውረድ
data = yf.download(ticker, period="3d", interval=timeframe)

if data.empty:
    st.error("ዳታ አልተገኘም")
    st.stop()

# 3. ዳታውን ማጽዳት
df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# ICT Logic
df['pdh'] = df['high'].shift(1).rolling(window=24, min_periods=1).max()
df['pdl'] = df['low'].shift(1).rolling(window=24, min_periods=1).min()
df = df.dropna().copy()

# 4. ቻርቱን በ Plotly መስራት (ይህ በፍጹም TypeError አይሰጥም)
fig = go.Figure(data=[go.Candlestick(
    x=df['datetime'] if 'datetime' in df.columns else df['date'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name="Price"
)])

# PDH እና PDL መስመሮችን መጨመር
fig.add_trace(go.Scatter(x=df['datetime'] if 'datetime' in df.columns else df['date'], y=df['pdh'], name="PDH", line=dict(color='red', width=1, dash='dash')))
fig.add_trace(go.Scatter(x=df['datetime'] if 'datetime' in df.columns else df['date'], y=df['pdl'], name="PDL", line=dict(color='green', width=1, dash='dash')))

fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)

# 5. ውጤቱን ማሳየት
col1, col2 = st.columns([3, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    last_row = df.iloc[-1]
    c_price = float(last_row['close'])
    pdh_val = float(last_row['pdh'])
    pdl_val = float(last_row['pdl'])

    status = "🔎 SCANNING"
    color = "white"
    
    if c_price > pdl_val and float(df.iloc[-2]['low']) < pdl_val:
        status = "🔥 BUY SIGNAL"
        color = "#26a69a"
    elif c_price < pdh_val and float(df.iloc[-2]['high']) > pdh_val:
        status = "⚠️ SELL SIGNAL"
        color = "#ef5350"

    st.markdown(f"### Status: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
    st.metric("አሁኑ ዋጋ", f"{c_price:,.5f}")
    st.write(f"**PDH:** {pdh_val:,.5f}")
    st.write(f"**PDL:** {pdl_val:,.5f}")
    if status != "🔎 SCANNING": st.balloons()
