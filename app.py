import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.parse
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    
    /* Metrics */
    div[data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #444444 !important; font-weight: 600 !important; }
    .metric-container { background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 15px; text-align: center; }

    /* Trend Badges */
    .trend-card { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.2rem; border: 2px solid transparent; }
    .trend-bull { background-color: #d1e7dd; color: #0f5132; border-color: #badbcc; }
    .trend-bear { background-color: #f8d7da; color: #842029; border-color: #f5c2c7; }
    .trend-neutral { background-color: #e2e3e5; color: #41464b; border-color: #d3d6d8; }

    /* Table */
    .stDataFrame { font-size: 1.1rem; }
    .stDataFrame td { vertical-align: middle !important; white-space: pre-wrap !important; }
    .stSidebar label { color: #333 !important; }
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
        req_start = start - timedelta(days=60) # Buffer
        df = yf.download(yf_symbol, start=req_start, end=end + timedelta(days=1), progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- VNS LOGIC (BOUNCE DETECTION) ---
def analyze_vns(df):
    df['BU'], df['BE'], df['Type'] = "", "", ""
    trend = "Neutral"
    
    last_peak = df.iloc[0]['High']
    last_trough = df.iloc[0]['Low']
    
    # Track "Active Swing" for Reversal Logic
    # For Teji: We track the lowest low after the peak (Potential Support)
    # For Mandi: We track the highest high after the trough (Potential Resist)
    
    swing_min = df.iloc[0]['Low']
    swing_min_idx = 0
    
    swing_max = df.iloc[0]['High']
    swing_max_idx = 0
    
    # State tracking
    last_peak_idx = 0
    last_trough_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        c_h, c_l = curr['High'], curr['Low']
        d_str = curr['Date'].strftime('%d-%b').upper()
        
        # --- TEJI (UPTREND) ---
        if trend == "Teji":
            if c_h > last_peak:
                # Continuation (New High)
                df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_h:.2f}"; df.at[i, 'Type'] = "bull_dark"
                
                last_peak = c_h; last_peak_idx = i
                swing_min = c_l; swing_min_idx = i # Reset swing low
            
            else:
                # Price is below peak. Track the lowest point.
                if c_l < swing_min:
                    swing_min = c_l; swing_min_idx = i
                
                # REVERSAL CHECK
                # If current low < swing_min... wait, that just updates swing_min.
                # A Reversal (Breakdown) happens when price drops below a *CONFIRMED* Reaction Low.
                # A Reaction Low is confirmed when price bounces up from it.
                
                # Check for "Bounce then Break"
                # Scan data between the 'swing_min' and 'current i'
                # If we find a High that is higher than current close, and now we are breaking the low...
                
                # Simplified Logic for "Look Back":
                # If we are dropping, check if we established a low previously that we are now breaking.
                # Actually, the user says: 20th High, 21st Low, 23rd Lower High, 24th Break.
                # On 24th, we break 21st Low.
                
                # So we iterate back to find the "Reaction Low"
                # The Reaction Low is the global min between Last Peak and (Current - 1)
                
                interim_df = df.iloc[last_peak_idx+1 : i] # Data since peak excluding today
                if not interim_df.empty:
                    # Find the reaction low in the interim period
                    reaction_idx = interim_df['Low'].idxmin()
                    reaction_val = df.at[reaction_idx, 'Low']
                    
                    # If today breaks that reaction low
                    if c_l < reaction_val:
                        # VALIDATE BOUNCE: Was there a bounce after reaction?
                        # Check highs between Reaction Index and Today
                        bounce_df = df.iloc[reaction_idx+1 : i]
                        if not bounce_df.empty:
                            # BOUNCE CONFIRMED -> BREAKDOWN
                            atak_idx = bounce_df['High'].idxmax()
                            atak_val = df.at[atak_idx, 'High']
                            
                            # 1. Mark Reaction (Past) - Light Green
                            r_date = df.at[reaction_idx, 'Date'].strftime('%d-%b').upper()
                            df.at[reaction_idx, 'BE'] = f"R(Teji) {r_date}\n{reaction_val:.2f}"
                            df.at[reaction_idx, 'Type'] = "bull_light"
                            
                            # 2. Mark Atak (Past) - Light Red
                            a_date = df.at[atak_idx, 'Date'].strftime('%d-%b').upper()
                            df.at[atak_idx, 'BU'] = f"ATAK (Top) {a_date}\n{atak_val:.2f}"
                            df.at[atak_idx, 'Type'] = "bear_light"
                            
                            # 3. Mark Mandi (Today) - Dark Red
                            df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_l:.2f}"
                            df.at[i, 'Type'] = "bear_dark"
                            
                            trend = "Mandi"
                            last_trough = c_l; last_trough_idx = i
                            swing_max = c_h; swing_max_idx = i

        # --- MANDI (DOWNTREND) ---
        elif trend == "Mandi":
            if c_l < last_trough:
                # Continuation (New Low)
                df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_l:.2f}"; df.at[i, 'Type'] = "bear_dark"
                
                last_trough = c_l; last_trough_idx = i
                swing_max = c_h; swing_max_idx = i # Reset swing high
                
            else:
                # Reversal Check: Breakout above Reaction High
                interim_df = df.iloc[last_trough_idx+1 : i] # Data since trough
                if not interim_df.empty:
                    reaction_idx = interim_df['High'].idxmax()
                    reaction_val = df.at[reaction_idx, 'High']
                    
                    if c_h > reaction_val:
                        # Check for Dip (Bounce)
                        dip_df = df.iloc[reaction_idx+1 : i]
                        if not dip_df.empty:
                            # BREAKOUT CONFIRMED
                            atak_idx = dip_df['Low'].idxmin()
                            atak_val = df.at[atak_idx, 'Low']
                            
                            # 1. Mark Reaction (Past) - Light Red
                            r_date = df.at[reaction_idx, 'Date'].strftime('%d-%b').upper()
                            df.at[reaction_idx, 'BU'] = f"R(Mandi) {r_date}\n{reaction_val:.2f}"
                            df.at[reaction_idx, 'Type'] = "bear_light"
                            
                            # 2. Mark Atak (Past) - Light Green
                            a_date = df.at[atak_idx, 'Date'].strftime('%d-%b').upper()
                            df.at[atak_idx, 'BE'] = f"ATAK (Bot) {a_date}\n{atak_val:.2f}"
                            df.at[atak_idx, 'Type'] = "bull_light"
                            
                            # 3. Mark Teji (Today) - Dark Green
                            df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_h:.2f}"
                            df.at[i, 'Type'] = "bull_dark"
                            
                            trend = "Teji"
                            last_peak = c_h; last_peak_idx = i
                            swing_min = c_l; swing_min_idx = i

        # --- NEUTRAL ---
        else:
            if c_h > last_peak: trend="Teji"; df.at[i, 'BU']="Start Teji"; df.at[i, 'Type']="bull_dark"; last_peak=c_h; last_peak_idx=i
            elif c_l < last_trough: trend="Mandi"; df.at[i, 'BE']="Start Mandi"; df.at[i, 'Type']="bear_dark"; last_trough=c_l; last_trough_idx=i

    # Return active levels based on current state
    if trend == "Teji": 
        # Active support is the lowest point since peak
        sw = df.iloc[last_peak_idx:len(df)]; act_sup = sw['Low'].min(); act_res = "-"
    else: 
        sw = df.iloc[last_trough_idx:len(df)]; act_res = sw['High'].max(); act_sup = "-"

    return df, trend, act_res, act_sup

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
                if "BU(T)" in bu_txt or "Start Teji" in bu_txt: styles[5] = 'background-color: #28a745; color: white; font-weight: bold; white-space: pre-wrap;' # Dark Green
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
