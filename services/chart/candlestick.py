"""
Dynamic Candlestick chart with live data.  Features:

- Multiple symbols and timeframes on the same chart.
- Indicators (moving averages, RSI, MACD, Bollinger Bands, etc.).
- Drawing tools (trendlines, Fibonacci retracement, etc.).
- Historical and live data display.
- Default symbol: BTC/USDT, default timeframe: 1D.
- Four default resistance and support levels.

Bokeh library used for charting: https://docs.bokeh.org/en/latest/docs/examples/topics/timeseries/candlestick.html
"""

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
            data = json.loads(message)
            if 'k' in data: #check if 'k' exists in the message
                kline = data['k']

                # Extract relevant information
                open_time = pd.to_datetime(kline['t'], unit='ms')
                open_price = float(kline['o'])
                high_price = float(kline['h'])
                low_price = float(kline['l'])
                close_price = float(kline['c'])
                volume = float(kline['v'])
                close_time = pd.to_datetime(kline['T'], unit='ms')

                # Create DataFrame
                df = pd.DataFrame([{
                    'Open Time': open_time,
                    'Open': open_price,
                    'High': high_price,
                    'Low': low_price,
                    'Close': close_price,
                    'Volume': volume,
                    'Close Time': close_time,
                }])

                print(f"\nNew kline data for {self.symbol.upper()} ({self.interval}):")
                print(f"Open Time: {df['Open Time'][0].strftime('%Y-%m-%d %H:%M:%S')}, Open: {df['Open'][0]:.2f}, High: {df['High'][0]:.2f}, Low: {df['Low'][0]:.2f}, Close: {df['Close'][0]:.2f}, Volume: {df['Volume'][0]:.2f}")

                # Update current price
                self.current_price = close_price

                if self.update_callback and callable(self.update_callback):
                    self.update_callback(df)
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
    

import os
import requests
import numpy as np
import pandas as pd
import bokeh.plotting as bk
from typing import List, Literal
from bokeh.resources import CDN
from bokeh.embed import file_html, components
from bokeh.models import (
    Label, ColumnDataSource, HoverTool, CrosshairTool, 
    NumeralTickFormatter, CDSView, BooleanFilter, DataRange1d, 
    ImageURL, CustomJS, Band, DatetimeTickFormatter, Row, Button
)


class ChartSettings:
    """
    Configuration settings for the candlestick chart.
    """
    def __init__(self, 
                 symbol: str = 'BTCUSDT',
                 interval: str = '1d',
                 resistance_levels: List[float] = [93000, 95000, 97000, 100000],
                 support_levels: List[float] = [50000, 60000, 50000, 55000, 65000],
                 theme: Literal['dark', 'light'] = 'light',
                 background_color_dark: str = '#171717',
                 background_color_light: str = '#FFFFFF',
                 border_fill_color_dark: str = '#171717',
                 border_fill_color_light: str = '#FFFFFF',
                 text_color_dark: str = '#FFFFFF',
                 text_color_light: str = '#000000',
                 grid_color: str = '#2A2A2A',
                 num_candles: int = 50,
                 bullish_color: str = '#09C283',
                 bearish_color: str = '#E93334',
                 sma_50_color: str = '#2962FF',
                 sma_200_color: str = '#FF6D00',
                 support_label_color: str = '#D82A2B',
                 resistance_label_color: str = '#2DDA99',
                 axis_line_color: str = '#565656',
                 title_font_size: str = '16px',
                 axis_font_size: str = '12px',
                 label_font_size: str = '10px'):

        self.symbol = symbol
        self.interval = interval
        self.resistance_levels = resistance_levels
        self.support_levels = support_levels
        self.theme = theme
        self.background_color_dark = background_color_dark
        self.background_color_light = background_color_light
        self.border_fill_color_dark = border_fill_color_dark
        self.border_fill_color_light = border_fill_color_light
        self.text_color_dark = text_color_dark
        self.text_color_light = text_color_light
        self.grid_color = grid_color
        self.num_candles = num_candles
        self.bullish_color = bullish_color
        self.bearish_color = bearish_color
        self.sma_50_color = sma_50_color
        self.sma_200_color = sma_200_color
        self.support_label_color = support_label_color
        self.resistance_label_color = resistance_label_color
        self.axis_line_color = axis_line_color
        self.title_font_size = title_font_size
        self.axis_font_size = axis_font_size
        self.label_font_size = label_font_size

    @property
    def background_color(self) -> str:
        """Get background color based on current theme"""
        return self.background_color_dark if self.theme == 'dark' else self.background_color_light

    @property
    def border_fill_color(self) -> str:
        """Get border fill color based on current theme"""
        return self.border_fill_color_dark if self.theme == 'dark' else self.border_fill_color_light

    @property
    def text_color(self) -> str:
        """Get text color based on current theme"""
        return self.text_color_dark if self.theme == 'dark' else self.text_color_light


