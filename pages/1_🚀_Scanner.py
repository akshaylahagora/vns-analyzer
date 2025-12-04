import streamlit as st
import pandas as pd
import requests
import time
import json
import os
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="F&O Scanner", page_icon="🔭", layout="wide")

st.title("🔭 F&O VNS Scanner (> ₹1000)")
st.markdown("Automated Daily Scanner. Runs once per day automatically, or when manually triggered.")

# --- CSS STYLING ---
st.markdown("""
<style>
    .scan-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ddd; }
    .bull-box { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
    .bear-box { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
    .neutral-box { background-color: #fff3cd; border-color: #ffeeba; color: #856404; }
    .metric-val { font-weight: bold; font-size: 1.1em; }
    .timestamp { font-size: 0.8em; color: #666; font-style: italic; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
SCAN_FILE = "daily_scan_results.json" # Local file to store results
FNO_STOCKS = [
    "RELIANCE", "HDFCBANK", "INFY", "TCS", "KOTAKBANK", "LT", "AXISBANK", "SBIN", 
    "BAJFINANCE", "TITAN", "ULTRACEMCO", "MARUTI", "ASIANPAINT", "HINDUNILVR", "M&M", 
    "ADANIENT", "GRASIM", "BAJAJFINSV", "NESTLEIND", "EICHERMOT", "DRREDDY", "DIVISLAB", 
    "APOLLOHOSP", "BRITANNIA", "TRENT", "HAL", "BEL", "SIEMENS", "INDIGO", "TATASTEEL", 
    "JIOFIN", "COALINDIA", "HCLTECH", "SUNPHARMA", "ADANIPORTS", "WIPRO"
]

# --- HELPER FUNCTIONS ---

def fetch_stock_data(symbol):
    """Fetches last 40 days of data."""
    try:
        end = datetime.now()
        start = end - timedelta(days=40)
        
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        session = requests.Session()
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=3)
        
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        response = session.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            df = pd.DataFrame(data)
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for col in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']:
                df[col] = df[col].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except:
        return None
    return None

def calculate_trend(df):
    """Runs VNS logic."""
    trend = "Neutral"
    last_bu, last_be = None, None
    
    for i in range(len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1] if i > 0 else None
        
        if prev is not None:
            if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']:
                last_bu = prev['CH_TRADE_HIGH_PRICE']
            if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']:
                last_be = prev['CH_TRADE_LOW_PRICE']
            
            if last_bu and row['CH_CLOSING_PRICE'] > last_bu: trend = "Bullish"
            elif last_be and row['CH_CLOSING_PRICE'] < last_be: trend = "Bearish"

    # Convert last 5 rows to dict for JSON storage
    history = df.tail(5).copy()
    history['Date'] = history['Date'].dt.strftime('%Y-%m-%d')
    history_data = history[['Date', 'CH_CLOSING_PRICE', 'CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE']].to_dict('records')

    return trend, last_bu, last_be, df.iloc[-1]['CH_CLOSING_PRICE'], history_data

def run_full_scan():
    """Performs the actual scanning process."""
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, stock in enumerate(FNO_STOCKS):
        status_text.text(f"Scanning {stock}...")
        df = fetch_stock_data(stock)
        
        if df is not None:
            last_price = df.iloc[-1]['CH_CLOSING_PRICE']
            if last_price > 1000:
                trend, bu, be, close, history = calculate_trend(df)
                results.append({
                    "Symbol": stock,
                    "Trend": trend,
                    "Close": close,
                    "BU": bu,
                    "BE": be,
                    "History": history # Storing small history in JSON
                })
        
        progress_bar.progress((i + 1) / len(FNO_STOCKS))
        time.sleep(0.1) # Be nice to NSE API

    progress_bar.empty()
    status_text.empty()
    
    # Save to JSON File
    today_str = datetime.now().strftime("%Y-%m-%d")
    save_data = {
        "date": today_str,
        "last_updated": datetime.now().strftime("%H:%M:%S"),
        "stocks": results
    }
    
    with open(SCAN_FILE, 'w') as f:
        json.dump(save_data, f)
        
    return save_data

def load_cached_data():
    """Loads data from file if it matches today's date."""
    if not os.path.exists(SCAN_FILE):
        return None
    
    try:
        with open(SCAN_FILE, 'r') as f:
            data = json.load(f)
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # If file date matches today, return data
        if data.get("date") == today_str:
            return data
        else:
            return None # File exists but is old
    except:
        return None

# --- MAIN LOGIC FLOW ---

# 1. Try to load today's data
cached_data = load_cached_data()

# 2. Sidebar Button to Force Refresh
with st.sidebar:
    st.write("Controls")
    force_scan = st.button("🔄 Force Scan Now")

# 3. Logic to decide whether to scan or show
if force_scan:
    st.warning("Forcing new scan...")
    current_data = run_full_scan()
    st.success("Scan Complete!")
    st.rerun() # Refresh to show new data

elif cached_data is None:
    # Auto-Scan triggered because file is missing or old
    st.info("📅 Date changed or no data found. Running Automatic Daily Scan...")
    current_data = run_full_scan()
    st.rerun()

else:
    # Data is fresh and ready
    current_data = cached_data


# --- DISPLAY RESULTS ---
if current_data:
    st.markdown(f"<div class='timestamp'>Last Scanned: {current_data['date']} at {current_data['last_updated']}</div>", unsafe_allow_html=True)
    
    stocks = current_data['stocks']
    bulls = [r for r in stocks if r['Trend'] == "Bullish"]
    bears = [r for r in stocks if r['Trend'] == "Bearish"]
    neutral = [r for r in stocks if r['Trend'] == "Neutral"]

    c1, c2, c3 = st.columns(3)

    # 🟢 BULLISH
    with c1:
        st.header(f"🟢 Bullish ({len(bulls)})")
        for s in bulls:
            with st.expander(f"{s['Symbol']} (₹{s['Close']:.2f})"):
                st.markdown(f"""
                <div class="scan-box bull-box">
                    <b>TEJI</b><br>
                    Res (BU): {s['BU'] if s['BU'] else '-'}<br>
                    Sup (BE): {s['BE'] if s['BE'] else '-'}
                </div>
                """, unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(s['History']))

    # 🔴 BEARISH
    with c2:
        st.header(f"🔴 Bearish ({len(bears)})")
        for s in bears:
            with st.expander(f"{s['Symbol']} (₹{s['Close']:.2f})"):
                st.markdown(f"""
                <div class="scan-box bear-box">
                    <b>MANDI</b><br>
                    Res (BU): {s['BU'] if s['BU'] else '-'}<br>
                    Sup (BE): {s['BE'] if s['BE'] else '-'}
                </div>
                """, unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(s['History']))

    # 🟡 NEUTRAL
    with c3:
        st.header(f"🟡 Neutral ({len(neutral)})")
        for s in neutral:
            with st.expander(f"{s['Symbol']} (₹{s['Close']:.2f})"):
                st.write("No Trend Detected")
                st.dataframe(pd.DataFrame(s['History']))
