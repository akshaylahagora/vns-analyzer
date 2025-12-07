import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta
import yfinance as yf

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    div[data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #444444 !important; font-weight: 600 !important; }
    .trend-card { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.2rem; border: 2px solid transparent; }
    .trend-bull { background-color: #d1e7dd; color: #0f5132; border-color: #badbcc; }
    .trend-bear { background-color: #f8d7da; color: #842029; border-color: #f5c2c7; }
    .trend-neutral { background-color: #e2e3e5; color: #41464b; border-color: #d3d6d8; }
    .stDataFrame { font-size: 1.1rem; }
    .stDataFrame td { vertical-align: middle !important; white-space: pre-wrap !important; }
    .stSidebar label { color: #333 !important; }
    .metric-container { background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- STOCK LIST ---
STOCK_LIST = [
    "360ONE", "ABB", "APLAPOLLO", "AUBANK", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ABCAPITAL", "ALKEM", "AMBER", "AMBUJACEM", "ANGELONE", "APOLLOHOSP", "ASHOKLEY", "ASIANPAINT", "ASTRAL", "AUROPHARMA", "DMART", "AXISBANK", "BSE", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BDL", "BEL", "BHARATFORG", "BHEL", "BPCL", "BHARTIARTL", "BIOCON", "BLUESTARCO", "BOSCHLTD", "BRITANNIA", "CGPOWER", "CANBK", "CDSL", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CAMS", "CONCOR", "CROMPTON", "CUMMINSIND", "CYIENT", "DLF", "DABUR", "DALBHARAT", "DELHIVERY", "DIVISLAB", "DIXON", "DRREDDY", "EICHERMOT", "EXIDEIND", "NYKAA", "FORTIS", "GAIL", "GMRAIRPORT", "GLENMARK", "GODREJCP", "GODREJPROP", "GRASIM", "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HFCL", "HAVELLS", "HEROMOTOCO", "HINDALCO", "HAL", "HINDPETRO", "HINDUNILVR", "HINDZINC", "POWERINDIA", "HUDCO", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDFCFIRSTB", "IIFL", "ITC", "INDIANB", "IEX", "IOC", "IRCTC", "IRFC", "IREDA", "INDUSTOWER", "INDUSINDBK", "NAUKRI", "INFY", "INOXWIND", "INDIGO", "JINDALSTEL", "JSWENERGY", "JSWSTEEL", "JIOFIN", "JUBLFOOD", "KEI", "KPITTECH", "KALYANKJIL", "KAYNES", "KFINTECH", "KOTAKBANK", "LTF", "LICHSGFIN", "LTIM", "LT", "LAURUSLABS", "LICI", "LODHA", "LUPIN", "M&M", "MANAPPURAM", "MANKIND", "MARICO", "MARUTI", "MFSL", "MAXHEALTH", "MAZDOCK", "MPHASIS", "MCX", "MUTHOOTFIN", "NBCC", "NCC", "NHPC", "NMDC", "NTPC", "NATIONALUM", "NESTLEIND", "NUVAMA", "OBEROIRLTY", "ONGC", "OIL", "PAYTM", "OFSS", "POLICYBZR", "PGEL", "PIIND", "PNBHOUSING", "PAGEIND", "PATANJALI", "PERSISTENT", "PETRONET", "PIDILITIND", "PPLPHARMA", "POLYCAB", "PFC", "POWERGRID", "PRESTIGE", "PNB", "RBLBANK", "RECLTD", "RVNL", "RELIANCE", "SBICARD", "SBILIFE", "SHREECEM", "SRF", "SAMMAANCAP", "MOTHERSON", "SHRIRAMFIN", "SIEMENS", "SOLARINDS", "SONACOMS", "SBIN", "SAIL", "SUNPHARMA", "SUPREMEIND", "SUZLON", "SYNGENE", "TATACONSUM", "TITAGARH", "TVSMOTOR", "TCS", "TATAELXSI", "TATAPOWER", "TATASTEEL", "TATATECH", "TECHM", "FEDERALBNK", "INDHOTEL", "PHOENIXLTD", "TITAN", "TORNTPHARM", "TORNTPOWER", "TRENT", "TIINDIA", "UNOMINDA", "UPL", "ULTRACEMCO", "UNIONBANK", "UNITDSPR", "VBL", "VEDL", "IDEA", "VOLTAS", "WIPRO", "YESBANK", "ZYDUSLIFE"
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

# --- FETCH DATA ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        yf_symbol = f"{symbol}.NS"
        req_start = start - timedelta(days=90) # Buffer to find context
        df = yf.download(yf_symbol, start=req_start, end=end + timedelta(days=1), progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- VNS LOGIC (SWING CONFIRMATION) ---
def analyze_vns(df):
    df['BU'], df['BE'], df['Type'] = "", "", ""
    trend = "Neutral" # Teji, Mandi
    
    # State Memory
    last_major_high = df.iloc[0]['High']
    last_major_low = df.iloc[0]['Low']
    
    reaction_low = df.iloc[0]['Low']
    reaction_high = df.iloc[0]['High']
    
    # Range Indices
    last_bottom_idx = 0
    last_top_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        c_h, c_l, c_c = curr['High'], curr['Low'], curr['Close']
        p_h, p_l = prev['High'], prev['Low']
        d_str = curr['Date'].strftime('%d-%b').upper()
        
        # --- 1. CONFIRM A TOP (BU) ---
        # Trigger: Low is broken (c_l < p_l)
        if c_l < p_l:
            # We have a confirmed local top. Now we check WHAT kind of top it is.
            
            # Find the highest high since the last confirmed bottom
            # Range: last_bottom_idx to i-1
            search_start = last_bottom_idx
            if search_start >= i: search_start = i-1 # Safety
            
            swing_df = df.iloc[search_start : i]
            if not swing_df.empty:
                peak_idx = swing_df['High'].idxmax()
                peak_val = df.at[peak_idx, 'High']
                
                # Logic to label this peak
                if trend == "Teji":
                    if peak_val >= last_major_high:
                        # Higher High -> Continuation
                        df.at[peak_idx, 'BU'] = f"BU(T) {d_str}\n{peak_val:.2f}"
                        df.at[peak_idx, 'Type'] = "bull_dark"
                        last_major_high = peak_val
                        last_top_idx = peak_idx
                    else:
                        # Lower High -> Atak
                        df.at[peak_idx, 'BU'] = f"ATAK (Top) {d_str}\n{peak_val:.2f}"
                        df.at[peak_idx, 'Type'] = "bear_light"
                        last_top_idx = peak_idx
                        
                elif trend == "Mandi":
                    # In Mandi, a top is a Reaction High
                    df.at[peak_idx, 'BU'] = f"R(Mandi) {d_str}\n{peak_val:.2f}"
                    df.at[peak_idx, 'Type'] = "bear_light"
                    reaction_high = peak_val
                    last_top_idx = peak_idx
                    
                else: # Neutral
                    if peak_val > last_major_high:
                        trend = "Teji"
                        df.at[peak_idx, 'BU'] = f"Start Teji\n{peak_val:.2f}"
                        df.at[peak_idx, 'Type'] = "bull_dark"
                        last_major_high = peak_val
                        last_top_idx = peak_idx

        # --- 2. CONFIRM A BOTTOM (BE) ---
        # Trigger: High is crossed (c_h > p_h)
        if c_h > p_h:
            # We have a confirmed local bottom.
            
            # Find lowest low since last confirmed top
            search_start = last_top_idx
            if search_start >= i: search_start = i-1
            
            swing_df = df.iloc[search_start : i]
            if not swing_df.empty:
                trough_idx = swing_df['Low'].idxmin()
                trough_val = df.at[trough_idx, 'Low']
                
                if trend == "Mandi":
                    if trough_val <= last_major_low:
                        # Lower Low -> Continuation
                        df.at[trough_idx, 'BE'] = f"BE(M) {d_str}\n{trough_val:.2f}"
                        df.at[trough_idx, 'Type'] = "bear_dark"
                        last_major_low = trough_val
                        last_bottom_idx = trough_idx
                    else:
                        # Higher Low -> Atak
                        df.at[trough_idx, 'BE'] = f"ATAK (Bot) {d_str}\n{trough_val:.2f}"
                        df.at[trough_idx, 'Type'] = "bull_light"
                        last_bottom_idx = trough_idx
                
                elif trend == "Teji":
                    # In Teji, a bottom is a Reaction Low
                    df.at[trough_idx, 'BE'] = f"R(Teji) {d_str}\n{trough_val:.2f}"
                    df.at[trough_idx, 'Type'] = "bull_light"
                    reaction_low = trough_val
                    last_bottom_idx = trough_idx
                    
                else: # Neutral
                    if trough_val < last_major_low:
                        trend = "Mandi"
                        df.at[trough_idx, 'BE'] = f"Start Mandi\n{trough_val:.2f}"
                        df.at[trough_idx, 'Type'] = "bear_dark"
                        last_major_low = trough_val
                        last_bottom_idx = trough_idx

        # --- 3. TREND SWITCHING (Immediate on Cross) ---
        if trend == "Teji" and c_c < reaction_low:
            trend = "Mandi"
            # We can mark the breakdown row if desired
            # df.at[i, 'BE'] = f"BREAKDOWN\n{c_c:.2f}"
            last_major_low = c_l # Start tracking new trend from here
            
        if trend == "Mandi" and c_c > reaction_high:
            trend = "Teji"
            # df.at[i, 'BU'] = f"BREAKOUT\n{c_c:.2f}"
            last_major_high = c_h

    # Active Levels for Header
    fin_res = reaction_high if trend == "Mandi" else "-"
    fin_sup = reaction_low if trend == "Teji" else "-"
    
    return df, trend, fin_res, fin_sup

# --- RENDER ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner("Fetching..."):
        raw_df = fetch_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            df_full, final_trend, fin_res, fin_sup = analyze_vns(raw_df)
            mask = (df_full['Date'] >= st.session_state.start_date) & (df_full['Date'] <= st.session_state.end_date)
            df = df_full.loc[mask].copy()
            
            c1, c2, c3, c4 = st.columns(4)
            def card(label, value): return f"""<div class="metric-container"><div style="font-size:0.9rem; color:#666; font-weight:bold;">{label}</div><div style="font-size:1.6rem; color:#000; font-weight:bold;">{value}</div></div>"""
            with c1:
                color, txt = ("#6c757d", "NEUTRAL")
                if final_trend == "Teji": color, txt = ("#d1e7dd", "BULLISH (TEJI)")
                elif final_trend == "Mandi": color, txt = ("#f8d7da", "BEARISH (MANDI)")
                st.markdown(f"""<div style="background:{color}; padding:15px; border-radius:8px; text-align:center; color:black; font-weight:bold; font-size:1.2rem; border:1px solid #ccc;">{txt}</div>""", unsafe_allow_html=True)
            with c2: st.markdown(card("Last Close", f"{df.iloc[-1]['Close']:.2f}"), unsafe_allow_html=True)
            with c3: st.markdown(card("Active Resist", f"{fin_res}"), unsafe_allow_html=True)
            with c4: st.markdown(card("Active Support", f"{fin_sup}"), unsafe_allow_html=True)
            
            st.divider()
            
            disp = df[['Date', 'Open', 'High', 'Low', 'Close', 'BU', 'BE', 'Type']].copy()
            disp.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (Teji/Resist)', 'BE (Mandi/Support)', 'Type']
            
            def color_cells(row):
                styles = ['background-color: white; color: black; white-space: pre-wrap;'] * len(row)
                bu_txt = str(row['BU (Teji/Resist)'])
                be_txt = str(row['BE (Mandi/Support)'])
                
                if "BU(T)" in bu_txt or "Start Teji" in bu_txt: styles[5] = 'background-color: #228B22; color: white; font-weight: bold; white-space: pre-wrap;'
                elif "R(" in bu_txt: styles[5] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; white-space: pre-wrap;'
                elif "ATAK" in bu_txt: styles[5] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; white-space: pre-wrap;'
                
                if "BE(M)" in be_txt or "Start Mandi" in be_txt: styles[6] = 'background-color: #8B0000; color: white; font-weight: bold; white-space: pre-wrap;'
                elif "R(" in be_txt: styles[6] = 'background-color: #d4edda; color: #155724; font-weight: bold; white-space: pre-wrap;'
                elif "ATAK" in be_txt: styles[6] = 'background-color: #d4edda; color: #155724; font-weight: bold; white-space: pre-wrap;'
                return styles

            st.dataframe(
                disp.style.apply(color_cells, axis=1).format({"Date": lambda t: t.strftime("%d-%b-%Y"), "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"}),
                column_config={"Type": None, "BU (Teji/Resist)": st.column_config.TextColumn(width="medium"), "BE (Mandi/Support)": st.column_config.TextColumn(width="medium")},
                use_container_width=True, height=800
            )
        else: st.error("⚠️ Data Error.")
else: st.info("👈 Click RUN")