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


import os
import requests
import pandas as pd
import bokeh.plotting as bk
from typing import List, Literal
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models import (
    Label, ColumnDataSource, HoverTool, CrosshairTool, 
    NumeralTickFormatter, CDSView, BooleanFilter, DataRange1d, 
    ImageURL, CustomJS, Band, DatetimeTickFormatter
)


class ChartSettings:
    """
    Configuration settings for the candlestick chart.

    Attributes:
        symbol (str): The default trading symbol (e.g., 'BTCUSDT').
        interval (str): The default timeframe interval (e.g., '1d').
        levels (List[float]): A list of support/resistance levels to plot on the chart.
        background_color (str): The background color of the chart.
        border_fill_color (str): The border color of the chart.
        text_color (str): The color of text elements on the chart.
        grid_color (str): The color of the grid lines.
        bullish_color (str): The color for bullish (increasing) candlesticks.
        bearish_color (str): The color for bearish (decreasing) candlesticks.
        sma_50_color (str): The color for the 50-period simple moving average (SMA).
        sma_200_color (str): The color for the 200-period SMA.
        support_resistance_color (str): The color for support and resistance levels.
        support_resistance_line_color (str): The color for support and resistance lines.
        title_font_size (str): The font size for the chart title.
        axis_font_size (str): The font size for axis labels.
        label_font_size (str): The font size for other labels.
    """
    # Default trading settings
    symbol: str = 'BTCUSDT'
    interval: str = '1d'
    levels: List[float] = [50000, 60000, 70000, 80000, 55000, 65000, 75000, 100000]
    
    # Theme
    theme: Literal['dark', 'light'] = 'light'

    # Chart colors
    background_color_dark: str = '#171717'  # Dark background
    background_color_light: str = '#FFFFFF'  # Light background
    border_fill_color_dark: str = '#171717'  # Dark border
    border_fill_color_light: str = '#FFFFFF'  # Light border
    text_color_dark: str = '#FFFFFF'  # Dark theme text
    text_color_light: str = '#000000'  # Light theme text

    grid_color: str = '#2A2A2A'  # Subtle grid lines
    num_candles: int = 50  # Number of candles to display
    
    # Candlestick colors
    bullish_color: str = '#09C283'  # Green for up candles
    bearish_color: str = '#E93334'  # Red for down candles
    
    # Technical indicator colors
    sma_50_color: str = '#2962FF'  # Blue for 50 SMA
    sma_200_color: str = '#FF6D00'  # Orange for 200 SMA
    support_label_color: str = '#D82A2B' 
    resistance_label_color: str = '#2DDA99' 

    # Axis styles
    axis_line_color: str = '#565656'
    
    # Text styling
    title_font_size: str = '16px'
    axis_font_size: str = '12px'
    label_font_size: str = '10px'

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
    """Configuration settings for Simple Moving Averages"""
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
    """Configuration settings for RSI indicator"""
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

