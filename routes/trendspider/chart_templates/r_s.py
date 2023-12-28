import requests
import pandas as pd
from typing import Dict, Any
import plotly.graph_objs as go
from flask import url_for

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
        

    fig.update_layout(
        yaxis_title='',
        xaxis_title='',
        xaxis_rangeslider_visible=True,
        font=dict(family='Arial', size=15, color='#fff'),
        autosize=True,
        paper_bgcolor='#fff',
        plot_bgcolor='#fff',
        
    
        
        xaxis=dict(
            showline=True,
            showgrid=True,
            color="#282828",
            linecolor="#B8BBBC",
            linewidth=2,
  
        ),

        yaxis=dict(
            showline=True,
            showgrid=True,
            side='right',
            color="#282828",
            linecolor="#B8BBBC",
            linewidth=2,    
            tickprefix="$",
            #showticklabels=False,  # Desactiva las etiquetas del eje y
        ),

        xaxis_rangeslider=dict( 
            visible=True,
            thickness=0.05,  # Ajusta el grosor del control deslizante de rango
            bgcolor='rgba(0,0,0,0)',  # Configura el fondo del control deslizante de rango
        ),
    )

    for support in support_lines:
        # Adds 4 support lines to the chart
        fig.add_annotation(
            go.layout.Annotation(
                x=df['Timestamp'].iloc[-1] + pd.Timedelta(minutes=15),  # Ajuste de posición a la derecha del gráfico
                y=support,
                xref="x",
                align="right",
                yref="y",
                xanchor="right",
                yanchor="middle",
                text=f"${support}",
                showarrow=False,
                font=dict(color="#FC5404", size=12),
                bordercolor="#FC5404",
                borderwidth=2,
                bgcolor="#fff",
            )
        )
        fig.add_shape(
            go.layout.Shape(
                type='line',
                x0=df['Timestamp'].iloc[0],
                y0=support,
                x1=df['Timestamp'].iloc[-2],
                y1=support,
                line=dict(color='#FC5404', width=2),
            )
        )

    for resistance in resistance_lines:
        # Adds 4 resistance lines to the chart
        fig.add_annotation(
            go.layout.Annotation(
                x=df['Timestamp'].iloc[-7] + pd.Timedelta(minutes=15),  # Ajuste de posición a la derecha del gráfico
                y=resistance,
                xref="x",
                yref="y",
                xanchor="left",  # Cambiado a la izquierda
                yanchor="middle",
                text=f"${resistance}",
                showarrow=False,
                font=dict(color="#F9B208", size=12),
                bordercolor="#F9B208",
                borderwidth=2,
                bgcolor="#fff",
            )
        )
        fig.add_shape(
            go.layout.Shape(
                type='line',
                x0=df['Timestamp'].iloc[0],
                y0=resistance,
                x1=df['Timestamp'].iloc[-1],
                y1=resistance,
                line=dict(color='#F9B208', width=2),
            )
        )

    fig.show()


# Usage
generate_chart_with_support_resistance(symbol='ETHUSDT',
                                       interval='1h',
                                       resistance_lines=[2320, 2356, 2424, 2550],
                                       support_lines=[2050, 2100, 2150, 2200])
