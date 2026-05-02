import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. የዌብሳይቱ ገጽታ
st.set_page_config(page_title="ICT Smart Money AI", layout="wide")
st.title("ICT Institutional Price Action Analysis")

# Sidebar - Asset እና Timeframe መምረጫ (5m ተጨምሯል)
assets = ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC", "CL=F"]
ticker = st.sidebar.selectbox("Asset ይምረጡ", assets)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "4h", "1d"])

# 2. ዳታ ማውረድ (ለ 5m እና 15m የ 1 ቀን ዳታ ይበቃል)
data = yf.download(ticker, period="2d" if timeframe in ["5m", "15m"] else "5d", interval=timeframe)

if data.empty:
    st.error("ዳታ ማግኘት አልተቻለም።")
    st.stop()

# 3. ICT Concepts (PDH, PDL, FVG)
data['PDH'] = data['High'].shift(1).rolling(window=24).max()
data['PDL'] = data['Low'].shift(1).rolling(window=24).min()
data['FVG_Up'] = (data['Low'] > data['High'].shift(2))
data['FVG_Down'] = (data['High'] < data['Low'].shift(2))

# 4. መረጃዎችን ወደ ነጠላ ቁጥር መቀየር
def safe_float(val):
    try: return float(val.iloc[-1]) if hasattr(val, 'iloc') else float(val)
    except: return 0.0

last_row = data.iloc[-1]
prev_row = data.iloc[-2]
c_price = safe_float(last_row['Close'])
pdl_val = safe_float(last_row['PDL'])
pdh_val = safe_float(last_row['PDH'])

entry, sl, tp = 0, 0, 0
status = "🔎 Waiting for ICT Setup..."
sig_color = "white"

# 5. ICT Entry Logic (Liquidity Sweep + FVG)
if c_price > pdl_val and safe_float(prev_row['Low']) < pdl_val and bool(last_row['FVG_Up'].any() if hasattr(last_row['FVG_Up'], 'any') else last_row['FVG_Up']):
    status = "🔥 ICT BULLISH REVERSAL (Buy)"
    sig_color = "green"
    entry = c_price
    sl = pdl_val - (pdl_val * 0.0005)
    tp = entry + (entry - sl) * 3

elif c_price < pdh_val and safe_float(prev_row['High']) > pdh_val and bool(last_row['FVG_Down'].any() if hasattr(last_row['FVG_Down'], 'any') else last_row['FVG_Down']):
    status = "⚠️ ICT BEARISH REVERSAL (Sell)"
    sig_color = "red"
    entry = c_price
    sl = pdh_val + (pdh_val * 0.0005)
    tp = entry - (sl - entry) * 3

# 6. የቻርት ስራ (Position Lines ተካተዋል)
fig = go.Figure(data=[go.Candlestick(x=data.index,
                open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'], name="Market")])

fig.add_hline(y=pdh_val, line_dash="dash", line_color="orange", annotation_text="PDH")
fig.add_hline(y=pdl_val, line_dash="dash", line_color="cyan", annotation_text="PDL")

if entry != 0:
    fig.add_hline(y=entry, line_color="blue", line_width=2, annotation_text="ENTRY")
    fig.add_hline(y=sl, line_color="red", line_dash="dot", annotation_text="SL")
    fig.add_hline(y=tp, line_color="green", line_dash="dot", annotation_text="TP")

fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)

# 7. ውጤቱን ማሳየት
col1, col2 = st.columns([2, 1])
with col1:
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.markdown(f"### Status: <span style='color:{sig_color}'>{status}</span>", unsafe_allow_html=True)
    if entry != 0:
        st.success(f"**ENTRY:** {entry:.5f}\n\n**SL:** {sl:.5f}\n\n**TP:** {tp:.5f}")
        st.balloons()
