import requests
import pandas as pd
from typing import Dict, Any
import plotly.graph_objs as go

def generate_ema_chart(symbol, interval, direction, ma_type, ma_period):
    # Obtiene los datos históricos del símbolo y el intervalo proporcionados
    data = get_kline_data(symbol, interval)

    # Crea un DataFrame a partir de los datos
    df = pd.DataFrame(data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTimestamp', 'QuoteAssetVolume', 'NumberofTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df['Close'] = pd.to_numeric(df['Close'])

    # Calcula la media móvil (MA) según el tipo y período proporcionados
    ma_window = int(ma_period)
    if ma_type.lower() == 'ema':
        df['MA'] = df['Close'].ewm(span=ma_window, adjust=False).mean()
    elif ma_type.lower() == 'sma':
        df['MA'] = df['Close'].rolling(window=ma_window).mean()
    else:
        raise ValueError("Type not valid, use 'sma' or 'ema'" )

    # Crea el gráfico utilizando Plotly
    ma_label = f'{ma_type.upper()} {ma_window}'
    fig = go.Figure(data=[go.Candlestick(
        x=df['Timestamp'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'),
        go.Scatter(
            x=df['Timestamp'],
            y=df['MA'],
            mode='lines',
            name=ma_label,
            line=dict(width=2, color='orange')
        )])

    # Configura el diseño del graficos. 
    fig.update_layout(
        title=f'Chart of {symbol} - {interval} - {ma_label} - {direction}',
        xaxis_title='Time Frames',
        yaxis_title='Price (USD)',
        xaxis_rangeslider_visible=True,
        font=dict(family='Arial', size=15, color='#fff'),
        autosize=True,
        paper_bgcolor='#0E1E25',  
        plot_bgcolor='#0E1E25',
    )

    # fig.show()
    image_bytes = fig.to_image(format="png")
    return image_bytes

binance_base_url = 'https://api3.binance.com'

# Gets historical data from Binance API
def get_kline_data(symbol: str, interval) -> Dict[str, Any]:

    formatted_symbol = symbol.upper()

    base_url = f"{binance_base_url}/api/v3/klines"
    params = {"symbol": formatted_symbol, "limit": 50, "interval": interval}
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve data: {e}")
        return f"Failed to retrieve data: {e}"

# Ejemplo de uso: BTC 1W CROSS DOWN EMA 20
# generate_ema_chart('BTCUSDT', '1w', 'CROSS DOWN', 'EMA', '20')