class SMASettings:
    """Configuration settings for Simple Moving Averages.

    Args:
        enabled (bool, optional): Whether to enable SMA calculation. Defaults to True.
        periods (List[int], optional): List of periods for SMA calculations. Defaults to [50, 200].
        colors (List[str], optional): List of colors for each SMA line. Defaults to ['#2962FF', '#FF6D00'].
        line_width (float, optional): Width of the SMA lines. Defaults to 1.5.
    """
    def __init__(self, 
                 enabled: bool = True,
                 periods: List[int] = [50, 200],
                 colors: List[str] = ['#2962FF', '#FF6D00'],
                 line_width: float = 1.5):
        self.enabled = enabled
        self.periods = periods
        self.colors = colors
        self.line_width = line_width


class RSISettings:
    """Configuration settings for RSI indicator.

    Args:
        enabled (bool, optional): Whether to enable RSI calculation. Defaults to True.
        period (int, optional): Period for RSI calculation. Defaults to 14.
        overbought (float, optional): Overbought level. Defaults to 70.
        oversold (float, optional): Oversold level. Defaults to 30.
        level_color (str, optional): Color of overbought/oversold levels. Defaults to '#202020'.
        line_color (str, optional): Color of RSI line. Defaults to '#6A0DAD'.
        line_width (float, optional): Width of RSI line. Defaults to 1.
        height (int, optional): Height of the RSI panel. Defaults to 150.
    """
    def __init__(self,
                 enabled: bool = True,
                 period: int = 14,
                 overbought: float = 70,
                 oversold: float = 30,
                 level_color: str = '#202020',
                 line_color: str = '#6A0DAD',
                 line_width: float = 1,
                 height: int = 150):
        self.enabled = enabled
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.level_color = level_color
        self.line_color = line_color
        self.line_width = line_width
        self.height = height


