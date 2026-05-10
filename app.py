import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime
import pytz
import time

# 1. መሰረታዊ መረጃዎች
API_KEY = '3f0123e009b84cf9b0c8be149407fd0e'
TELEGRAM_TOKEN = '8714391964:AAFSzs1jZyhP6Spx8C2oDeIJ-NJnwtPrx9c'
CHAT_ID = '8125084772'

st.set_page_config(page_title="Central Bank AI Predictor", layout="wide")

# 2. Sidebar - ምርጫዎች
st.sidebar.title("Settings & Links")
asset_choice = st.sidebar.selectbox("Asset ምርጫ", ["XAU/USD (Gold)", "BTC/USD"])
timeframe = st.sidebar.selectbox("የሰዓት ምርጫ (Timeframe)", ["1min", "5min", "15min", "1h"])

st.sidebar.markdown("---")
st.sidebar.write("📢 **Telegram Bot Status**")
st.sidebar.success("Connected & Waiting for ICT Signals")

# 3. የቴሌግራም መልዕክት መላኪያ ፋንክሽን
def send_telegram_signal(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try:
        requests.get(url)
    except:
        pass

# 4. ዳታ ማምጫ (ከ Twelve Data)
def get_crypto_gold_data(symbol, tf):
    clean_symbol = "BTC/USD" if symbol == "BTC/USD" else "XAU/USD"
    url = f"https://api.twelvedata.com/time_series?symbol={clean_symbol}&interval={tf}&apikey={API_KEY}&outputsize=100"
    try:
        res = requests.get(url).json()
        if 'values' in res:
            df = pd.DataFrame(res['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
            return df.iloc[::-1] # ለቻርት እንዲመች ቅደም ተከተል ማስተካከል
        return None
    except:
        return None

# 5. ICT Strategy (FVG & OB) መመርመሪያ
def check_ict_strategy(df, symbol):
    if len(df) < 5: return
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    third_row = df.iloc[-3]
    
    price = last_row['close']
    signal_found = False
    
    # ቀለል ያለ FVG እና OB መመርመሪያ (ምሳሌ)
    if last_row['high'] < third_row['low']: # Bearish FVG
        msg = f"📉 *ICT SIGNAL: BEARISH FVG DETECTED*\n\nAsset: {symbol}\nPrice: ${price:,.2f}\n\n🎯 Entry: {price:,.2f}\n🛑 SL: {last_row['high'] + 2.5:,.2f}\n✅ TP: {price - 10.0:,.2f}"
        send_telegram_signal(msg)
        st.toast("Bearish Signal Sent to Telegram!")

    elif last_row['low'] > third_row['high']: # Bullish FVG
        msg = f"📈 *ICT SIGNAL: BULLISH FVG DETECTED*\n\nAsset: {symbol}\nPrice: ${price:,.2f}\n\n🎯 Entry: {price:,.2f}\n🛑 SL: {last_row['low'] - 2.5:,.2f}\n✅ TP: {price + 10.0:,.2f}"
        send_telegram_signal(msg)
        st.toast("Bullish Signal Sent to Telegram!")

# 6. ገጹን ማሳየት
st.title("🏛 Central Bank Price Action Analysis (AI)")

df = get_crypto_gold_data(asset_choice, timeframe)

if df is not None:
    latest_price = df['close'].iloc[-1]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"{asset_choice} Price", f"${latest_price:,.2f}")
    with col2:
        et_tz = pytz.timezone('Africa/Addis_Ababa')
        st.metric("Current Time (ET)", datetime.now(et_tz).strftime("%H:%M:%S"))

    # ቻርት ማስተካከያ (ተነባቢ እንዲሆን)
    fig = go.Figure(data=[go.Candlestick(x=df['datetime'],
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'],
                increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
    
    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)

    # ስትራቴጂውን መፈተሽ
    check_ict_strategy(df, asset_choice)
    st.success("ዳታው በትክክል እየመጣ ነው! ቦቱ ሲግናል እየፈለገ ነው...")
else:
    st.error("ዳታውን ማግኘት አልተቻለም።")

# 7. Auto-Refresh (በየሰከንዱ እንዲታደስ የሚያደርግ)
st.empty()
# የ 10 ሰከንድ ቆይታ (ለነፃ API የተመከረ)
time.sleep(10)
st.rerun()
