import json
import websocket
import threading
import pandas as pd

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
        """
        Handles incoming messages from the Binance WebSocket.

        This method parses the incoming JSON message, extracts candlestick data,
        updates the current price, and calls the update callback function if available.
        It handles both closed and open candles, providing different messages for each case.

        Args:
            ws (websocket.WebSocketApp): The WebSocket client instance.
            message (str): The incoming JSON message from the Binance WebSocket.
        """
        try:
            data = json.loads(message)
            if 'k' in data:
                kline = data['k']
                
                # Extract relevant information
                open_time = pd.to_datetime(kline['t'], unit='ms')
                close_time = pd.to_datetime(kline['T'], unit='ms')
                is_closed = kline['x']  # Whether this kline is closed
                
                # Create DataFrame with the new data
                new_data = pd.DataFrame([{
                    'Open Time': open_time,
                    'Close Time': close_time,
                    'Open': float(kline['o']),
                    'High': float(kline['h']),
                    'Low': float(kline['l']),
                    'Close': float(kline['c']),
                    'Volume': float(kline['v'])
                }])

                # Update current price
                self.current_price = float(kline['c'])

                if is_closed:
                    # This is a new candle, append it to the data
                    print(f"\nNew closed kline for {self.symbol.upper()} ({self.interval})")
                    if self.update_callback and callable(self.update_callback):
                        self.update_callback(new_data, is_new_candle=True)
                else:
                    # This is an update to the current candle
                    print(f"\nUpdating current kline for {self.symbol.upper()} ({self.interval})")
                    
                    if self.update_callback and callable(self.update_callback):
                        self.update_callback(new_data, is_new_candle=False)

                print(f"Time: {open_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Open: {new_data['Open'][0]:.2f}")
                print(f"High: {new_data['High'][0]:.2f}")
                print(f"Low: {new_data['Low'][0]:.2f}")
                print(f"Close: {new_data['Close'][0]:.2f}")
                print(f"Volume: {new_data['Volume'][0]:.2f}")
                print(f"Is Closed: {is_closed}")

            else:
                print("Waiting for kline data...")

        except Exception as e:
            print(f"Error processing message: {e}")


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
    



# import time
# from datetime import datetime
# import pandas as pd

# def update_callback(data: pd.DataFrame, is_new_candle: bool):
#     """
#     Callback function to handle updates from the WebSocket
#     """
#     bar_type = "NEW" if is_new_candle else "UPDATE"
#     print(f"\n=== {bar_type} CANDLE RECEIVED ===")
#     print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#     print(f"Open: {data['Open'].values[0]:.2f}")
#     print(f"High: {data['High'].values[0]:.2f}")
#     print(f"Low: {data['Low'].values[0]:.2f}")
#     print(f"Close: {data['Close'].values[0]:.2f}")
#     print(f"Volume: {data['Volume'].values[0]:.2f}")
#     print("=" * 30)

# def test_binance_websocket():
#     """
#     Test function demonstrating various features of BinanceWebSocket
#     """
#     # Initialize WebSocket with BTC/USDT pair and 1-minute interval
#     ws = BinanceWebSocket(
#         symbol="btcusdt",
#         interval="1m",
#         update_callback=update_callback
#     )

#     try:
#         # Start the WebSocket connection
#         print("\nStarting WebSocket connection...")
#         ws.start()

#         # Wait for connection to establish
#         time.sleep(2)

#         # Test current price
#         print("\nTesting current price...")
#         for _ in range(3):
#             price = ws.get_current_price()
#             print(f"Current BTC price: ${price:.2f}" if price else "Waiting for price data...")
#             time.sleep(1)

#         # Test symbol update
#         print("\nTesting symbol update...")
#         ws.update_symbol("ethusdt")
#         time.sleep(5)

#         # Test interval update
#         print("\nTesting interval update...")
#         ws.update_interval("5m")
#         time.sleep(5)

#         # Let it run for a while to receive updates
#         print("\nWaiting for updates (30 seconds)...")
#         time.sleep(30)

#     except KeyboardInterrupt:
#         print("\nTest interrupted by user")
#     except Exception as e:
#         print(f"\nAn error occurred: {e}")
#     finally:
#         # Clean up
#         print("\nCleaning up...")
#         ws.stop()
#         print("Test completed")

# if __name__ == "__main__":
#     # Import the BinanceWebSocket class
#     from ws_binance import BinanceWebSocket
    
#     print("Starting Binance WebSocket Test")
#     print("=" * 50)
#     print("This test will:")
#     print("1. Connect to Binance WebSocket")
#     print("2. Display real-time price updates")
#     print("3. Test symbol switching")
#     print("4. Test interval switching")
#     print("5. Run for 30 seconds")
#     print("=" * 50)
    
#     test_binance_websocket()