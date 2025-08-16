import yfinance as yf
import streamlit as st

def fetch_stock_price(ticker):
    """
    Fetch the current stock price for a given ticker symbol.
    """
    stock = yf.Ticker(ticker)
    stock_info = stock.history(period="1d")
    if not stock_info.empty:
        return stock_info['Close'].iloc[-1]
    else:
        return None

def fetch_company_info(ticker):
    """
    Fetch the full company name, market cap, and total shares for a given ticker symbol.
    """
    stock = yf.Ticker(ticker)
    info = stock.info
    name = info.get("longName", None)
    market_cap = info.get("marketCap", None)
    shares = info.get("sharesOutstanding", None)
    return name, market_cap, shares

st.set_page_config(page_title="Simple Stock Price Checker", page_icon="💹")
st.title("💹 Simple Stock Price Checker")
st.subheader("Enter a stock ticker symbol to get the latest closing price.")

# Input and button on the same row, left aligned
input_col, btn_col = st.columns([4, 1])
with input_col:
    ticker_symbol = st.text_input(
        label="",
        value="",
        placeholder="e.g. AAPL, MSFT, TSLA"
    )
with btn_col:
    fetch_btn = st.button("Fetch Stock Price")

if fetch_btn and ticker_symbol:
    ticker_clean = ticker_symbol.strip().upper()
    price = fetch_stock_price(ticker_clean)
    company_name, market_cap, shares = fetch_company_info(ticker_clean)
    if price is not None and company_name:
        market_cap_str = f"${market_cap:,.0f}" if market_cap is not None else "N/A"
        shares_str = f"{shares:,}" if shares is not None else "N/A"
        st.success(f"Company Name: **{company_name}**")
        st.success(f"Stock Price: **${price:.2f}**")
        st.success(f"Market Cap: **{market_cap_str}**")
        st.success(f"Total Shares Outstanding: **{shares_str}**")
    elif price is not None:
        st.success(f"Stock Price for **{ticker_clean}**: **${price:.2f}**")
        st.info("(Company name, market cap, or shares outstanding not found)")
    else:
        st.error(f"Could not fetch the stock price for **{ticker_clean}**. Please check the symbol and try again.")

