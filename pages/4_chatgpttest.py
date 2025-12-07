import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import date, timedelta

# -------------------------
# Helpers: Fetch F&O list
# -------------------------

@st.cache_data(show_spinner=True)
def fetch_fo_stock_list() -> pd.DataFrame:
    """
    Fetch NSE F&O stock list by scraping Dhan's NSE F&O lot-size page.
    Returns a DataFrame with at least a 'Symbol' column.
    """
    url = "https://dhan.co/nse-fno-lot-size/"
    try:
        tables = pd.read_html(url)
        # Usually the first table is the full list, containing 'Symbol'
        df = tables[0]
        # Try to normalize symbol column name
        possible_cols = [c for c in df.columns if "symbol" in str(c).lower()]
        if possible_cols:
            df.rename(columns={possible_cols[0]: "Symbol"}, inplace=True)
        else:
            # Fallback: assume first col is symbol
            df.rename(columns={df.columns[0]: "Symbol"}, inplace=True)

        # Clean symbol (remove spaces, etc.)
        df["Symbol"] = df["Symbol"].astype(str).str.strip()

        # Remove index derivatives like NIFTY, BANKNIFTY etc if you want only stocks
        index_like = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"}
        df = df[~df["Symbol"].isin(index_like)]

        df = df.drop_duplicates(subset=["Symbol"]).reset_index(drop=True)
        return df[["Symbol"]]
    except Exception as e:
        # Fallback: minimal static list
        fallback_symbols = ["RELIANCE", "HDFCBANK", "TCS", "INFY", "ICICIBANK"]
        return pd.DataFrame({"Symbol": fallback_symbols})


# -------------------------
# Helpers: Fetch OHLC data
# -------------------------

def fetch_yahoo_ohlc(symbol: str, start: date, end: date) -> pd.DataFrame:
    """
    Fetch daily OHLC data from Yahoo Finance for an NSE stock.
    symbol: NSE symbol without suffix (e.g., 'KOTAKBANK').
    """
    ticker = symbol.upper().strip() + ".NS"
    data = yf.download(ticker, start=start, end=end + timedelta(days=1))
    if data.empty:
        return pd.DataFrame()

    data = data.reset_index()
    data.rename(columns={"Date": "Date", "High": "High", "Low": "Low"}, inplace=True)
    return data[["Date", "High", "Low"]]


# -------------------------
# VNS Logic on High/Low
# -------------------------

