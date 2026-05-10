import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import plotly.graph_objects as go

# 1. ገጹን ማስተካከል
st.set_page_config(page_title="Central Bank AI Predictor", layout="wide")

API_KEY = '3f0123e009b84cf9b0c8be149407fd0e'

# 2. የጎን ሳጥን (Sidebar) - ምርጫዎች
st.sidebar.title("Settings & Links")
asset_choice = st.sidebar.selectbox("Asset ምርጫ", ["XAU/USD (Gold)", "EUR/USD", "GBP/USD"])
timeframe = st.sidebar.selectbox("የሰዓት ምርጫ (Timeframe)", ["1min", "5min", "15min", "1h"])

st.sidebar.markdown("---")
st.sidebar.write("📢 **Telegram Channel**")
st.sidebar.info("https://t.me/your_link_here")

# 3. ዳታ ማምጫ ፋንክሽን
def get_gold_data():
    url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={timeframe}&apikey={API_KEY}&outputsize=50"
    try:
        res = requests.get(url).json()
        if 'values' in res:
            df = pd.DataFrame(res['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
            return df
        return None
    except:
        return None

# 4. ዋናው ገጽ
st.title("🏛 Central Bank Price Action Analysis (AI)")

df = get_gold_data()

if df is not None:
    latest_price = df['close'].iloc[0]
    
    # ዋጋ እና ሰዓት ማሳያ
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"{asset_choice} Price", f"${latest_price:,.2f}")
    with col2:
        et_tz = pytz.timezone('Africa/Addis_Ababa')
        st.metric("Current Time (ET)", datetime.now(et_tz).strftime("%H:%M:%S"))

    # 5. ቻርት (Chart) መመለስ
    fig = go.Figure(data=[go.Candlestick(x=df['datetime'],
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'])])
    fig.update_layout(title=f"{asset_choice} Live Chart", xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.success("ዳታው በትክክል እየመጣ ነው!")
else:
    st.error("ዳታውን ማግኘት አልተቻለም።")

# 6. እራሱን Refresh እንዲያደርግ (በየ 60 ሰከንዱ)
st.empty()
time_left = 60
if st.button('Refresh Now'):
    st.rerun()

# በየደቂቃው እንዲቀየር የሚረዳ (Streamlit hack)
import time
time.sleep(60)
st.rerun()
