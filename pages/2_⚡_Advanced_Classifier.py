import streamlit as st
import pandas as pd
import requests
import urllib.parse
import time
import json
import os
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Advanced Classifier", page_icon="⚡", layout="wide")

st.title("⚡ Advanced VNS Classifier")
st.markdown("Identifies **Breakouts**, **Trend Continuation**, and **Reversal Risks**. • **Auto-Saves Results**")

# --- PRO CSS (VISIBILITY & LAYOUT) ---
st.markdown("""
<style>
    /* Force Light Mode */
    .stApp { background-color: white; color: black; }
    
    /* VISIBILITY FIXES */
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"], .stMarkdown {
        color: #000000 !important;
    }
    
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
    
    /* Sidebar text fix */
    .stSidebar label { color: #333 !important; }
    
    /* Modal Width */
    div[data-testid="stDialog"] { width: 85vw; } 
    
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
CLASS_FILE = "daily_classification_results.json" 

FNO_STOCKS = [
    "360ONE", "ABB", "APLAPOLLO", "AUBANK", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", 
    "ABCAPITAL", "ALKEM", "AMBER", "AMBUJACEM", "ANGELONE", "APOLLOHOSP", "ASHOKLEY", "ASIANPAINT", 
    "ASTRAL", "AUROPHARMA", "DMART", "AXISBANK", "BSE", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", 
    "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BDL", "BEL", "BHARATFORG", "BHEL", "BPCL", 
    "BHARTIARTL", "BIOCON", "BLUESTARCO", "BOSCHLTD", "BRITANNIA", "CGPOWER", "CANBK", "CDSL", 
    "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CAMS", "CONCOR", "CROMPTON", 
    "CUMMINSIND", "CYIENT", "DLF", "DABUR", "DALBHARAT", "DELHIVERY", "DIVISLAB", "DIXON", 
    "DRREDDY", "EICHERMOT", "EXIDEIND", "NYKAA", "FORTIS", "GAIL", "GMRAIRPORT", "GLENMARK", 
    "GODREJCP", "GODREJPROP", "GRASIM", "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HFCL", 
    "HAVELLS", "HEROMOTOCO", "HINDALCO", "HAL", "HINDPETRO", "HINDUNILVR", "HINDZINC", "POWERINDIA", 
    "HUDCO", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDFCFIRSTB", "IIFL", "ITC", "INDIANB", "IEX", 
    "IOC", "IRCTC", "IRFC", "IREDA", "INDUSTOWER", "INDUSINDBK", "NAUKRI", "INFY", "INOXWIND", 
    "INDIGO", "JINDALSTEL", "JSWENERGY", "JSWSTEEL", "JIOFIN", "JUBLFOOD", "KEI", "KPITTECH", 
    "KALYANKJIL", "KAYNES", "KFINTECH", "KOTAKBANK", "LTF", "LICHSGFIN", "LTIM", "LT", "LAURUSLABS", 
    "LICI", "LODHA", "LUPIN", "M&M", "MANAPPURAM", "MANKIND", "MARICO", "MARUTI", "MFSL", 
    "MAXHEALTH", "MAZDOCK", "MPHASIS", "MCX", "MUTHOOTFIN", "NBCC", "NCC", "NHPC", "NMDC", 
    "NTPC", "NATIONALUM", "NESTLEIND", "NUVAMA", "OBEROIRLTY", "ONGC", "OIL", "PAYTM", "OFSS", 
    "POLICYBZR", "PGEL", "PIIND", "PNBHOUSING", "PAGEIND", "PATANJALI", "PERSISTENT", "PETRONET", 
    "PIDILITIND", "PPLPHARMA", "POLYCAB", "PFC", "POWERGRID", "PRESTIGE", "PNB", "RBLBANK", 
    "RECLTD", "RVNL", "RELIANCE", "SBICARD", "SBILIFE", "SHREECEM", "SRF", "SAMMAANCAP", 
    "MOTHERSON", "SHRIRAMFIN", "SIEMENS", "SOLARINDS", "SONACOMS", "SBIN", "SAIL", "SUNPHARMA", 
    "SUPREMEIND", "SUZLON", "SYNGENE", "TATACONSUM", "TITAGARH", "TVSMOTOR", "TCS", "TATAELXSI", 
    "TATAPOWER", "TATASTEEL", "TATATECH", "TECHM", "FEDERALBNK", "INDHOTEL", "PHOENIXLTD", 
    "TITAN", "TORNTPHARM", "TORNTPOWER", "TRENT", "TIINDIA", "UNOMINDA", "UPL", "ULTRACEMCO", 
    "UNIONBANK", "UNITDSPR", "VBL", "VEDL", "IDEA", "VOLTAS", "WIPRO", "YESBANK", "ZYDUSLIFE"
]
FNO_STOCKS = sorted(list(set(FNO_STOCKS)))

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
    # Custom handled in widget

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 1. Period (Affects Scan Data)
    st.subheader("1. Analysis Period")
    
    # Added "2M" and "Custom"
    period_sel = st.radio(
        "Duration", 
        ["1M", "2M", "3M", "6M", "1Y", "Custom"], 
        index=2, # Default 3M
        horizontal=True, 
        key="class_duration_select", 
        on_change=update_class_settings
    )
    
    # Custom Date Picker
    if period_sel == "Custom":
        c_dates = st.date_input("Select Range", value=st.session_state.custom_date_range)
        if len(c_dates) == 2:
            st.session_state.class_start_date = datetime.combine(c_dates[0], datetime.min.time())
            st.session_state.custom_date_range = c_dates
            # End date handled in fetcher (usually Now)
    
    st.divider()
    
    # 2. View Filters (Instant)
    st.subheader("2. View Filters")
    c1, c2 = st.columns(2)
    view_min = c1.number_input("Min Price", 0, value=1000, step=100) # Default 1000
    view_max = c2.number_input("Max Price", 0, value=100000, step=500)
    
    category_filter = st.selectbox("Show Category", ["All", "Bullish Only", "Bearish Only", "Atak (Reversals) Only", "High Momentum Only"])
    
    st.divider()
    force_scan = st.button("🔄 Force Refresh", type="primary", use_container_width=True)

# --- CORE LOGIC ---
def fetch_stock_data(symbol, start_date):
    try:
        safe_symbol = urllib.parse.quote(symbol)
        end = datetime.now()
        # Buffer for calculations
        req_start = start_date - timedelta(days=5)
        
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        s = requests.Session(); s.headers.update(headers)
        s.get("https://www.nseindia.com", timeout=3)
        
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
    trend = "Neutral"; last_bu = None; last_be = None; signal_desc = "Neutral"; category = "Neutral"
    
    # Store history for Popup
    history_records = []
    
    for i in range(1, len(df)):
        row = df.iloc[i]; prev = df.iloc[i-1]
        c_h, c_l, c_c = row['CH_TRADE_HIGH_PRICE'], row['CH_TRADE_LOW_PRICE'], row['CH_CLOSING_PRICE']
        p_h, p_l = prev['CH_TRADE_HIGH_PRICE'], prev['CH_TRADE_LOW_PRICE']
        
        low_broken = c_l < p_l
        high_broken = c_h > p_h
        
        is_atak_top = last_bu and (last_bu*0.995 <= c_h <= last_bu*1.005) and c_c < last_bu
        is_atak_bot = last_be and (last_be*0.995 <= c_l <= last_be*1.005) and c_c > last_be
        
        current_signal = ""
        bu_val, be_val = None, None
        signal_type = ""
        
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
            
        if trend == "Bearish" and last_bu and c_c > last_bu:
            trend = "Bullish"; current_signal = "BREAKOUT (Teji)"; bu_val=None; signal_type="bull"
        if trend == "Bullish" and last_be and c_c < last_be:
            trend = "Bearish"; current_signal = "BREAKDOWN (Mandi)"; be_val=None; signal_type="bear"
            
        # Record for History (JSON Serializable)
        history_records.append({
            'Date': row['Date'].strftime('%d-%b-%Y'),
            'Open': row['CH_OPENING_PRICE'], 'High': row['CH_TRADE_HIGH_PRICE'],
            'Low': row['CH_TRADE_LOW_PRICE'], 'Close': row['CH_CLOSING_PRICE'],
            'BU': bu_val, 'BE': be_val, 'Signal': current_signal, 'Type': signal_type
        })

        if i == len(df) - 1:
            signal_desc = current_signal
            if "BREAKOUT" in current_signal: category = "Highly Bullish"
            elif "BREAKDOWN" in current_signal: category = "Highly Bearish"
            elif "ATAK (Top)" in current_signal: category = "Atak (Teji Side)"
            elif "ATAK (Bottom)" in current_signal: category = "Atak (Mandi Side)"
            elif trend == "Bullish": category = "Bullish"
            elif trend == "Bearish": category = "Bearish"

    last_row = df.iloc[-1]
    pct_change = ((last_row['CH_CLOSING_PRICE'] - last_row['CH_PREVIOUS_CLS_PRICE']) / last_row['CH_PREVIOUS_CLS_PRICE']) * 100
    
    # Return Last Known Levels for Header
    return category, signal_desc, last_row['CH_CLOSING_PRICE'], pct_change, history_records, last_bu, last_be, trend

def run_full_scan():
    results = []
    bar = st.progress(0)
    status = st.empty()
    
    start_date = st.session_state.class_start_date
    duration_used = st.session_state.class_duration_label
    
    for i, stock in enumerate(FNO_STOCKS):
        status.caption(f"Scanning {stock}...")
        df = fetch_stock_data(stock, start_date)
        
        if df is not None:
            cat, sig, close, chg, history, fin_bu, fin_be, fin_trend = classify_stock(df)
            if close > 0: 
                results.append({ 
                    "Symbol": stock, "Price": close, "Change": chg, "Category": cat, "Signal": sig,
                    "History": history, "BU": fin_bu, "BE": fin_be, "Trend": fin_trend
                })
        
        bar.progress((i + 1) / len(FNO_STOCKS))
        time.sleep(0.1) 
        
    bar.empty(); status.empty()
    
    save_payload = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "last_updated": datetime.now().strftime("%H:%M:%S"),
        "duration_label": duration_used,
        "stocks": results
    }
    with open(CLASS_FILE, 'w') as f: json.dump(save_payload, f)
    
    return save_payload

def check_auto_scan():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    if not os.path.exists(CLASS_FILE): return True, "Initial Setup"
    try:
        with open(CLASS_FILE, 'r') as f: data = json.load(f)
        file_date = data.get("date")
        if file_date != today_str and now.hour >= 18: return True, "Daily Update"
        return False, data
    except: return True, "Error"

# --- CONTROLLER ---
should_scan, payload = check_auto_scan()

if force_scan:
    st.toast("Forcing Scan...")
    current_data = run_full_scan()
    st.rerun()
elif should_scan is True:
    st.info(f"📅 Running Auto-Scan ({payload})...")
    current_data = run_full_scan()
    st.rerun()
else:
    current_data = payload

# --- POPUP DIALOG (VNS DETAILS) ---
@st.dialog("Stock Analysis", width="large")
def show_details(item):
    st.subheader(f"{item['Symbol']} : ₹{item['Price']:.2f} ({item['Change']:.2f}%)")
    
    c1, c2, c3 = st.columns(3)
    def card(label, value):
        return f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>"""
    
    with c1: st.markdown(card("Trend", item['Trend']), unsafe_allow_html=True)
    with c2: st.markdown(card("Resistance (BU)", f"{item['BU']:.2f}" if item['BU'] else "-"), unsafe_allow_html=True)
    with c3: st.markdown(card("Support (BE)", f"{item['BE']:.2f}" if item['BE'] else "-"), unsafe_allow_html=True)
    
    st.divider()
    
    # Table Styling
    def color_rows(row):
        s = row['Type']
        if s == 'bull': return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
        if s == 'bear': return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
        if s == 'warn': return ['background-color: #fff3cd; color: #664d03; font-weight: bold'] * len(row)
        if s == 'info': return ['background-color: #e2e6ea; color: #0c5460; font-style: italic'] * len(row)
        return [''] * len(row)

    hist_df = pd.DataFrame(item['History'])
    if not hist_df.empty:
        st.dataframe(
            hist_df.style.apply(color_rows, axis=1).format({
                "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}", "BU": "{:.2f}", "BE": "{:.2f}"
            }, na_rep=""),
            column_config={"Type": None}, 
            use_container_width=True, 
            height=400
        )
    else:
        st.write("No history data available.")

# --- DISPLAY ---
if current_data:
    data_dur = current_data.get('duration_label', 'Unknown')
    st.caption(f"Last Scanned: {current_data['date']} {current_data['last_updated']} | Duration: {data_dur}")
    
    if data_dur != st.session_state.class_duration_label:
        st.warning(f"⚠️ Displaying **{data_dur}** data. You selected **{st.session_state.class_duration_label}**. Click Force Refresh.")
    
    st.divider()
    
    # 1. SEARCH
    search_query = st.text_input("🔍 Search Stock", placeholder="e.g. RELIANCE").upper()
    data = current_data['stocks']
    
    # 2. FILTER PRICE
    data = [d for d in data if view_min <= d['Price'] <= view_max]
    
    # 3. FILTER SEARCH
    if search_query: data = [d for d in data if search_query in d['Symbol']]
        
    # Buckets
    high_bull = [d for d in data if d['Category'] == "Highly Bullish"]
    bull = [d for d in data if d['Category'] == "Bullish"]
    high_bear = [d for d in data if d['Category'] == "Highly Bearish"]
    bear = [d for d in data if d['Category'] == "Bearish"]
    atak_teji = [d for d in data if d['Category'] == "Atak (Teji Side)"]
    atak_mandi = [d for d in data if d['Category'] == "Atak (Mandi Side)"]
    
    # Filter Categories
    cats_to_show = []
    sel_cat = category_filter
    
    if sel_cat == "All":
        cats_to_show = [
            ("🚀 Highly Bullish", high_bull, "b-high-bull"),
            ("🟢 Bullish", bull, "b-bull"),
            ("🩸 Highly Bearish", high_bear, "b-high-bear"),
            ("🔴 Bearish", bear, "b-bear"),
            ("⚠️ Atak on Teji", atak_teji, "b-atak-top"),
            ("🛡️ Atak on Mandi", atak_mandi, "b-atak-bot")
        ]
    elif sel_cat == "Bullish Only": cats_to_show = [("🟢 Bullish", bull, "b-bull")]
    elif sel_cat == "Bearish Only": cats_to_show = [("🔴 Bearish", bear, "b-bear")]
    elif sel_cat == "High Momentum Only": cats_to_show = [("🚀 Highly Bullish", high_bull, "b-high-bull"), ("🩸 Highly Bearish", high_bear, "b-high-bear")]
    elif sel_cat == "Atak Only": cats_to_show = [("⚠️ Atak on Teji", atak_teji, "b-atak-top"), ("🛡️ Atak on Mandi", atak_mandi, "b-atak-bot")]

    def render_category(title, items, border_class):
        # Force Black Header
        st.markdown("""<style>.streamlit-expanderHeader {color: black !important; font-weight: bold;}</style>""", unsafe_allow_html=True)
        
        with st.expander(f"{title} ({len(items)})", expanded=True):
            if not items: st.caption("No stocks.")
            
            for item in items:
                chg_color = "chg-green" if item['Change'] >= 0 else "chg-red"
                chg_sign = "+" if item['Change'] >= 0 else ""
                tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{item['Symbol']}"
                
                st.markdown(f"""
                <div class="class-card {border_class}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="stock-title">{item['Symbol']}</span>
                        <span class="stock-price">₹{item['Price']:.2f}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                        <span class="{chg_color}">{chg_sign}{item['Change']:.2f}%</span>
                        <a href="{tv_link}" target="_blank" class="chart-link">📈 Chart</a>
                    </div>
                    <div class="signal-text">Signal: {item['Signal']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # POPUP BUTTON
                if st.button(f"🔍 View {item['Symbol']}", key=f"btn_{item['Symbol']}", use_container_width=True):
                    show_details(item)

    if category_filter == "All":
        c1, c2, c3 = st.columns(3)
        with c1: 
            render_category(cats_to_show[0][0], cats_to_show[0][1], cats_to_show[0][2])
            render_category(cats_to_show[3][0], cats_to_show[3][1], cats_to_show[3][2])
        with c2: 
            render_category(cats_to_show[1][0], cats_to_show[1][1], cats_to_show[1][2])
            render_category(cats_to_show[4][0], cats_to_show[4][1], cats_to_show[4][2])
        with c3: 
            render_category(cats_to_show[2][0], cats_to_show[2][1], cats_to_show[2][2])
            render_category(cats_to_show[5][0], cats_to_show[5][1], cats_to_show[5][2])
    else:
        for cat in cats_to_show:
            render_category(cat[0], cat[1], cat[2])
