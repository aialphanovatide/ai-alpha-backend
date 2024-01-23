import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def get_total_marketcap_data(): # TOTAL MC CRYPTO - BTC MC - ETH MC = TOTAL3 
    coinstats_url = "https://openapiv1.coinstats.app/markets"  # TOTAL MC CRYPTO ACTUAL  EL MARKET CAP DE TODAS INCL BTC ETH ALTCOINS 
    binance_btc_url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=1" # BTC MC HISTO + ACT
    binance_eth_url = "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1h&limit=1" # ETH MC HISTO + ACT

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
    # Obtener datos relevantes de las respuestas
    total_market_cap = coinstats_data["marketCap"]
    btc_market_cap = float(binance_btc_data[0][4])
    eth_market_cap = float(binance_eth_data[0][4])

    # Calcular el Total3 Market Cap
    total3_market_cap = total_market_cap - (btc_market_cap + eth_market_cap)

    return total3_market_cap

if __name__ == "__main__":
    data = get_total_marketcap_data()

    if data:
        coinstats_data, binance_btc_data, binance_eth_data = data
        total3_market_cap = calculate_total3_market_cap(coinstats_data, binance_btc_data, binance_eth_data)
        print("Total3 Market Cap:", total3_market_cap)

        # Crear un DataFrame para el gráfico
        df = pd.DataFrame({
            'timestamp': [datetime.utcfromtimestamp(int(binance_btc_data[0][0]) / 1000)],
            'Total3 Market Cap': [total3_market_cap]
        })

        # Crear el gráfico de velas con Plotly Graph Objects
        fig = go.Figure(data=[go.Candlestick(x=df['timestamp'],
                                             open=df['Total3 Market Cap'],
                                             high=df['Total3 Market Cap'],
                                             low=df['Total3 Market Cap'],
                                             close=df['Total3 Market Cap'])])

        # Mostrar el gráfico
        fig.show()

    else:
        print("No se pudo obtener la data necesaria.")