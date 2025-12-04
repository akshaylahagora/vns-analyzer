import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Master Tool", layout="wide")

st.title("📊 VNS Theory Master Tool")
st.markdown("Automatic NSE Data Fetching & Analysis")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Configuration")
symbol = st.sidebar.text_input("Stock Symbol", value="KOTAKBANK").upper()
duration = st.sidebar.selectbox("Duration", ["1 Month", "3 Months", "6 Months", "1 Year"])

# Calculate Dates
end_date = datetime.now()
if duration == "1 Month":
    start_date = end_date - timedelta(days=30)
elif duration == "3 Months":
    start_date = end_date - timedelta(days=90)
elif duration == "6 Months":
    start_date = end_date - timedelta(days=180)
else:
    start_date = end_date - timedelta(days=365)

# --- NSE FETCHING FUNCTION ---
@st.cache_data(ttl=600) # Cache data for 10 mins to prevent blocking
def get_nse_data(sym, start, end):
    try:
        # NSE requires headers to look like a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.nseindia.com/",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        # 1. Get Cookies
        session.get("https://www.nseindia.com", timeout=10)
        
        # 2. Fetch Data
        from_str = start.strftime("%d-%m-%Y")
        to_str = end.strftime("%d-%m-%Y")
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={from_str}&to={to_str}&symbol={sym}&type=priceVolumeDeliverable&series=ALL"
        
        response = session.get(url, timeout=10)
        
        if response.status_code != 200:
            return None, f"Error: Server returned {response.status_code}"
            
        data_json = response.json()
        raw_data = data_json['data'] if 'data' in data_json else data_json
        
        # Filter Equity only
        df = pd.DataFrame(raw_data)
        df = df[df['CH_SERIES'] == 'EQ']
        
        # Clean Data
        df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
        df['High'] = df['CH_TRADE_HIGH_PRICE'].astype(float)
        df['Low'] = df['CH_TRADE_LOW_PRICE'].astype(float)
        df['Open'] = df['CH_OPENING_PRICE'].astype(float)
        df['Close'] = df['CH_CLOSING_PRICE'].astype(float)
        
        return df.sort_values('Date').reset_index(drop=True), None
        
    except Exception as e:
        return None, str(e)

# --- VNS LOGIC ENGINE ---
def run_vns_analysis(df):
    results = []
    trend = "Neutral"
    last_bu = None
    last_be = None
    
    for i in range(len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1] if i > 0 else None
        
        bu = None
        be = None
        signal = ""
        css_class = "" # We will use this for coloring in dataframe
        
        if prev is not None:
            # 1. Define Levels
            if row['Low'] < prev['Low']:
                bu = prev['High']
                last_bu = prev['High']
                
            if row['High'] > prev['High']:
                be = prev['Low']
                last_be = prev['Low']
            
            # 2. Logic & Signals
            
            # Breakout (Teji)
            if last_bu and row['Close'] > last_bu and trend != "Bullish":
                trend = "Bullish"
                signal = "🟢 TEJI (Breakout)"
                
            # Breakdown (Mandi)
            elif last_be and row['Close'] < last_be and trend != "Bearish":
                trend = "Bearish"
                signal = "🔴 MANDI (Breakdown)"
                
            # Atak (Double Top)
            elif trend == "Bullish" and last_bu and (last_bu * 0.995 <= row['High'] <= last_bu * 1.005) and row['Close'] < last_bu:
                signal = "⚠️ ATAK (Double Top)"
                
            # Atak (Double Bottom)
            elif trend == "Bearish" and last_be and (last_be * 0.995 <= row['Low'] <= last_be * 1.005) and row['Close'] > last_be:
                signal = "⚠️ ATAK (Double Bottom)"
                
            # Reactions
            else:
                if trend == "Bullish":
                    if row['Low'] < prev['Low']:
                        signal = "🔵 Reaction (Buy Dip)"
                    elif row['High'] > prev['High']:
                        signal = "Teji Continuation"
                elif trend == "Bearish":
                    if row['High'] > prev['High']:
                        signal = "🔵 Reaction (Sell Rise)"
                    elif row['Low'] < prev['Low']:
                        signal = "Mandi Continuation"
        
        results.append({
            'Date': row['Date'].strftime('%d-%b-%Y'),
            'Open': row['Open'],
            'High': row['High'],
            'Low': row['Low'],
            'Close': row['Close'],
            'BU (Resist)': bu,
            'BE (Support)': be,
            'Signal': signal
        })
        
    return pd.DataFrame(results), trend

# --- MAIN UI EXECUTION ---
if st.sidebar.button("Run Analysis"):
    with st.spinner(f"Fetching data for {symbol}..."):
        df, error = get_nse_data(symbol, start_date, end_date)
        
        if error:
            st.error(f"Failed to fetch data: {error}. NSE might be blocking the request. Try again in a minute.")
        elif df is None or df.empty:
            st.warning("No data found. Check symbol.")
        else:
            analyzed_df, current_trend = run_vns_analysis(df)
            
            # Dashboard Status
            st.divider()
            c1, c2 = st.columns([1, 3])
            c1.metric("Current State", current_trend, delta_color="normal" if current_trend=="Neutral" else "inverse")
            c2.info(f"Analyzed {len(df)} days of data from {start_date.date()} to {end_date.date()}")
            
            # Formatting for display
            def highlight_vns(row):
                s = row['Signal']
                styles = [''] * len(row)
                if "TEJI" in s: return ['background-color: #d4edda; color: black'] * len(row)
                if "MANDI" in s: return ['background-color: #f8d7da; color: black'] * len(row)
                if "ATAK" in s: return ['background-color: #fff3cd; color: black'] * len(row)
                if "Reaction" in s: return ['background-color: #e2e6ea; color: black'] * len(row)
                return styles

            st.dataframe(
                analyzed_df.style.apply(highlight_vns, axis=1)
                .format({
                    'Open': '{:.2f}', 'High': '{:.2f}', 'Low': '{:.2f}', 'Close': '{:.2f}',
                    'BU (Resist)': '{:.2f}', 'BE (Support)': '{:.2f}'
                }, na_rep=""),
                use_container_width=True,
                height=600
            )

# Footer instructions
st.sidebar.markdown("---")
st.sidebar.caption("Note: NSE API is sensitive. If it fails, wait 10 seconds and try again.")