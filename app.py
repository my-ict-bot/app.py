import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# የዌብሳይቱ ገጽታ ቅንጅት
st.set_page_config(page_title="ICT Market Maker Bot", layout="wide")

st.title("🏹 ICT Institutional Algorithm Bot")
st.subheader("Central Bank Price Action Analysis (Forex & Commodities)")

# Side Bar ለምርጫዎች
symbol = st.sidebar.selectbox("የሚተነተን Asset ምረጥ", ["EURUSD=X", "GBPUSD=X", "GC=F", "CL=F", "BTC-USD"])
timeframe = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h", "1d"])

def get_ict_data(symbol, tf):
    # ዳታውን ከ Yahoo Finance ማውረድ
    df = yf.download(symbol, period="5d", interval=tf)
 
    # የ ICT Liquidity ደረጃዎችን ማስላት
    df['PDH'] = df['High'].shift(1).rolling(window=20).max() # Previous Daily High lookback
    df['PDL'] = df['Low'].shift(1).rolling(window=20).min()  # Previous Daily Low lookback
 
    # Fair Value Gap (FVG) መለየት
    df['FVG_Up'] = (df['Low'] > df['High'].shift(2)) & (df['Close'].shift(1) > df['High'].shift(2))
    df['FVG_Down'] = (df['High'] < df['Low'].shift(2)) & (df['Close'].shift(1) < df['Low'].shift(2))
 
    return df

data = get_ict_data(symbol, timeframe)
if not data.empty:
    last_row = data.iloc[-1]
    # የተቀረው የኮድህ ክፍል እዚህ ይግባ
else:
    st.warning("ለተመረጠው Asset ዳታ ማግኘት አልተቻለም። እባክህ ሌላ ሞክር።")
prev_row = data.iloc[-2]

# --- ALGORITHM LOGIC (THE BRAIN) ---
st.write(f"### የተመረጠው: {symbol} ወቅታዊ ትንታኔ")

col1, col2, col3 = st.columns(3)

# ICT Logic: Liquidity Sweep + FVG Reversal
status = "Neutral ⚖️"
entry = 0
sl = 0
tp = 0
signal_color = "white"

# Bullish Setup: ዋጋ ከPDL በታች ወርዶ ከተመለሰ (Liquidity Raid)
# መረጃዎቹን ወደ ነጠላ ቁጥር (float) በመቀየር ማወዳደር
# መረጃዎቹን በጥንቃቄ ወደ ነጠላ ቁጥር መቀየር
try:
    close_price = float(last_row['Close'].iloc[0] if hasattr(last_row['Close'], 'iloc') else last_row['Close'])
    pdl_level = float(last_row['PDL'].iloc[0] if hasattr(last_row['PDL'], 'iloc') else last_row['PDL'])
    pdh_level = float(last_row['PDH'].iloc[0] if hasattr(last_row['PDH'], 'iloc') else last_row['PDH'])
    prev_low = float(prev_row['Low'].iloc[0] if hasattr(prev_row['Low'], 'iloc') else prev_row['Low'])
    prev_high = float(prev_row['High'].iloc[0] if hasattr(prev_row['High'], 'iloc') else prev_row['High'])
except Exception as e:
    st.error(f"ቁጥሮቹን በማንበብ ላይ ስህተት ተፈጥሯል: {e}")
    st.stop()
close_price = float(last_row['Close'].iloc[0] if hasattr(last_row['Close'], 'iloc') else last_row['Close'])
pdl_level = float(last_row['PDL'].iloc[0] if hasattr(last_row['PDL'], 'iloc') else last_row['PDL'])
prev_low = float(prev_row['Low'].iloc[0] if hasattr(prev_row['Low'], 'iloc') else prev_row['Low'])
# መረጃው በምን አይነት መልኩ ቢመጣ (ነጠላ ቁጥርም ይሁን ዝርዝር) በትክክል እንዲነበብ ማድረግ
def safe_float(value):
    if hasattr(value, 'iloc'):
        return float(value.iloc[0])
    return float(value)

# አሁን ተለዋዋጮቹን በዚህ መልኩ ጥራ
close_price = safe_float(last_row['Close'])
pdl_level = safe_float(last_row['PDL'])
pdh_level = safe_float(last_row['PDH'])
prev_low = safe_float(prev_row['Low'])
prev_high = safe_float(prev_row['High'])
# መረጃው በምን አይነት መልኩ ቢመጣ በትክክል እንዲነበብ የሚያደርግ ፋንክሽን
def safe_float(value):
    try:
 # --- መስመር 85 አካባቢ የሚጨመር የ FVG እና OB ስሌት ---

