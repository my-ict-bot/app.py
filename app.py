import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# ገጹን ማስተካከል
st.set_page_config(page_title="Central Bank AI Predictor", layout="wide")

API_KEY = '3f0123e009b84cf9b0c8be149407fd0e'
SYMBOL = 'XAU/USD'

def get_data():
    url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval=1min&apikey={API_KEY}&outputsize=1"
    try:
        res = requests.get(url).json()
        if 'values' in res:
            return float(res['values'][0]['close'])
        return None
    except:
        return None

# ዌብሳይቱ ላይ የሚታይ ጽሁፍ
st.title("🏛 Central Bank Price Action Analysis (AI)")

gold_price = get_data()

if gold_price:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("XAU/USD (Gold) Price", f"${gold_price:,.2f}")
    with col2:
        et_tz = pytz.timezone('Africa/Addis_Ababa')
        st.metric("Current Time (ET)", datetime.now(et_tz).strftime("%H:%M:%S"))
    
    st.success("ዳታው በትክክል እየመጣ ነው!")
else:
    st.error("ዳታውን ማግኘት አልተቻለም። እባክህ API Key ወይም ኢንተርኔትህን ፈትሽ።")
