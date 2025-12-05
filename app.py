import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="VNS Pro Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (EXCEL GRID LOOK) ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    
    /* Global Font */
    html, body, div, span, applet, object, iframe, h1, h2, h3, h4, h5, h6, p, blockquote, pre, a, abbr, acronym, address, big, cite, code, del, dfn, em, img, ins, kbd, q, s, samp, small, strike, strong, sub, sup, tt, var, b, u, i, center, dl, dt, dd, ol, ul, li, fieldset, form, label, legend, table, caption, tbody, tfoot, thead, tr, th, td, article, aside, canvas, details, embed, figure, figcaption, footer, header, hgroup, menu, nav, output, ruby, section, summary, time, mark, audio, video {
        font-family: 'Arial', sans-serif;
    }

    /* Tabs */
    div[role="radiogroup"] { flex-wrap: wrap; gap: 5px; }
    div[role="radiogroup"] > label { 
        border: 1px solid #ccc; 
        background: #f8f9fa;
        color: #333;
    }

    /* --- THE EXCEL TABLE STYLES --- */
    .excel-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 15px; /* Larger font */
        color: #000;
        margin-top: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .excel-table th {
        background-color: #f2f2f2;
        color: #333;
        font-weight: bold;
        border: 1px solid #999;
        padding: 12px 8px;
        text-align: center;
    }
    
    .excel-table td {
        border: 1px solid #999; /* Darker border like Excel */
        padding: 8px;
        text-align: center;
        vertical-align: middle;
        line-height: 1.4;
    }

    /* Data Stacking */
    .cell-top { font-weight: bold; font-size: 1.1em; color: #000; display: block; }
    .cell-bot { font-size: 1.0em; color: #444; display: block; margin-top: 2px; }

    /* --- VNS SIGNAL COLORS (High Contrast) --- */
    
    /* TEJI: Light Green BG, Black Text */
    .bg-bull { background-color: #90EE90 !important; color: #000 !important; font-weight: bold; }
    
    /* MANDI: Light Red/Salmon BG, Black Text */
    .bg-bear { background-color: #FF9999 !important; color: #000 !important; font-weight: bold; }
    
    /* ATAK: Gold BG, Black Text */
    .bg-atak { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; }
    
    /* REACTION: Light Blue BG, Black Text */
    .bg-info { background-color: #E6F3FF !important; color: #000 !important; font-style: italic; }

</style>
""", unsafe_allow_html=True)

# --- STOCK LIST ---
STOCK_LIST = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "SBIN", "BHARTIARTL", 
    "L&T", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "TATAMOTORS", "MARUTI", "HCLTECH", 
    "SUNPHARMA", "TITAN", "BAJFINANCE", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID", 
    "M&M", "ADANIENT", "ADANIPORTS", "COALINDIA", "WIPRO", "BAJAJFINSV", "NESTLEIND", 
    "JSWSTEEL", "GRASIM", "ONGC", "TATASTEEL", "HDFCLIFE", "SBILIFE", "DRREDDY", 
    "EICHERMOT", "CIPLA", "DIVISLAB", "BPCL", "HINDALCO", "HEROMOTOCO", "APOLLOHOSP", 
    "TATACONSUM", "BRITANNIA", "UPL", "ZOMATO", "PAYTM", "DLF", "INDIGO", "HAL", 
    "BEL", "VBL", "TRENT", "JIOFIN", "ADANIPOWER", "IRFC", "PFC", "RECLTD", "BHEL"
]
STOCK_LIST.sort()

# --- SESSION STATE ---
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.now() - timedelta(days=60) # Default 2M
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now()

def update_dates():
    selection = st.session_state.duration_selector
    now = datetime.now()
    st.session_state.end_date = now
    if selection == "1M": st.session_state.start_date = now - timedelta(days=30)
    elif selection == "2M": st.session_state.start_date = now - timedelta(days=60)
    elif selection == "3M": st.session_state.start_date = now - timedelta(days=90)
    elif selection == "6M": st.session_state.start_date = now - timedelta(days=180)
    elif selection == "1Y": st.session_state.start_date = now - timedelta(days=365)
    elif selection == "YTD": st.session_state.start_date = datetime(now.year, 1, 1)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK") if "KOTAKBANK" in STOCK_LIST else 0)
    st.divider()
    st.subheader("Time Period")
    st.radio("Quick Select:", ["1M", "2M", "3M", "6M", "1Y", "YTD", "Custom"], index=1, horizontal=True, key="duration_selector", on_change=update_dates)
    date_range = st.date_input("Date Range", value=(st.session_state.start_date, st.session_state.end_date), min_value=datetime(2000, 1, 1), max_value=datetime.now())
    if len(date_range) == 2:
        st.session_state.start_date = datetime.combine(date_range[0], datetime.min.time())
        st.session_state.end_date = datetime.combine(date_range[1], datetime.min.time())
    st.divider()
    run_btn = st.button("🚀 Run VNS Analysis", type="primary", use_container_width=True)

# --- FETCH DATA ---
@st.cache_data(ttl=300)
def fetch_nse_data(symbol, start, end):
    try:
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        session = requests.Session(); session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=5)
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        response = session.get(url, timeout=10)
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

# --- VNS LOGIC ---
def analyze_vns(df):
    df['BU_Class'] = "" 
    df['BE_Class'] = ""
    df['BU_Text'] = ""
    df['BE_Text'] = ""
    
    trend = "Neutral"
    last_bu_level = None
    last_be_level = None
    
    # Iterate through data
    for i in range(1, len(df)):
        curr_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        curr_high = curr_row['CH_TRADE_HIGH_PRICE']
        curr_low = curr_row['CH_TRADE_LOW_PRICE']
        prev_high = prev_row['CH_TRADE_HIGH_PRICE']
        prev_low = prev_row['CH_TRADE_LOW_PRICE']
        curr_close = curr_row['CH_CLOSING_PRICE']
        
        low_broken = curr_low < prev_low
        high_broken = curr_high > prev_high
        
        # Format Date for the Signal Text
        date_str = prev_row['Date'].strftime('%d-%b').upper()
        
        # --- 1. ATAK DETECTION ---
        if last_bu_level and (last_bu_level * 0.995 <= curr_high <= last_bu_level * 1.005) and curr_close < last_bu_level:
            df.at[i, 'BU_Text'] = f"ATAK (Top)<br>{curr_high}"
            df.at[i, 'BU_Class'] = "bg-atak"
            
        if last_be_level and (last_be_level * 0.995 <= curr_low <= last_be_level * 1.005) and curr_close > last_be_level:
            df.at[i, 'BE_Text'] = f"ATAK (Bottom)<br>{curr_low}"
            df.at[i, 'BE_Class'] = "bg-atak"

        # --- 2. TREND LOGIC ---
        if trend == "Bullish":
            if low_broken: 
                df.at[i-1, 'BU_Text'] = f"BU(T) {date_str}<br>{prev_high}"
                df.at[i-1, 'BU_Class'] = "bg-bull"
                last_bu_level = prev_high 
            if high_broken: 
                df.at[i-1, 'BE_Text'] = f"R(Teji)<br>{prev_low}"
                df.at[i-1, 'BE_Class'] = "bg-info"
                last_be_level = prev_low 

        elif trend == "Bearish":
            if high_broken: 
                df.at[i-1, 'BE_Text'] = f"BE(M) {date_str}<br>{prev_low}"
                df.at[i-1, 'BE_Class'] = "bg-bear"
                last_be_level = prev_low 
            if low_broken: 
                df.at[i-1, 'BU_Text'] = f"R(Mandi) {date_str}<br>{prev_high}"
                df.at[i-1, 'BU_Class'] = "bg-info"
                last_bu_level = prev_high 

        else: # Neutral
            if high_broken:
                trend = "Bullish"
                df.at[i-1, 'BE_Text'] = f"Start Teji<br>{prev_low}"
                df.at[i-1, 'BE_Class'] = "bg-bull"
            elif low_broken:
                trend = "Bearish"
                df.at[i-1, 'BU_Text'] = f"Start Mandi<br>{prev_high}"
                df.at[i-1, 'BU_Class'] = "bg-bear"
        
        # --- 3. SWITCHING ---
        if trend == "Bearish" and last_bu_level and curr_close > last_bu_level:
             trend = "Bullish"
             df.at[i, 'BU_Text'] = "BREAKOUT (Teji)"
             df.at[i, 'BU_Class'] = "bg-bull"
        if trend == "Bullish" and last_be_level and curr_close < last_be_level:
             trend = "Bearish"
             df.at[i, 'BE_Text'] = "BREAKDOWN (Mandi)"
             df.at[i, 'BE_Class'] = "bg-bear"
        
    return df

# --- RENDER OUTPUT ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner(f"Fetching data for {selected_stock}..."):
        raw_df = fetch_nse_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            analyzed_df = analyze_vns(raw_df)
            
            # --- CONSTRUCT HTML TABLE ---
            table_html = """
            <table class="excel-table">
                <thead>
                    <tr>
                        <th style="width:15%">Date</th>
                        <th style="width:20%">High<br><span style="font-weight:normal; font-size:0.9em">Low</span></th>
                        <th style="width:20%">Open<br><span style="font-weight:normal; font-size:0.9em">Close</span></th>
                        <th style="width:22%">BU (Resistance)</th>
                        <th style="width:22%">BE (Support)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for index, row in analyzed_df.iterrows():
                date_display = row['Date'].strftime('%d-%b-%Y')
                
                # Stacked Numbers
                high_low = f"<span class='cell-top'>{row['CH_TRADE_HIGH_PRICE']:.2f}</span><span class='cell-bot'>{row['CH_TRADE_LOW_PRICE']:.2f}</span>"
                open_close = f"<span class='cell-top'>{row['CH_OPENING_PRICE']:.2f}</span><span class='cell-bot'>{row['CH_CLOSING_PRICE']:.2f}</span>"
                
                # VNS Columns with Colors
                bu_content = row['BU_Text']
                bu_class = row['BU_Class']
                
                be_content = row['BE_Text']
                be_class = row['BE_Class']
                
                table_html += f"""
                <tr>
                    <td>{date_display}</td>
                    <td>{high_low}</td>
                    <td>{open_close}</td>
                    <td class="{bu_class}">{bu_content}</td>
                    <td class="{be_class}">{be_content}</td>
                </tr>
                """
                
            table_html += "</tbody></table>"
            
            # Render HTML safely
            st.markdown(table_html, unsafe_allow_html=True)
            
        else: st.error("⚠️ Could not fetch data.")
else: st.info("👈 Select options and click RUN.")
