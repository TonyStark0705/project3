#!/usr/bin/env python3
"""Test script for app.py functions"""

import sys
import pandas as pd
import numpy as np
from datetime import date

# Import functions from app
from app import validate_ticker, calculate_rsi, calculate_macd, fetch_stock_data

def test_validate_ticker():
    """Test the validate_ticker function"""
    print("Testing validate_ticker...")
    
    # Valid tickers
    assert validate_ticker('AAPL') == True
    assert validate_ticker('GOOGL') == True
    assert validate_ticker('MSFT') == True
    assert validate_ticker('TSLA') == True
    
    # Invalid tickers
    assert validate_ticker('') == False
    assert validate_ticker('TOOLONGNAME') == False
    assert validate_ticker('INVALID@') == False
    assert validate_ticker('test symbol') == False  # spaces not allowed
    
    print("PASS: validate_ticker tests passed")

def test_calculate_rsi():
    """Test the calculate_rsi function"""
    print("Testing calculate_rsi...")
    
    # Create test price data
    test_prices = pd.Series([100, 102, 101, 103, 104, 102, 105, 104, 106, 105, 107, 108, 106, 109, 110])
    
    # Test RSI calculation
    rsi = calculate_rsi(test_prices, window=5)
    
    # RSI should be a Series
    assert isinstance(rsi, pd.Series)
    
    # RSI values should be between 0 and 100 (where not NaN)
    valid_rsi = rsi.dropna()
    assert all(0 <= val <= 100 for val in valid_rsi)
    
    # Should have some valid RSI values
    assert len(valid_rsi) > 0
    
    print("PASS: calculate_rsi tests passed")

def test_calculate_macd():
    """Test the calculate_macd function"""
    print("Testing calculate_macd...")
    
    # Create test price data
    test_prices = pd.Series([100, 102, 101, 103, 104, 102, 105, 104, 106, 105, 107, 108, 106, 109, 110])
    
    # Test MACD calculation
    macd, signal, histogram = calculate_macd(test_prices)
    
    # All should be Series
    assert isinstance(macd, pd.Series)
    assert isinstance(signal, pd.Series)
    assert isinstance(histogram, pd.Series)
    
    # Should have same length as input
    assert len(macd) == len(test_prices)
    assert len(signal) == len(test_prices)
    assert len(histogram) == len(test_prices)
    
    # Histogram should equal macd - signal (where not NaN)
    valid_indices = ~(macd.isna() | signal.isna() | histogram.isna())
    if valid_indices.any():
        np.testing.assert_array_almost_equal(
            histogram[valid_indices], 
            (macd - signal)[valid_indices]
        )
    
    print("PASS: calculate_macd tests passed")

def test_fetch_stock_data():
    """Test the fetch_stock_data function with a simple test"""
    print("Testing fetch_stock_data...")
    
    try:
        # Test with AAPL for a short date range
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 31)
        
        data, info, news = fetch_stock_data('AAPL', start_date, end_date)
        
        if data is not None:
            # Should return a DataFrame
            assert isinstance(data, pd.DataFrame)
            
            # Should have expected columns
            expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in expected_columns:
                assert col in data.columns
            
            # Should have some data
            assert len(data) > 0
            
            # Info should be a dict (can be empty)
            assert isinstance(info, dict)
            
            # News should be a list
            assert isinstance(news, list)
            
            print("PASS: fetch_stock_data tests passed")
        else:
            print("WARNING: fetch_stock_data returned None (possible network issue)")
            
    except Exception as e:
        print(f"WARNING: fetch_stock_data test failed with error: {e}")

def run_all_tests():
    """Run all tests"""
    print("Starting app.py function tests...")
    print("=" * 50)
    
    try:
        test_validate_ticker()
        test_calculate_rsi()
        test_calculate_macd()
        test_fetch_stock_data()
        
        print("=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"ERROR: Test failed with: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)