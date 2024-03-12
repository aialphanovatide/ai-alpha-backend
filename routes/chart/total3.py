import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def get_total_marketcap_data():
    coinstats_url = "https://openapiv1.coinstats.app/markets"
    binance_btc_url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=1000"
    binance_eth_url = "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1d&limit=1000"
    

    headers = {
        "accept": "application/json",
        "X-API-KEY": "NIb3gJkhzc3vcCc1IUANagMIxlufKRdba5kG3WJ1h6s="
    }

    coinstats_response = requests.get(coinstats_url, headers=headers)
    binance_btc_response = requests.get(binance_btc_url)
    binance_eth_response = requests.get(binance_eth_url)

    coinstats_data = coinstats_response.json()
    binance_btc_data = binance_btc_response.json()
    binance_eth_data = binance_eth_response.json()

    return coinstats_data, binance_btc_data, binance_eth_data

def calculate_total3_market_cap(coinstats_data, binance_btc_data, binance_eth_data):
    total_market_cap = coinstats_data["marketCap"]
    btc_market_caps = [float(entry[4]) for entry in binance_btc_data]
    eth_market_caps = [float(entry[4]) for entry in binance_eth_data]
    
    total3_market_caps = []
    for btc_mc, eth_mc in zip(btc_market_caps, eth_market_caps):
        total3_market_caps.append(total_market_cap - btc_mc - eth_mc)
    
    return total3_market_caps

def calculate_candlestick_data(timestamps, market_caps):
    candlestick_data = []

    for i in range(len(timestamps)):
        candlestick = {}

        candlestick['timestamp'] = timestamps[i]

        if i > 0:
            candlestick['open'] = market_caps[i - 1]
            candlestick['close'] = market_caps[i]
            candlestick['high'] = max(market_caps[i - 1], market_caps[i])
            candlestick['low'] = min(market_caps[i - 1], market_caps[i])
        else:
            candlestick['open'] = market_caps[i]
            
            candlestick['close'] = market_caps[i]
            candlestick['high'] = market_caps[i]
            candlestick['low'] = market_caps[i]

        candlestick_data.append(candlestick)

    return candlestick_data

if __name__ == "__main__":
    data = get_total_marketcap_data()

    if data:
        coinstats_data, binance_btc_data, binance_eth_data = data
        total3_market_caps = calculate_total3_market_cap(coinstats_data, binance_btc_data, binance_eth_data)
        timestamps = [pd.to_datetime(int(x[0]), unit='ms') for x in binance_btc_data]

        candlestick_data = calculate_candlestick_data(timestamps, total3_market_caps)

        # Crear el gráfico de velas con Plotly Graph Objects
        fig = go.Figure(data=[go.Candlestick(x=[entry['timestamp'] for entry in candlestick_data],
                                             open=[entry['open'] for entry in candlestick_data],
                                             high=[entry['high'] for entry in candlestick_data],
                                             low=[entry['low'] for entry in candlestick_data],
                                             close=[entry['close'] for entry in candlestick_data],
                                             increasing_line_color= 'green',  # Color para velas alcistas
                                             decreasing_line_color= 'red'      # Color para velas bajistas
                                             )])

        # Ajustar el diseño del gráfico
        fig.update_layout(title='Total3 Market Cap Candlestick',
                          yaxis_title='Total3 Market Cap',
                          xaxis_title='Date',
                          xaxis_rangeslider_visible=False)

        # Mostrar el gráfico
        fig.show()

    else:
        print("No se pudo obtener la data necesaria.")
