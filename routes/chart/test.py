# import plotly.graph_objects as go
# from datetime import datetime
# import requests

# # Get historical market cap data for the entire cryptocurrency market
# url = 'https://api.coingecko.com/api/v3/global/market_chart'
# params = {'vs_currency': 'usd', 'days': '10'}  # Adjust the parameters as needed
# response = requests.get(url, params=params)
# data = response.json()
# print(data)

# timestamps = [datetime.utcfromtimestamp(timestamp/1000) for timestamp in data['prices']]
# market_cap_data = data['total_market_cap']

# # Create the candlestick chart
# fig = go.Figure(data=[go.Scatter(x=timestamps, y=market_cap_data, mode='lines', name='Market Cap')])

# # Customize the layout
# fig.update_layout(
#     xaxis_rangeslider_visible=False,
#     xaxis_title='Fecha',
#     yaxis_title='Capitalización de Mercado (USD)',
#     title='Capitalización de Mercado Total de Criptomonedas'
# )

# # Show the chart
# # fig.show()


# # ---------------------------------------------------------------------------------------------

# import plotly.graph_objects as go
# import pandas as pd
# from datetime import datetime, timedelta
# import numpy as np
# import requests
# from typing import Dict, Any

# # Generate random financial data
# np.random.seed(42)
# num_days = 100
# date_today = datetime.now()
# dates = [date_today - timedelta(days=i) for i in range(num_days)]
# open_prices = np.random.uniform(150, 200, num_days)
# close_prices = np.random.uniform(150, 200, num_days)
# high_prices = np.maximum(open_prices, close_prices) + np.random.uniform(0, 10, num_days)
# low_prices = np.minimum(open_prices, close_prices) - np.random.uniform(0, 10, num_days)

# # Create a DataFrame
# df_random = pd.DataFrame({'Date': dates, 'Open': open_prices, 'High': high_prices, 'Low': low_prices, 'Close': close_prices})

# # Sort DataFrame by date
# df_random = df_random.sort_values('Date')

# binance_base_url = 'https://api3.binance.com'

# # Gets historical data from Binance API
# def get_kline_data(symbol: str, interval) -> Dict[str, Any]:

#     formatted_symbol = symbol.upper()
#     formatted_interval = interval.casefold()

#     base_url = f"{binance_base_url}/api/v3/klines"
#     params = {"symbol": formatted_symbol, "limit": 50, "interval": formatted_interval}
    
#     try:
#         response = requests.get(base_url, params=params)
#         response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
#         data = response.json()
#         return data
#     except requests.exceptions.RequestException as e:
#         print(f"Failed to retrieve data: {e}")
#         return f"Failed to retrieve data: {e}"


# def create_chart():
#     fig = go.Figure(data=[go.Candlestick(x=df_random['Date'],
#                     open=df_random['Open'],
#                     high=df_random['High'],
#                     low=df_random['Low'],
#                     close=df_random['Close'])],
#                     Increasing=dict(
#                         fillcolor="mediumblue"
#                     ),
                   
#                     )

#     fig.update_layout(title='',
#                     xaxis_title='',
#                     yaxis_title='',
#                     xaxis_rangeslider_visible=False,
#                     paper_bgcolor="#282828",
#                     plot_bgcolor="#282828",
#                     xaxis=dict(
#                     showline=True,
#                     showgrid=False,
#                     tickfont=dict(
#                             color='#fff'  
#                     )
#                     ),
#                     yaxis=dict(
#                         showline=True,
#                         showgrid=False,
#                         side='right',
#                         tickfont=dict(
#                             color='#fff'  
#                         )
#                     ),
#                     )

#     fig.show()


# # create_chart()

# # ----------------------------------------------------------------------------------------------------------
    

# import requests
# import pandas as pd
# import plotly.graph_objects as go
# from datetime import datetime

# def get_total_marketcap_data(): # TOTAL MC CRYPTO - BTC MC - ETH MC = TOTAL3 
#     coinstats_url = "https://openapiv1.coinstats.app/markets"  # TOTAL MC CRYPTO ACTUAL  EL MARKET CAP DE TODAS INCL BTC ETH ALTCOINS 
#     binance_btc_url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=1" # BTC MC HISTO + ACT
#     binance_eth_url = "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1h&limit=1" # ETH MC HISTO + ACT

#     headers = {
#         "accept": "application/json",
#         "X-API-KEY": "NIb3gJkhzc3vcCc1IUANagMIxlufKRdba5kG3WJ1h6s="
#     }

#     coinstats_response = requests.get(coinstats_url, headers=headers)
#     binance_btc_response = requests.get(binance_btc_url)
#     binance_eth_response = requests.get(binance_eth_url)

#     coinstats_data = coinstats_response.json()
#     binance_btc_data = binance_btc_response.json()
#     binance_eth_data = binance_eth_response.json()

#     return coinstats_data, binance_btc_data, binance_eth_data

# def calculate_total3_market_cap(coinstats_data, binance_btc_data, binance_eth_data):
#     # Obtener datos relevantes de las respuestas
#     total_market_cap = coinstats_data["marketCap"]
#     btc_market_cap = float(binance_btc_data[0][4])
#     eth_market_cap = float(binance_eth_data[0][4])

#     # Calcular el Total3 Market Cap
#     total3_market_cap = total_market_cap - (btc_market_cap + eth_market_cap)

#     return total3_market_cap

# if __name__ == "__main__":
#     data = get_total_marketcap_data()

#     if data:
#         coinstats_data, binance_btc_data, binance_eth_data = data
#         total3_market_cap = calculate_total3_market_cap(coinstats_data, binance_btc_data, binance_eth_data)
#         print("Total3 Market Cap:", total3_market_cap)

#         # Crear un DataFrame para el gráfico
#         df = pd.DataFrame({
#             'timestamp': [datetime.utcfromtimestamp(int(binance_btc_data[0][0]) / 1000)],
#             'Total3 Market Cap': [total3_market_cap]
#         })

#         # Crear el gráfico de velas con Plotly Graph Objects
#         fig = go.Figure(data=[go.Candlestick(x=df['timestamp'],
#                                              open=df['Total3 Market Cap'],
#                                              high=df['Total3 Market Cap'],
#                                              low=df['Total3 Market Cap'],
#                                              close=df['Total3 Market Cap'])])

#         # Mostrar el gráfico
#         fig.show()

#     else:
#         print("No se pudo obtener la data necesaria.")