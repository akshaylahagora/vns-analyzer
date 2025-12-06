import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.parse
import time
import json
import os
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pro F&O Scanner", page_icon="🔭", layout="wide")

st.title("🔭 Pro F&O Scanner")
st.markdown("Automated VNS Scanner • **Updates daily after 6:00 PM**")

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] { color: #000000 !important; }
    
    .stock-card {
        background-color: #ffffff;
        padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 5px;
    }
    .stock-symbol { font-size: 1.1em; font-weight: 800; color: #333; }
    .stock-price { font-size: 1.0em; font-weight: 600; color: #555; }
    
    .col-header { padding: 10px; border-radius: 8px; color: white; font-weight: bold; text-align: center; margin-bottom: 15px; text-transform: uppercase; }
    div[data-testid="stDialog"] { width: 85vw; } 
    .stSidebar label { color: #333 !important; }
    .streamlit-expanderHeader { color: #000000 !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- CONFIG ---
SCAN_FILE = "daily_scan_results.json" 
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

if 'scan_start_date' not in st.session_state: st.session_state.scan_start_date = datetime.now() - timedelta(days=30)
if 'scan_duration_label' not in st.session_state: st.session_state.scan_duration_label = "1M"

def update_scan_settings():
    sel = st.session_state.duration_select
    st.session_state.scan_duration_label = sel
    now = datetime.now()
    days = {"1M":30, "2M":60, "3M":90, "6M":180, "1Y":365}
    if sel in days: st.session_state.scan_start_date = now - timedelta(days=days[sel])

with st.sidebar:
    st.header("⚙️ Scanner Settings")
    st.radio("Duration", ["1M", "2M", "3M", "6M", "1Y"], index=0, horizontal=True, key="duration_select", on_change=update_scan_settings)
    st.divider()
    c1, c2 = st.columns(2)
    view_min = c1.number_input("Min", 1000, value=1000)
    view_max = c2.number_input("Max", 0, value=100000)
    st.divider()
    scan_delay = st.slider("Delay (sec)", 0.0, 1.0, 0.1)
    force_scan = st.button("🔄 Force Refresh", type="primary", use_container_width=True)

# --- CORE ---
def fetch_stock_data(symbol, start_date):
    try:
        yf_symbol = f"{symbol}.NS"
        req_start = start_date - timedelta(days=30) # Buffer
        df = yf.download(yf_symbol, start=req_start, progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

def analyze_vns_full(df):
    results = []
    trend = "Neutral"
    last_peak = df.iloc[0]['High']; last_trough = df.iloc[0]['Low']
    reaction_support = df.iloc[0]['Low']; reaction_resist = df.iloc[0]['High']
    last_peak_idx = 0; last_trough_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]; c_h, c_l = curr['High'], curr['Low']
        bu, be, signal, signal_type = None, None, "", ""
        
        if trend == "Teji":
            if c_h > last_peak:
                bu = f"T (Teji) {c_h:.2f}"; signal_type="bull_dark"; signal="New High"
                swing_df = df.iloc[last_peak_idx:i+1]; reaction_support = swing_df['Low'].min()
                be = f"R (Sup) {reaction_support:.2f}"
                last_peak = c_h; last_peak_idx = i
            elif c_l < reaction_support:
                bu = f"ATAK (Top) {last_peak:.2f}"; be = f"M (Mandi) {c_l:.2f}"; signal_type="bear_dark"; signal="Reversal"
                trend = "Mandi"; last_trough = c_l; last_trough_idx = i; reaction_resist = c_h
        elif trend == "Mandi":
            if c_l < last_trough:
                be = f"M (Mandi) {c_l:.2f}"; signal_type="bear_dark"; signal="New Low"
                swing_df = df.iloc[last_trough_idx:i+1]; reaction_resist = swing_df['High'].max()
                bu = f"R (Resist) {reaction_resist:.2f}"
                last_trough = c_l; last_trough_idx = i
            elif c_h > reaction_resist:
                be = f"ATAK (Bot) {last_trough:.2f}"; bu = f"T (Teji) {c_h:.2f}"; signal_type="bull_dark"; signal="Reversal"
                trend = "Teji"; last_peak = c_h; last_peak_idx = i; reaction_support = c_l
        else:
            if c_h > last_peak: trend="Teji"; bu="Start Teji"; signal_type="bull_dark"; last_peak=c_h; last_peak_idx=i
            elif c_l < last_trough: trend="Mandi"; be="Start Mandi"; signal_type="bear_dark"; last_trough=c_l; last_trough_idx=i
        
        # Use color types matching Home.py
        # Mapping logic to color types:
        # T (Teji) -> bull_dark (Dark Green)
        # M (Mandi) -> bear_dark (Dark Red)
        # R (Sup/Res) -> Light Green / Light Red based on trend context
        # ATAK -> Light Red (Top) / Light Green (Bottom)
        
        color_type = ""
        if "T (Teji)" in str(bu) or "Start Teji" in str(bu): color_type = "bull_dark"
        elif "M (Mandi)" in str(be) or "Start Mandi" in str(be): color_type = "bear_dark"
        elif "ATAK (Top)" in str(bu): color_type = "bear_light"
        elif "ATAK (Bot)" in str(be): color_type = "bull_light"
        elif "R (Sup)" in str(be): color_type = "bull_light"
        elif "R (Resist)" in str(bu): color_type = "bear_light"

        results.append({
            'Date': curr['Date'].strftime('%d-%b-%Y'), 'Open': curr['Open'], 'High': curr['High'], 'Low': curr['Low'], 'Close': curr['Close'],
            'BU': bu, 'BE': be, 'Signal': signal, 'Type': color_type
        })
    return trend, reaction_resist, reaction_support, df.iloc[-1]['Close'], results

def run_full_scan():
    results = []; bar = st.progress(0); status = st.empty()
    start_date = st.session_state.scan_start_date; dur = st.session_state.scan_duration_label
    for i, stock in enumerate(FNO_STOCKS):
        status.caption(f"Scanning {stock}...")
        df = fetch_stock_data(stock, start_date)
        if df is not None:
            trend, res, sup, close, hist = analyze_vns_full(df)
            results.append({ "Symbol": stock, "Trend": trend, "Close": close, "BU": res, "BE": sup, "History": hist })
        bar.progress((i+1)/len(FNO_STOCKS)); time.sleep(scan_delay)
    bar.empty(); status.empty()
    save = { "date": datetime.now().strftime("%Y-%m-%d"), "last_updated": datetime.now().strftime("%H:%M:%S"), "duration_label": dur, "stocks": results }
    with open(SCAN_FILE, 'w') as f: json.dump(save, f)
    return save

def check_scan():
    now = datetime.now(); today = now.strftime("%Y-%m-%d")
    if not os.path.exists(SCAN_FILE): return True, "Init"
    try:
        with open(SCAN_FILE, 'r') as f: data = json.load(f)
        if data.get("date") != today and now.hour >= 18: return True, "Daily"
        return False, data
    except: return True, "Error"

do_scan, payload = check_scan()
if force_scan: st.toast("Scanning..."); current_data = run_full_scan(); st.rerun()
elif do_scan: st.info("Auto-Scanning..."); current_data = run_full_scan(); st.rerun()
else: current_data = payload

# --- DISPLAY ---
if current_data:
    st.caption(f"Last Scanned: {current_data['date']} {current_data['last_updated']}")
    all_s = current_data['stocks']; filtered = [s for s in all_s if view_min_price <= s['Close'] <= view_max_price]
    bulls = [s for s in filtered if s['Trend'] == "Teji"]
    bears = [s for s in filtered if s['Trend'] == "Mandi"]
    neut = [s for s in filtered if s['Trend'] == "Neutral"]

    @st.dialog("Details", width="large")
    def show(s):
        st.subheader(f"{s['Symbol']} : {s['Close']:.2f}")
        c1,c2,c3 = st.columns(3)
        c1.metric("Trend", s['Trend']); c2.metric("Resistance", f"{s['BU']:.2f}"); c3.metric("Support", f"{s['BE']:.2f}")
        st.divider()
        h = pd.DataFrame(s['History'])
        def color(row):
            t = row['Type']
            # EXACT COLOR MAPPING FROM HOME.PY
            if t=='bull_dark': return ['background-color: #228B22; color: white; font-weight: bold']*len(row) # Dark Green
            if t=='bear_dark': return ['background-color: #8B0000; color: white; font-weight: bold']*len(row) # Dark Red
            if t=='bull_light': return ['background-color: #90EE90; color: black; font-weight: bold']*len(row) # Light Green
            if t=='bear_light': return ['background-color: #FFC0CB; color: black; font-weight: bold']*len(row) # Light Red
            return ['']*len(row)
            
        st.dataframe(h.style.apply(color, axis=1), column_config={"Type": None}, use_container_width=True, height=400)

    def render(lst, title, col):
        st.markdown(f"<div style='background:{col}; padding:8px; border-radius:5px; color:white; text-align:center; font-weight:bold;'>{title} ({len(lst)})</div>", unsafe_allow_html=True)
        for s in lst:
            with st.container():
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="stock-symbol">{s['Symbol']}</span>
                        <span class="stock-price">{s['Close']:.2f}</span>
                    </div>
                    <div style="font-size:0.85em; color:#666; display:flex; justify-content:space-between;">
                        <span>Res: {s['BU']:.2f}</span><span>Sup: {s['BE']:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View", key=s['Symbol'], use_container_width=True): show(s)

    c1, c2, c3 = st.columns(3)
    with c1: render(bulls, "TEJI (BULL)", "#28a745")
    with c2: render(bears, "MANDI (BEAR)", "#dc3545")
    with c3: render(neut, "NEUTRAL", "#6c757d")
