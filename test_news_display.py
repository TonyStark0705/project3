#!/usr/bin/env python3
"""Simple test to verify news display in Streamlit"""

import streamlit as st
from app import fetch_stock_data
from datetime import date

st.title("News Display Test")

if st.button("Test News Display"):
    with st.spinner("Fetching news..."):
        data, info, news = fetch_stock_data('AAPL', date(2023, 1, 1), date(2023, 1, 31))
    
    st.write(f"Found {len(news)} news articles")
    
    if news:
        st.markdown("### 📰 Recent News")
        
        for i, article in enumerate(news[:3]):  # Show first 3
            title = article.get('title', 'No Title')
            publisher = article.get('publisher', 'Unknown')
            
            st.markdown(f"**{i+1}. {title}**")
            st.caption(f"📡 {publisher}")
            
            summary = article.get('summary', 'No summary')
            # Simple cleaning
            import re
            clean_summary = re.sub('<[^<]+?>', '', summary) if summary else 'No summary'
            
            st.write(clean_summary[:100] + "..." if len(clean_summary) > 100 else clean_summary)
            st.markdown("---")
    else:
        st.error("No news found!")