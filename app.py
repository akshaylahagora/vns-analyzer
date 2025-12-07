import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta
import yfinance as yf

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    
    /* Metrics */
    div[data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #444444 !important; font-weight: 600 !important; }
    
    /* Trend Cards */
    .trend-card { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.2rem; border: 2px solid transparent; }
    .trend-bull { background-color: #d1e7dd; color: #0f5132; border-color: #badbcc; }
    .trend-bear { background-color: #f8d7da; color: #842029; border-color: #f5c2c7; }
    .trend-neutral { background-color: #e2e3e5; color: #41464b; border-color: #d3d6d8; }

    /* Table Font */
    .stDataFrame { font-size: 1.1rem; }
    .stDataFrame td { vertical-align: middle !important; white-space: pre-wrap !important; }
    .stSidebar label { color: #333 !important; }
    
    .metric-container {
        background-color: #f8f9fa; border: 1px solid #ddd;
        border-radius: 8px; padding: 15px; text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- STOCK LIST ---
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

# --- FETCH DATA ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        yf_symbol = f"{symbol}.NS"
        req_start = start - timedelta(days=60) # Buffer for calculation
        df = yf.download(yf_symbol, start=req_start, end=end + timedelta(days=1), progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- VNS LOGIC (RETROACTIVE MARKING) ---
def analyze_vns(df):
    df['BU'], df['BE'], df['Type'] = "", "", ""
    trend = "Neutral"
    
    last_peak = df.iloc[0]['High']
    last_trough = df.iloc[0]['Low']
    
    # We track the "Active Swing" min/max to detect reaction
    swing_low = df.iloc[0]['Low'] 
    swing_low_idx = 0
    
    swing_high = df.iloc[0]['High']
    swing_high_idx = 0
    
    # Track Indices
    last_peak_idx = 0
    last_trough_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        c_h, c_l = curr['High'], curr['Low']
        d_str = curr['Date'].strftime('%d-%b').upper()
        
        # --- TEJI (UPTREND) ---
        if trend == "Teji":
            # 1. Continuation (New High)
            if c_h > last_peak:
                df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_h:.2f}"; df.at[i, 'Type'] = "bull_dark"
                
                last_peak = c_h; last_peak_idx = i
                swing_low = c_l; swing_low_idx = i # Reset swing low tracker
                
            else:
                # Update Lowest Low since peak
                if c_l < swing_low:
                    swing_low = c_l; swing_low_idx = i
                
                # Check for Breakdown of the CONFIRMED Reaction
                # A reaction is the lowest point between the Peak and the Breakdown
                # But we only know it's a breakdown when we cross below it.
                
                # If we drop below the lowest low seen so far in this pullback...
                # Wait, "Reaction" is simply the lowest point between two highs.
                # If we are dropping, and we break the 'swing_low' we were tracking... 
                # actually, we just update swing_low if we drop below it, UNLESS we had a bounce.
                
                # Correct Logic: 
                # We need to find if there was a bounce (higher low) that is now being broken.
                # OR if we are breaking the "Lowest Low" established after the Peak.
                
                # Let's simplify:
                # 1. We have a Peak at last_peak_idx.
                # 2. We have a lowest point since then at swing_low_idx.
                # 3. If price rose from swing_low_idx (bounce) and THEN breaks swing_low...
                
                if i > swing_low_idx: 
                    # Check if there was a bounce between swing_low_idx and now
                    interim = df.iloc[swing_low_idx+1 : i]
                    if not interim.empty:
                        bounce_high = interim['High'].max()
                        
                        # If current low breaks the swing low
                        if c_l < swing_low:
                            # BREAKDOWN CONFIRMED
                            
                            # 1. Mark Reaction (The low that was broken)
                            r_date = df.at[swing_low_idx, 'Date'].strftime('%d-%b').upper()
                            df.at[swing_low_idx, 'BE'] = f"R(Teji) {r_date}\n{swing_low:.2f}"
                            df.at[swing_low_idx, 'Type'] = "bull_light" # Light Green
                            
                            # 2. Mark Atak (The high of the bounce)
                            atak_idx = interim['High'].idxmax()
                            atak_val = df.at[atak_idx, 'High']
                            a_date = df.at[atak_idx, 'Date'].strftime('%d-%b').upper()
                            
                            df.at[atak_idx, 'BU'] = f"ATAK (Top) {a_date}\n{atak_val:.2f}"
                            df.at[atak_idx, 'Type'] = "bear_light" # Light Red
                            
                            # 3. Mark Mandi Start (Today)
                            df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_l:.2f}"
                            df.at[i, 'Type'] = "bear_dark"
                            
                            trend = "Mandi"
                            last_trough = c_l; last_trough_idx = i
                            swing_high = c_h; swing_high_idx = i # Reset for Mandi

        # --- MANDI (DOWNTREND) ---
        elif trend == "Mandi":
            # 1. Continuation (New Low)
            if c_l < last_trough:
                df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_l:.2f}"; df.at[i, 'Type'] = "bear_dark"
                
                last_trough = c_l; last_trough_idx = i
                swing_high = c_h; swing_high_idx = i
                
            else:
                # Update Highest High since trough
                if c_h > swing_high:
                    swing_high = c_h; swing_high_idx = i
                    
                # Check Breakout (Price breaks Swing High)
                if i > swing_high_idx:
                    interim = df.iloc[swing_high_idx+1 : i]
                    if not interim.empty:
                        dip_low = interim['Low'].min()
                        
                        if c_h > swing_high:
                            # BREAKOUT CONFIRMED
                            
                            # 1. Mark Reaction (The high that was broken)
                            r_date = df.at[swing_high_idx, 'Date'].strftime('%d-%b').upper()
                            df.at[swing_high_idx, 'BU'] = f"R(Mandi) {r_date}\n{swing_high:.2f}"
                            df.at[swing_high_idx, 'Type'] = "bear_light" # Light Red
                            
                            # 2. Mark Atak (The low of the dip)
                            atak_idx = interim['Low'].idxmin()
                            atak_val = df.at[atak_idx, 'Low']
                            a_date = df.at[atak_idx, 'Date'].strftime('%d-%b').upper()
                            
                            df.at[atak_idx, 'BE'] = f"ATAK (Bot) {a_date}\n{atak_val:.2f}"
                            df.at[atak_idx, 'Type'] = "bull_light" # Light Green
                            
                            # 3. Mark Teji Start (Today)
                            df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_h:.2f}"
                            df.at[i, 'Type'] = "bull_dark"
                            
                            trend = "Teji"
                            last_peak = c_h; last_peak_idx = i
                            swing_low = c_l; swing_low_idx = i

        # --- NEUTRAL ---
        else:
            if c_h > last_peak:
                trend = "Teji"; df.at[i, 'BU'] = "Start Teji"; df.at[i, 'Type']="bull_dark"
                last_peak=c_h; last_peak_idx=i; swing_low=c_l; swing_low_idx=i
            elif c_l < last_trough:
                trend = "Mandi"; df.at[i, 'BE'] = "Start Mandi"; df.at[i, 'Type']="bear_dark"
                last_trough=c_l; last_trough_idx=i; swing_high=c_h; swing_high_idx=i
                
    # Return active levels
    fin_res = swing_high if trend == "Mandi" else "-"
    fin_sup = swing_low if trend == "Teji" else "-"
    
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
                
                # BU Colors
                if "BU(T)" in bu_txt or "Start Teji" in bu_txt: styles[5] = 'background-color: #228B22; color: white; font-weight: bold; white-space: pre-wrap;' # Dark Green
                elif "R(" in bu_txt: styles[5] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; white-space: pre-wrap;' # Light Red
                elif "ATAK" in bu_txt: styles[5] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; white-space: pre-wrap;' # Light Red
                
                # BE Colors
                if "BE(M)" in be_txt or "Start Mandi" in be_txt: styles[6] = 'background-color: #8B0000; color: white; font-weight: bold; white-space: pre-wrap;' # Dark Red
                elif "R(" in be_txt: styles[6] = 'background-color: #d4edda; color: #155724; font-weight: bold; white-space: pre-wrap;' # Light Green
                elif "ATAK" in be_txt: styles[6] = 'background-color: #d4edda; color: #155724; font-weight: bold; white-space: pre-wrap;' # Light Green
                
                return styles

            st.dataframe(
                disp.style.apply(color_cells, axis=1).format({"Date": lambda t: t.strftime("%d-%b-%Y"), "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"}),
                column_config={"Type": None, "BU (Teji/Resist)": st.column_config.TextColumn(width="medium"), "BE (Mandi/Support)": st.column_config.TextColumn(width="medium")},
                use_container_width=True, height=800
            )
        else: st.error("⚠️ Data Error.")
else: st.info("👈 Click RUN")