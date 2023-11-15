import requests
import pandas as pd
from typing import Dict, Any
import plotly.graph_objs as go

binance_base_url = 'https://api3.binance.com'

# Gets historical data from Binance API
def get_kline_data(symbol: str, interval) -> Dict[str, Any]:

    formatted_symbol = symbol.upper()
    formatted_interval = interval.casefold()

    base_url = f"{binance_base_url}/api/v3/klines"
    params = {"symbol": formatted_symbol, "limit": 50, "interval": formatted_interval}
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve data: {e}")
        return f"Failed to retrieve data: {e}"

def generate_chart_with_support_resistance(symbol, interval, resistance, support):


    binance_data = get_kline_data(symbol, interval)
    df = pd.DataFrame(binance_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTimestamp', 'QuoteAssetVolume', 'NumberofTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df['Close'] = pd.to_numeric(df['Close'])

    # Crea un gráfico con líneas de resistencia y soporte
    fig = go.Figure()

    # Agrega el gráfico de velas (candlestick)
    fig.add_trace(go.Candlestick(
        x=df['Timestamp'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'))

    # Agrega una línea de resistencia al gráfico
    fig.add_shape(
        go.layout.Shape(
            type='line',
            x0=df['Timestamp'].iloc[0],
            y0=resistance,
            x1=df['Timestamp'].iloc[-1],
            y1=resistance,
            line=dict(color='red', width=2),
        )
    )

    # Agrega una etiqueta a la línea de resistencia
    fig.add_annotation(
        go.layout.Annotation(
            x=df['Timestamp'].iloc[-1],
            y=resistance,
            text=f'Resistance - ${resistance}',
            showarrow=True,
            arrowhead=2,
        )
    )

    # Agrega una línea de soporte al gráfico
    fig.add_shape(
        go.layout.Shape(
            type='line',
            x0=df['Timestamp'].iloc[0],
            y0=support,
            x1=df['Timestamp'].iloc[-1],
            y1=support,
            line=dict(color='blue', width=2),
           
        )
    )

    # Agrega una etiqueta a la línea de soporte
    fig.add_annotation(
        go.layout.Annotation(
            x=df['Timestamp'].iloc[-1],
            y=support,
            text=f'Support - ${support}',
            showarrow=True,
            arrowhead=2,
        )
    )

    # Configura el diseño del gráfico
    fig.update_layout(
        
        title=dict(text=f'{symbol.upper()} - Support and Resistance'),
        yaxis_title='Price (USD)',
        xaxis_title=f'Time Frames ({str(interval).upper()})',
        xaxis_rangeslider_visible=False,
        font=dict(family='Arial', size=15, color='#fff'),
        autosize=True,
        paper_bgcolor='#0E1E25',
        plot_bgcolor='#0E1E25',
        
    )
    # Change grid color and axis colors
    fig.update_xaxes(showline=True, linewidth=1, linecolor='#0E1E25', gridcolor='#0E1E25')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='#0E1E25', gridcolor='#0E1E25')
    
    # Muestra el gráfico
    fig.show()
    image_bytes = fig.to_image(format="png")
    return image_bytes


# Usage
# generate_chart_with_support_resistance(symbol='ETHUSDT',
#                                        interval='1d',
#                                        resistance=1863,
#                                        support=1653)
