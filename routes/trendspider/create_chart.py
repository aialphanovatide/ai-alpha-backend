import requests
import pytz
import pandas as pd
import plotly.graph_objects as go

binance_base_url = 'https://api3.binance.com'

def get_kline_data(symbol):
   
    base_url = f"{binance_base_url}/api/v3/klines"
    params = {"symbol": str(symbol.upper()), "limit": 40, "interval": '4h'}
    response = requests.get(base_url, params=params)
    data = response.json()
    return data

def generate_chart(symbol_asset: str, last_price: float) -> bytes:
 
    price_whole_number = float(last_price)
    
    binance_data = get_kline_data(symbol_asset)
    symbol_with_usdt = symbol_asset[:3] + '/' + symbol_asset[3:]

    df = pd.DataFrame(binance_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTimestamp', 'QuoteAssetVolume', 'NumberofTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms').dt.tz_localize('UTC')

    london_timezone = pytz.timezone('Europe/London')
    df['Timestamp'] = df['Timestamp'].dt.tz_convert(london_timezone)
    df['Close'] = pd.to_numeric(df['Close'])

    closest_price_row = df.iloc[(df['Close'] - price_whole_number).abs().idxmin()]
   

    fig = go.Figure(data=[go.Candlestick(
                    x=df['Timestamp'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'])])


    fig.update_layout(
        title=dict(text=f'Candlestick Chart of {symbol_with_usdt.upper()}'),
        yaxis_title='Price (USD)',
        xaxis_title='Time Frames',
        xaxis_rangeslider_visible=False,
        font=dict(family='Arial', size=15, color='#fff'),
        autosize=True,
        paper_bgcolor='#0E1E25',  
        plot_bgcolor='#0E1E25', 
        annotations=[dict(
                    x=closest_price_row['Timestamp'], y=price_whole_number, xref='x', yref='y',
                    showarrow=True, arrowhead=2, arrowcolor='#FF6F00', ax=0, ay=-60, text=f'Last Price: {last_price}')
                ]
    )

    image_bytes = fig.to_image(format="png")
    return image_bytes