import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import requests
from typing import Dict, Any

# Generate random financial data
np.random.seed(42)
num_days = 100
date_today = datetime.now()
dates = [date_today - timedelta(days=i) for i in range(num_days)]
open_prices = np.random.uniform(150, 200, num_days)
close_prices = np.random.uniform(150, 200, num_days)
high_prices = np.maximum(open_prices, close_prices) + np.random.uniform(0, 10, num_days)
low_prices = np.minimum(open_prices, close_prices) - np.random.uniform(0, 10, num_days)

# Create a DataFrame
df_random = pd.DataFrame({'Date': dates, 'Open': open_prices, 'High': high_prices, 'Low': low_prices, 'Close': close_prices})

# Sort DataFrame by date
df_random = df_random.sort_values('Date')

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


def create_chart():
    fig = go.Figure(data=[go.Candlestick(x=df_random['Date'],
                    open=df_random['Open'],
                    high=df_random['High'],
                    low=df_random['Low'],
                    close=df_random['Close'])],
                    Increasing=dict(
                        fillcolor="mediumblue"
                    ),
                   
                    )

    fig.update_layout(title='',
                    xaxis_title='',
                    yaxis_title='',
                    xaxis_rangeslider_visible=False,
                    paper_bgcolor="#282828",
                    plot_bgcolor="#282828",
                    xaxis=dict(
                    showline=True,
                    showgrid=False,
                    tickfont=dict(
                            color='#fff'  
                    )
                    ),
                    yaxis=dict(
                        showline=True,
                        showgrid=False,
                        side='right',
                        tickfont=dict(
                            color='#fff'  
                        )
                    ),
                    )

    fig.show()


create_chart()
