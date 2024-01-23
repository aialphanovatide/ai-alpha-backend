import plotly.graph_objects as go
from datetime import datetime
import requests

# Get historical market cap data for the entire cryptocurrency market
url = 'https://api.coingecko.com/api/v3/global/market_chart'
params = {'vs_currency': 'usd', 'days': '10'}  # Adjust the parameters as needed
response = requests.get(url, params=params)
data = response.json()
print(data)

timestamps = [datetime.utcfromtimestamp(timestamp/1000) for timestamp in data['prices']]
market_cap_data = data['total_market_cap']

# Create the candlestick chart
fig = go.Figure(data=[go.Scatter(x=timestamps, y=market_cap_data, mode='lines', name='Market Cap')])

# Customize the layout
fig.update_layout(
    xaxis_rangeslider_visible=False,
    xaxis_title='Fecha',
    yaxis_title='Capitalización de Mercado (USD)',
    title='Capitalización de Mercado Total de Criptomonedas'
)

# Show the chart
fig.show()
