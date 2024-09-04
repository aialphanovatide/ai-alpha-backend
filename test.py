# import websocket
# import json
# from datetime import datetime

# # Configuración
# SYMBOL = "btcusdt"
# INTERVAL = "1m"  # Puedes cambiar esto a 5m, 15m, 30m, 1h, etc.

# def on_message(ws, message):
#     data = json.loads(message)
#     if 'k' in data:
#         kline = data['k']
#         print(f"Symbol: {kline['s']}")
#         print(f"Interval: {kline['i']}")
#         print(f"Open time: {datetime.fromtimestamp(kline['t'] / 1000)}")
#         print(f"Open: {kline['o']}")
#         print(f"High: {kline['h']}")
#         print(f"Low: {kline['l']}")
#         print(f"Close: {kline['c']}")
#         print(f"Volume: {kline['v']}")
#         print("--------------------")

# def on_error(ws, error):
#     print(f"Error: {error}")

# def on_close(ws, close_status_code, close_msg):
#     print("WebSocket connection closed")

# def on_open(ws):
#     print("WebSocket connection opened")
#     subscribe_message = {
#         "method": "SUBSCRIBE",
#         "params": [
#             f"{SYMBOL}@kline_{INTERVAL}"
#         ],
#         "id": 1
#     }
#     ws.send(json.dumps(subscribe_message))

# if __name__ == "__main__":
#     websocket.enableTrace(True)
#     ws = websocket.WebSocketApp(f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_{INTERVAL}",
#                                 on_open=on_open,
#                                 on_message=on_message,
#                                 on_error=on_error,
#                                 on_close=on_close)

#     ws.run_forever()