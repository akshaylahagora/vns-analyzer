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
st.markdown("Automated VNS Scanner • **Updates daily after 6:00 PM**")

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

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    
    /* Card Container */
    .stock-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 5px;
    }
    .stock-symbol { font-size: 1.1em; font-weight: 800; color: #333; }
    .stock-price { font-size: 1.0em; font-weight: 600; color: #555; }
    
    /* Headers for Columns */
    .col-header { 
        padding: 10px; border-radius: 8px; color: white; 
        font-weight: bold; text-align: center; margin-bottom: 15px; text-transform: uppercase; 
    }
    
    /* Modal/Dialog Styling Fixes */
    div[data-testid="stDialog"] { width: 80vw; } 
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'scan_start_date' not in st.session_state:
    st.session_state.scan_start_date = datetime.now() - timedelta(days=30)
if 'scan_duration_label' not in st.session_state:
    st.session_state.scan_duration_label = "1M"

def update_scan_settings():
    selection = st.session_state.duration_select
    st.session_state.scan_duration_label = selection
    now = datetime.now()
    if selection == "1M": st.session_state.scan_start_date = now - timedelta(days=30)
    elif selection == "3M": st.session_state.scan_start_date = now - timedelta(days=90)
    elif selection == "6M": st.session_state.scan_start_date = now - timedelta(days=180)
    elif selection == "1Y": st.session_state.scan_start_date = now - timedelta(days=365)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Scanner Settings")
    st.subheader("1. Period")
    st.radio("Duration", ["1M", "3M", "6M", "1Y"], index=0, horizontal=True, key="duration_select", on_change=update_scan_settings)
    st.divider()
    st.subheader("2. Price Filter (₹)")
    c1, c2 = st.columns(2)
    view_min_price = c1.number_input("Min", min_value=0, value=1000, step=100)
    view_max_price = c2.number_input("Max", min_value=0, value=100000, step=500)
    st.divider()
    st.subheader("3. Speed")
    scan_delay = st.slider("Delay (sec)", 0.1, 5.0, 0.5, 0.1)
    st.divider()
    force_scan = st.button("🔄 Force Refresh", type="primary", use_container_width=True)

# --- CORE LOGIC ---
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
    duration_used = st.session_state.scan_duration_label
    
    for i, stock in enumerate(FNO_STOCKS):
        status_text.caption(f"Scanning {stock}...")
        df = fetch_stock_data(stock, start_date)
        if df is not None:
            trend, bu, be, close, history = analyze_vns_full(df)
            scan_results.append({ "Symbol": stock, "Trend": trend, "Close": close, "BU": bu, "BE": be, "History": history })
        progress_bar.progress((i + 1) / len(FNO_STOCKS))
        time.sleep(scan_delay) 

    progress_bar.empty(); status_text.empty()
    save_payload = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "last_updated": datetime.now().strftime("%H:%M:%S"),
        "duration_label": duration_used,
        "stocks": scan_results
    }
    with open(SCAN_FILE, 'w') as f: json.dump(save_payload, f)
    return save_payload

def check_auto_scan():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    if not os.path.exists(SCAN_FILE): return True, "Initial Setup"
    try:
        with open(SCAN_FILE, 'r') as f: data = json.load(f)
        file_date = data.get("date")
        if file_date != today_str and now.hour >= 18: return True, "6 PM Update"
        return False, data
    except: return True, "Error"

# --- MAIN CONTROLLER ---
should_scan, payload = check_auto_scan()

if force_scan:
    st.toast("Forcing Refresh...")
    current_data = run_full_scan()
    st.rerun()
elif should_scan is True:
    st.info(f"📅 Running Auto-Scan ({payload})...")
    current_data = run_full_scan()
    st.rerun()
else:
    current_data = payload

# --- POPUP DIALOG ---
@st.dialog("Stock Details", width="large")
def show_details(stock):
    st.subheader(f"{stock['Symbol']} : ₹{stock['Close']:.2f}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Trend", stock['Trend'])
    m2.metric("Resistance (BU)", f"{stock['BU']:.2f}" if stock['BU'] else "-")
    m3.metric("Support (BE)", f"{stock['BE']:.2f}" if stock['BE'] else "-")
    
    st.divider()
    
    def color_rows(row):
        s = row['Type']
        if s == 'bull': return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
        if s == 'bear': return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
        if s == 'warn': return ['background-color: #fff3cd; color: #664d03; font-weight: bold'] * len(row)
        if s == 'info': return ['background-color: #e2e6ea; color: #0c5460; font-style: italic'] * len(row)
        return [''] * len(row)

    hist_df = pd.DataFrame(stock['History'])
    st.dataframe(
        hist_df.style.apply(color_rows, axis=1).format({
            "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}", "BU": "{:.2f}", "BE": "{:.2f}"
        }, na_rep=""),
        column_config={"Type": None}, 
        use_container_width=True, 
        height=500
    )

# --- RENDER UI ---
if current_data:
    data_duration = current_data.get('duration_label', 'Unknown')
    st.caption(f"Last Scanned: {current_data['date']} {current_data['last_updated']} | Data Duration: {data_duration}")
    
    if data_duration != st.session_state.scan_duration_label:
        st.warning(f"⚠️ Data is {data_duration}, but you selected {st.session_state.scan_duration_label}. Click Force Refresh.")

    all_stocks = current_data['stocks']
    filtered_stocks = [s for s in all_stocks if view_min_price <= s['Close'] <= view_max_price]

    bulls = [r for r in filtered_stocks if r['Trend'] == "Bullish"]
    bears = [r for r in filtered_stocks if r['Trend'] == "Bearish"]
    neutral = [r for r in filtered_stocks if r['Trend'] == "Neutral"]

    def render_list(stock_list, header_text, header_color):
        st.markdown(f"""
        <div style="background-color:{header_color}; padding:8px; border-radius:6px; color:white; font-weight:bold; text-align:center; margin-bottom:10px;">
            {header_text} ({len(stock_list)})
        </div>
        """, unsafe_allow_html=True)
        
        for s in stock_list:
            # FIX: Format strings BEFORE putting in HTML
            bu_text = f"{s['BU']:.2f}" if s['BU'] else "-"
            be_text = f"{s['BE']:.2f}" if s['BE'] else "-"

            st.markdown(f"""
            <div class="stock-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="stock-symbol">{s['Symbol']}</span>
                    <span class="stock-price">₹{s['Close']:.2f}</span>
                </div>
                <div style="font-size:0.85em; color:#666; margin-top:5px; display:flex; justify-content:space-between;">
                    <span>BU: {bu_text}</span>
                    <span>BE: {be_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🔍 View {s['Symbol']}", key=f"btn_{s['Symbol']}", use_container_width=True):
                show_details(s)

    c1, c2, c3 = st.columns(3)
    with c1: render_list(bulls, "🟢 BULLISH / TEJI", "#28a745")
    with c2: render_list(bears, "🔴 BEARISH / MANDI", "#dc3545")
    with c3: render_list(neutral, "⚪ NEUTRAL", "#6c757d")
