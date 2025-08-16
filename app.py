import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import numpy as np
from plotly.subplots import make_subplots
import re
from io import BytesIO

# Try to import web scraping dependencies, with fallback
try:
    import requests
    from bs4 import BeautifulSoup
    import urllib.parse
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    print("Web scraping dependencies not available")

st.set_page_config(page_title="Advanced Stock Analyzer", page_icon="📈", layout="wide")

st.title("📈 Advanced Stock Data Analyzer")
st.markdown("---")

def validate_ticker(ticker):
    """Validate ticker format"""
    if not ticker or len(ticker) > 10 or not re.match(r'^[A-Z0-9.-]+$', ticker):
        return False
    return True

def calculate_rsi(prices, window=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram


def fetch_breaking_news(ticker, company_name=""):
    """Fetch breaking news from multiple reliable sources"""
    news_list = []
    
    # Only try web scraping if dependencies are available
    if not WEB_SCRAPING_AVAILABLE:
        print("Web scraping not available, skipping breaking news")
        return news_list
    
    # 1. Try Google Finance RSS
    try:
        google_rss = f"https://news.google.com/rss/search?q={ticker}+stock+OR+{company_name.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(google_rss, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:8]
            
            for item in items:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                description = item.find('description')
                source = item.find('source')
                
                if title and link:
                    try:
                        timestamp = pd.to_datetime(pub_date.text).timestamp() if pub_date else pd.Timestamp.now().timestamp()
                    except:
                        timestamp = pd.Timestamp.now().timestamp()
                    
                    publisher = source.text if source else 'Google News'
                    summary = description.text if description else f"Latest news about {ticker} from reliable financial sources."
                    
                    news_list.append({
                        'title': title.text.strip(),
                        'link': link.text.strip(),
                        'summary': summary.strip(),
                        'publisher': publisher,
                        'providerPublishTime': timestamp
                    })
    except Exception as e:
        print(f"Google News RSS error: {e}")
    
    return news_list


def filter_valid_news(news_list):
    """Filter out empty or invalid news articles"""
    valid_news = []
    for article in news_list:
        # Check if article has essential content
        title = article.get('title', '').strip()
        link = article.get('link', '').strip()
        
        # Skip articles with missing or placeholder content
        if (title and 
            title != 'No Title' and 
            title != 'NO TITLE' and
            link and 
            link != 'No Link' and 
            link != 'NO LINK' and
            not title.startswith('http')):  # Skip malformed titles that are actually URLs
            valid_news.append(article)
    
    return valid_news

def fetch_stock_data(ticker, start_date, end_date):
    try:
        # Validate ticker
        if not validate_ticker(ticker):
            st.error(f"Invalid ticker format: '{ticker}'. Please use valid stock symbols (e.g., AAPL, GOOGL).")
            return None, None, None
        
        # Get stock data and company info
        stock = yf.Ticker(ticker)
        stock_data = stock.history(start=start_date, end=end_date)
        
        if stock_data.empty:
            st.error(f"No data found for ticker '{ticker}'. Please check the symbol and try again.")
            return None, None, None
        
        # Get company info
        try:
            info = stock.info
        except:
            info = {}
        
        company_name = info.get('longName', ticker)
        
        # Step 1: Try yfinance news
        yf_news = []
        try:
            yf_news = stock.news[:10]
            print(f"YFinance news count: {len(yf_news)}")
        except Exception as e:
            print(f"YFinance news error: {e}")
        
        # Step 2: Try breaking news from Google and other reliable sources
        breaking_news = fetch_breaking_news(ticker, company_name)
        print(f"Breaking news count: {len(breaking_news)}")
        
        # Step 3: Combine all real news
        all_real_news = yf_news + breaking_news
        
        # Step 4: Filter out empty/invalid articles and only use real news
        if all_real_news:
            # Filter out empty articles first
            filtered_news = filter_valid_news(all_real_news)
            if filtered_news:
                # Sort filtered news by date and limit to 15 most recent
                filtered_news.sort(key=lambda x: x.get('providerPublishTime', 0), reverse=True)
                all_news = filtered_news[:15]
            else:
                print("No valid news articles after filtering")
                all_news = []
        else:
            print("No real news found for ticker")
            all_news = []
        
        print(f"Final news count: {len(all_news)}")
        
        # Debug: Print first news item if available
        if all_news:
            print(f"First news item: {all_news[0].get('title', 'No title')}")
        else:
            print("No news items found - this should not happen!")
        
        # Flatten MultiIndex columns if they exist
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_data.columns = stock_data.columns.get_level_values(0)
        
        return stock_data, info, all_news
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, None, None

# Input controls
col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

with col1:
    ticker = st.text_input("Enter Stock Ticker Symbol", value="AAPL", placeholder="e.g., AAPL, GOOGL, TSLA").strip().upper()

with col2:
    date_range = st.date_input(
        "Select Date Range",
        value=(date(2020, 1, 1), date(2023, 1, 1)),
        min_value=date(2000, 1, 1),
        max_value=date.today()
    )

with col3:
    chart_type = st.selectbox("Chart Type", ["Line", "Candlestick"], index=0)

with col4:
    show_ma = st.checkbox("Show Moving Averages", value=False)

# Technical indicators section
st.markdown("### Technical Analysis Options")
col_tech1, col_tech2, col_tech3 = st.columns(3)
with col_tech1:
    show_rsi = st.checkbox("Show RSI", value=False)
with col_tech2:
    show_macd = st.checkbox("Show MACD", value=False)
with col_tech3:
    compare_spy = st.checkbox("Compare with S&P 500", value=False)

fetch_button = st.button("📊 Fetch Data", type="primary")

if fetch_button and ticker:
    if len(date_range) == 2:
        start_date, end_date = date_range
        
        with st.spinner(f"Fetching data for {ticker}..."):
            data, info, news = fetch_stock_data(ticker, start_date, end_date)
            
            # Fetch S&P 500 data for comparison if requested
            spy_data = None
            if compare_spy:
                spy_data, _, _ = fetch_stock_data('SPY', start_date, end_date)
        
        if data is not None:
            st.success(f"Successfully fetched {len(data)} days of data for {ticker}")
            
            # Calculate technical indicators
            if show_ma:
                data['MA20'] = data['Close'].rolling(window=20).mean()
                data['MA50'] = data['Close'].rolling(window=50).mean()
            
            if show_rsi:
                data['RSI'] = calculate_rsi(data['Close'])
            
            if show_macd:
                data['MACD'], data['MACD_Signal'], data['MACD_Histogram'] = calculate_macd(data['Close'])
            
            # Full width chart
            st.subheader("📊 Stock Price & Volume Chart")
            
            # Create subplots with shared x-axis
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                              vertical_spacing=0.05,
                              subplot_titles=[f'{ticker} Price', 'Volume'],
                              row_heights=[0.7, 0.3])
            
            # Color volume bars based on price movement
            colors = ['green' if data['Close'].iloc[i] >= data['Open'].iloc[i] 
                     else 'red' for i in range(len(data))]
            
            if chart_type == "Line":
                # Add line chart to top subplot
                fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines',
                                       name=ticker, line=dict(color='blue')), row=1, col=1)
                
                # Add moving averages to line chart
                if show_ma:
                    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], mode='lines', 
                                           name='MA20', line=dict(color='orange', width=2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], mode='lines',
                                           name='MA50', line=dict(color='red', width=2)), row=1, col=1)
                
                # Add S&P 500 comparison
                if compare_spy and spy_data is not None:
                    # Normalize both series to start at 100 for comparison
                    normalized_stock = (data['Close'] / data['Close'].iloc[0]) * 100
                    normalized_spy = (spy_data['Close'] / spy_data['Close'].iloc[0]) * 100
                    fig.add_trace(go.Scatter(x=spy_data.index, y=normalized_spy, mode='lines',
                                           name='S&P 500', line=dict(color='purple', width=2, dash='dot')), row=1, col=1)
                    fig.update_yaxes(title_text="Normalized Price (Base=100)", row=1, col=1)
                else:
                    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
                    
            else:  # Candlestick
                # Add candlestick chart to top subplot
                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name=ticker
                ), row=1, col=1)
                
                # Add moving averages to candlestick chart
                if show_ma:
                    fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], mode='lines',
                                           name='MA20', line=dict(color='orange', width=2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=data.index, y=data['MA50'], mode='lines',
                                           name='MA50', line=dict(color='red', width=2)), row=1, col=1)
                
                fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            
            # Add volume chart to bottom subplot
            fig.add_trace(go.Bar(
                x=data.index,
                y=data['Volume'],
                marker_color=colors,
                name='Volume',
                opacity=0.7,
                showlegend=False
            ), row=2, col=1)
            
            # Update layout
            fig.update_layout(
                title=f'{ticker} Stock Analysis',
                height=600,
                xaxis_rangeslider_visible=False
            )
            fig.update_xaxes(title_text="Date", row=2, col=1)
            fig.update_yaxes(title_text="Volume", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Always show news section since we guarantee news content
            # Layout with news: News (2/3 width) and Company Info (1/3 width)
            col_news, col_company = st.columns([2, 1])
            
            with col_news:
                st.markdown(f"### 📰 Recent News ({len(news)} articles)")
                
                # Show message if no real news available
                if len(news) == 0:
                    st.info("No recent news available from Yahoo Finance or Google News for this ticker.")
                    st.caption("News sources may be temporarily unavailable or no articles found for this time period.")
                else:
                    # Display news with better formatting
                    for i, article in enumerate(news):
                        title = article.get('title', 'No Title')
                        
                        # Create a container for each news item
                        with st.container():
                            # Top row: Source and Time
                            col_source, col_time = st.columns([1, 1])
                            
                            publish_time = article.get('providerPublishTime', 0)
                            publisher = article.get('publisher', 'Unknown')
                            link = article.get('link', '')
                            
                            with col_source:
                                if link:
                                    st.caption(f"📡 [{publisher}]({link})")
                                else:
                                    st.caption(f"📡 {publisher}")
                            
                            with col_time:
                                if publish_time:
                                    try:
                                        # Calculate time difference for "X hours ago" format
                                        news_time = pd.to_datetime(publish_time, unit='s')
                                        now = pd.Timestamp.now()
                                        diff = now - news_time
                                        
                                        if diff.days > 0:
                                            time_str = f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
                                        elif diff.seconds > 3600:
                                            hours = diff.seconds // 3600
                                            time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
                                        elif diff.seconds > 60:
                                            minutes = diff.seconds // 60
                                            time_str = f"{minutes} min ago"
                                        else:
                                            time_str = "Just now"
                                    except:
                                        time_str = "Recent"
                                else:
                                    time_str = "Recent"
                                
                                st.caption(f"🕒 {time_str}")
                            
                            # Get and clean summary content
                            summary = article.get('summary', title)  # Use title as fallback
                            # Clean HTML tags and decode HTML entities
                            summary = re.sub('<[^<]+?>', '', summary) if summary else title
                            summary = re.sub('&nbsp;', ' ', summary)  # Replace &nbsp; with spaces
                            summary = re.sub('&amp;', '&', summary)   # Replace &amp; with &
                            summary = re.sub('&lt;', '<', summary)    # Replace &lt; with <
                            summary = re.sub('&gt;', '>', summary)    # Replace &gt; with >
                            summary = summary.strip()
                            
                            # If summary is just the title repeated, try to create better content
                            if summary.lower() == title.lower() or len(summary) < 50:
                                # Create a brief description based on the title
                                if 'stock' in title.lower() or 'shares' in title.lower():
                                    summary = f"Latest market analysis and trading insights for {ticker}. "
                                    summary += "Investors are monitoring key developments and price movements in the stock."
                                elif 'earnings' in title.lower() or 'revenue' in title.lower():
                                    summary = f"Financial performance update for {ticker}. "
                                    summary += "Analysts review quarterly results and provide market outlook."
                                elif 'investment' in title.lower() or 'fund' in title.lower():
                                    summary = f"Investment activity and institutional interest in {ticker}. "
                                    summary += "Market participants assess portfolio allocation strategies."
                                else:
                                    summary = f"Breaking news and market updates for {ticker}. "
                                    summary += "Financial markets react to latest corporate developments."
                            
                            # Extract first 2 sentences with more content (up to 250 characters)
                            sentences = summary.split('. ')
                            if len(sentences) >= 2:
                                content = '. '.join(sentences[:2])
                                if not content.endswith('.'):
                                    content += '.'
                            else:
                                content = sentences[0]
                                if not content.endswith('.'):
                                    content += '.'
                            
                            # Limit to 250 characters for more detailed content
                            if len(content) > 250:
                                content = content[:247] + "..."
                            
                            # Display content in bold
                            st.markdown(f"**{content}**")
                            
                            # Link is now in the header, no separate link needed
                            
                            # Separator
                            st.markdown("---")
            
            with col_company:
                st.markdown("### 📊 Company Overview")
                
                # Company info
                if info:
                    # Company basic info in compact format
                    company_name = info.get('longName', ticker)
                    if len(company_name) > 30:
                        company_name = company_name[:30] + "..."
                    st.markdown(f"**{company_name}**")
                    st.caption(f"Sector: {info.get('sector', 'N/A')}")
                    
                    # Key financials in 2-column layout
                    col1, col2 = st.columns(2)
                    
                    # Calculate price metrics
                    current_price = data['Close'].iloc[-1]
                    price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
                    percent_change = (price_change / data['Close'].iloc[0]) * 100
                    
                    with col1:
                        st.metric("Price", f"${current_price:.2f}")
                        st.metric("High", f"${data['High'].max():.2f}")
                        
                        market_cap = info.get('marketCap', 0)
                        if market_cap > 0:
                            market_cap_str = f"${market_cap/1e9:.1f}B" if market_cap > 1e9 else f"${market_cap/1e6:.1f}M"
                        else:
                            market_cap_str = "N/A"
                        st.metric("Market Cap", market_cap_str)
                        
                        pe_ratio = info.get('trailingPE', 'N/A')
                        if isinstance(pe_ratio, (int, float)):
                            pe_ratio = f"{pe_ratio:.1f}"
                        st.metric("P/E", pe_ratio)
                    
                    with col2:
                        st.metric("Change", f"{percent_change:+.1f}%")
                        st.metric("Low", f"${data['Low'].min():.2f}")
                        
                        volume_str = f"{data['Volume'].mean()/1e6:.1f}M" if data['Volume'].mean() > 1e6 else f"{data['Volume'].mean()/1e3:.1f}K"
                        st.metric("Avg Vol", volume_str)
                        
                        beta = info.get('beta', 'N/A')
                        if isinstance(beta, (int, float)):
                            beta = f"{beta:.2f}"
                        st.metric("Beta", beta)
                    
                    # Additional metrics
                    dividend_yield = info.get('dividendYield', 0)
                    if dividend_yield:
                        st.metric("Dividend", f"{dividend_yield*100:.1f}%")
                    
                    # Technical indicators (if enabled)
                    if show_ma:
                        st.markdown("**Moving Averages**")
                        current_ma20 = data['MA20'].iloc[-1] if not pd.isna(data['MA20'].iloc[-1]) else 0
                        current_ma50 = data['MA50'].iloc[-1] if not pd.isna(data['MA50'].iloc[-1]) else 0
                        col_ma1, col_ma2 = st.columns(2)
                        with col_ma1:
                            st.metric("MA20", f"${current_ma20:.2f}")
                        with col_ma2:
                            st.metric("MA50", f"${current_ma50:.2f}")
                    
                    if show_rsi:
                        current_rsi = data['RSI'].iloc[-1] if not pd.isna(data['RSI'].iloc[-1]) else 0
                        rsi_status = "🔴 Overbought" if current_rsi > 70 else "🟢 Oversold" if current_rsi < 30 else "🟡 Neutral"
                        st.metric("RSI", f"{current_rsi:.1f}")
                        st.caption(rsi_status)
                    
                    if compare_spy and spy_data is not None:
                        spy_change = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[0] - 1) * 100
                        outperformance = percent_change - spy_change
                        perf_color = "🟢" if outperformance > 0 else "🔴"
                        st.metric("vs S&P 500", f"{perf_color} {outperformance:+.1f}%")
                    
                    # Company description (compact)
                    business_summary = info.get('longBusinessSummary', '')
                    if business_summary:
                        st.markdown("**About:**")
                        # Truncate to fit better
                        if len(business_summary) > 200:
                            business_summary = business_summary[:200] + "..."
                        st.caption(business_summary)
                        
                else:
                    # Basic metrics if no company info available
                    current_price = data['Close'].iloc[-1]
                    price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
                    percent_change = (price_change / data['Close'].iloc[0]) * 100
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Price", f"${current_price:.2f}")
                        st.metric("High", f"${data['High'].max():.2f}")
                    with col2:
                        st.metric("Change", f"{percent_change:+.1f}%")
                        st.metric("Low", f"${data['Low'].min():.2f}")
                    
                    volume_str = f"{data['Volume'].mean()/1e6:.1f}M" if data['Volume'].mean() > 1e6 else f"{data['Volume'].mean()/1e3:.1f}K"
                    st.metric("Avg Volume", volume_str)
            
            # Technical Indicators (full width)
            if show_rsi or show_macd:
                st.markdown("### 📈 Technical Indicators")
            
            if show_rsi:
                st.subheader("RSI (Relative Strength Index)")
                rsi_fig = go.Figure()
                rsi_fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI'))
                rsi_fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
                rsi_fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
                rsi_fig.update_layout(title=f'{ticker} RSI', yaxis_title="RSI", yaxis=dict(range=[0, 100]))
                st.plotly_chart(rsi_fig, use_container_width=True)
            
            if show_macd:
                st.subheader("MACD (Moving Average Convergence Divergence)")
                macd_fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                       subplot_titles=['MACD Line', 'MACD Histogram'],
                                       row_heights=[0.7, 0.3])
                
                macd_fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='blue')), row=1, col=1)
                macd_fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], name='Signal', line=dict(color='red')), row=1, col=1)
                macd_fig.add_trace(go.Bar(x=data.index, y=data['MACD_Histogram'], name='Histogram', marker_color='gray'), row=2, col=1)
                
                macd_fig.update_layout(title=f'{ticker} MACD', showlegend=True)
                st.plotly_chart(macd_fig, use_container_width=True)
            
            st.subheader("📋 Recent Data")
            st.dataframe(data.tail(10), use_container_width=True)
            
            # Download options
            st.subheader("💾 Export Data")
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                csv = data.to_csv()
                st.download_button(
                    label="📊 Download CSV",
                    data=csv,
                    file_name=f"{ticker}_stock_data.csv",
                    mime="text/csv"
                )
            
            with col_dl2:
                # Create Excel file with multiple sheets
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    # Remove timezone from datetime index for Excel compatibility
                    data_for_excel = data.copy()
                    if hasattr(data_for_excel.index, 'tz') and data_for_excel.index.tz is not None:
                        data_for_excel.index = data_for_excel.index.tz_localize(None)
                    data_for_excel.to_excel(writer, sheet_name='Stock Data')
                    if info:
                        info_df = pd.DataFrame([info])
                        info_df.to_excel(writer, sheet_name='Company Info')
                excel_data = excel_buffer.getvalue()
                
                st.download_button(
                    label="📈 Download Excel",
                    data=excel_data,
                    file_name=f"{ticker}_comprehensive_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.warning("Please select both start and end dates.")

elif fetch_button:
    st.warning("Please enter a stock ticker symbol.")

st.markdown("---")
st.markdown("**Note:** Data is fetched from Yahoo Finance. Technical indicators help identify trends and trading opportunities.")