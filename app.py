import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime
import pytz
import time

# 1. Configuration (የአንተ መረጃዎች)
API_KEY = '3f0123e009b84cf9b0c8be149407fd0e'
TELEGRAM_TOKEN = '8714391964:AAFSzs1jZyhP6Spx8C2oDeIJ-NJnwtPrx9c'
CHAT_ID = '8125084772'

st.set_page_config(page_title="Central Bank AI Predictor", layout="wide")

# 2. Sidebar
st.sidebar.title("Settings & Links")
# Twelve Data ለወርቅ XAU/USD ነው የሚጠቀመው
asset_choice = st.sidebar.selectbox("Asset ምርጫ", ["XAU/USD", "BTC/USD"])
timeframe = st.sidebar.selectbox("የሰዓት ምርጫ (Timeframe)", ["1min", "5min", "15min", "1h"])

st.sidebar.markdown("---")
st.sidebar.info("📢 Telegram Bot Connected")

# 3. Telegram Function
def send_telegram_signal(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try: requests.get(url)
    except: pass

# 4. Data Fetching (ለ XAU/USD እና BTC/USD)
def get_market_data(symbol, tf):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={tf}&apikey={API_KEY}&outputsize=50"
    try:
        response = requests.get(url)
        data = response.json()
        if 'values' in data:
            df = pd.DataFrame(data['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
            return df.sort_values('datetime', ascending=True)
        return None
    except:
        return None

# 5. ICT Logic (FVG Detection)
def check_ict_signals(df, symbol):
    if len(df) < 5: return
    last = df.iloc[-1]
    third = df.iloc[-3]
    price = last['close']
    
    # Simple Bullish FVG check
    if last['low'] > third['high']:
        msg = f"🚀 *ICT BULLISH SIGNAL*\nAsset: {symbol}\nPrice: ${price:,.2f}\nEntry: {price}\nSL: {last['low']-5}\nTP: {price+15}"
        send_telegram_signal(msg)
        st.toast("Signal Sent!")

# 6. UI
st.title("🏛 Central Bank Price Action Analysis (AI)")

df = get_market_data(asset_choice, timeframe)

if df is not None:
    latest_price = df['close'].iloc[-1]
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"{asset_choice} Price", f"${latest_price:,.2f}")
    with col2:
        et_tz = pytz.timezone('Africa/Addis_Ababa')
        st.metric("Ethiopia Time", datetime.now(et_tz).strftime("%H:%M:%S"))

    # Candlestick Chart
    fig = go.Figure(data=[go.Candlestick(x=df['datetime'],
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'],
                increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    check_ict_signals(df, asset_choice)
    st.success("ዳታው በትክክል እየመጣ ነው። ቦቱ ሲግናል እየፈለገ ነው...")
else:
    st.error("ዳታው አልመጣም። እባክህ ለ 30 ሰከንድ ጠብቅ (API Limit)...")

# 7. Auto Refresh
time.sleep(20) # APIው እንዳይዘጋ 20 ሰከንድ መጠበቅ ይመከራል
st.rerun()
