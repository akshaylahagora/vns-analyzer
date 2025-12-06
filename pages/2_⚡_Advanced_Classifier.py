import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.parse
import time
import json
import os
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Advanced Classifier", page_icon="⚡", layout="wide")

st.title("⚡ Advanced VNS Classifier")
st.markdown("Identifies **Breakouts**, **Trend Continuation**, and **Reversal Risks**. • **Auto-Saves Results**")

# --- PRO CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    div[data-testid="stMetricValue"] { color: #000000 !important; }
    
    .metric-card { background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; text-align: center; }
    .metric-label { font-size: 0.8rem; font-weight: 600; color: #666; text-transform: uppercase; margin-bottom: 4px; }
    .metric-value { font-size: 1.2rem; font-weight: 800; color: #000; }
    
    .class-card { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 12px; border-left-width: 6px; border-left-style: solid; border: 1px solid #eee; }
    
    .stock-title { font-size: 1.2rem; font-weight: 800; color: #2c3e50; }
    .stock-price { font-size: 1.1rem; font-weight: 600; color: #333; }
    .signal-text { font-size: 0.9rem; font-weight: 600; margin-top: 5px; color: #555; }
    .chg-green { color: #008000; font-weight: bold; font-size: 0.9rem; }
    .chg-red { color: #d63031; font-weight: bold; font-size: 0.9rem; }
    
    .b-high-bull { border-left-color: #00b894; } .b-bull { border-left-color: #55efc4; }      
    .b-high-bear { border-left-color: #d63031; } .b-bear { border-left-color: #fab1a0; }      
    .b-atak-top { border-left-color: #e17055; }  .b-atak-bot { border-left-color: #fdcb6e; }  
    
    .chart-link { text-decoration: none; font-size: 0.8rem; color: #0984e3; font-weight: bold; float: right; }
    .stSidebar label { color: #333 !important; }
    div[data-testid="stDialog"] { width: 85vw; } 
</style>
""", unsafe_allow_html=True)

# --- CONFIG ---
CLASS_FILE = "daily_classification_results.json" 
SECTOR_MAP = { "NIFTY": "Index", "RELIANCE": "Energy", "HDFCBANK": "Banking", "TCS": "IT", "MARUTI": "Auto", "SUNPHARMA": "Pharma", "ITC": "FMCG", "BAJFINANCE": "Finance", "TATASTEEL": "Metal", "ULTRACEMCO": "Cement", "LT": "Infra" } 
# Use the full list variable from Home.py ideally, keeping simplified here for length
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

# --- STATE ---
if 'class_start_date' not in st.session_state: st.session_state.class_start_date = datetime.now() - timedelta(days=90)
if 'class_duration_label' not in st.session_state: st.session_state.class_duration_label = "3M"
if 'custom_date_range' not in st.session_state: st.session_state.custom_date_range = (datetime.now() - timedelta(days=90), datetime.now())

def update_class_settings():
    sel = st.session_state.class_duration_select; st.session_state.class_duration_label = sel
    now = datetime.now(); days = {"1M":30, "2M":60, "3M":90, "6M":180, "1Y":365}
    if sel in days: st.session_state.class_start_date = now - timedelta(days=days[sel])

with st.sidebar:
    st.header("⚙️ Settings")
    st.radio("Duration", ["1M", "2M", "3M", "6M", "1Y", "Custom"], index=2, horizontal=True, key="class_duration_select", on_change=update_class_settings)
    if st.session_state.class_duration_label == "Custom":
        c_dates = st.date_input("Select Range", value=st.session_state.custom_date_range)
        if len(c_dates) == 2: st.session_state.class_start_date = datetime.combine(c_dates[0], datetime.min.time()); st.session_state.custom_date_range = c_dates
    st.divider()
    c1, c2 = st.columns(2)
    view_min = c1.number_input("Min", 0, value=1000) 
    view_max = c2.number_input("Max", 0, value=100000)
    category_filter = st.selectbox("Category", ["All", "Bullish Only", "Bearish Only", "Atak Only", "High Momentum Only"])
    sector_filter = st.selectbox("Sector", ["All"] + sorted(list(set(SECTOR_MAP.values()))))
    st.divider()
    force_scan = st.button("🔄 Force Refresh", type="primary", use_container_width=True)

# --- LOGIC ---
def fetch_stock_data(symbol, start_date):
    try:
        yf_symbol = f"{symbol}.NS"
        req_start = start_date - timedelta(days=60)
        df = yf.download(yf_symbol, start=req_start, progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

def classify_stock(df):
    trend = "Neutral"; last_peak = df.iloc[0]['High']; last_trough = df.iloc[0]['Low']
    reaction_support = df.iloc[0]['Low']; reaction_resist = df.iloc[0]['High']
    last_peak_idx=0; last_trough_idx=0
    signal_desc = "Neutral"; category = "Neutral"
    history_records = []
    
    for i in range(1, len(df)):
        curr = df.iloc[i]; c_h, c_l = curr['High'], curr['Low']
        bu, be, signal, signal_type = None, None, "", ""
        
        # Same VNS Logic as Home.py
        if trend == "Teji":
            if c_h > last_peak:
                bu = f"T (Teji) {c_h:.2f}"; signal_type="bull_dark"; signal="New High"
                swing = df.iloc[last_peak_idx:i+1]; reaction_support = swing['Low'].min()
                be = f"R (Sup) {reaction_support:.2f}"
                last_peak = c_h; last_peak_idx = i
            elif c_l < reaction_support:
                bu = f"ATAK (Top) {last_peak:.2f}"; be = f"M (Mandi) {c_l:.2f}"; signal_type="bear_dark"; signal="Reversal"
                trend = "Mandi"; last_trough = c_l; last_trough_idx = i; reaction_resist = c_h
        elif trend == "Mandi":
            if c_l < last_trough:
                be = f"M (Mandi) {c_l:.2f}"; signal_type="bear_dark"; signal="New Low"
                swing = df.iloc[last_trough_idx:i+1]; reaction_resist = swing['High'].max()
                bu = f"R (Resist) {reaction_resist:.2f}"
                last_trough = c_l; last_trough_idx = i
            elif c_h > reaction_resist:
                be = f"ATAK (Bot) {last_trough:.2f}"; bu = f"T (Teji) {c_h:.2f}"; signal_type="bull_dark"; signal="Reversal"
                trend = "Teji"; last_peak = c_h; last_peak_idx = i; reaction_support = c_l
        else:
            if c_h > last_peak: trend="Teji"; bu="Start Teji"; signal_type="bull_dark"; last_peak=c_h; last_peak_idx=i
            elif c_l < last_trough: trend="Mandi"; be="Start Mandi"; signal_type="bear_dark"; last_trough=c_l; last_trough_idx=i
            
        # Map Color Types
        color_type = ""
        if "T (Teji)" in str(bu) or "Start Teji" in str(bu): color_type = "bull_dark"
        elif "M (Mandi)" in str(be) or "Start Mandi" in str(be): color_type = "bear_dark"
        elif "ATAK (Top)" in str(bu): color_type = "bear_light"
        elif "ATAK (Bot)" in str(be): color_type = "bull_light"
        elif "R (Sup)" in str(be): color_type = "bull_light"
        elif "R (Resist)" in str(bu): color_type = "bear_light"

        history_records.append({ 'Date': curr['Date'].strftime('%d-%b-%Y'), 'Open': curr['Open'], 'High': curr['High'], 'Low': curr['Low'], 'Close': curr['Close'], 'BU': bu, 'BE': be, 'Signal': signal, 'Type': color_type })
        
        if i == len(df)-1:
            signal_desc = signal
            if "ATAK" in str(bu): category = "Atak (Teji Side)"
            elif "ATAK" in str(be): category = "Atak (Mandi Side)"
            elif trend == "Teji": category = "Highly Bullish" if "Reversal" in signal else "Bullish"
            elif trend == "Mandi": category = "Highly Bearish" if "Reversal" in signal else "Bearish"

    last = df.iloc[-1]; pct = ((last['Close'] - df.iloc[-2]['Close'])/df.iloc[-2]['Close'])*100
    return category, signal_desc, last['Close'], pct, history_records, reaction_resist, reaction_support, trend

def run_full_scan():
    results = []; bar = st.progress(0); status = st.empty()
    start_date = st.session_state.class_start_date; dur = st.session_state.class_duration_label
    for i, stock in enumerate(FNO_STOCKS):
        status.caption(f"Scanning {stock}...")
        df = fetch_stock_data(stock, start_date)
        if df is not None:
            cat, sig, close, chg, hist, res, sup, tr = classify_stock(df)
            if close > 0: results.append({ "Symbol": stock, "Sector": SECTOR_MAP.get(stock, "Other"), "Price": close, "Change": chg, "Category": cat, "Signal": sig, "History": hist, "BU": res, "BE": sup, "Trend": tr })
        bar.progress((i+1)/len(FNO_STOCKS)); time.sleep(0.05)
    bar.empty(); status.empty()
    save = { "date": datetime.now().strftime("%Y-%m-%d"), "last_updated": datetime.now().strftime("%H:%M:%S"), "duration_label": dur, "stocks": results }
    with open(CLASS_FILE, 'w') as f: json.dump(save, f)
    return save

def check_scan():
    now = datetime.now(); today = now.strftime("%Y-%m-%d")
    if not os.path.exists(CLASS_FILE): return True, "Init"
    try:
        with open(CLASS_FILE, 'r') as f: data = json.load(f)
        if data.get("date") != today and now.hour >= 18: return True, "Daily"
        if data.get("duration_label") != st.session_state.class_duration_label: return True, "Duration Change"
        if data.get('stocks') and len(data['stocks']) > 0 and 'Trend' not in data['stocks'][0]: return True, "Schema"
        return False, data
    except: return True, "Error"

do_scan, payload = check_scan()
if force_scan: st.toast("Scanning..."); current_data = run_full_scan(); st.rerun()
elif do_scan: st.info("Auto-Scanning..."); current_data = run_full_scan(); st.rerun()
else: current_data = payload

# --- DISPLAY ---
if current_data:
    st.caption(f"Last: {current_data['date']} {current_data['last_updated']} | {current_data.get('duration_label')}")
    if current_data.get('duration_label') != st.session_state.class_duration_label: st.warning(f"Data mismatch. Click Refresh.")
    st.divider()
    search = st.text_input("🔍 Search", placeholder="e.g. RELIANCE").upper()
    data = current_data['stocks']
    data = [d for d in data if view_min <= d['Price'] <= view_max]
    if sector_filter != "All": data = [d for d in data if d.get('Sector') == sector_filter]
    if search: data = [d for d in data if search in d['Symbol']]
        
    high_bull = [d for d in data if d['Category'] == "Highly Bullish"]
    bull = [d for d in data if d['Category'] == "Bullish"]
    high_bear = [d for d in data if d['Category'] == "Highly Bearish"]
    bear = [d for d in data if d['Category'] == "Bearish"]
    atak_teji = [d for d in data if d['Category'] == "Atak (Teji Side)"]
    atak_mandi = [d for d in data if d['Category'] == "Atak (Mandi Side)"]
    
    cats = []
    if category_filter == "All": cats = [("🚀 Highly Bullish", high_bull, "b-high-bull"), ("🟢 Bullish", bull, "b-bull"), ("🩸 Highly Bearish", high_bear, "b-high-bear"), ("🔴 Bearish", bear, "b-bear"), ("⚠️ Atak Teji", atak_teji, "b-atak-top"), ("🛡️ Atak Mandi", atak_mandi, "b-atak-bot")]
    elif category_filter == "Bullish Only": cats = [("🟢 Bullish", bull, "b-bull")]
    elif category_filter == "High Momentum Only": cats = [("🚀 Highly Bullish", high_bull, "b-high-bull")]
    
    def render(title, items, border):
        st.markdown("""<style>.streamlit-expanderHeader {color: black !important; font-weight: bold;}</style>""", unsafe_allow_html=True)
        with st.expander(f"{title} ({len(items)})", expanded=True):
            if not items: st.caption("None"); return
            for i in items:
                col = "chg-green" if i['Change']>=0 else "chg-red"
                st.markdown(f"<div class='class-card {border}'><div style='display:flex; justify-content:space-between;'><span class='stock-title'>{i['Symbol']} <span style='font-size:0.8em;color:#999;'>({i['Sector']})</span></span><span class='stock-price'>{i['Price']:.2f}</span></div><div style='margin-top:4px;'><span class='{col}'>{i['Change']:.2f}%</span></div><div class='signal-text'>{i['Signal']}</div></div>", unsafe_allow_html=True)
                if st.button(f"View {i['Symbol']}", key=i['Symbol'], use_container_width=True): show_details(i)
                
    @st.dialog("Details", width="large")
    def show_details(s):
        st.subheader(f"{s['Symbol']} : {s['Price']:.2f}")
        c1,c2,c3 = st.columns(3)
        c1.metric("Trend", s['Trend']); c2.metric("Resist", f"{s['BU']:.2f}"); c3.metric("Support", f"{s['BE']:.2f}")
        st.divider()
        def color(row):
            t = row['Type']
            # EXACT COLOR MAPPING
            if t=='bull_dark': return ['background-color:#228B22; color:white; font-weight:bold']*len(row) # Dark Green
            if t=='bear_dark': return ['background-color:#8B0000; color:white; font-weight:bold']*len(row) # Dark Red
            if t=='bull_light': return ['background-color:#90EE90; color:black; font-weight:bold']*len(row) # Light Green
            if t=='bear_light': return ['background-color:#FFC0CB; color:black; font-weight:bold']*len(row) # Light Red
            return ['']*len(row)
        st.dataframe(pd.DataFrame(s['History']).style.apply(color, axis=1), column_config={"Type": None}, use_container_width=True, height=400)

    if category_filter == "All":
        c1, c2, c3 = st.columns(3)
        with c1: render(cats[0][0], cats[0][1], cats[0][2]); render(cats[3][0], cats[3][1], cats[3][2])
        with c2: render(cats[1][0], cats[1][1], cats[1][2]); render(cats[4][0], cats[4][1], cats[4][2])
        with c3: render(cats[2][0], cats[2][1], cats[2][2]); render(cats[5][0], cats[5][1], cats[5][2])
    else:
        for c in cats: render(c[0], c[1], c[2])