class ChartWidget:
    BASE_URL = 'https://api3.binance.com/api/v3'
    
    def __init__(self, config: ChartSettings = ChartSettings(), sma: SMASettings = SMASettings(), rsi: RSISettings = RSISettings()):
        """
        Initializes the ChartWidget with configuration settings for the chart, 
        Simple Moving Averages (SMA), and Relative Strength Index (RSI) indicators.

        Args:
            config (ChartSettings): Configuration settings for the chart. Defaults to ChartSettings().
            sma (SMASettings): Configuration settings for SMA indicators. Defaults to SMASettings().
            rsi (RSISettings): Configuration settings for RSI indicator. Defaults to RSISettings().
        """
        self.config = config
        self.sma = sma
        self.rsi = rsi
        self.symbol = self.config.symbol  # Default symbol from settings
        self.interval = self.config.interval  # Default interval from settings

        self.source: ColumnDataSource = None  # Store ColumnDataSource for updates
        self.df : pd.DataFrame = None  # Store DataFrame for updates

        self.timeframe_mapping = {
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080
        }
        
        # WebSocket handler
        self.websocket = None
        self._running = False
        self._thread = None

    def update_chart_data(self, df):
        """Handle incoming WebSocket data updates"""
        if not self.source:
            return
        
        # Extract the latest row of data from the DataFrame
        latest_data = df.iloc[0]
        
        # Convert timestamp to datetime
        timestamp = latest_data['Open Time']
        
        # Update existing candle or add new one
        if latest_data['Close Time'] <= pd.Timestamp.now():
            # Add new candle
            new_data = {
                'Open Time': [timestamp],
                'Open': [latest_data['Open']],
                'High': [latest_data['High']],
                'Low': [latest_data['Low']],
                'Close': [latest_data['Close']],
                'Volume': [latest_data['Volume']]
            }
            
            # Convert the new data to a dictionary with lists for each column
            new_data_dict = new_data.to_dict(orient='list')
            
            # Stream the new data to the source
            self.source.stream(new_data_dict, rollover=len(self.source.data['Open Time']))
                
        else:
            # Update current candle
            last_idx = -1
            self.source.data['High'][last_idx] = max(self.source.data['High'][last_idx], latest_data['High'])
            self.source.data['Low'][last_idx] = min(self.source.data['Low'][last_idx], latest_data['Low'])
            self.source.data['Close'][last_idx] = latest_data['Close']
            self.source.data['Volume'][last_idx] = latest_data['Volume']
        
        # Trigger source update
        self.source.change.emit()

    def start_live_updates(self):
        """Start receiving live updates"""
        if self.websocket is None:
            self.websocket = BinanceWebSocket(
                symbol=self.symbol,
                interval=self.interval,
                # update_callback=self.update_chart_data
            )
            self.websocket.start()
            
            # Start the keep-alive thread
            self._running = True
            self._thread = threading.Thread(target=self._keep_alive)
            self._thread.daemon = True
            self._thread.start()

    def stop_live_updates(self):
        """Stop receiving live updates"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        if self.websocket:
            self.websocket.stop()
            self.websocket = None

    def _keep_alive(self):
        """Keep the WebSocket connection alive"""
        while self._running:
            time.sleep(1)  # Check every second
            if not self.websocket.is_connected:
                print("WebSocket disconnected, attempting to reconnect...")
                self.websocket.start()

    def get_historical_data(self, 
                   symbol: str = 'BTCUSDT', 
                   interval: str = '1d', 
                   limit: int = 500) -> pd.DataFrame:
        """
        Fetch kline (candlestick) data directly from Binance API
        
        :param symbol: Trading pair symbol
        :param interval: Timeframe interval
        :param limit: Number of data points to retrieve
        :return: DataFrame with kline data
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(f'{self.BASE_URL}/klines', params=params)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}, {response.text}")
        
        data = response.json()
        
        # Extract only the needed columns
        extracted_data = [{'Open Time': item[0], 'Open': item[1], 'High': item[2], 'Low': item[3], 'Close': item[4], 'Volume': item[5], 'Close Time': item[6]} for item in data]

        # Convert to DataFrame
        df = pd.DataFrame(extracted_data)
        
        # Convert numeric columns
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        
        # Convert timestamps
        df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
        
        return df

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate and add basic technical indicators to the input DataFrame.

        Args:
            df (pd.DataFrame): DataFrame containing price data with a 'Close' column.

        Returns:
            pd.DataFrame: DataFrame with added 'SMA_50', 'SMA_200', and 'RSI' columns.
        """
        if self.sma.enabled:
            for period in self.sma.periods:
                self.df[f'SMA_{period}'] = self.df['Close'].rolling(window=period).mean()
        
        if self.rsi.enabled:
            # Calculate RSI
            delta = self.df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi.period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi.period).mean()
            
            rs = gain / loss
            self.df['RSI'] = 100 - (100 / (1 + rs))
        
        return self.df

    def create_candlestick_chart(self) -> bk.figure:
        # Fetch historical data and populate self.df
        self.df = self.get_historical_data(self.symbol, self.interval)
        
        # Calculate technical indicators
        self.df = self.calculate_technical_indicators(self.df)

        # Create ColumnDataSource
        self.source = ColumnDataSource(self.df)

        # Calculate initial ranges based on the number of candles
        time_min = self.df['Open Time'].iloc[-self.config.num_candles]
        time_max = self.df['Open Time'].max()

        # X Data Range
        x_range = DataRange1d(
            start=time_min,
            end=time_max,
            bounds=(self.df['Open Time'].min(), self.df['Open Time'].max())  # Allow scrolling to full range
        )

        # Add a callback to enforce x-range limits
        x_range_callback = CustomJS(
            args=dict(
                x_range=x_range,
                min_bound=self.df['Open Time'].min(),
                max_bound=self.df['Open Time'].max()
            ),
            code="""
            // Ensure start is not before min_bound
            if (x_range.start < min_bound) {
                const delta = min_bound - x_range.start;
                x_range.start = min_bound;
                x_range.end = Math.min(x_range.end + delta, max_bound);
            }
            
            // Ensure end is not after max_bound
            if (x_range.end > max_bound) {
                const delta = x_range.end - max_bound;
                x_range.end = max_bound;
                x_range.start = Math.max(x_range.start - delta, min_bound);
            }
            """
        )

        # Attach the callback to both start and end changes
        x_range.js_on_change('start', x_range_callback)
        x_range.js_on_change('end', x_range_callback)

        callback, y_range = self._calculate_y_range(time_min, time_max)

        # Create figure
        self.p = bk.figure(
            x_axis_type='datetime',
            sizing_mode='stretch_both',
            background_fill_color=self.config.background_color,
            border_fill_color=self.config.border_fill_color,
            toolbar_location=None,
            y_axis_location="right",
            x_range=x_range,
            y_range=y_range,
            tools="xpan",
            active_drag="xpan"
        )

        # Trigger initial y-axis range calculation
        self.p.js_on_event('document_ready', callback)
        
        # Attach the callback to x_range changes
        x_range.js_on_change('start', callback)
        x_range.js_on_change('end', callback)

        # Style the figure
        self.style_figure(self.p)

        # Add candlesticks
        self.add_candlesticks(self.p)

        # Add current price line and label
        self.add_current_price_elements(self.p)

        # Support and Resistance levels
        self.add_support_resistance_levels(self.p)

        # Add technical indicators
        chart = self.add_technical_indicators(self.p)

        html = file_html(chart, CDN, "Candlestick Chart")

        # Save the chart to an HTML file
        chart_path = "templates/chart.html"
        with open(chart_path, "w") as f:
            f.write(html)

        return self.p

    def _calculate_y_range(self, time_min, time_max):

        # Calculate initial y-range values
        visible_df = self.df[self.df['Open Time'].between(time_min, time_max)]
        min_price = visible_df['Low'].min()
        max_price = visible_df['High'].max()
        padding = (max_price - min_price) * 0.05

        # Create DataRange1d with initial values
        y_range_end = max_price + padding if not self.config.resistance_levels and not self.config.support_levels else max(self.config.resistance_levels + self.config.support_levels) + padding
        y_range = DataRange1d(
            start=min_price - padding,
            end=y_range_end,
            follow='end'
        )

        # Callback to update y-range based on visible x-range
        callback = CustomJS(
            args=dict(y_range=y_range, source=self.source, initial_start=time_min, initial_end=time_max),
            code="""
            function updateYRange(start, end) {
                const data = source.data;
                const time = data['Open Time'];
                
                // Find indices of visible points
                let visible_indices = [];
                for (let i = 0; i < time.length; i++) {
                    if (time[i] >= start && time[i] <= end) {
                        visible_indices.push(i);
                    }
                }
                
                // Calculate min and max of visible points
                let min_price = Infinity;
                let max_price = -Infinity;
                
                for (let i of visible_indices) {
                    min_price = Math.min(min_price, data['Low'][i]);
                    max_price = Math.max(max_price, data['High'][i]);
                }
                
                // Add some padding (5%)
                const padding = (max_price - min_price) * 0.05;
                y_range.start = min_price - padding;
                y_range.end = max_price + padding;
            }
            
            // Only update on range changes
            updateYRange(cb_obj.start, cb_obj.end);
            """
        )

        return callback, y_range

    def style_figure(self, p):
        p.outline_line_color = None
        p.xaxis.major_label_text_color = self.config.text_color
        p.xaxis.axis_line_color = self.config.axis_line_color
        p.xaxis.major_tick_line_color = self.config.axis_line_color
        p.xaxis.minor_tick_line_color = None
        p.yaxis.major_label_text_color = self.config.text_color
        p.yaxis.axis_line_color = self.config.axis_line_color
        p.yaxis.major_tick_line_color = self.config.axis_line_color
        p.yaxis.minor_tick_line_color = None
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None
        p.yaxis.formatter = NumeralTickFormatter(format="$0,0.00")
        p.xaxis.formatter = DatetimeTickFormatter(
            milliseconds="%Y-%m-%d", seconds="%Y-%m-%d", minutes="%Y-%m-%d",
            hours="%Y-%m-%d", days="%Y-%m-%d", months="%Y-%m-%d", years="%Y-%m-%d"
        )
        # Disable zoom
        p.toolbar.active_scroll = None  # Disable wheel zoom

    def add_candlesticks(self, p):
        inc = self.source.data['Close'] > self.source.data['Open']
        dec = self.source.data['Open'] > self.source.data['Close']
        
        # Hover tool
        hover = HoverTool(
            tooltips="""
                <div style="background-color: {self.config.background_color}; padding: 8px;">
                    <div style="color: {self.config.text_color}; font-size: {self.config.label_font_size}; display: grid; grid-template-columns: auto auto; gap: 8px;">
                        <div style="font-weight: bold;">Date:</div>
                        <div>@{Open Time}{%F}</div>
                        <div style="font-weight: bold;">Open:</div>
                        <div>$@Open{0,0.00}</div>
                        <div style="font-weight: bold;">Close:</div>
                        <div>$@Close{0,0.00}</div>
                        <div style="font-weight: bold;">High:</div>
                        <div>$@High{0,0.00}</div>
                        <div style="font-weight: bold;">Low:</div>
                        <div>$@Low{0,0.00}</div>
                        <div style="font-weight: bold;">Volume:</div>
                        <div>@Volume{0,0.00}</div>
                    </div>
                </div>
            """,
            formatters={'@{Open Time}': 'datetime'},
            renderers=[],
            point_policy='follow_mouse'
        )

        # Candlestick bars (wicks) - keep them thin
        w1 = p.segment(x0='Open Time', 
                       x1='Open Time', 
                       y0='Low', 
                       y1='High',
                       color=self.config.bullish_color, 
                       line_width=1, 
                       source=self.source, 
                       view=CDSView(filter=BooleanFilter(inc))
                       )
        
        w2 = p.segment(x0='Open Time', 
                       x1='Open Time', 
                       y0='Low', 
                       y1='High',
                       color=self.config.bearish_color, 
                       line_width=1, 
                       source=self.source, 
                       view=CDSView(filter=BooleanFilter(dec))
                       )
                       
        # Bullish (increasing) candlesticks - hollow with green outline
        b1 = p.vbar(x='Open Time', 
                    width=25, 
                    top='Open', 
                    bottom='Close',
                    fill_color=self.config.bullish_color, 
                    line_color=self.config.bullish_color, 
                    source=self.source,
                    view=CDSView(filter=BooleanFilter(inc)), 
                    fill_alpha=0.0, 
                    line_width=8)
        
        # Bearish (decreasing) candlesticks - filled red
        b2 = p.vbar(x='Open Time', 
                    width=25, 
                    top='Open', 
                    bottom='Close',
                    fill_color=self.config.bearish_color, 
                    line_color=self.config.bearish_color, 
                    source=self.source,
                    view=CDSView(filter=BooleanFilter(dec)), 
                    fill_alpha=0.0, 
                    line_width=8
                    )
        
        # Add only candlestick renderers to hover tool
        hover.renderers = [w1, w2, b1, b2]
        
        # Crosshair Cursor
        crosshair = CrosshairTool(
            line_color=self.config.axis_line_color,      
            line_alpha=0.3,         
            line_width=1            
        )

        p.add_tools(hover, crosshair)

    def add_technical_indicators(self, p):
        if self.sma.enabled:
            for period, color in zip(self.sma.periods, self.sma.colors):
                p.line('Open Time', 
                       f'SMA_{period}', 
                       line_color=color, 
                       legend_label=f'SMA {period}',
                       line_width=self.sma.line_width, 
                       source=self.source)

            # Modify the legend configuration
            self.p.add_layout(self.p.legend[0], 'above')  # Move legend above the chart
            self.p.legend.orientation = "horizontal"  # Make legend horizontal
            self.p.legend.spacing = 20  # Add some spacing between legend items
            self.p.legend.margin = 0  # Remove margin
            self.p.legend.padding = 5  # Add some padding inside the legend
            self.p.legend.label_text_font_size = "8pt"  # Adjust font size if needed
            self.p.legend.border_line_alpha = 0  # Remove border
            self.p.legend.background_fill_alpha = 0  # Make background transparent
            self.p.legend.location = "top_left"
            self.p.legend.border_line_color = self.config.text_color
            self.p.legend.background_fill_color = self.config.background_color
            self.p.legend.label_text_color = self.config.text_color
            self.p.legend.click_policy = "hide"


        if self.rsi.enabled:
            # Create a separate figure for RSI
            rsi_figure = bk.figure(
                x_axis_type='datetime',
                x_range=p.x_range,  # Share x-axis with the main plot
                y_range=(0, 100),
                height=self.rsi.height,
                sizing_mode='stretch_width',
                background_fill_color=self.config.background_color,
                border_fill_color=self.config.border_fill_color,
                toolbar_location=None,
                tools="xpan",  # Only allow panning on x-axis
                active_drag="xpan",  # Make pan the active drag tool
                y_axis_location="right",
                min_border_top=10,
                min_border_bottom=10
            )

            rsi_figure.xaxis.formatter = DatetimeTickFormatter(
                milliseconds="%Y-%m-%d",
                seconds="%Y-%m-%d",
                minutes="%Y-%m-%d",
                hours="%Y-%m-%d",
                days="%Y-%m-%d",
                months="%Y-%m-%d",
                years="%Y-%m-%d"
            )

            # Plot the RSI line
            rsi_figure.line(
                x='Open Time', 
                y='RSI', 
                line_color=self.rsi.line_color,
                line_width=self.rsi.line_width,
                source=self.source
            )

            # Add overbought/oversold lines
            rsi_figure.line(
                x=[self.df['Open Time'].min(), self.df['Open Time'].max()], 
                y=[self.rsi.overbought, self.rsi.overbought], 
                line_color=self.rsi.level_color, 
                line_dash='dashed', 
                line_width=self.rsi.line_width,
                line_alpha=0.5
            )
            rsi_figure.line(
                x=[self.df['Open Time'].min(), self.df['Open Time'].max()], 
                y=[self.rsi.oversold, self.rsi.oversold], 
                line_color=self.rsi.level_color, 
                line_dash='dashed', 
                line_width=self.rsi.line_width,
                line_alpha=0.5
            )

            # Style RSI panel
            rsi_figure.xaxis.visible = False
            rsi_figure.yaxis.visible = True
            rsi_figure.yaxis.axis_line_color = None
            rsi_figure.yaxis.major_label_text_color = self.config.text_color
            rsi_figure.yaxis.major_label_text_font_size = self.config.label_font_size
            rsi_figure.yaxis.ticker = [self.rsi.oversold, self.rsi.overbought]
            rsi_figure.ygrid.grid_line_color = None
            rsi_figure.grid.grid_line_color = None
            rsi_figure.outline_line_color = None

            # Combine the main plot and RSI plot
            layout = bk.column([p, rsi_figure], sizing_mode='stretch_both', spacing=0)
            return layout
        else:
            return p

    def add_current_price_elements(self, p):
        # Use the current price from the WebSocket
        current_price = self.websocket.get_current_price() if self.websocket and self.websocket.is_connected else self.df['Close'].iloc[-1]
        
        # Create ColumnDataSource for current price label
        current_price_label_source = ColumnDataSource({
            'x': [self.df['Open Time'].max()],  # Start at the right edge
            'y': [current_price],
            'text': [f'${current_price:,.2f}']
        })

        # Create ColumnDataSource for current price line
        current_price_line_source = ColumnDataSource({
            'x': [[self.df['Open Time'].min(), self.df['Open Time'].max()]],
            'y': [[current_price, current_price]]
        })

        # Add current price line
        p.multi_line(xs='x',
                     ys='y',
                     source=current_price_line_source,
                     line_color=self.config.text_color,
                     line_dash='dotted',
                     line_width=1,
                     line_alpha=0.5,
                     level='overlay')

        # Add current price label
        p.text(x='x',
               y='y',
               text='text',
               source=current_price_label_source,
               text_color=self.config.text_color,
               text_font_size=self.config.label_font_size,
               text_align='right',  # Align text to the right
               text_baseline='middle',
               x_offset=-10,  # Negative offset to move label left of the point
               background_fill_color=self.config.background_color,
               background_fill_alpha=0.8,
               border_line_color=self.config.text_color,
               border_line_width=0.5,
               padding=5,
               level='overlay',
               border_radius=5)

        # Update the callback to keep label on right side
        price_callback = CustomJS(
            args=dict(
                label_source=current_price_label_source,
                line_source=current_price_line_source,
                x_range=p.x_range,
                y_range=p.y_range,
                current_price=current_price
            ),
            code="""
                const x_start = x_range.start;
                const x_end = x_range.end;
                const y_start = y_range.start;
                const y_end = y_range.end;
                
                // Update label position to stay at right edge
                const label_data = label_source.data;
                label_data.x[0] = x_end;  // Keep label at right edge
                
                // Update line position
                const line_data = line_source.data;
                line_data.x[0] = [x_start, x_end];
                
                // If current price is not in visible range, position both at top
                if (current_price < y_start || current_price > y_end) {
                    const top_position = y_end - ((y_end - y_start) * 0.05);
                    label_data.y[0] = top_position;
                    line_data.y[0] = [top_position, top_position];
                } else {
                    label_data.y[0] = current_price;
                    line_data.y[0] = [current_price, current_price];
                }
                
                label_source.change.emit();
                line_source.change.emit();
            """
        )

        # Attach callback to both x and y range updates
        p.x_range.js_on_change('start', price_callback)
        p.x_range.js_on_change('end', price_callback)
        p.y_range.js_on_change('start', price_callback)
        p.y_range.js_on_change('end', price_callback)

    def add_update_callback(self, p):
        def update_chart(df):
            print('DF:', df.columns)
            print('Source:', self.source.data.keys())
            new_data = df.iloc[0]
            print('New data:', new_data)

            # Calculate technical indicators for the new data
            df_with_indicators = self.calculate_technical_indicators(df)

            # Convert the new data (Series) to a dictionary
            new_data_dict = df_with_indicators.iloc[0].to_dict()

            # Ensure each value is a list to match the expected format for stream()
            for key in new_data_dict:
                new_data_dict[key] = [new_data_dict[key]]

            # Add the index column to the new data dictionary
            new_data_dict['index'] = [len(self.source.data['Open Time'])]

            # Stream the new data to the source
            self.source.stream(new_data_dict, rollover=len(self.source.data['Open Time']))

            # Update the current price elements
            if self.websocket and self.websocket.is_connected:
                current_price = self.websocket.get_current_price()
                self.current_price_label_source.data.update({'y': [current_price], 'text': [f'${current_price:.2f}']})
                self.current_price_line_source.data.update({'y': [[current_price, current_price]]})

            p.x_range.end = new_data['Open Time']
            p.y_range.start = min(p.y_range.start, new_data['Low'])
            p.y_range.end = max(p.y_range.end, new_data['High'])

        self.websocket.update_callback = update_chart

    def add_support_resistance_levels(self, p):
        # ColumnDataSource for support and resistance labels
        support_label_source = ColumnDataSource({
            'x': [],
            'y': [],
            'text': []
        })

        resistance_label_source = ColumnDataSource({
            'x': [],
            'y': [],
            'text': []
        })

        # Handle support levels
        if self.config.support_levels:
            for level in self.config.support_levels:
                p.line(x=[self.df['Open Time'].min(), self.df['Open Time'].max()], 
                       y=[level, level],
                       line_color=self.config.support_label_color, 
                       line_dash='dashed', 
                       line_width=2, 
                       hover_line_alpha=0
                )
                
                label = f'${level}'
                support_label_source.data['x'].append(self.df['Open Time'].min())
                support_label_source.data['y'].append(level)
                support_label_source.data['text'].append(label)

            # Create support labels
            p.text(x='x', 
                y='y', 
                text='text',
                source=support_label_source,
                text_color=self.config.text_color,
                text_font_size=self.config.label_font_size,
                text_align='left',
                text_baseline='middle',
                x_offset=10,
                background_fill_color=self.config.support_label_color,
                background_fill_alpha=0.8,
                padding=5)

        # Handle resistance levels
        if self.config.resistance_levels:
            for level in self.config.resistance_levels:
                p.line(x=[self.df['Open Time'].min(), self.df['Open Time'].max()], 
                       y=[level, level],
                       line_color=self.config.resistance_label_color, 
                       line_dash='dashed', 
                       line_width=1, 
                       hover_line_alpha=0)
                
                label = f'${level}'
                resistance_label_source.data['x'].append(self.df['Open Time'].min())
                resistance_label_source.data['y'].append(level)
                resistance_label_source.data['text'].append(label)

            # Create resistance labels
            p.text(x='x', 
                y='y', 
                text='text',
                source=resistance_label_source,
                text_color=self.config.text_color,
                text_font_size=self.config.label_font_size,
                text_align='left',
                text_baseline='middle',
                x_offset=10,
                background_fill_color=self.config.resistance_label_color,
                background_fill_alpha=1,
                padding=5)

        # Update callback to handle both sources
        callback = CustomJS(
            args=dict(
                support_source=support_label_source,
                resistance_source=resistance_label_source,
                x_range=p.x_range
            ), 
            code="""
                const start = x_range.start;
                
                // Update support label positions
                const support_data = support_source.data;
                for (let i = 0; i < support_data.x.length; i++) {
                    support_data.x[i] = start;
                }
                support_source.change.emit();
                
                // Update resistance label positions
                const resistance_data = resistance_source.data;
                for (let i = 0; i < resistance_data.x.length; i++) {
                    resistance_data.x[i] = start;
                }
                resistance_source.change.emit();
            """
        )

        # Attach callback to x_range updates
        p.x_range.js_on_change('start', callback)
        p.x_range.js_on_change('end', callback)     

    def get_chart_components(self):
        """Return the script and div components for embedding the chart."""
        self.create_candlestick_chart()
        script, div = components(self.p)
        return script, div
    


if __name__ == '__main__':
    # Create a ChartWidget instance with default settings
    chart = ChartWidget(config=ChartSettings(interval='1h'))
    
    # Create the candlestick chart
    chart.create_candlestick_chart()

    # # Start live updates
    # try:
    #     print("Press Ctrl+C to stop live updates")
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("Stopping live updates...")
    # finally:
    #     chart.stop_live_updates()