# 1. FVG (Fair Value Gap) ስሌት
# FVG Up (Bullish): የ 1ኛው ሻማ High ከ 3ኛው ሻማ Low በታች ሲሆን
data['FVG_Up'] = (data['Low'] > data['High'].shift(2))
# --- መስመር 85 አካባቢ የሚጨመር የ FVG እና OB ስሌት ---

# 1. FVG (Fair Value Gap) ስሌት
# FVG Up (Bullish): የ 1ኛው ሻማ High ከ 3ኛው ሻማ Low በታች ሲሆን
data['FVG_Up'] = (data['Low'] > data['High'].shift(2))
# FVG Down (Bearish): የ 1ኛው ሻማ Low ከ 3ኛው ሻማ High በላይ ሲሆን
data['FVG_Down'] = (data['High'] < data['Low'].shift(2))

# የቅርብ ጊዜውን የ FVG ሁኔታ ማወቅ
last_fvg_up = data['FVG_Up'].iloc[-1]
last_fvg_down = data['FVG_Down'].iloc[-1]

# 2. Order Block (OB) መኖሩን ማረጋገጫ (ቀላል ዘዴ)
# Bullish OB: የቀድሞው ሻማ ቀይ ሆኖ አሁኑ ሻማ ከሱ በላይ ሲዘጋ
is_bullish_ob = (data['Close'].shift(1) < data['Open'].shift(1)) and (data['Close'] > data['High'].shift(1))
# Bearish OB: የቀድሞው ሻማ አረንጓዴ ሆኖ አሁኑ ሻማ ከሱ በታች ሲዘጋ
is_bearish_ob = (data['Close'].shift(1) > data['Open'].shift(1)) and (data['Close'] < data['Low'].shift(1))

last_ob_bull = is_bullish_ob.iloc[-1]
last_ob_bear = is_bearish_ob.iloc[-1]
# 1. ዳታውን ወደ ነጠላ ቁጥር መቀየር
def to_single_float(val):
    try:
        return float(val.iloc[0]) if hasattr(val, 'iloc') else float(val)
    except: return 0.0

c_price = to_single_float(last_row['Close'])
pdl_val = to_single_float(last_row['PDL'])
pdh_val = to_single_float(last_row['PDH'])
p_low = to_single_float(prev_row['Low'])
p_high = to_single_float(prev_row['High'])

entry, sl, tp = 0, 0, 0
status = "No Clear Signal"
signal_color = "white"

# 2. Entry Logic (Liquidity Swept + FVG/OB confirmation)
# BUY: ዋጋ ከ PDL በታች ወርዶ ሲመለስ + FVG ካለ
if c_price > pdl_val and p_low < pdl_val and last_fvg_up:
    status = "PRO BUY SIGNAL (OB + FVG Confirmed)"
    signal_color = "green"
    entry = round(c_price, 5)
    sl = round(pdl_val - (pdl_val * 0.0005), 5)
    tp = round(entry + (entry - sl) * 3, 5) # 1:3 Risk/Reward

# SELL: ዋጋ ከ PDH በላይ ወጥቶ ሲመለስ + FVG ካለ
elif c_price < pdh_val and p_high > pdh_val and last_fvg_down:
    status = "PRO SELL SIGNAL (OB + FVG Confirmed)"
    signal_color = "red"
    entry = round(c_price, 5)
    sl = round(pdh_val + (pdh_val * 0.0005), 5)
    tp = round(entry - (sl - entry) * 3, 5)

# 3. የድምፅ ማስጠንቀቂያ (Alert)
if entry != 0:
    st.balloons() # የእንኳን ደስ አለህ ምልክት
    # ለድምፅ ማስጠንቀቂያ (ይህ በብሮውዘሩ ላይ ድምፅ ያሰማል)
    st.components.v1.html("""
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg">
        </audio>
    """, height=0)

# 4. መረጃውን በዌብሳይቱ ላይ ማሳየት
col1, col2 = st.columns(2)
with col1:
    st.metric("አሁኑ ዋጋ", f"{c_price:.5f}")
with col2:
    st.markdown(f"### **ሁኔታ:** <span style='color:{signal_color}'>{status}</span>", unsafe_allow_html=True)

if entry != 0:
    st.markdown(f"""
    <div style="background-color:#1e1e1e; padding:20px; border-radius:10px; border: 2px solid {signal_color};">
        <h2 style="color:{signal_color}; text-align:center;">🎯 ትክክለኛ Entry ተገኝቷል!</h2>
        <p style="font-size:20px; text-align:center;">
            <b>ENTRY:</b> {entry} | <b>SL:</b> {sl} | <b>TP:</b> {tp}
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("🔎 ገበያው ትክክለኛውን የ Manipulation ዞን (OB/FVG) እየጠበቀ ነው...")

st.write("#### የቅርብ ጊዜ የዋጋ እንቅስቃሴዎች")
st.dataframe(data.tail(10))
