# --- IMPROVED FETCH DATA (Bypass NSE Blocking) ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        safe_symbol = urllib.parse.quote(symbol)
        
        # 1. Headers to look exactly like a real Chrome Browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.nseindia.com/get-quotes/equity?symbol=" + safe_symbol,
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        # 2. Create Session & Get Cookies (Crucial Step)
        s = requests.Session()
        s.headers.update(headers)
        
        # Visit Homepage first to set cookies
        homepage = s.get("https://www.nseindia.com", timeout=10)
        
        # 3. Fetch Actual Data
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={safe_symbol}&type=priceVolumeDeliverable&series=ALL"
        r = s.get(url, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            # Handle case where NSE returns {"error": ...} inside 200 OK
            if 'data' not in data: return None
            
            df = pd.DataFrame(data['data'])
            if df.empty: return None
            
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for c in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']: 
                df[c] = df[c].astype(float)
                
            return df.sort_values('Date').reset_index(drop=True)
            
    except Exception as e:
        # st.error(f"Debug Error: {e}") # Uncomment to see error details
        return None
    return None
