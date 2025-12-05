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

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    
    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Arial, sans-serif;
    }

    /* Tabs */
    div[role="radiogroup"] { flex-wrap: wrap; gap: 5px; }
    div[role="radiogroup"] label { 
        border: 1px solid #ddd; 
        background: #f8f9fa;
        padding: 5px 15px;
        border-radius: 4px;
    }

    /* TABLE STYLING (The Excel Look) */
    .vns-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        border: 1px solid #ccc;
    }
    .vns-table th {
        background-color: #2c3e50;
        color: white;
        padding: 10px;
        text-align: center;
        border: 1px solid #ccc;
    }
    .vns-table td {
        padding: 8px;
        border: 1px solid #ccc;
        text-align: center;
        vertical-align: middle;
    }
    
    /* Number Stacking */
    .top-val { font-weight: bold; color: #000; font-size: 1.1em; }
    .bot-val { color: #555; font-size: 0.9em; margin-top: 2px; }
    
    /* VNS Colors (Excel Standard) */
    .bg-bull { background-color: #C6EFCE; color: #006100; font-weight: bold; } /* Green */
    .bg-bear { background-color: #FFC7CE; color: #9C0006; font-weight: bold; } /* Red */
    .bg-atak { background-color: #FFEB9C; color: #9C6500; font-weight: bold; } /* Yellow */
    .bg-info { background-color: #BDD7EE; color: #000000; font-style: italic; } /* Blue */
    
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
    df['BU_Class'] = "" # To store CSS class for color
    df['BE_Class'] = ""
    df['BU_Text'] = ""  # To store Display Text
    df['BE_Text'] = ""
    
    trend = "Neutral"
    last_bu_level = None
    last_be_level = None
    
    for i in range(1, len(df)):
        curr_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        curr_high, curr_low = curr_row['CH_TRADE_HIGH_PRICE'], curr_row['CH_TRADE_LOW_PRICE']
        prev_high, prev_low = prev_row['CH_TRADE_HIGH_PRICE'], prev_row['CH_TRADE_LOW_PRICE']
        curr_close = curr_row['CH_CLOSING_PRICE']
        
        low_broken = curr_low < prev_low
        high_broken = curr_high > prev_high
        date_str = prev_row['Date'].strftime('%d-%b').upper()
        
        # 1. ATAK CHECK
        if last_bu_level and (last_bu_level * 0.995 <= curr_high <= last_bu_level * 1.005) and curr_close < last_bu_level:
            df.at[i, 'BU_Text'] = f"ATAK (Top)\n{curr_high}"
            df.at[i, 'BU_Class'] = "bg-atak"
            
        if last_be_level and (last_be_level * 0.995 <= curr_low <= last_be_level * 1.005) and curr_close > last_be_level:
            df.at[i, 'BE_Text'] = f"ATAK (Bottom)\n{curr_low}"
            df.at[i, 'BE_Class'] = "bg-atak"

        # 2. TREND LOGIC
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
        
        # 3. SWITCHING
        if trend == "Bearish" and last_bu_level and curr_close > last_bu_level:
             trend = "Bullish"
             df.at[i, 'BU_Text'] = "BREAKOUT (Teji)"
             df.at[i, 'BU_Class'] = "bg-bull"
        if trend == "Bullish" and last_be_level and curr_close < last_be_level:
             trend = "Bearish"
             df.at[i, 'BE_Text'] = "BREAKDOWN (Mandi)"
             df.at[i, 'BE_Class'] = "bg-bear"
        
    return df

# --- OUTPUT ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner(f"Fetching data for {selected_stock}..."):
        raw_df = fetch_nse_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            analyzed_df = analyze_vns(raw_df)
            
            # --- GENERATE HTML TABLE (For Perfect Styling) ---
            html = """
            <table class="vns-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>High<br>Low</th>
                        <th>Open<br>Close</th>
                        <th>BU (Resistance)</th>
                        <th>BE (Support)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for index, row in analyzed_df.iterrows():
                date_str = row['Date'].strftime('%d-%b-%Y')
                
                # Stacked Values
                hl_cell = f"<div class='top-val'>{row['CH_TRADE_HIGH_PRICE']:.2f}</div><div class='bot-val'>{row['CH_TRADE_LOW_PRICE']:.2f}</div>"
                oc_cell = f"<div class='top-val'>{row['CH_OPENING_PRICE']:.2f}</div><div class='bot-val'>{row['CH_CLOSING_PRICE']:.2f}</div>"
                
                # BU Cell
                bu_class = row['BU_Class']
                bu_text = row['BU_Text'] if row['BU_Text'] else ""
                
                # BE Cell
                be_class = row['BE_Class']
                be_text = row['BE_Text'] if row['BE_Text'] else ""
                
                html += f"""
                <tr>
                    <td>{date_str}</td>
                    <td>{hl_cell}</td>
                    <td>{oc_cell}</td>
                    <td class="{bu_class}">{bu_text}</td>
                    <td class="{be_class}">{be_text}</td>
                </tr>
                """
                
            html += "</tbody></table>"
            
            # Render HTML
            st.markdown(html, unsafe_allow_html=True)
            
        else: st.error("⚠️ Could not fetch data.")
else: st.info("👈 Select options and click RUN.")
