import streamlit as st
import pandas as pd
import requests
import time
import json
import os
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pro F&O Scanner", page_icon="🔭", layout="wide")

st.title("🔭 Pro F&O Scanner")
st.markdown("Automated VNS Scanner • **Clean View**")

# --- CONFIGURATION ---
SCAN_FILE = "daily_scan_results.json" 

# Broad list of F&O Stocks
FNO_STOCKS = [
    "RELIANCE", "HDFCBANK", "INFY", "TCS", "KOTAKBANK", "LT", "AXISBANK", "SBIN", 
    "BAJFINANCE", "TITAN", "ULTRACEMCO", "MARUTI", "ASIANPAINT", "HINDUNILVR", "M&M", 
    "ADANIENT", "GRASIM", "BAJAJFINSV", "NESTLEIND", "EICHERMOT", "DRREDDY", "DIVISLAB", 
    "APOLLOHOSP", "BRITANNIA", "TRENT", "HAL", "BEL", "SIEMENS", "INDIGO", "TATASTEEL", 
    "JIOFIN", "COALINDIA", "HCLTECH", "SUNPHARMA", "ADANIPORTS", "WIPRO", "VEDL", "DLF",
    "POLYCAB", "HAVELLS", "SRF", "TATAMOTORS", "MRF", "SHREECEM", "BOSCHLTD"
]

# --- SESSION STATE ---
if 'scan_start_date' not in st.session_state:
    st.session_state.scan_start_date = datetime.now() - timedelta(days=30) # Default 1M
if 'scan_duration_label' not in st.session_state:
    st.session_state.scan_duration_label = "1M"

def update_scan_dates():
    selection = st.session_state.scan_duration_selector
    st.session_state.scan_duration_label = selection
    now = datetime.now()
    if selection == "1M": st.session_state.scan_start_date = now - timedelta(days=30)
    elif selection == "3M": st.session_state.scan_start_date = now - timedelta(days=90)
    elif selection == "6M": st.session_state.scan_start_date = now - timedelta(days=180)
    elif selection == "1Y": st.session_state.scan_start_date = now - timedelta(days=365)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Scanner Settings")
    
    st.subheader("1. Period")
    st.radio("Duration", ["1M", "3M", "6M", "1Y"], index=0, horizontal=True, key="scan_duration_selector", on_change=update_scan_dates)
    
    st.divider()
    
    st.subheader("2. Price Filter (₹)")
    c1, c2 = st.columns(2)
    min_price = c1.number_input("Min", min_value=0, value=1000, step=100)
    max_price = c2.number_input("Max", min_value=0, value=100000, step=500)
    
    st.divider()
    
    st.subheader("3. Speed")
    scan_delay = st.slider("Delay (sec)", 0.1, 5.0, 0.5, 0.1)
    
    st.divider()
    force_scan = st.button("🔄 Force Refresh", type="primary", use_container_width=True)

# --- CORE FUNCTIONS ---
def fetch_stock_data(symbol, start_date):
    try:
        end = datetime.now()
        req_start = start_date - timedelta(days=5) 
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        session = requests.Session(); session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=3)
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={req_start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            df = pd.DataFrame(response.json().get('data', []))
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for col in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']:
                df[col] = df[col].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except: return None
    return None

def analyze_vns_full(df):
    results = []
    trend = "Neutral"
    last_bu, last_be = None, None
    for i in range(len(df)):
        row = df.iloc[i]; prev = df.iloc[i-1] if i > 0 else None
        bu, be, signal, signal_type = None, None, "", ""
        if prev is not None:
            if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']: bu = prev['CH_TRADE_HIGH_PRICE']; last_bu = bu
            if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']: be = prev['CH_TRADE_LOW_PRICE']; last_be = be
            
            if last_bu and row['CH_CLOSING_PRICE'] > last_bu and trend != "Bullish":
                trend = "Bullish"; signal = "TEJI (Breakout)"; signal_type = "bull"
            elif last_be and row['CH_CLOSING_PRICE'] < last_be and trend != "Bearish":
                trend = "Bearish"; signal = "MANDI (Breakdown)"; signal_type = "bear"
            elif trend == "Bullish" and last_bu and (row['CH_TRADE_HIGH_PRICE'] >= last_bu * 0.995) and row['CH_CLOSING_PRICE'] < last_bu:
                signal = "ATAK (Top)"; signal_type = "warn"
            elif trend == "Bearish" and last_be and (row['CH_TRADE_LOW_PRICE'] <= last_be * 1.005) and row['CH_CLOSING_PRICE'] > last_be:
                signal = "ATAK (Bottom)"; signal_type = "warn"
            else:
                if trend == "Bullish":
                    if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']: signal = "Reaction (Buy)"; signal_type = "info"
                    elif row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']: signal = "Teji Cont."; signal_type = "bull_light"
                elif trend == "Bearish":
                    if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']: signal = "Reaction (Sell)"; signal_type = "info"
                    elif row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']: signal = "Mandi Cont."; signal_type = "bear_light"
        
        results.append({
            'Date': row['Date'].strftime('%d-%b-%Y'), 'Open': row['CH_OPENING_PRICE'], 
            'High': row['CH_TRADE_HIGH_PRICE'], 'Low': row['CH_TRADE_LOW_PRICE'], 
            'Close': row['CH_CLOSING_PRICE'], 'BU': bu, 'BE': be, 'Signal': signal, 'Type': signal_type
        })
    return trend, last_bu, last_be, df.iloc[-1]['CH_CLOSING_PRICE'], results

def run_full_scan():
    progress_bar = st.progress(0)
    status_text = st.empty()
    scan_results = []
    start_date = st.session_state.scan_start_date
    
    for i, stock in enumerate(FNO_STOCKS):
        status_text.caption(f"Analyzing {stock}...")
        df = fetch_stock_data(stock, start_date)
        if df is not None:
            last_price = df.iloc[-1]['CH_CLOSING_PRICE']
            if min_price <= last_price <= max_price:
                trend, bu, be, close, history = analyze_vns_full(df)
                scan_results.append({ "Symbol": stock, "Trend": trend, "Close": close, "BU": bu, "BE": be, "History": history })
        progress_bar.progress((i + 1) / len(FNO_STOCKS))
        time.sleep(scan_delay) 

    progress_bar.empty(); status_text.empty()
    save_payload = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "last_updated": datetime.now().strftime("%H:%M:%S"),
        "config": { "duration": st.session_state.scan_duration_label, "min_price": min_price, "max_price": max_price },
        "stocks": scan_results
    }
    with open(SCAN_FILE, 'w') as f: json.dump(save_payload, f)
    return save_payload

