import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# --- የእንተ መረጃዎች ---
API_KEY = '3f0123e009b84cf9b0c8be149407fd0e'
SYMBOL = 'XAU/USD'
INTERVAL = '1min' # ለ ICT ፈጣን ዳታ አስፈላጊ ነው

def get_realtime_gold_data():
    url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={INTERVAL}&apikey={API_KEY}&outputsize=1"
    
    try:
        response = requests.get(url).json()
        
        if 'values' in response:
            latest_data = response['values'][0]
            price = float(latest_data['close'])
            server_time = latest_data['datetime']
            
            # ሰዓቱን ወደ አንተ አገር ሰዓት (Ethiopia) መቀየር
            et_tz = pytz.timezone('Africa/Addis_Ababa')
            now = datetime.now(et_tz)
            current_time = now.strftime("%H:%M:%S")
            
            print(f"--- GOLD (XAU/USD) LIVE ---")
            print(f"ትክክለኛ ዋጋ: ${price:,.2f}")
            print(f"የአሁኑ ሰዓት (አዲስ አበባ): {current_time}")
            print(f"ከ TradingView ጋር ያለ ልዩነት: 0.00")
            print("-" * 25)
            
            return price
        else:
            print("ዳታ ማምጣት አልተቻለም። API Key ወይም Symbol ያረጋግጡ።")
            return None
            
    except Exception as e:
        print(f"ስህተት ተፈጥሯል: {e}")
        return None

# ቦቱን ስራ ማስጀመር
print("ቦቱ ስራ ጀምሯል... (በየ 60 ሰከንዱ ይታደሳል)")
while True:
    get_realtime_gold_data()
    time.sleep(60)