def compute_vns_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply VNS Teji/Mandi/Atak/Reaction-like swing logic based ONLY on High & Low.
    df must have columns: Date, High, Low (daily data).
    Returns a DataFrame of signals with columns:
    ['Date', 'Price', 'Type', 'Info'].
    """
    if df.empty or len(df) < 2:
        return pd.DataFrame(columns=["Date", "Price", "Type", "Info"])

    df = df.sort_values("Date").reset_index(drop=True)

    last_teji_high = None   # last Teji (BU) pivot high
    last_mandi_low = None   # last Mandi (BE) pivot low
    last_major_event = None # "Teji" or "Mandi" (for breakout/breakdown sequences)

    signals = []

    # First pass: detect Teji/Mandi/Atak (double top/bottom-like)
    for i in range(1, len(df)):
        y = df.iloc[i - 1]
        t = df.iloc[i]

        y_high = float(y["High"])
        y_low = float(y["Low"])
        t_high = float(t["High"])
        t_low = float(t["Low"])

        # 1) Today's low breaks yesterday's low → yesterday's high becomes pivot
        if t_low < y_low:
            pivot_price = y_high
            pivot_date = y["Date"]

            if last_teji_high is None:
                signal_type = "Teji (BU)"
                info = "First Teji: low break after this high."
                last_teji_high = pivot_price
                last_major_event = "Teji"
            else:
                if pivot_price > last_teji_high:
                    signal_type = "Teji (BU)"
                    info = "New higher Teji high."
                    last_teji_high = pivot_price
                    last_major_event = "Teji"
                elif pivot_price < last_teji_high:
                    signal_type = "Atak (Double Top)"
                    info = f"Lower high vs previous Teji {last_teji_high:.2f}."
                else:
                    signal_type = "Reaction"
                    info = "Low break, but equal to previous Teji high."

            signals.append(
                {
                    "Date": pivot_date,
                    "Price": pivot_price,
                    "Type": signal_type,
                    "Info": info,
                }
            )

        # 2) Today's high breaks yesterday's high → yesterday's low becomes pivot
        if t_high > y_high:
            pivot_price = y_low
            pivot_date = y["Date"]

            if last_mandi_low is None:
                signal_type = "Mandi (BE)"
                info = "First Mandi: high break after this low."
                last_mandi_low = pivot_price
                last_major_event = "Mandi"
            else:
                if pivot_price < last_mandi_low:
                    signal_type = "Mandi (BE)"
                    info = "New lower Mandi low."
                    last_mandi_low = pivot_price
                    last_major_event = "Mandi"
                elif pivot_price > last_mandi_low:
                    signal_type = "Atak (Double Bottom)"
                    info = f"Higher low vs previous Mandi {last_mandi_low:.2f}."
                else:
                    signal_type = "Reaction"
                    info = "High break, but equal to previous Mandi low."

            signals.append(
                {
                    "Date": pivot_date,
                    "Price": pivot_price,
                    "Type": signal_type,
                    "Info": info,
                }
            )

    # Convert to DataFrame for second-pass processing (breakouts/breakdowns)
    sig_df = pd.DataFrame(signals)
    if sig_df.empty:
        return sig_df

    # Second pass: detect Breakout / Breakdown based on Teji–Mandi–Teji or
    # Mandi–Teji–Mandi type sequences.
    # We work on a copy sorted by date.
    sig_df = sig_df.sort_values("Date").reset_index(drop=True)

    extra_rows = []

    # Track last Teji and last Mandi indices
    last_teji_idx = None
    last_mandi_idx = None

    for i, row in sig_df.iterrows():
        stype = str(row["Type"])

        if stype.startswith("Teji"):
            last_teji_idx = i
        if stype.startswith("Mandi"):
            last_mandi_idx = i

        # Look for breakout: Teji then Mandi then price crosses Teji level
        # We'll use the underlying price data to check.
        if last_teji_idx is not None and last_mandi_idx is not None:
            # If last Teji is before last Mandi, then we can watch for a breakout above that Teji
            if sig_df.loc[last_teji_idx, "Date"] < sig_df.loc[last_mandi_idx, "Date"]:
                teji_price = sig_df.loc[last_teji_idx, "Price"]
                mandi_date = sig_df.loc[last_mandi_idx, "Date"]

                # Check if after Mandi date, any day's High >= teji_price
                post = df[df["Date"] > mandi_date]
                crossed = post[post["High"] >= teji_price]
                if not crossed.empty:
                    brk_row = crossed.iloc[0]
                    extra_rows.append(
                        {
                            "Date": brk_row["Date"],
                            "Price": teji_price,
                            "Type": "Breakout",
                            "Info": f"Price High crossed Teji level {teji_price:.2f} after Mandi.",
                        }
                    )
                    # Reset so we don't keep adding multiple breakouts for the same pair
                    last_teji_idx = None
                    last_mandi_idx = None

            # Look for breakdown: Mandi then Teji then price breaks below Mandi level
            elif sig_df.loc[last_mandi_idx, "Date"] < sig_df.loc[last_teji_idx, "Date"]:
                mandi_price = sig_df.loc[last_mandi_idx, "Price"]
                teji_date = sig_df.loc[last_teji_idx, "Date"]

                post = df[df["Date"] > teji_date]
                crossed = post[post["Low"] <= mandi_price]
                if not crossed.empty:
                    brk_row = crossed.iloc[0]
                    extra_rows.append(
                        {
                            "Date": brk_row["Date"],
                            "Price": mandi_price,
                            "Type": "Breakdown",
                            "Info": f"Price Low broke Mandi level {mandi_price:.2f} after Teji.",
                        }
                    )
                    last_teji_idx = None
                    last_mandi_idx = None

    if extra_rows:
        sig_df = pd.concat([sig_df, pd.DataFrame(extra_rows)], ignore_index=True)
        sig_df = sig_df.sort_values("Date").reset_index(drop=True)

    return sig_df


# -------------------------
# Streamlit UI
# -------------------------

st.set_page_config(page_title="VNS Theory Scanner (High/Low Only)", layout="wide")

st.title("📈 VNS Theory Scanner (High & Low Based)")
st.write("Fetch F&O stocks from NSE (via Dhan), get Yahoo data, and mark Teji / Mandi / Atak / Breakout / Breakdown using only High & Low.")

# Sidebar: pick stock, duration
with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("1️⃣ Select F&O Stock")
    fo_df = fetch_fo_stock_list()
    symbol_list = fo_df["Symbol"].tolist()
    selected_symbol = st.selectbox("F&O Stock Symbol", symbol_list, index=0)

    st.subheader("2️⃣ Select Duration")
    today = date.today()

    duration_choice = st.radio(
        "Time Range",
        ["1 week", "1 month", "2 months", "3 months", "Custom"],
        index=1,
    )

    if duration_choice == "1 week":
        start_date = today - timedelta(days=7)
        end_date = today
    elif duration_choice == "1 month":
        start_date = today - timedelta(days=30)
        end_date = today
    elif duration_choice == "2 months":
        start_date = today - timedelta(days=60)
        end_date = today
    elif duration_choice == "3 months":
        start_date = today - timedelta(days=90)
        end_date = today
    else:
        # Custom date range
        custom_range = st.date_input(
            "Custom Date Range",
            value=(today - timedelta(days=90), today),
        )
        if isinstance(custom_range, tuple) or isinstance(custom_range, list):
            start_date, end_date = custom_range
        else:
            # If single date is chosen accidentally, use it as end; start 60 days earlier
            end_date = custom_range
            start_date = end_date - timedelta(days=60)

    st.markdown("---")
    run_button = st.button("🚀 Run VNS Scan")


# Main panel
if run_button:
    st.subheader(f"📊 Yahoo Price Data: {selected_symbol} ({start_date} → {end_date})")

    data = fetch_yahoo_ohlc(selected_symbol, start=start_date, end=end_date)

    if data.empty:
        st.error("No data returned from Yahoo Finance. Check symbol or date range.")
    else:
        st.write("Raw high/low data used for VNS logic:")
        st.dataframe(data, use_container_width=True)

        st.subheader("🧠 VNS Signals (High/Low Only)")
        sig_df = compute_vns_signals(data)

        if sig_df.empty:
            st.warning("No VNS signals detected in the selected period.")
        else:
            st.dataframe(sig_df, use_container_width=True)

else:
    st.info("Select stock & duration in the sidebar, then click **Run VNS Scan**.")
