# chart/total3.py

from typing import List, Dict, Any
from tvDatafeed import TvDatafeed, Interval
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

TW_USER = os.getenv('TW_USER')
TW_PASS = os.getenv('TW_PASS')

def fetch_total_3_data(days: int = 15) -> Any:
    """
    Fetch raw data for CRYPTOCAP:TOTAL3 from TradingView.

    Args:
        days (int): Number of days of data to fetch. Defaults to 15.

    Returns:
        Any: Raw data from TvDatafeed.

    Raises:
        RuntimeError: If there's an error fetching data from TradingView.
    """
    try:
        tv = TvDatafeed(TW_USER, TW_PASS)
        data = tv.get_hist(
            symbol='CRYPTOCAP:TOTAL3',
            exchange='CRYPTOCAP',
            interval=Interval.in_daily,
            n_bars=days,
            fut_contract=None,
            extended_session=False
        )
        return data.iloc[::-1]
    except Exception as e:
        raise RuntimeError(f"Error fetching data from TradingView: {str(e)}")

def process_total_3_data(raw_data: Any) -> List[Dict[str, Any]]:
    """
    Process raw data into a list of dictionaries.

    Args:
        raw_data (Any): Raw data from TvDatafeed.

    Returns:
        List[Dict[str, Any]]: Processed data as a list of dictionaries.
    """
    results = []
    for index, row in raw_data.iterrows():
        package = {
            'date': index.strftime('%Y-%m-%d'),
            'open': round(row['open'], 2),
            'high': round(row['high'], 2),
            'low': round(row['low'], 2),
            'close': round(row['close'], 2)
        }
        results.append(package)
    return results

def get_total_3_data(days: int = 15) -> List[Dict[str, Any]]:
    """
    Retrieve and process total market cap data for the top 3 cryptocurrencies.

    Args:
        days (int): Number of days of data to fetch. Defaults to 15.

    Returns:
        List[Dict[str, Any]]: Processed data as a list of dictionaries.

    Raises:
        RuntimeError: If there's an error fetching or processing the data.
    """
    try:
        raw_data = fetch_total_3_data(days)
        return process_total_3_data(raw_data)
    except Exception as e:
        raise RuntimeError(f"Error in get_total_3_data: {str(e)}")