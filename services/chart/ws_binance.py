import websocket
import json
import time
import threading
import pandas as pd
from datetime import datetime

class BinanceWebSocket:
    def __init__(self, symbol, interval, update_callback=None):
        self.symbol = symbol.lower()
        self.interval = interval
        self.update_callback = update_callback
        self.ws = None
        self.ws_thread = None
        self.is_connected = False
        self.current_price = None
        
        print(f"Initialized BinanceWebSocket for {self.symbol.upper()} {self.interval}")
    def _on_message(self, ws, message):
        try:
            print("Received message:", message)  # Debug: Print the raw message
            data = json.loads(message)
            print("Parsed JSON data:", data)  # Debug: Print the parsed JSON data

            if 'k' in data:  # Check if 'k' exists in the message
                kline = data['k']
                print("Kline data:", kline)  # Debug: Print the kline data

                # Extract relevant information
                open_time = pd.to_datetime(kline['t'], unit='ms')
                open_price = float(kline['o'])
                high_price = float(kline['h'])
                low_price = float(kline['l'])
                close_price = float(kline['c'])
                volume = float(kline['v'])
                close_time = pd.to_datetime(kline['T'], unit='ms')
                quote_asset_volume = float(kline['q'])
                number_of_trades = int(kline['n'])
                taker_buy_base_volume = float(kline['V'])
                taker_buy_quote_volume = float(kline['Q'])

                # Create DataFrame
                df = pd.DataFrame([{
                    'Open Time': open_time,
                    'Open': open_price,
                    'High': high_price,
                    'Low': low_price,
                    'Close': close_price,
                    'Volume': volume,
                    'Close Time': close_time,
                    'Quote Asset Volume': quote_asset_volume,
                    'Number of Trades': number_of_trades,
                    'Taker Buy Base Volume': taker_buy_base_volume,
                    'Taker Buy Quote Volume': taker_buy_quote_volume
                }])

                print("DataFrame created:", df)  # Debug: Print the DataFrame

                # Update current price
                self.current_price = close_price

                if self.update_callback and callable(self.update_callback):
                    print("Calling update_callback with DataFrame")  # Debug: Before calling the callback
                    self.update_callback(df)
            else:
                print("Waiting for kline data...")

        except Exception as e:
            print(f"Error processing message: {e}")
            print("Exception type:", type(e))  # Debug: Print the type of exception


    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        self.is_connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket closed. Status: {close_status_code}, Message: {close_msg}")
        self.is_connected = False

    def _on_open(self, ws):
        print("WebSocket connection opened")
        self.is_connected = True
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": [f"{self.symbol}@kline_{self.interval}"],
            "id": 1
        }
        ws.send(json.dumps(subscribe_message))

    def start(self):
        socket = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{self.interval}"
        self.ws = websocket.WebSocketApp(socket,
                                         on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close,
                                         on_open=self._on_open)
        
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def stop(self):
        if self.ws:
            self.ws.close()
        if self.ws_thread:
            self.ws_thread.join(timeout=1)
        print("WebSocket connection closed")

    def update_symbol(self, new_symbol):
        if new_symbol.lower() != self.symbol:
            self.symbol = new_symbol.lower()
            if self.is_connected:
                self.stop()
                self.start()

    def update_interval(self, new_interval):
        if new_interval != self.interval:
            self.interval = new_interval
            if self.is_connected:
                self.stop()
                self.start()

    def get_current_price(self):
        return self.current_price


# if __name__ == '__main__':
#     def update_callback(df):
#         print("Callback received data:")
#         print(df)
#         print(f"Current price: {ws.get_current_price()}")

#     ws = BinanceWebSocket('BTCUSDT', '1m')
#     ws.start()
    
#     try:
#         time.sleep(10)  # Run for 10 seconds
#         print("Updating symbol to ETHUSDT")
#         ws.update_symbol('ETHUSDT')
#         time.sleep(10)  # Run for another 10 seconds
#         print("Updating interval to 5m")
#         ws.update_interval('5m')
#         time.sleep(10)  # Run for another 10 seconds
#     except KeyboardInterrupt:
#         print("Closing WebSocket connection...")
#     finally:
#         ws.stop()