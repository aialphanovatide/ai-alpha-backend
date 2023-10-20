import requests
import warnings
import pandas as pd
from typing import Dict, Any
import plotly.graph_objects as go
warnings.simplefilter("ignore", category=FutureWarning)

binance_base_url = 'https://api3.binance.com'

# Gets historical data from Binance API
def get_kline_data(symbol: str) -> Dict[str, Any]:

    formatted_symbol = symbol.upper()

    base_url = f"{binance_base_url}/api/v3/klines"
    params = {"symbol": formatted_symbol, "limit": 50, "interval": '15m'}
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve data: {e}")
        return f"Failed to retrieve data: {e}"
    

# Checks if the indicator is in the strategy name expected value in the form: "SOLUSDT 4h Support 1"
def get_indicator(indicator: str, strategy_name: str) -> str:

    formatted_startegy_name = strategy_name.casefold().strip()

    if indicator in formatted_startegy_name:
        return True
    else:
        return False
   

def generate_signal_chart(symbol_asset: str, last_price: str) -> bytes:
 
    last_price = float(last_price)
    binance_data = get_kline_data(symbol_asset)

    df = pd.DataFrame(binance_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTimestamp', 'QuoteAssetVolume', 'NumberofTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms') 
    # Convert 'Close' column to numeric
    df['Close'] = pd.to_numeric(df['Close'])

    # Find the row with the closest price to the given price
    closest_price_row = df.iloc[(df['Close'] - last_price).abs().idxmin()]
   

    fig = go.Figure(data=[go.Candlestick(
                    x=df['Timestamp'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'])])


    fig.update_layout(
        title=dict(text=f'Chart of {symbol_asset}'),
        yaxis_title='Price (USD)',
        xaxis_title='Time Frames',
        xaxis_rangeslider_visible=False,
        font=dict(family='Arial', size=15, color='#fff'),
        autosize=True,
        paper_bgcolor='#0E1E25',  
        plot_bgcolor='#0E1E25', 
        annotations=[dict(
                    x=closest_price_row['Timestamp'], y=last_price, xref='x', yref='y',
                    showarrow=True, arrowhead=2, arrowcolor='#FF6F00', ax=0, ay=-60, text=f'Last Price: {last_price}')
                ]
    )
    image_bytes = fig.to_image(format="png")
    return image_bytes


def generate_alert_chart(symbol: str, last_price: str) -> bytes:
 
    last_price = float(last_price)
    symbol = symbol.split(':')[1].replace('^', '').strip() # result: SOLUSDT
    binance_data = get_kline_data(symbol)

    df = pd.DataFrame(binance_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTimestamp', 'QuoteAssetVolume', 'NumberofTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])

    df['Timestamp'] = df['Timestamp'].astype('datetime64[ms]')
    # Convert 'Close' column to numeric
    df['Close'] = pd.to_numeric(df['Close'])

    # Find the row with the closest price to the given price
    closest_price_row = df.iloc[(df['Close'] - last_price).abs().idxmin()]
   
    fig = go.Figure(data=[go.Candlestick(
                    x=df['Timestamp'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'])])


    fig.update_layout(
        title=dict(text=f'Chart of {symbol}'),
        yaxis_title='Price (USD)',
        xaxis_title='Time Frames',
        xaxis_rangeslider_visible=False,
        font=dict(family='Arial', size=15, color='#fff'),
        autosize=True,
        paper_bgcolor='#0E1E25',  
        plot_bgcolor='#0E1E25', 
        annotations=[dict(
                    x=closest_price_row['Timestamp'], y=last_price, xref='x', yref='y',
                    showarrow=True, arrowhead=2, arrowcolor='#FF6F00', ax=0, ay=-60, text=f'Last Price: {last_price}')
                ]
    )

    image_bytes = fig.to_image(format="png")
    return image_bytes

# {"bot_name": "SOLUSDT 4h Support 1", "symbol": "BINANCE:^SOLUSDT",  "time_frame": "%alert_note%", "status": "touch", "last_price": "23.5100", "type": "alert"}

# generate_alert_chart("BINANCE:^SOLUSDT", "26.5100")
# generate_signal_chart("SOLUSDT", "26.5100")
# print(get_indicator('rsi', 'BTC 4H RSI<35'))