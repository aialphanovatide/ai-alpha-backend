import re
import requests
import numpy as np
import pandas as pd
from typing import Dict, Any
import plotly.graph_objs as go
from plotly.subplots import make_subplots


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

def calculate_rsi(df, period=14):

    close_prices = df['Close']
    delta = close_prices.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    avg_loss = np.where(avg_loss == 0, 0.0001, avg_loss)

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def generate_rsi_chart(symbol, interval, rsi_condition):

    period = int(re.search(r'\d+', rsi_condition).group())

    if 'RSI>' in rsi_condition:
        rsi_operator = '>'
        rsi_value = int(rsi_condition.split('RSI>')[1])
    elif 'RSI<' in rsi_condition:
        rsi_operator = '<'
        rsi_value = int(rsi_condition.split('RSI<')[1])
    else:
        rsi_operator = None
        rsi_value = None

    binance_data = get_kline_data(symbol, interval)
    df = pd.DataFrame(binance_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTimestamp', 'QuoteAssetVolume', 'NumberofTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df['Close'] = pd.to_numeric(df['Close'])

    rsi = calculate_rsi(df, period)

    fig = make_subplots(rows=2, cols=1,  
                        shared_xaxes=False, 
                        shared_yaxes=False,
                        print_grid=False,
                        row_heights=[0.7, 0.3],
                        subplot_titles=(" ", "RSI"))

    fig.add_trace(go.Candlestick(
        x=df['Timestamp'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'
    ), row=1, col=1,)

    fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=rsi,
        mode='lines',
        name=f'RSI {period}',
        line=dict(width=2, color='blue'),
    ),  row=2, col=1,)


    fig.update_layout(coloraxis=dict(colorscale='Bluered_r'),         
        title=dict(text=f'{symbol.upper()} - RSI {rsi_operator} {period}', font=dict(color='white')),
        paper_bgcolor='#0E1E25',
        plot_bgcolor='#0E1E25',
        showlegend=True,
        xaxis_rangeslider_visible=False,
        font=dict(color='#fff'))

    fig.add_shape(type="line", x0=df['Timestamp'].iloc[0], x1=df['Timestamp'].iloc[-1], y0=20, y1=20, row=2, col=1, line=dict(color="green", width=1, dash="dash"))
    fig.add_shape(type="line", x0=df['Timestamp'].iloc[0], x1=df['Timestamp'].iloc[-1], y0=80, y1=80, row=2, col=1, line=dict(color="red", width=1, dash="dash"))

    # Remove gridlines on the scatter plot
    fig.update_xaxes(showgrid=False, zeroline=False, row=2, col=1)
    fig.update_yaxes(showgrid=False, zeroline=False, row=2, col=1)

    fig.show()

def generate_chart_with_rsi_from_params(symbol, interval, rsi_condition):
    

    period = int(re.search(r'\d+', rsi_condition).group())

    if 'RSI>' in rsi_condition:
        rsi_operator = '>'
        rsi_value = int(rsi_condition.split('RSI>')[1])
    elif 'RSI<' in rsi_condition:
        rsi_operator = '<'
        rsi_value = int(rsi_condition.split('RSI<')[1])
    else:
        rsi_operator = None
        rsi_value = None

    binance_data = get_kline_data(symbol, interval)
    df = pd.DataFrame(binance_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTimestamp', 'QuoteAssetVolume', 'NumberofTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df['Close'] = pd.to_numeric(df['Close'])

    rsi = calculate_rsi(df, period)

    # CREATES CANDLESTICK CHART
    candlestick_fig = go.Figure()

    candlestick_fig.add_trace(go.Candlestick(
        x=df['Timestamp'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'
    ))

    # CUSTOMIZE CANDLESTICK
    candlestick_fig.update_layout(
        yaxis_title='Price (USD)',
        xaxis_title=f'Time Frames ({interval})',
        xaxis_rangeslider_visible=False,
        font=dict(family='Arial', size=15, color='#fff'),
        autosize=True,
        paper_bgcolor='#0E1E25',
        plot_bgcolor='#0E1E25'
    )

    # CREATES RSI CHART
    rsi_fig = go.Figure()

    rsi_fig.add_trace(go.Scatter(
        x=df['Timestamp'],
        y=rsi,
        mode='lines',
        name=f'RSI {period}',
        line=dict(width=2, color='blue')
    ))

    if len(df) >= 2:
        rsi_fig.add_shape(
            dict(
                type="line",
                x0=df['Timestamp'].iloc[0],
                x1=df['Timestamp'].iloc[-1],
                y0=70,
                y1=70,
                opacity=0.3,
                line=dict(color="red", width=2),
                name="Overbought (70)"
            )
        )

        rsi_fig.add_shape(
            dict(
                type="line",
                x0=df['Timestamp'].iloc[0],
                x1=df['Timestamp'].iloc[-1],
                y0=30,
                y1=30,
                opacity=0.3,
                line=dict(color="green", width=2),
                name="Oversold (30)"
            )
        )
        # Add text labels for the overbought and oversold regions
        rsi_fig.add_annotation(
            text="Overbought",
            x=df['Timestamp'].iloc[0],
            y=80, 
            showarrow=False,
            font=dict(color="white", size=12),
        )

        rsi_fig.add_annotation(
            text="Oversold",
            x=df['Timestamp'].iloc[0],
            y=30, 
            showarrow=False,
            font=dict(color="white", size=12),
        )

    else:
        print("There is not enough data to geenrate the RSI chart")

    # Personalizar el diseño del gráfico del indicador RSI
    rsi_fig.update_layout(
        yaxis_title='RSI',
        xaxis_title=f'Time Frames ({interval})',
        xaxis_rangeslider_visible=False,
        font=dict(family='Arial', size=15, color='#fff'),
        autosize=True,
        paper_bgcolor='#0E1E25',
        plot_bgcolor='#0E1E25'
    )

    # Crear subplots
    subplots = make_subplots(rows=2, cols=1, 
                             shared_xaxes=False, 
                             shared_yaxes=False,
                             row_heights=[0.7, 0.3],
                             subplot_titles=(" ", "RSI")
                             )

    # # Agregar los gráficos a los subplots
    subplots.add_trace(candlestick_fig.data[0], row=1, col=1)
    subplots.add_trace(rsi_fig.data[0], row=2, col=1)

    # Actualizar diseño de los subplots
    subplots.update_layout(
        title=dict(text=f'{symbol.upper()} - RSI {period}'),
        paper_bgcolor='#0E1E25',
        plot_bgcolor='#0E1E25',
        showlegend=True,
        xaxis_rangeslider_visible=False,
    )


    # Mostrar los subplots
    subplots.show()

# generate_chart_with_rsi_from_params("BTCUSDT", "1d", "RSI>70")
generate_rsi_chart("BTCUSDT", "1d", "RSI>70")