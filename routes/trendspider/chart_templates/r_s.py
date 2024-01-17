import requests
import pandas as pd
from typing import Dict, Any
import plotly.graph_objs as go
from flask import url_for
import time

binance_base_url = 'https://api3.binance.com'


# Gets historical data from Binance API
def get_kline_data(symbol: str, interval: str) -> Dict[str, Any]:

    formatted_symbol = symbol.upper()
    formatted_interval = interval.casefold()

    base_url = f"{binance_base_url}/api/v3/klines"
    params = {"symbol": formatted_symbol, "limit": 200, "interval": formatted_interval}
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve data: {e}")
        return f"Failed to retrieve data: {e}"


def generate_chart_with_support_resistance(symbol, interval, resistance_lines, support_lines, num_candles=50):

    while True:  # Bucle infinito para actualizar continuamente

        data = get_kline_data(symbol, interval)
        df = pd.DataFrame(data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTimestamp', 'QuoteAssetVolume', 'NumberofTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df['Close'] = pd.to_numeric(df['Close'])

        fig = go.Figure()

        # Creates the candlestick chart
        fig.add_trace(go.Candlestick(
            x=df['Timestamp'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='#3adf00', decreasing_line_color='#fc5404'
        ))

        # Resto del código para configurar el diseño y las líneas de soporte/resistencia

        fig.show()

        time.sleep(2)  # Espera dos segundos antes de la próxima actualización


# Usage
generate_chart_with_support_resistance(symbol='ETHUSDT',
                                       interval='1s',
                                       resistance_lines=[2320, 2356, 2424, 2550],
                                       support_lines=[2050, 2100, 2150, 2200])
