import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. የቴሌግራም መረጃ ---
BOT_TOKEN = "8697770325:AAEBF1hdY69TwJo53thF7yzyhm9uWJaSsE0"
CHAT_ID = "8125084772"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try: requests.get(url, timeout=5)
    except: pass

# --- 2. ገጽታ ---
st.set_page_config(page_title="ICT Smart Money AI", layout="wide")
st_autorefresh(interval=60000, key="live_update")

st.title("🏹 ICT Advanced Strategy Terminal")

# Sidebar
st.sidebar.header("Settings")
ticker = st.sidebar.selectbox("Asset", ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD"])
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "1d"])

# --- 3. ዳታ ማውረድ ---
data = yf.download(ticker, period="3d", interval=timeframe)
if data.empty: st.stop()

df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# --- 4. ICT Calculations ---
high_3d = df['high'].max()
low_3d = df['low'].min()
equilibrium = (high_3d + low_3d) / 2
ote_deep = low_3d + (high_3d - low_3d) * 0.79
ote_shallow = low_3d + (high_3d - low_3d) * 0.62

# --- 5. UI Layout ---
col1, col2 = st.columns([3, 1])

with col1:
    fig = go.Figure(data=[go.Candlestick(x=df.iloc[:,0], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
    fig.add_hline(y=equilibrium, line_dash="dot", line_color="yellow", annotation_text="Equilibrium")
    fig.add_hrect(y0=ote_shallow, y1=ote_deep, fillcolor="gold", opacity=0.1, line_width=0, annotation_text="OTE Zone")
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Market Status")
    
    # *** ይሄው እዚህ ጋር ነው የሙከራ ቁልፉ ***
    if st.button("📢 ቴሌግራምን ሞክር"):
        send_telegram_msg("🚀 ሰላም! የቴሌግራም ቦቱ አሁን በትክክል ተገናኝቷል። ሲግናል ሲኖር መልዕክት ይደርስሃል።")
        st.success("የሙከራ መልዕክት ተልኳል!")

    curr_price = df.iloc[-1]['close']
    st.metric("Current Price", f"{curr_price:,.2f}")
    
    st.divider()
    
    # የሲግናል ማጣሪያ
    in_ote = ote_shallow <= curr_price <= ote_deep
    if in_ote:
        st.success("🎯 Price in OTE Zone!")
        send_telegram_msg(f"🎯 ICT ALERT: {ticker}\nPrice is in OTE Zone ({curr_price:,.2f})!")
    else:
        st.info("Market is Scanning...")

    st.write(f"🕒 Sync: {datetime.now().strftime('%H:%M:%S')}")