class ChartAPI:
    BASE_URL = 'https://api3.binance.com/api/v3'
    
    def __init__(self, config: ChartSettings = ChartSettings(), sma: SMASettings = SMASettings(), rsi: RSISettings = RSISettings()):
        self.config = config
        self.sma = sma
        self.rsi = rsi
        self.timeframe_mapping = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
    
    def get_klines(self, 
                   symbol: str = 'BTCUSDT', 
                   interval: str = '1d', 
                   limit: int = 800) -> pd.DataFrame:
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
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=[
            'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
            'Close Time', 'Quote Asset Volume', 'Number of Trades',
            'TB Base Volume', 'TB Quote Volume', 'Ignore'
        ])
        
        # Convert numeric columns
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        
        # Convert timestamps
        df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
        
        return df
    
    def get_current_price(self, symbol: str = 'BTCUSDT') -> float:
        """
        Get current price for a symbol
        
        :param symbol: Trading pair symbol
        :return: Current price
        """
        response = requests.get(f'{self.BASE_URL}/ticker/price', 
                                params={'symbol': symbol})
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}, {response.text}")
        
        return float(response.json()['price'])
    
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
                df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
        
        if self.rsi.enabled:
            # Calculate RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi.period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi.period).mean()
            
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    
    def create_bokeh_chart(self, 
                            df: pd.DataFrame, 
                            symbol: str = 'BTCUSDT', 
                            interval: str = '1d') -> str:
        """
        Create interactive Bokeh candlestick chart
        
        :param df: Input DataFrame with price data
        :param symbol: Trading pair symbol
        :param interval: Timeframe interval
        :return: Path to generated HTML chart
        """

        logo_source = ColumnDataSource({
            'url': ['https://www.shutterstock.com/image-vector/golden-bitcoin-coin-crypto-currency-600nw-749467579.jpg'],  
            'x': [df['Open Time'].min()],
            'y': [df['High'].max()],
        })

        levels = self.config.levels

        # Prepare data source
        source = ColumnDataSource(df)

        # Get current price
        current_price = self.get_current_price()

        # Calculate padding for x-axis (time)
        time_min = df['Open Time'].iloc[-self.config.num_candles]
        time_max = df['Open Time'].max()


        # Support/resistance levels
        support_levels = []
        resistance_levels = []
        if self.config.levels:
            levels.sort()
            support_levels = levels[:4]
            resistance_levels = levels[4:]

        # X Data Range
        x_range = DataRange1d(
            start=time_min,
            end=time_max,
            bounds=(df['Open Time'].min(), df['Open Time'].max())  # Allow scrolling to full range
        )

        # Calculate initial y-range values
        visible_df = df[df['Open Time'].between(time_min, time_max)]
        min_price = visible_df['Low'].min()
        max_price = visible_df['High'].max()
        padding = (max_price - min_price) * 0.05
        
        # Create DataRange1d with initial values
        y_range_end = max_price + padding if not resistance_levels else max(resistance_levels) + padding
        y_range = DataRange1d(
            start=min_price - padding,
            end=y_range_end,
            follow='end'
        )

        # Callback to update y-range based on visible x-range
        callback = CustomJS(
            args=dict(y_range=y_range, source=source, initial_start=time_min, initial_end=time_max),
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

        # Create figure with proper ranges
        p = bk.figure(
            x_axis_type='datetime', 
            sizing_mode='stretch_both',
            # title=f'{symbol} ({interval}) - ${current_price:.2f}',
            # width=300,
            # height=300,
            # active_scroll='wheel_zoom',
            background_fill_color=self.config.background_color,
            border_fill_color=self.config.background_color,
            toolbar_location=None,
            y_axis_location="right",
            x_range=x_range,
            y_range=y_range,
            tools="xpan",  # Only allow panning on x-axis
            active_drag="xpan"  # Make pan the active drag tool
        )

         # Disable zoom
        p.toolbar.active_scroll = None  # Disable wheel zoom

        # Trigger initial y-axis range calculation
        p.js_on_event('document_ready', callback)
        
        # Attach the callback to x_range changes
        x_range.js_on_change('start', callback)
        x_range.js_on_change('end', callback)

        # Create the logo image glyph
        logo = ImageURL(
            url='url',
            x='x', 
            y='y',
            w=50,  # Fixed width in pixels
            h=50,  # Fixed height in pixels
            anchor="bottom_left",  # Position in bottom left corner
            global_alpha=0.8,  # Slight transparency
            w_units="screen",   # Use screen pixels for width
            h_units="screen", 
        )
        p.add_glyph(logo_source, logo)
        
        # Create ColumnDataSource for current price label
        current_price_label_source = ColumnDataSource({
            'x': [time_max],  # Start at the right edge
            'y': [current_price],
            'text': [f'${current_price:,.2f}']
        })

        # Create ColumnDataSource for current price line
        current_price_line_source = ColumnDataSource({
            'x': [[df['Open Time'].min(), df['Open Time'].max()]],
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

       
        # Remove the outer box
        p.outline_line_color = None 

        # Style the axes and remove extra grid lines
        p.xaxis.major_label_text_color = self.config.text_color
        p.xaxis.axis_line_color = self.config.axis_line_color
        p.xaxis.major_tick_line_color = self.config.axis_line_color
        p.xaxis.minor_tick_line_color = None  # Remove minor ticks
    
        p.yaxis.major_label_text_color = self.config.text_color
        p.yaxis.axis_line_color = self.config.axis_line_color
        p.yaxis.major_tick_line_color = self.config.axis_line_color
        p.yaxis.minor_tick_line_color = None  # Remove minor ticks
        p.title.text_color = self.config.text_color

        # Hide both x and y grids completely
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None
        p.xgrid.minor_grid_line_color = None  # Remove minor grid lines
        p.ygrid.minor_grid_line_color = None  # Remove minor grid lines

        # Customize y-axis number format
        p.yaxis.formatter = NumeralTickFormatter(format="$0,0.00")


        # Customize x-axis date format
        p.xaxis.formatter = DatetimeTickFormatter(
            milliseconds="%Y-%m-%d",
            seconds="%Y-%m-%d",
            minutes="%Y-%m-%d",
            hours="%Y-%m-%d",
            days="%Y-%m-%d",
            months="%Y-%m-%d",
            years="%Y-%m-%d"
        )
        
        # Define colors based on price movement
        inc = source.data['Close'] > source.data['Open']
        dec = source.data['Open'] > source.data['Close']
        
        # Create views for up/down candles
        inc_view = CDSView(filter=BooleanFilter(inc))
        dec_view = CDSView(filter=BooleanFilter(dec))
        
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
        
        # Candlestick segments (wicks) - keep them thin
        w1 = p.segment(x0='Open Time', 
                       x1='Open Time', 
                       y0='Low', 
                       y1='High',
                       color=self.config.bullish_color, 
                       line_width=1, 
                       source=source, 
                       view=inc_view
                       )
        
        w2 = p.segment(x0='Open Time', 
                       x1='Open Time', 
                       y0='Low', 
                       y1='High',
                       color=self.config.bearish_color, 
                       line_width=1, 
                       source=source, 
                       view=dec_view
                       )
        
        # Bullish (increasing) candlesticks - hollow with green outline
        b1 = p.vbar(x='Open Time', 
                    width=30, 
                    top='Open', 
                    bottom='Close',
                    fill_color=self.config.bullish_color, 
                    line_color=self.config.bullish_color, 
                    source=source,
                    view=inc_view, 
                    fill_alpha=0.0, 
                    line_width=8)
        
        # Bearish (decreasing) candlesticks - filled red
        b2 = p.vbar(x='Open Time', 
                    width=30, 
                    top='Open', 
                    bottom='Close',
                    fill_color=self.config.bearish_color, 
                    line_color=self.config.bearish_color, 
                    source=source,
                    view=dec_view, 
                    fill_alpha=0.0, 
                    line_width=9
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
        if support_levels:
            for level in support_levels:
                p.line(x=[df['Open Time'].min(), df['Open Time'].max()], 
                    y=[level, level],
                    line_color=self.config.support_label_color, 
                    line_dash='dashed', 
                    line_width=1, 
                    hover_line_alpha=0
                )
                
                label = '$' + str(level)
                support_label_source.data['x'].append(time_min)
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
        if resistance_levels:
            for level in resistance_levels:
                p.line(x=[df['Open Time'].min(), df['Open Time'].max()], 
                    y=[level, level],
                    line_color=self.config.resistance_label_color, 
                    line_dash='dashed', 
                    line_width=0.5, 
                    hover_line_alpha=0)
                
                label = '$' + str(level)
                resistance_label_source.data['x'].append(time_min)
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
                background_fill_alpha=0.8,
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


        # Plot SMAs if enabled
        if self.sma.enabled:
            # Plot SMA-50
            p.line('Open Time', 'SMA_50', 
                line_color=self.config.sma_50_color,
                line_width=self.sma.line_width,
                legend_label='SMA-50',
                source=source)


            # Plot SMA-200
            p.line('Open Time', 'SMA_200', 
                line_color=self.config.sma_200_color,
                line_width=self.sma.line_width,
                legend_label='SMA-200',
                source=source)

            # Modify the legend configuration
            p.add_layout(p.legend[0], 'above')  # Move legend above the chart
            p.legend.orientation = "horizontal"  # Make legend horizontal
            p.legend.spacing = 20  # Add some spacing between legend items
            p.legend.margin = 0  # Remove margin
            p.legend.padding = 5  # Add some padding inside the legend
            p.legend.label_text_font_size = "8pt"  # Adjust font size if needed
            p.legend.border_line_alpha = 0  # Remove border
            p.legend.background_fill_alpha = 0  # Make background transparent
            p.legend.location = "top_left"
            p.legend.border_line_color = self.config.text_color
            p.legend.background_fill_color = self.config.background_color
            p.legend.label_text_color = self.config.text_color
            p.legend.click_policy = "hide"

        # Create RSI panel if enabled
        if self.rsi.enabled:
            rsi = bk.figure(
                x_axis_type='datetime',
                x_range=p.x_range,
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

            # Customize x-axis date format
            rsi.xaxis.formatter = DatetimeTickFormatter(
                milliseconds="%Y-%m-%d",
                seconds="%Y-%m-%d",
                minutes="%Y-%m-%d",
                hours="%Y-%m-%d",
                days="%Y-%m-%d",
                months="%Y-%m-%d",
                years="%Y-%m-%d"
            )

            # Plot the RSI line with all data points
            rsi.line(x='Open Time', 
                    y='RSI', 
                    line_color=self.rsi.line_color,
                    line_width=self.rsi.line_width,
                    source=source,
                ) 

            # Add overbought/oversold lines
            rsi.line(x=[df['Open Time'].min(), df['Open Time'].max()], 
                    y=[self.rsi.overbought, self.rsi.overbought], 
                    line_color=self.rsi.level_color, 
                    line_dash='dashed', 
                    line_width=self.rsi.line_width,
                    line_alpha=0.5)
            rsi.line(x=[df['Open Time'].min(), df['Open Time'].max()], 
                    y=[self.rsi.oversold, self.rsi.oversold], 
                    line_color=self.rsi.level_color, 
                    line_dash='dashed', 
                    line_width=self.rsi.line_width,
                    line_alpha=0.5)

            # Style RSI panel
            rsi.xaxis.visible = False
            rsi.yaxis.visible = True
            rsi.yaxis.axis_line_color = None
            rsi.yaxis.major_label_text_color = self.config.text_color
            rsi.yaxis.major_label_text_font_size = self.config.label_font_size
            
            # Only show ticks for overbought, oversold, and midpoint levels
            rsi.yaxis.ticker = [self.rsi.oversold, self.rsi.overbought]
            
            # Remove all grid lines
            rsi.ygrid.grid_line_color = None
            rsi.grid.grid_line_color = None
            
            # Set y-range with small padding
            rsi.y_range.start = 0
            rsi.y_range.end = 100
            
            # Remove outline
            rsi.outline_line_color = None

            # Create layout with both charts and minimal spacing
            layout = bk.column([p, rsi], 
                             sizing_mode='stretch_both',
                             spacing=0)
        else:
            layout = p

        # Output to HTML
        output_dir = 'chart_outputs'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'{symbol}_{interval}_chart.html')

        # Save the plot to HTML string
        html = file_html(layout, CDN, title=f'{symbol} Chart')

        # Write the modified HTML to file
        with open(output_path, 'w') as f:
            f.write(html)
        
        # Save the chart
        # bk.output_file(output_path)
        # bk.save(p)
        
        return output_path

# Example usage
if __name__ == '__main__':
    # Initialize Binance API client
    binance_api = ChartAPI()
    
    # Fetch kline data
    df = binance_api.get_klines(symbol='BTCUSDT', interval='1d')
    
    # Calculate technical indicators
    df_with_indicators = binance_api.calculate_technical_indicators(df)
    
    # Create and save chart
    chart_path = binance_api.create_bokeh_chart(df_with_indicators)
    print(f"Chart saved to {chart_path}")