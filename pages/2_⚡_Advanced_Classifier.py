import streamlit as st
import pandas as pd
import requests
import urllib.parse
import time
import json
import os
import yfinance as yf
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Advanced Classifier", page_icon="⚡", layout="wide")

st.title("⚡ Advanced VNS Classifier")
st.markdown("Identifies **Breakouts**, **Trend Continuation**, and **Reversal Risks**. • **Auto-Saves Results**")

# --- PRO CSS ---
st.markdown("""
<style>
    /* Force Light Mode */
    .stApp { background-color: white; color: black; }
    
    /* VISIBILITY FIXES */
    div[data-testid="stMetricValue"] { color: #000000 !important; }
    div[data-testid="stMetricLabel"] { color: #444444 !important; }
    
    /* MODAL METRIC CARDS */
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-label { font-size: 0.8rem; font-weight: 600; color: #666; text-transform: uppercase; margin-bottom: 4px; }
    .metric-value { font-size: 1.2rem; font-weight: 800; color: #000; }
    
    /* CARD DESIGN */
    .class-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 12px;
        border-left-width: 6px;
        border-left-style: solid;
        border-top: 1px solid #eee;
        border-right: 1px solid #eee;
        border-bottom: 1px solid #eee;
        transition: transform 0.1s;
    }
    .class-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
    
    /* TEXT STYLES */
    .stock-title { font-size: 1.2rem; font-weight: 800; color: #2c3e50 !important; }
    .stock-price { font-size: 1.1rem; font-weight: 600; color: #333 !important; }
    .signal-text { font-size: 0.9rem; font-weight: 600; margin-top: 5px; color: #555 !important; }
    
    /* CHANGE BADGES */
    .chg-green { color: #008000 !important; font-weight: bold; font-size: 0.9rem; }
    .chg-red { color: #d63031 !important; font-weight: bold; font-size: 0.9rem; }
    
    /* BORDER COLORS */
    .b-high-bull { border-left-color: #00b894; } 
    .b-bull { border-left-color: #55efc4; }      
    .b-high-bear { border-left-color: #d63031; } 
    .b-bear { border-left-color: #fab1a0; }      
    .b-atak-top { border-left-color: #e17055; }  
    .b-atak-bot { border-left-color: #fdcb6e; }  
    
    /* LINK BUTTON */
    .chart-link {
        text-decoration: none; font-size: 0.8rem; color: #0984e3 !important; font-weight: bold; float: right;
    }
    .chart-link:hover { text-decoration: underline; }
    
    /* Sidebar text fix */
    .stSidebar label { color: #333 !important; }
    div[data-testid="stDialog"] { width: 85vw; } 
    
    /* Table Fix */
    .stDataFrame td { white-space: pre-wrap !important; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
CLASS_FILE = "daily_classification_results.json" 

# --- SECTOR MAPPING (180 Stocks) ---
SECTOR_MAP = {
    "NIFTY": "Index", "BANKNIFTY": "Index",
    "RELIANCE": "Energy", "ONGC": "Energy", "COALINDIA": "Energy", "NTPC": "Energy", "POWERGRID": "Energy", "TATAPOWER": "Energy", "ADANIGREEN": "Energy", "ADANIENSOL": "Energy", "IOC": "Energy", "BPCL": "Energy", "GAIL": "Energy", "PETRONET": "Energy", "OIL": "Energy",
    "HDFCBANK": "Banking", "ICICIBANK": "Banking", "SBIN": "Banking", "AXISBANK": "Banking", "KOTAKBANK": "Banking", "INDUSINDBK": "Banking", "AUBANK": "Banking", "BANDHANBNK": "Banking", "BANKBARODA": "Banking", "FEDERALBNK": "Banking", "IDFCFIRSTB": "Banking", "PNB": "Banking", "RBLBANK": "Banking", "CANBK": "Banking",
    "TCS": "IT", "INFY": "IT", "HCLTECH": "IT", "WIPRO": "IT", "TECHM": "IT", "LTIM": "IT", "PERSISTENT": "IT", "COFORGE": "IT", "MPHASIS": "IT", "LTTS": "IT", "TATAELXSI": "IT",
    "MARUTI": "Auto", "TATAMOTORS": "Auto", "M&M": "Auto", "BAJAJ-AUTO": "Auto", "EICHERMOT": "Auto", "HEROMOTOCO": "Auto", "TVSMOTOR": "Auto", "ASHOKLEY": "Auto", "BHARATFORG": "Auto", "BALKRISIND": "Auto", "MRF": "Auto", "BOSCHLTD": "Auto", "MOTHERSON": "Auto",
    "SUNPHARMA": "Pharma", "DRREDDY": "Pharma", "CIPLA": "Pharma", "DIVISLAB": "Pharma", "APOLLOHOSP": "Pharma", "LUPIN": "Pharma", "AUROPHARMA": "Pharma", "ALKEM": "Pharma", "BIOCON": "Pharma", "TORNTPHARM": "Pharma", "ZYDUSLIFE": "Pharma", "SYNGENE": "Pharma", "LAURUSLABS": "Pharma", "GLENMARK": "Pharma", "GRANULES": "Pharma",
    "ITC": "FMCG", "HINDUNILVR": "FMCG", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG", "TATACONSUM": "FMCG", "MARICO": "FMCG", "DABUR": "FMCG", "COLPAL": "FMCG", "GODREJCP": "FMCG", "UBL": "FMCG", "VBL": "FMCG",
    "BAJFINANCE": "Finance", "BAJAJFINSV": "Finance", "CHOLAFIN": "Finance", "SHRIRAMFIN": "Finance", "MUTHOOTFIN": "Finance", "SBICARD": "Finance", "HDFCLIFE": "Finance", "SBILIFE": "Finance", "ICICIPRULI": "Finance", "ICICIGI": "Finance", "PFC": "Finance", "RECLTD": "Finance", "ABCAPITAL": "Finance", "LICHSGFIN": "Finance", "M&MFIN": "Finance", "MANAPPURAM": "Finance",
    "TATASTEEL": "Metal", "HINDALCO": "Metal", "JSWSTEEL": "Metal", "VEDL": "Metal", "SAIL": "Metal", "NMDC": "Metal", "NATIONALUM": "Metal", "JINDALSTEL": "Metal",
    "ULTRACEMCO": "Cement", "GRASIM": "Cement", "AMBUJACEM": "Cement", "ACC": "Cement", "SHREECEM": "Cement", "DALBHARAT": "Cement", "RAMCOCEM": "Cement",
    "LT": "Infra", "ADANIENT": "Infra", "ADANIPORTS": "Infra", "DLF": "Realty", "GODREJPROP": "Realty", "OBEROIRLTY": "Realty", "HAL": "Defence", "BEL": "Defence", "BDL": "Defence", "INDIGO": "Aviation",
    "TITAN": "Consumer", "ASIANPAINT": "Consumer", "BERGEPAINT": "Consumer", "HAVELLS": "Consumer", "VOLTAS": "Consumer", "TRENT": "Consumer", "PIDILITIND": "Consumer", "PAGEIND": "Consumer", "JIOFIN": "Finance", "BHARTIARTL": "Telecom", "IDEA": "Telecom", "INDHOTEL": "Hospitality"
}

FNO_STOCKS_LIST = list(SECTOR_MAP.keys())
FNO_STOCKS_LIST.sort()

# --- SESSION STATE ---
if 'class_start_date' not in st.session_state:
    st.session_state.class_start_date = datetime.now() - timedelta(days=90) # Default 3M
if 'class_duration_label' not in st.session_state:
    st.session_state.class_duration_label = "3M"
if 'custom_date_range' not in st.session_state:
    st.session_state.custom_date_range = (datetime.now() - timedelta(days=90), datetime.now())

def update_class_settings():
    selection = st.session_state.class_duration_select
    st.session_state.class_duration_label = selection
    now = datetime.now()
    if selection == "1M": st.session_state.class_start_date = now - timedelta(days=30)
    elif selection == "2M": st.session_state.class_start_date = now - timedelta(days=60)
    elif selection == "3M": st.session_state.class_start_date = now - timedelta(days=90)
    elif selection == "6M": st.session_state.class_start_date = now - timedelta(days=180)
    elif selection == "1Y": st.session_state.class_start_date = now - timedelta(days=365)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.subheader("1. Analysis Period")
    st.info("Changing Period triggers a new scan.")
    period_sel = st.radio("Duration", ["1M", "2M", "3M", "6M", "1Y", "Custom"], index=2, horizontal=True, key="class_duration_select", on_change=update_class_settings)
    
    if period_sel == "Custom":
        c_dates = st.date_input("Select Range", value=st.session_state.custom_date_range)
        if len(c_dates) == 2:
            st.session_state.class_start_date = datetime.combine(c_dates[0], datetime.min.time())
            st.session_state.custom_date_range = c_dates
    
    st.divider()
    
    st.subheader("2. View Filters")
    c1, c2 = st.columns(2)
    view_min = c1.number_input("Min Price", 0, value=1000, step=100) 
    view_max = c2.number_input("Max Price", 0, value=100000, step=500)
    
    category_filter = st.selectbox("Category", ["All", "Bullish Only", "Bearish Only", "Atak Only", "High Momentum Only"])
    sector_filter = st.selectbox("Sector", ["All"] + sorted(list(set(SECTOR_MAP.values()))))
    
    st.divider()
    force_scan = st.button("🔄 Force Refresh Now", type="primary", use_container_width=True)

# --- CORE LOGIC ---
def fetch_stock_data(symbol, start_date):
    try:
        safe_symbol = urllib.parse.quote(symbol)
        end = datetime.now()
        req_start = start_date - timedelta(days=5)
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        s = requests.Session(); s.headers.update(headers); s.get("https://www.nseindia.com", timeout=3)
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={req_start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={safe_symbol}&type=priceVolumeDeliverable&series=ALL"
        r = s.get(url, timeout=5)
        if r.status_code == 200:
            df = pd.DataFrame(r.json().get('data', []))
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for c in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE', 'CH_PREVIOUS_CLS_PRICE']: 
                df[c] = df[c].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except: return None
    return None

def classify_stock(df):
    trend = "Neutral"; last_peak = df.iloc[0]['CH_TRADE_HIGH_PRICE']; last_trough = df.iloc[0]['CH_TRADE_LOW_PRICE']
    reaction_support = df.iloc[0]['CH_TRADE_LOW_PRICE']; reaction_resist = df.iloc[0]['CH_TRADE_HIGH_PRICE']
    last_peak_idx=0; last_trough_idx=0
    signal_desc = "Neutral"; category = "Neutral"; history_records = []
    
    for i in range(1, len(df)):
        curr = df.iloc[i]; c_h, c_l = curr['CH_TRADE_HIGH_PRICE'], curr['CH_TRADE_LOW_PRICE']
        bu, be, signal, signal_type = None, None, "", ""
        
        # TEJI (Up)
        if trend == "Teji":
            if c_h > last_peak:
                bu = f"T (Teji)\n{c_h:.2f}"; signal_type="bull_dark"; signal="New High"
                swing = df.iloc[last_peak_idx:i+1]; reaction_support = swing['CH_TRADE_LOW_PRICE'].min()
                be = f"R (Sup)\n{reaction_support:.2f}"
                last_peak = c_h; last_peak_idx = i
            elif c_l < reaction_support:
                bu = f"ATAK (Top)\n{last_peak:.2f}"; be = f"M (Mandi)\n{c_l:.2f}"; signal_type="bear_dark"; signal="Reversal"
                trend = "Mandi"; last_trough = c_l; last_trough_idx = i; reaction_resist = c_h

        # MANDI (Down)
        elif trend == "Mandi":
            if c_l < last_trough:
                be = f"M (Mandi)\n{c_l:.2f}"; signal_type="bear_dark"; signal="New Low"
                swing = df.iloc[last_trough_idx:i+1]; reaction_resist = swing['CH_TRADE_HIGH_PRICE'].max()
                bu = f"R (Resist)\n{reaction_resist:.2f}"
                last_trough = c_l; last_trough_idx = i
            elif c_h > reaction_resist:
                be = f"ATAK (Bot)\n{last_trough:.2f}"; bu = f"T (Teji)\n{c_h:.2f}"; signal_type="bull_dark"; signal="Reversal"
                trend = "Teji"; last_peak = c_h; last_peak_idx = i; reaction_support = c_l
        
        # NEUTRAL
        else:
            if c_h > last_peak: trend="Teji"; bu="Start Teji"; signal_type="bull_dark"; last_peak=c_h; last_peak_idx=i
            elif c_l < last_trough: trend="Mandi"; be="Start Mandi"; signal_type="bear_dark"; last_trough=c_l; last_trough_idx=i

        # Map Color Types for History
        color_type = ""
        if "T (Teji)" in str(bu) or "Start Teji" in str(bu): color_type = "bull_dark"
        elif "M (Mandi)" in str(be) or "Start Mandi" in str(be): color_type = "bear_dark"
        elif "ATAK (Top)" in str(bu) or "R (Resist)" in str(bu): color_type = "bear_light"
        elif "ATAK (Bot)" in str(be) or "R (Sup)" in str(be): color_type = "bull_light"

        history_records.append({
            'Date': curr['Date'].strftime('%d-%b-%Y'), 'Open': curr['CH_OPENING_PRICE'], 'High': curr['CH_TRADE_HIGH_PRICE'],
            'Low': curr['CH_TRADE_LOW_PRICE'], 'Close': curr['CH_CLOSING_PRICE'], 'BU': bu, 'BE': be, 'Signal': signal, 'Type': color_type
        })
        
        if i == len(df) - 1:
            signal_desc = signal
            if "Reversal" in signal and trend == "Teji": category = "Highly Bullish"
            elif "Reversal" in signal and trend == "Mandi": category = "Highly Bearish"
            elif trend == "Teji": category = "Bullish"
            elif trend == "Mandi": category = "Bearish"
            
            if last_bu and (last_bu*0.995 <= c_h <= last_bu*1.005) and curr['CH_CLOSING_PRICE'] < last_bu: category = "Atak (Teji Side)"
            if last_be and (last_be*0.995 <= c_l <= last_be*1.005) and curr['CH_CLOSING_PRICE'] > last_be: category = "Atak (Mandi Side)"

    last_row = df.iloc[-1]
    pct_change = ((last_row['CH_CLOSING_PRICE'] - last_row['CH_PREVIOUS_CLS_PRICE']) / last_row['CH_PREVIOUS_CLS_PRICE']) * 100
    
    return category, signal_desc, last_row['CH_CLOSING_PRICE'], pct_change, history_records, last_bu, last_be, trend

def run_full_scan():
    results = []; bar = st.progress(0); status = st.empty()
    start_date = st.session_state.class_start_date; dur = st.session_state.class_duration_label
    
    for i, stock in enumerate(FNO_STOCKS_LIST):
        status.caption(f"Scanning {stock}...")
        df = fetch_stock_data(stock, start_date)
        if df is not None:
            cat, sig, close, chg, history, fin_bu, fin_be, fin_trend = classify_stock(df)
            if close > 0: 
                sec = SECTOR_MAP.get(stock, "Other")
                results.append({ "Symbol": stock, "Sector": sec, "Price": close, "Change": chg, "Category": cat, "Signal": sig, "History": history, "BU": fin_bu, "BE": fin_be, "Trend": fin_trend })
        bar.progress((i + 1) / len(FNO_STOCKS_LIST)); time.sleep(0.1) 
    bar.empty(); status.empty()
    save = { "date": datetime.now().strftime("%Y-%m-%d"), "last_updated": datetime.now().strftime("%H:%M:%S"), "duration_label": dur, "stocks": results }
    with open(CLASS_FILE, 'w') as f: json.dump(save, f)
    return save

def check_auto_scan():
    now = datetime.now(); today = now.strftime("%Y-%m-%d")
    if not os.path.exists(CLASS_FILE): return True, "Init"
    try:
        with open(CLASS_FILE, 'r') as f: data = json.load(f)
        if data.get("date") != today and now.hour >= 18: return True, "Daily"
        if data.get("duration_label") != st.session_state.class_duration_label: return True, "Dur"
        if data.get('stocks') and len(data['stocks']) > 0:
             if 'Trend' not in data['stocks'][0]: return True, "Schema"
        return False, data
    except: return True, "Error"

should_scan, payload = check_auto_scan()
if force_scan: st.toast("Scanning..."); current_data = run_full_scan(); st.rerun()
elif should_scan is True: st.info("Auto-Scanning..."); current_data = run_full_scan(); st.rerun()
else: current_data = payload

# --- POPUP ---
@st.dialog("Stock Analysis", width="large")
def show_details(item):
    st.subheader(f"{item['Symbol']} : ₹{item['Price']:.2f} ({item['Change']:.2f}%)")
    
    c1, c2, c3 = st.columns(3)
    def card(label, value): return f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>"""
    with c1: st.markdown(card("Trend", item['Trend']), unsafe_allow_html=True)
    
    # Handle None
    bu_disp = f"{item['BU']:.2f}" if item['BU'] else "-"
    be_disp = f"{item['BE']:.2f}" if item['BE'] else "-"
    
    with c2: st.markdown(card("Resistance (BU)", bu_disp), unsafe_allow_html=True)
    with c3: st.markdown(card("Support (BE)", be_disp), unsafe_allow_html=True)
    
    st.divider()
    
    def color_rows(row):
        s = row['Type']
        # EXACT MATCH WITH HOME.PY
        if s == 'bull_dark': return ['background-color: #228B22; color: white; font-weight: bold; white-space: pre-wrap;']*len(row)
        if s == 'bear_dark': return ['background-color: #8B0000; color: white; font-weight: bold; white-space: pre-wrap;']*len(row)
        if s == 'bull_light': return ['background-color: #90EE90; color: black; font-weight: bold; white-space: pre-wrap;']*len(row)
        if s == 'bear_light': return ['background-color: #FFC0CB; color: black; font-weight: bold; white-space: pre-wrap;']*len(row)
        return ['white-space: pre-wrap;']*len(row)

    hist_df = pd.DataFrame(item['History'])
    if not hist_df.empty:
        # Convert numeric cols just in case, but keep BU/BE as objects/strings
        for c in ["Open", "High", "Low", "Close"]: hist_df[c] = pd.to_numeric(hist_df[c])
        
        st.dataframe(
            hist_df.style.apply(color_rows, axis=1).format({"Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"}),
            column_config={
                "Type": None,
                "BU": st.column_config.TextColumn("BU (Resist)", width="medium"), # Use TextColumn for strings
                "BE": st.column_config.TextColumn("BE (Support)", width="medium")  # Use TextColumn for strings
            }, 
            use_container_width=True, 
            height=400
        )
    else:
        st.write("No history data available.")

if current_data:
    data_dur = current_data.get('duration_label', 'Unknown')
    st.caption(f"Last Scanned: {current_data['date']} {current_data['last_updated']} | Duration: {data_dur}")
    st.divider()
    
    search_query = st.text_input("🔍 Search Stock", placeholder="e.g. RELIANCE").upper()
    data = current_data['stocks']
    data = [d for d in data if view_min <= d['Price'] <= view_max]
    
    if sector_filter != "All": data = [d for d in data if d.get('Sector') == sector_filter]
    if search_query: data = [d for d in data if search_query in d['Symbol']]
        
    high_bull = [d for d in data if d['Category'] == "Highly Bullish"]
    bull = [d for d in data if d['Category'] == "Bullish"]
    high_bear = [d for d in data if d['Category'] == "Highly Bearish"]
    bear = [d for d in data if d['Category'] == "Bearish"]
    atak_teji = [d for d in data if d['Category'] == "Atak (Teji Side)"]
    atak_mandi = [d for d in data if d['Category'] == "Atak (Mandi Side)"]
    
    cats_to_show = []
    if category_filter == "All":
        cats_to_show = [("🚀 Highly Bullish", high_bull, "b-high-bull"), ("🟢 Bullish", bull, "b-bull"), ("🩸 Highly Bearish", high_bear, "b-high-bear"), ("🔴 Bearish", bear, "b-bear"), ("⚠️ Atak on Teji", atak_teji, "b-atak-top"), ("🛡️ Atak on Mandi", atak_mandi, "b-atak-bot")]
    elif category_filter == "Bullish Only": cats_to_show = [("🟢 Bullish", bull, "b-bull")]
    elif category_filter == "Bearish Only": cats_to_show = [("🔴 Bearish", bear, "b-bear")]
    elif category_filter == "High Momentum Only": cats_to_show = [("🚀 Highly Bullish", high_bull, "b-high-bull"), ("🩸 Highly Bearish", high_bear, "b-high-bear")]
    elif category_filter == "Atak Only": cats_to_show = [("⚠️ Atak on Teji", atak_teji, "b-atak-top"), ("🛡️ Atak on Mandi", atak_mandi, "b-atak-bot")]

    def render_category(title, items, border_class):
        st.markdown("""<style>.streamlit-expanderHeader {color: black !important; font-weight: bold;}</style>""", unsafe_allow_html=True)
        with st.expander(f"{title} ({len(items)})", expanded=True):
            if not items: st.caption("No stocks.")
            for item in items:
                chg_color = "chg-green" if item['Change'] >= 0 else "chg-red"
                sign = "+" if item['Change'] >= 0 else ""
                tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{item['Symbol']}"
                st.markdown(f"""<div class="class-card {border_class}"><div style="display:flex; justify-content:space-between; align-items:center;"><span class="stock-title">{item['Symbol']} <span style='font-size:0.8em; color:#999; font-weight:normal;'>({item['Sector']})</span></span><span class="stock-price">₹{item['Price']:.2f}</span></div><div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;"><span class="{chg_color}">{sign}{item['Change']:.2f}%</span><a href="{tv_link}" target="_blank" class="chart-link">📈 Chart</a></div><div class="signal-text">Signal: {item['Signal']}</div></div>""", unsafe_allow_html=True)
                if st.button(f"🔍 View {item['Symbol']}", key=f"btn_{item['Symbol']}", use_container_width=True): show_details(item)

    if category_filter == "All":
        c1, c2, c3 = st.columns(3)
        with c1: render_category(cats_to_show[0][0], cats_to_show[0][1], cats_to_show[0][2]); render_category(cats_to_show[3][0], cats_to_show[3][1], cats_to_show[3][2])
        with c2: render_category(cats_to_show[1][0], cats_to_show[1][1], cats_to_show[1][2]); render_category(cats_to_show[4][0], cats_to_show[4][1], cats_to_show[4][2])
        with c3: render_category(cats_to_show[2][0], cats_to_show[2][1], cats_to_show[2][2]); render_category(cats_to_show[5][0], cats_to_show[5][1], cats_to_show[5][2])
    else:
        for cat in cats_to_show: render_category(cat[0], cat[1], cat[2])
