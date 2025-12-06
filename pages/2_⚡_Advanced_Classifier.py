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
    .stApp { background-color: white; color: black; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] { color: #000000 !important; }
    
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
    
    .stock-title { font-size: 1.2rem; font-weight: 800; color: #2c3e50 !important; }
    .stock-price { font-size: 1.1rem; font-weight: 600; color: #333 !important; }
    .signal-text { font-size: 0.9rem; font-weight: 600; margin-top: 5px; color: #555 !important; }
    
    .chg-green { color: #008000 !important; font-weight: bold; font-size: 0.9rem; }
    .chg-red { color: #d63031 !important; font-weight: bold; font-size: 0.9rem; }
    
    .b-high-bull { border-left-color: #00b894; } 
    .b-bull { border-left-color: #55efc4; }      
    .b-high-bear { border-left-color: #d63031; } 
    .b-bear { border-left-color: #fab1a0; }      
    .b-atak-top { border-left-color: #e17055; }  
    .b-atak-bot { border-left-color: #fdcb6e; }  
    
    .chart-link {
        text-decoration: none; font-size: 0.8rem; color: #0984e3 !important; font-weight: bold; float: right;
    }
    .chart-link:hover { text-decoration: underline; }
    
    .stSidebar label { color: #333 !important; }
    div[data-testid="stDialog"] { width: 85vw; } 
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
CLASS_FILE = "daily_classification_results.json" 

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

# --- CORE LOGIC (YAHOO FINANCE) ---
def fetch_stock_data(symbol, start_date):
    try:
        yf_symbol = f"{symbol}.NS"
        df = yf.download(yf_symbol, start=start_date, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'CH_OPENING_PRICE', 'High': 'CH_TRADE_HIGH_PRICE', 'Low': 'CH_TRADE_LOW_PRICE', 'Close': 'CH_CLOSING_PRICE'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

def classify_stock(df):
    trend = "Neutral"; last_bu = None; last_be = None; signal_desc = "Neutral"; category = "Neutral"
    history_records = []
    
    for i in range(1, len(df)):
        row = df.iloc[i]; prev = df.iloc[i-1]
        c_h, c_l, c_c = row['CH_TRADE_HIGH_PRICE'], row['CH_TRADE_LOW_PRICE'], row['CH_CLOSING_PRICE']
        p_h, p_l = prev['CH_TRADE_HIGH_PRICE'], prev['CH_TRADE_LOW_PRICE']
        low_broken = c_l < p_l; high_broken = c_h > p_h
        
        is_atak_top = last_bu and (last_bu*0.995 <= c_h <= last_bu*1.005) and c_c < last_bu
        is_atak_bot = last_be and (last_be*0.995 <= c_l <= last_be*1.005) and c_c > last_be
        
        current_signal = ""; bu_val, be_val = None, None; signal_type = ""
        
        if trend == "Bullish":
            if low_broken: last_bu = p_h; current_signal = "Top Made (BU)"; bu_val=p_h; signal_type="bull"
            if high_broken: last_be = p_l; current_signal = "Reaction Buy"; be_val=p_l; signal_type="info"
            if is_atak_top: current_signal = "ATAK (Top)"; signal_type="warn"
        elif trend == "Bearish":
            if high_broken: last_be = p_l; current_signal = "Bottom Made (BE)"; be_val=p_l; signal_type="bear"
            if low_broken: last_bu = p_h; current_signal = "Reaction Sell"; bu_val=p_h; signal_type="info"
            if is_atak_bot: current_signal = "ATAK (Bottom)"; signal_type="warn"
        else: 
            if high_broken: trend="Bullish"; last_be=p_l; current_signal="Start Bull"; be_val=p_l; signal_type="bull"
            elif low_broken: trend="Bearish"; last_bu=p_h; current_signal="Start Bear"; bu_val=p_h; signal_type="bear"
            
        if trend == "Bearish" and last_bu and c_c > last_bu: trend = "Bullish"; current_signal = "BREAKOUT (Fresh Teji)"; bu_val=None; signal_type="bull"
        if trend == "Bullish" and last_be and c_c < last_be: trend = "Bearish"; current_signal = "BREAKDOWN (Fresh Mandi)"; be_val=None; signal_type="bear"
            
        history_records.append({
            'Date': row['Date'].strftime('%d-%b-%Y'), 'Open': row['CH_OPENING_PRICE'], 'High': row['CH_TRADE_HIGH_PRICE'],
            'Low': row['CH_TRADE_LOW_PRICE'], 'Close': row['CH_CLOSING_PRICE'], 'BU': bu_val, 'BE': be_val, 'Signal': current_signal, 'Type': signal_type
        })

        if i == len(df) - 1:
            signal_desc = current_signal
            if "BREAKOUT" in current_signal: category = "Highly Bullish"
            elif "BREAKDOWN" in current_signal: category = "Highly Bearish"
            elif "ATAK (Top)" in current_signal: category = "Atak (Teji Side)"
            elif "ATAK (Bottom)" in current_signal: category = "Atak (Mandi Side)"
            elif trend == "Bullish": category = "Bullish"
            elif trend == "Bearish": category = "Bearish"

    # Calc % Change manually since we rely on rows now
    if len(df) >= 2:
        last = df.iloc[-1]; prev = df.iloc[-2]
        pct = ((last['CH_CLOSING_PRICE'] - prev['CH_CLOSING_PRICE']) / prev['CH_CLOSING_PRICE']) * 100
    else:
        pct = 0.0
        
    return category, signal_desc, df.iloc[-1]['CH_CLOSING_PRICE'], pct, history_records, last_bu, last_be, trend

def run_full_scan():
    results = []; bar = st.progress(0); status = st.empty()
    start_date = st.session_state.class_start_date
    duration_used = st.session_state.class_duration_label
    
    for i, stock in enumerate(FNO_STOCKS_LIST):
        status.caption(f"Scanning {stock}...")
        df = fetch_stock_data(stock, start_date)
        if df is not None and not df.empty:
            cat, sig, close, chg, history, fin_bu, fin_be, fin_trend = classify_stock(df)
            if close > 0: 
                sec = SECTOR_MAP.get(stock, "Other")
                results.append({ "Symbol": stock, "Sector": sec, "Price": close, "Change": chg, "Category": cat, "Signal": sig, "History": history, "BU": fin_bu, "BE": fin_be, "Trend": fin_trend })
        bar.progress((i + 1) / len(FNO_STOCKS_LIST)); time.sleep(0.05) 
        
    bar.empty(); status.empty()
    save_payload = { "date": datetime.now().strftime("%Y-%m-%d"), "last_updated": datetime.now().strftime("%H:%M:%S"), "duration_label": duration_used, "stocks": results }
    with open(CLASS_FILE, 'w') as f: json.dump(save_payload, f)
    return save_payload

def check_auto_scan():
    now = datetime.now(); today_str = now.strftime("%Y-%m-%d")
    if not os.path.exists(CLASS_FILE): return True, "Initial Setup"
    try:
        with open(CLASS_FILE, 'r') as f: data = json.load(f)
        if data.get("date") != today_str and now.hour >= 18: return True, "Daily Update"
        if data.get("duration_label") != st.session_state.class_duration_label: return True, "Duration Change"
        if data.get('stocks') and len(data['stocks']) > 0:
            if 'Sector' not in data['stocks'][0]: return True, "Schema Update"
        return False, data
    except: return True, "Error"

# --- MAIN ---
should_scan, payload = check_auto_scan()
if force_scan: st.toast("Scanning..."); current_data = run_full_scan(); st.rerun()
elif should_scan is True: st.info(f"Auto-Scan... {payload}"); current_data = run_full_scan(); st.rerun()
else: current_data = payload

# --- POPUP ---
@st.dialog("Stock Analysis", width="large")
def show_details(item):
    st.subheader(f"{item['Symbol']} : ₹{item['Price']:.2f} ({item['Change']:.2f}%)")
    c1, c2, c3 = st.columns(3)
    def card(label, value): return f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>"""
    with c1: st.markdown(card("Trend", item['Trend']), unsafe_allow_html=True)
    with c2: st.markdown(card("Resistance (BU)", f"{item['BU']:.2f}" if item['BU'] else "-"), unsafe_allow_html=True)
    with c3: st.markdown(card("Support (BE)", f"{item['BE']:.2f}" if item['BE'] else "-"), unsafe_allow_html=True)
    st.divider()
    def color_rows(row):
        s = row['Type']
        if s == 'bull': return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
        if s == 'bear': return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
        if s == 'warn': return ['background-color: #fff3cd; color: #664d03; font-weight: bold'] * len(row)
        if s == 'info': return ['background-color: #e2e6ea; color: #0c5460; font-style: italic'] * len(row)
        return [''] * len(row)
    hist_df = pd.DataFrame(item['History'])
    if not hist_df.empty:
        st.dataframe(hist_df.style.apply(color_rows, axis=1).format({"Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}", "BU": "{:.2f}", "BE": "{:.2f}"}, na_rep=""), column_config={"Type": None}, use_container_width=True, height=400)
    else: st.write("No history data.")

# --- DISPLAY ---
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
                st.markdown(f"""
                <div class="class-card {border_class}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="stock-title">{item['Symbol']} <span style='font-size:0.8em; color:#999; font-weight:normal;'>({item['Sector']})</span></span>
                        <span class="stock-price">₹{item['Price']:.2f}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                        <span class="{chg_color}">{sign}{item['Change']:.2f}%</span>
                        <a href="{tv_link}" target="_blank" class="chart-link">📈 Chart</a>
                    </div>
                    <div class="signal-text">Signal: {item['Signal']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🔍 View {item['Symbol']}", key=f"btn_{item['Symbol']}", use_container_width=True):
                    show_details(item)

    if category_filter == "All":
        c1, c2, c3 = st.columns(3)
        with c1: render_category(cats_to_show[0][0], cats_to_show[0][1], cats_to_show[0][2]); render_category(cats_to_show[3][0], cats_to_show[3][1], cats_to_show[3][2])
        with c2: render_category(cats_to_show[1][0], cats_to_show[1][1], cats_to_show[1][2]); render_category(cats_to_show[4][0], cats_to_show[4][1], cats_to_show[4][2])
        with c3: render_category(cats_to_show[2][0], cats_to_show[2][1], cats_to_show[2][2]); render_category(cats_to_show[5][0], cats_to_show[5][1], cats_to_show[5][2])
    else:
        for cat in cats_to_show: render_category(cat[0], cat[1], cat[2])
