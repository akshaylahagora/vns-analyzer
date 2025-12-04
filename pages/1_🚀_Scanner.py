import streamlit as st
import pandas as pd
import requests
import time
import json
import os
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Pro F&O Scanner", page_icon="🔭", layout="wide")

st.title("🔭 Pro F&O Scanner")
st.markdown("Automated VNS Scanner • **cleaner & faster**")

# --- IMPROVED CSS (BEAUTIFUL UI) ---
st.markdown("""
<style>
    /* Global Clean Up */
    .stApp { background-color: #f4f6f9; }
    
    /* Card Design */
    .stock-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 12px;
        border: 1px solid #e0e0e0;
        transition: transform 0.2s;
    }
    .stock-card:hover { transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    
    /* Header Styles */
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .stock-name { font-size: 1.1em; font-weight: 700; color: #2c3e50; }
    .stock-price { font-size: 1em; font-weight: 600; color: #34495e; }
    
    /* VNS Badges */
    .badge { padding: 4px 10px; border-radius: 6px; font-size: 0.8em; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
    .badge-bull { background-color: #e3f9e5; color: #0f5132; border: 1px solid #c3e6cb; }
    .badge-bear { background-color: #ffe5e5; color: #842029; border: 1px solid #f5c6cb; }
    .badge-neutral { background-color: #fff3cd; color: #664d03; border: 1px solid #ffecb5; }
    
    /* Level Indicators */
    .levels { font-size: 0.85em; color: #555; display: flex; justify-content: space-between; background: #f8f9fa; padding: 8px; border-radius: 6px; margin-top: 5px; }
    .lvl-label { font-weight: 600; color: #888; font-size: 0.9em; }
    
    /* Column Headers */
    .col-header { text-align: center; font-weight: 700; padding: 10px; border-radius: 8px; margin-bottom: 15px; color: white; }
    .head-bull { background: #27ae60; }
    .head-bear { background: #c0392b; }
    .head-neutral { background: #7f8c8d; }

    /* Remove default Streamlit expansion gap */
    .streamlit-expanderHeader { font-size: 0.9em; }
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

# --- SESSION STATE (Default 1M) ---
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
    st.header("⚙️ Settings")
    
    st.subheader("1. Period")
    st.radio(
        "Duration", ["1M", "3M", "6M", "1Y"], 
        index=0, # <--- DEFAULT SELECTED IS NOW 1M (Index 0)
        horizontal=True,
        key="scan_duration_selector", 
        on_change=update_scan_dates
    )
    
    st.divider()
    
    st.subheader("2. Price Filter (₹)")
    c1, c2 = st.columns(2)
    min_price = c1.number_input("Min", min_value=0, value=1000, step=100)
    max_price = c2.number_input("Max", min_value=0, value=100000, step=500)
    
    st.divider()
    
    st.subheader("3. Speed")
    scan_delay = st.slider("Delay (sec)", 0.1, 5.0, 0.5, 0.1)
    
    st.markdown("---")
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

    # Table Styling
    def color_rows(row):
        s = row['Type']
        if s == 'bull': return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
        if s == 'bear': return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
        if s == 'warn': return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)
        if s == 'info': return ['background-color: #e2e6ea; color: #0c5460; font-style: italic'] * len(row)
        return [''] * len(row)

    def render_card(stock, type_cls, badge_name):
        res = f"{stock['BU']:.2f}" if stock['BU'] else "-"
        sup = f"{stock['BE']:.2f}" if stock['BE'] else "-"
        
        # HTML Card
        st.markdown(f"""
        <div class="stock-card">
            <div class="card-header">
                <span class="stock-name">{stock['Symbol']}</span>
                <span class="badge {type_cls}">{badge_name}</span>
            </div>
            <div class="stock-price">₹{stock['Close']:.2f}</div>
            <div class="levels">
                <div><span class="lvl-label">RES (BU):</span> {res}</div>
                <div><span class="lvl-label">SUP (BE):</span> {sup}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Expander with Table
        with st.expander("View Details"):
            df = pd.DataFrame(stock['History'])
            st.dataframe(
                df.style.apply(color_rows, axis=1).format({"Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}", "BU": "{:.2f}", "BE": "{:.2f}"}, na_rep=""),
                column_config={"Type": None}, use_container_width=True, height=250
            )

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"<div class='col-header head-bull'>TEJI / BULLISH ({len(bulls)})</div>", unsafe_allow_html=True)
        for s in bulls: render_card(s, "badge-bull", "TEJI")
            
    with c2:
        st.markdown(f"<div class='col-header head-bear'>MANDI / BEARISH ({len(bears)})</div>", unsafe_allow_html=True)
        for s in bears: render_card(s, "badge-bear", "MANDI")

    with c3:
        st.markdown(f"<div class='col-header head-neutral'>NEUTRAL ({len(neutral)})</div>", unsafe_allow_html=True)
        for s in neutral: render_card(s, "badge-neutral", "NEUTRAL")
