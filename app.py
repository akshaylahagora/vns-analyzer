import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS (VISIBILITY FIX) ---
st.markdown("""
<style>
    /* Force Background to White */
    .stApp { background-color: white; color: black; }
    
    /* 1. FORCE METRICS TEXT TO BLACK (Fixes visibility issue) */
    div[data-testid="stMetricValue"] { 
        color: #000000 !important; 
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] { 
        color: #444444 !important; 
        font-weight: 600 !important;
    }
    
    /* 2. TREND BADGES */
    .status-bull { 
        background-color: #d1e7dd; color: #0f5132; padding: 10px; border-radius: 8px; 
        font-weight: bold; text-align: center; border: 2px solid #badbcc; font-size: 1.2rem; 
    }
    .status-bear { 
        background-color: #f8d7da; color: #842029; padding: 10px; border-radius: 8px; 
        font-weight: bold; text-align: center; border: 2px solid #f5c2c7; font-size: 1.2rem; 
    }
    .status-neutral { 
        background-color: #e2e3e5; color: #41464b; padding: 10px; border-radius: 8px; 
        font-weight: bold; text-align: center; border: 2px solid #d3d6d8; font-size: 1.2rem; 
    }

    /* 3. TABLE TEXT SIZE */
    .stDataFrame { font-size: 1.1rem; }
    
    /* 4. SIDEBAR INPUTS */
    .stSelectbox label, .stRadio label, .stDateInput label {
        color: #333 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- COMPLETE STOCK LIST ---
STOCK_LIST = [
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
STOCK_LIST = sorted(list(set(STOCK_LIST))) 

# --- STATE ---
if 'start_date' not in st.session_state: st.session_state.start_date = datetime.now() - timedelta(days=60)
if 'end_date' not in st.session_state: st.session_state.end_date = datetime.now()

def update_dates():
    sel = st.session_state.duration_selector
    now = datetime.now()
    st.session_state.end_date = now
    days = {"1M":30, "2M":60, "3M":90, "6M":180, "1Y":365}
    if sel == "YTD": st.session_state.start_date = datetime(now.year, 1, 1)
    elif sel in days: st.session_state.start_date = now - timedelta(days=days[sel])

with st.sidebar:
    st.header("⚙️ Settings")
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK") if "KOTAKBANK" in STOCK_LIST else 0)
    st.divider()
    st.radio("Period:", ["1M", "2M", "3M", "6M", "1Y", "YTD", "Custom"], index=1, horizontal=True, key="duration_selector", on_change=update_dates)
    date_range = st.date_input("Range", (st.session_state.start_date, st.session_state.end_date))
    if len(date_range) == 2: st.session_state.start_date, st.session_state.end_date = [datetime.combine(d, datetime.min.time()) for d in date_range]
    st.divider()
    run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

# --- DATA ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        # Encode symbol for URL
        safe_symbol = urllib.parse.quote(symbol)
        
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        s = requests.Session(); s.headers.update(headers); s.get("https://www.nseindia.com", timeout=5)
        
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={safe_symbol}&type=priceVolumeDeliverable&series=ALL"
        r = s.get(url, timeout=10)
        
        if r.status_code == 200:
            df = pd.DataFrame(r.json().get('data', []))
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for c in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']: df[c] = df[c].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except: return None
    return None

# --- LOGIC ---
def analyze_vns(df):
    df['BU'], df['BE'], df['Type'] = "", "", ""
    trend = "Neutral"
    last_bu, last_be = None, None
    
    for i in range(1, len(df)):
        curr = df.iloc[i]; prev = df.iloc[i-1]
        c_h, c_l, c_c = curr['CH_TRADE_HIGH_PRICE'], curr['CH_TRADE_LOW_PRICE'], curr['CH_CLOSING_PRICE']
        p_h, p_l = prev['CH_TRADE_HIGH_PRICE'], prev['CH_TRADE_LOW_PRICE']
        d_str = prev['Date'].strftime('%d-%b').upper()
        
        # ATAK
        if last_bu and (last_bu*0.995 <= c_h <= last_bu*1.005) and c_c < last_bu:
            df.at[i, 'BU'] = f"ATAK (Top) {c_h}"; df.at[i, 'Type'] = "warn"
        if last_be and (last_be*0.995 <= c_l <= last_be*1.005) and c_c > last_be:
            df.at[i, 'BE'] = f"ATAK (Bottom) {c_l}"; df.at[i, 'Type'] = "warn"

        # TREND
        if trend == "Bullish":
            if c_l < p_l: 
                df.at[i-1, 'BU'] = f"BU(T) {d_str} : {p_h}"; df.at[i-1, 'Type']="bull"; last_bu = p_h
            if c_h > p_h: 
                df.at[i-1, 'BE'] = f"R(Teji) : {p_l}"; df.at[i-1, 'Type']="info"; last_be = p_l
        
        elif trend == "Bearish":
            if c_h > p_h: 
                df.at[i-1, 'BE'] = f"BE(M) {d_str} : {p_l}"; df.at[i-1, 'Type']="bear"; last_be = p_l
            if c_l < p_l: 
                df.at[i-1, 'BU'] = f"R(Mandi) {d_str} : {p_h}"; df.at[i-1, 'Type']="info"; last_bu = p_h
                
        else: # Neutral
            if c_h > p_h: trend="Bullish"; df.at[i-1, 'BE']=f"Start Teji : {p_l}"; df.at[i-1, 'Type']="bull"; last_be=p_l
            elif c_l < p_l: trend="Bearish"; df.at[i-1, 'BU']=f"Start Mandi : {p_h}"; df.at[i-1, 'Type']="bear"; last_bu=p_h
            
        # SWITCH
        if trend == "Bearish" and last_bu and c_c > last_bu:
            trend="Bullish"; df.at[i, 'BU']="BREAKOUT (Teji)"; df.at[i, 'Type']="bull"
        if trend == "Bullish" and last_be and c_c < last_be:
            trend="Bearish"; df.at[i, 'BE']="BREAKDOWN (Mandi)"; df.at[i, 'Type']="bear"
            
    return df, trend, last_bu, last_be

# --- RENDER ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner("Fetching..."):
        raw_df = fetch_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            df, final_trend, final_res, final_sup = analyze_vns(raw_df)
            
            # --- OVERALL TREND HEADER ---
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown("**Overall Trend**")
                if final_trend == "Bullish":
                    st.markdown('<div class="status-bull">BULLISH (TEJI)</div>', unsafe_allow_html=True)
                elif final_trend == "Bearish":
                    st.markdown('<div class="status-bear">BEARISH (MANDI)</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-neutral">NEUTRAL</div>', unsafe_allow_html=True)
            
            with c2: st.metric("Last Close", f"{df.iloc[-1]['CH_CLOSING_PRICE']:.2f}")
            with c3: st.metric("Active Resistance", f"{final_res:.2f}" if final_res else "-")
            with c4: st.metric("Active Support", f"{final_sup:.2f}" if final_sup else "-")
            
            st.divider()
            
            # --- TABLE ---
            disp_df = df[['Date', 'CH_OPENING_PRICE', 'CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_CLOSING_PRICE', 'BU', 'BE', 'Type']].copy()
            disp_df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (Resist)', 'BE (Support)', 'Type']
            
            def color_rows(row):
                s = row['Type']
                if s == 'bull': return ['background-color: #C6EFCE; color: #006100; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'bear': return ['background-color: #FFC7CE; color: #9C0006; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'warn': return ['background-color: #FFEB9C; color: #9C5700; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'info': return ['background-color: #E6F3FF; color: #000; font-style: italic; white-space: pre-wrap;'] * len(row)
                return ['white-space: pre-wrap;'] * len(row)

            st.dataframe(
                disp_df.style.apply(color_rows, axis=1).format({
                    "Date": lambda t: t.strftime("%d-%b-%Y"),
                    "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"
                }),
                column_config={"Type": None, "BU (Resist)": st.column_config.TextColumn(width="medium"), "BE (Support)": st.column_config.TextColumn(width="medium")},
                use_container_width=True,
                height=800
            )
        else: st.error("⚠️ Data Error. Check symbol or try again.")
else: st.info("👈 Click RUN")
