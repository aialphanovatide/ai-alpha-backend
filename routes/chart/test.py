import asyncio
import websockets
import json
import ccxt
from datetime import datetime

exchange = ccxt.binance()

async def get_ohlcv_data(symbol, timeframe):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=30)
        return [
            {
                'timestamp': candle[0],
                'open': candle[1],
                'high': candle[2],
                'low': candle[3],
                'close': candle[4]
            } for candle in ohlcv
        ]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

async def print_crypto_data():
    symbol = "BTC/USDT" 
    timeframes = ['1h', '4h', '1d', '1w']
    
    while True:
        print(f"\n--- Data Update at {datetime.now()} ---")
        for timeframe in timeframes:
            data = await get_ohlcv_data(symbol, timeframe)
            if data:
                print(f"\nSymbol: {symbol}, Timeframe: {timeframe}")
                print(f"Last 30 periods:")
                for candle in data:
                    print(f"  Timestamp: {datetime.fromtimestamp(candle['timestamp']/1000)}")
                    print(f"  Open: {candle['open']:.2f}")
                    print(f"  High: {candle['high']:.2f}")
                    print(f"  Low: {candle['low']:.2f}")
                    print(f"  Close: {candle['close']:.2f}")
                    print("  ---")
            else:
                print(f"No data available for {symbol} {timeframe}")
        
        print(f"\nWaiting for 60 seconds before next update...")
        await asyncio.sleep(60)

async def main():
    print("Starting data printing...")
    await print_crypto_data()

if __name__ == "__main__":
    asyncio.run(main())