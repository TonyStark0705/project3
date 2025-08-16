#!/usr/bin/env python3
"""Debug script to check news structure and display"""

from app import fetch_stock_data
from datetime import date
import json

print("=== NEWS DEBUG ANALYSIS ===")
print("Fetching news for AAPL...")

# Fetch data
data, info, news = fetch_stock_data('AAPL', date(2023, 1, 1), date(2023, 1, 31))

print(f"\nNews fetched: {len(news)} articles")
print(f"News type: {type(news)}")

if news:
    print(f"\nFirst article structure:")
    first_article = news[0]
    print(f"Type: {type(first_article)}")
    print(f"Keys: {list(first_article.keys()) if isinstance(first_article, dict) else 'Not a dict'}")
    
    print(f"\nFirst article content:")
    for key, value in first_article.items():
        print(f"  {key}: {value}")
    
    print(f"\n=== ALL ARTICLES SUMMARY ===")
    for i, article in enumerate(news[:5]):  # Show first 5
        title = article.get('title', 'NO TITLE')
        publisher = article.get('publisher', 'NO PUBLISHER')
        link = article.get('link', 'NO LINK')
        pub_time = article.get('providerPublishTime', 'NO TIME')
        
        print(f"{i+1}. {title[:80]}...")
        print(f"    Publisher: {publisher}")
        print(f"    Link: {link[:50]}...")
        print(f"    Time: {pub_time}")
        print()

else:
    print("ERROR: No news articles returned!")

print("=== END DEBUG ===")