def load_data():
    if not os.path.exists(SCAN_FILE): return None
    try:
        with open(SCAN_FILE, 'r') as f: data = json.load(f)
        if data.get("date") != datetime.now().strftime("%Y-%m-%d"): return None
        saved_config = data.get("config", {})
        if saved_config.get("duration") != st.session_state.scan_duration_label: return None
        if saved_config.get("min_price") != min_price: return None
        if saved_config.get("max_price") != max_price: return None
        return data
    except: return None

# --- MAIN LOGIC ---
cached = load_data()
if force_scan:
    st.toast("Forcing Refresh..."); current_data = run_full_scan(); st.rerun()
elif cached is None:
    st.info(f"📅 Running Daily Scan ({st.session_state.scan_duration_label})..."); current_data = run_full_scan(); st.rerun()
else:
    current_data = cached

# --- RENDER UI ---
if current_data:
    st.caption(f"Last Update: {current_data['last_updated']} | Duration: {current_data['config']['duration']}")
    
    stocks = current_data['stocks']
    bulls = [r for r in stocks if r['Trend'] == "Bullish"]
    bears = [r for r in stocks if r['Trend'] == "Bearish"]
    neutral = [r for r in stocks if r['Trend'] == "Neutral"]

    # --- READABLE TABLE STYLING ---
    # Used high contrast colors for text
    def color_rows(row):
        s = row['Type']
        # Light Green bg, Dark Green text
        if s == 'bull': return ['background-color: #d4edda; color: #0f5132; font-weight: bold'] * len(row)
        # Light Red bg, Dark Red text
        if s == 'bear': return ['background-color: #f8d7da; color: #842029; font-weight: bold'] * len(row)
        # Light Yellow bg, Dark Brown text
        if s == 'warn': return ['background-color: #fff3cd; color: #664d03; font-weight: bold'] * len(row)
        # Light Blue bg, Dark Blue text
        if s == 'info': return ['background-color: #cff4fc; color: #055160; font-style: italic'] * len(row)
        return [''] * len(row)

    def render_list(stock_list, header_emoji, header_text, header_color):
        # Header with distinct background
        st.markdown(f"""
        <div style="background-color:{header_color}; padding:10px; border-radius:8px; color:white; font-weight:bold; text-align:center; margin-bottom:10px;">
            {header_emoji} {header_text} ({len(stock_list)})
        </div>
        """, unsafe_allow_html=True)
        
        for s in stock_list:
            # Clean Title: SYMBOL  |  PRICE
            label = f"**{s['Symbol']}** :  ₹{s['Close']:.2f}"
            
            with st.expander(label):
                # 1. Summary Metrics inside expander
                m1, m2 = st.columns(2)
                m1.metric("Resistance (BU)", f"{s['BU']:.2f}" if s['BU'] else "-")
                m2.metric("Support (BE)", f"{s['BE']:.2f}" if s['BE'] else "-")
                
                st.divider()
                
                # 2. Readable Table
                hist_df = pd.DataFrame(s['History'])
                st.dataframe(
                    hist_df.style.apply(color_rows, axis=1).format({
                        "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}", "BU": "{:.2f}", "BE": "{:.2f}"
                    }, na_rep=""),
                    column_config={"Type": None}, # Hide Type col
                    use_container_width=True, 
                    height=300
                )

    c1, c2, c3 = st.columns(3)
    
    with c1:
        render_list(bulls, "📈", "BULLISH / TEJI", "#28a745") # Green Header
            
    with c2:
        render_list(bears, "📉", "BEARISH / MANDI", "#dc3545") # Red Header

    with c3:
        render_list(neutral, "⚪", "NEUTRAL", "#6c757d") # Grey Header
