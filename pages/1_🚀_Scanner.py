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
st.markdown("Automated VNS Scanner with Dynamic Controls.")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .scan-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ddd; }
    
    /* Box Colors */
    .bull-box { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
    .bear-box { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
    .neutral-box { background-color: #fff3cd; border-color: #ffeeba; color: #856404; }
    
    /* Timestamp footer */
    .timestamp { font-size: 0.8em; color: #666; font-style: italic; margin-bottom: 10px; }
    
    /* Sidebar Input Styling */
    div[data-testid="stInput"] > div { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
SCAN_FILE = "daily_scan_results.json" 

# Broad list of F&O Stocks
FNO_STOCKS = [
    "RELIANCE", "HDFCBANK", "INFY", "TCS", "KOTAKBANK", "LT", "AXISBANK", "SBIN", 
    "BAJFINANCE", "TITAN", "ULTRACEMCO", "MARUTI", "ASIANPAINT", "HINDUNILVR", "M&M", 
    "ADANIENT", "GRASIM", "BAJAJFINSV", "NESTLEIND", "EICHERMOT", "DRREDDY", "DIVISLAB", 
    "APOLLOHOSP", "BRITANNIA", "TRENT", "HAL", "BEL", "SIEMENS", "INDIGO", "TATASTEEL", 
    "JIOFIN", "COALINDIA", "HCLTECH", "SUNPHARMA", "ADANIPORTS", "WIPRO", "VEDL", "DLF",
    "POLYCAB", "HAVELLS", "SRF", "EICHERMOT", "TATAMOTORS", "MRF", "SHREECEM", "BOSCHLTD"
]

# --- SESSION STATE INITIALIZATION ---
if 'scan_start_date' not in st.session_state:
    st.session_state.scan_start_date = datetime.now() - timedelta(days=90)
if 'scan_duration_label' not in st.session_state:
    st.session_state.scan_duration_label = "3M"

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
    
    # 1. Date Range
    st.subheader("1. Analysis Period")
    st.radio(
        "Duration", ["1M", "3M", "6M", "1Y"], index=1, horizontal=True,
        key="scan_duration_selector", on_change=update_scan_dates
    )
    
    st.divider()
    
    # 2. Price Band (Dynamic - No Hard Cap)
    st.subheader("2. Price Filter (₹)")
    c1, c2 = st.columns(2)
    # Default is 1000, but min is 0. Max is effectively infinite.
    min_price = c1.number_input("Min Price", min_value=0, value=1000, step=100)
    # Default is 100,000 to cover MRF, but user can type higher.
    max_price = c2.number_input("Max Price", min_value=0, value=100000, step=500)
    
    st.divider()
    
    # 3. Request Speed (Dynamic)
    st.subheader("3. Scan Speed")
    scan_delay = st.slider(
        "Delay between requests (seconds)", 
        min_value=0.1, max_value=5.0, value=0.5, step=0.1,
        help="Increase this if you encounter connection errors or blocking."
    )
    
    st.divider()
    force_scan = st.button("🔄 Force Scan Now", type="primary", use_container_width=True)

# --- CORE FUNCTIONS ---

def fetch_stock_data(symbol, start_date):
    """Fetches data from start_date to now."""
    try:
        end = datetime.now()
        req_start = start_date - timedelta(days=5) # Buffer
        
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
        row = df.iloc[i]
        prev = df.iloc[i-1] if i > 0 else None
        bu, be, signal, signal_type = None, None, "", ""
        
        if prev is not None:
            if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']: bu = prev['CH_TRADE_HIGH_PRICE']; last_bu = bu
            if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']: be = prev['CH_TRADE_LOW_PRICE']; last_be = be
            
            if last_bu and row['CH_CLOSING_PRICE'] > last_bu and trend != "Bullish":
                trend = "Bullish"; signal = "TEJI (Breakout)"; signal_type = "bull"
            elif last_be and row['CH_CLOSING_PRICE'] < last_be and trend != "Bearish":
                trend = "Bearish"; signal = "MANDI (Breakdown)"; signal_type = "bear"
            elif trend == "Bullish" and last_bu and (row['CH_TRADE_HIGH_PRICE'] >= last_bu * 0.995) and row['CH_CLOSING_PRICE'] < last_bu:
                signal = "ATAK (Double Top)"; signal_type = "warn"
            elif trend == "Bearish" and last_be and (row['CH_TRADE_LOW_PRICE'] <= last_be * 1.005) and row['CH_CLOSING_PRICE'] > last_be:
                signal = "ATAK (Double Bottom)"; signal_type = "warn"
            else:
                if trend == "Bullish":
                    if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']: signal = "Reaction (Buy Dip)"; signal_type = "info"
                    elif row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']: signal = "Teji Continuation"; signal_type = "bull_light"
                elif trend == "Bearish":
                    if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']: signal = "Reaction (Sell Rise)"; signal_type = "info"
                    elif row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']: signal = "Mandi Continuation"; signal_type = "bear_light"
        
        results.append({
            'Date': row['Date'].strftime('%d-%b-%Y'), 
            'Open': row['CH_OPENING_PRICE'], 'High': row['CH_TRADE_HIGH_PRICE'],
            'Low': row['CH_TRADE_LOW_PRICE'], 'Close': row['CH_CLOSING_PRICE'],
            'BU': bu, 'BE': be, 'Signal': signal, 'Type': signal_type
        })
        
    return trend, last_bu, last_be, df.iloc[-1]['CH_CLOSING_PRICE'], results

def run_full_scan():
    progress_bar = st.progress(0)
    status_text = st.empty()
    scan_results = []
    
    start_date = st.session_state.scan_start_date
    
    for i, stock in enumerate(FNO_STOCKS):
        status_text.text(f"Scanning {stock}...")
        df = fetch_stock_data(stock, start_date)
        
        if df is not None:
            last_price = df.iloc[-1]['CH_CLOSING_PRICE']
            
            # --- DYNAMIC PRICE FILTER (UNRESTRICTED) ---
            if min_price <= last_price <= max_price:
                trend, bu, be, close, history = analyze_vns_full(df)
                scan_results.append({
                    "Symbol": stock, "Trend": trend, "Close": close,
                    "BU": bu, "BE": be, "History": history
                })
        
        progress_bar.progress((i + 1) / len(FNO_STOCKS))
        
        # --- DYNAMIC DELAY ---
        time.sleep(scan_delay) 

    progress_bar.empty()
    status_text.empty()
    
    # Save Data + METADATA
    save_payload = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "last_updated": datetime.now().strftime("%H:%M:%S"),
        "config": {
            "duration": st.session_state.scan_duration_label,
            "min_price": min_price,
            "max_price": max_price
        },
        "stocks": scan_results
    }
    
    with open(SCAN_FILE, 'w') as f:
        json.dump(save_payload, f)
        
    return save_payload

def load_data():
    if not os.path.exists(SCAN_FILE): return None
    try:
        with open(SCAN_FILE, 'r') as f: data = json.load(f)
        
        # 1. Check Date
        if data.get("date") != datetime.now().strftime("%Y-%m-%d"): return None
        
        # 2. Check Settings (If user changed price band, we must re-scan)
        saved_config = data.get("config", {})
        if saved_config.get("duration") != st.session_state.scan_duration_label: return None
        if saved_config.get("min_price") != min_price: return None
        if saved_config.get("max_price") != max_price: return None
            
        return data
    except: return None

# --- MAIN LOGIC ---

cached = load_data()

# Trigger Logic
if force_scan:
    st.toast(f"Starting Force Scan (Delay: {scan_delay}s)...")
    current_data = run_full_scan()
    st.rerun()
elif cached is None:
    st.info(f"📅 Scanning New Settings ({st.session_state.scan_duration_label} | ₹{min_price}-{max_price})...")
    current_data = run_full_scan()
    st.rerun()
else:
    current_data = cached

# --- RENDER RESULTS ---

if current_data:
    st.markdown(f"<div class='timestamp'>Last Updated: {current_data['last_updated']} | Range: {current_data['config']['duration']} | Filter: ₹{current_data['config']['min_price']} - ₹{current_data['config']['max_price']}</div>", unsafe_allow_html=True)
    
    stocks = current_data['stocks']
    bulls = [r for r in stocks if r['Trend'] == "Bullish"]
    bears = [r for r in stocks if r['Trend'] == "Bearish"]
    neutral = [r for r in stocks if r['Trend'] == "Neutral"]

    c1, c2, c3 = st.columns(3)

    # Style Function
    def color_rows(row):
        s = row['Type']
        if s == 'bull': return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
        if s == 'bear': return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
        if s == 'warn': return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)
        if s == 'info': return ['background-color: #e2e6ea; color: #0c5460; font-style: italic'] * len(row)
        return [''] * len(row)

    def render_list(stock_list, col_type):
        for s in stock_list:
            res_txt = f"BU: {s['BU']:.2f}" if s['BU'] else "BU: -"
            sup_txt = f"BE: {s['BE']:.2f}" if s['BE'] else "BE: -"
            css_class = "bull-box" if col_type == "bull" else "bear-box" if col_type == "bear" else "neutral-box"
            
            with st.expander(f"{s['Symbol']} (₹{s['Close']:.2f})"):
                st.markdown(f"""
                <div class="scan-box {css_class}">
                    <div style="display:flex; justify-content:space-between;">
                        <span>{res_txt}</span><span>{sup_txt}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                # Full Table
                hist_df = pd.DataFrame(s['History'])
                st.dataframe(
                    hist_df.style.apply(color_rows, axis=1).format({
                        "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}",
                        "BU": "{:.2f}", "BE": "{:.2f}"
                    }, na_rep=""),
                    column_config={"Type": None}, use_container_width=True, height=300
                )

    with c1:
        st.header(f"🟢 Bullish ({len(bulls)})")
        render_list(bulls, "bull")
    with c2:
        st.header(f"🔴 Bearish ({len(bears)})")
        render_list(bears, "bear")
    with c3:
        st.header(f"🟡 Neutral ({len(neutral)})")
        render_list(neutral, "neutral")
