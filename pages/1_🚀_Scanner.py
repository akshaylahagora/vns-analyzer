
import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="F&O Scanner", page_icon="🔭", layout="wide")

st.title("🔭 F&O VNS Scanner (> ₹1000)")
st.markdown("Scans major F&O stocks for VNS Trends based on **Last 1 Month** data.")

# --- CSS FOR STATUS ---
st.markdown("""
<style>
    .scan-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ddd; }
    .bull-box { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
    .bear-box { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
    .neutral-box { background-color: #fff3cd; border-color: #ffeeba; color: #856404; }
    .metric-label { font-size: 0.8em; color: #666; }
    .metric-val { font-weight: bold; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# --- LIST OF F&O STOCKS (Sample of High Value Stocks) ---
# In a real production app, you might fetch this list dynamically.
FNO_STOCKS = [
    "RELIANCE", "HDFCBANK", "INFY", "TCS", "KOTAKBANK", "LT", "AXISBANK", "SBIN", 
    "BAJFINANCE", "TITAN", "ULTRACEMCO", "MARUTI", "ASIANPAINT", "HINDUNILVR", "M&M", 
    "ADANIENT", "GRASIM", "BAJAJFINSV", "NESTLEIND", "EICHERMOT", "DRREDDY", "DIVISLAB", 
    "APOLLOHOSP", "BRITANNIA", "TRENT", "HAL", "BEL", "SIEMENS", "INDIGO", "TATASTEEL", 
    "JIOFIN", "COALINDIA", "HCLTECH", "SUNPHARMA", "ADANIPORTS", "WIPRO"
]

# --- HELPER FUNCTIONS ---

@st.cache_data(ttl=600)
def fetch_stock_data(symbol):
    """Fetches last 30 days of data for a single stock."""
    try:
        end = datetime.now()
        start = end - timedelta(days=35) # Fetch 35 to ensure we have 30 trading days
        
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        session = requests.Session()
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=3)
        
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        response = session.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            df = pd.DataFrame(data)
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for col in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']:
                df[col] = df[col].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except:
        return None
    return None

def calculate_trend(df):
    """Runs VNS logic on the dataframe and returns the FINAL status."""
    trend = "Neutral"
    last_bu, last_be = None, None
    
    # We need to process the whole month to find the current state
    for i in range(len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1] if i > 0 else None
        
        if prev is not None:
            if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']:
                last_bu = prev['CH_TRADE_HIGH_PRICE']
            if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']:
                last_be = prev['CH_TRADE_LOW_PRICE']
            
            # State Machine
            if last_bu and row['CH_CLOSING_PRICE'] > last_bu: trend = "Bullish"
            elif last_be and row['CH_CLOSING_PRICE'] < last_be: trend = "Bearish"
            # (Note: Standard VNS retains previous trend until reversed, 
            # so we don't need extensive 'else' logic for the final snapshot, 
            # just the reversal triggers)

    return trend, last_bu, last_be, df.iloc[-1]['CH_CLOSING_PRICE']

# --- MAIN SCANNER UI ---

if st.button("🚀 Start Scan (This takes time)"):
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Scan Loop
    for i, stock in enumerate(FNO_STOCKS):
        status_text.text(f"Scanning {stock}...")
        
        df = fetch_stock_data(stock)
        
        if df is not None:
            # Check price > 1000
            last_price = df.iloc[-1]['CH_CLOSING_PRICE']
            
            if last_price > 1000:
                trend, bu, be, close = calculate_trend(df)
                results.append({
                    "Symbol": stock,
                    "Trend": trend,
                    "Close": close,
                    "BU": bu,
                    "BE": be,
                    "Data": df # Store full DF for the expander
                })
        
        # Update progress
        progress_bar.progress((i + 1) / len(FNO_STOCKS))
        time.sleep(0.1) # Small delay to be nice to NSE API

    progress_bar.empty()
    status_text.empty()
    
    # --- DISPLAY RESULTS ---
    
    # Separate lists
    bulls = [r for r in results if r['Trend'] == "Bullish"]
    bears = [r for r in results if r['Trend'] == "Bearish"]
    neutral = [r for r in results if r['Trend'] == "Neutral"]

    col1, col2, col3 = st.columns(3)

    # 🟢 BULLISH COLUMN
    with col1:
        st.header(f"🟢 Bullish ({len(bulls)})")
        for stock in bulls:
            with st.expander(f"{stock['Symbol']} (₹{stock['Close']:.2f})"):
                st.markdown(f"""
                <div class="scan-box bull-box">
                    <b>Trend: TEJI</b><br>
                    Support (BE): {stock['BE']}<br>
                    Resistance (BU): {stock['BU']}
                </div>
                """, unsafe_allow_html=True)
                st.dataframe(stock['Data'].tail(5)[['Date', 'CH_CLOSING_PRICE', 'CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE']])

    # 🔴 BEARISH COLUMN
    with col2:
        st.header(f"🔴 Bearish ({len(bears)})")
        for stock in bears:
            with st.expander(f"{stock['Symbol']} (₹{stock['Close']:.2f})"):
                st.markdown(f"""
                <div class="scan-box bear-box">
                    <b>Trend: MANDI</b><br>
                    Support (BE): {stock['BE']}<br>
                    Resistance (BU): {stock['BU']}
                </div>
                """, unsafe_allow_html=True)
                st.dataframe(stock['Data'].tail(5)[['Date', 'CH_CLOSING_PRICE', 'CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE']])

    # 🟡 NEUTRAL COLUMN
    with col3:
        st.header(f"🟡 Neutral ({len(neutral)})")
        for stock in neutral:
            with st.expander(f"{stock['Symbol']} (₹{stock['Close']:.2f})"):
                st.write("No clear breakout/breakdown in last 30 days.")
                st.dataframe(stock['Data'].tail(5))

else:
    st.info("Click 'Start Scan' to analyze F&O stocks > 1000. Please wait 30-60 seconds for the scan to complete.")
