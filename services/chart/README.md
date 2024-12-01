# Chart Widget Documentation

An advanced interactive charting widget that supports real-time candlestick charts with technical indicators. Compatible with both web and mobile implementations.

## Features

- Real-time candlestick data updates via WebSocket
- Technical indicators (SMA-50, SMA-200, RSI)
- Support and resistance levels
- Current price indicator
- Dark/Light theme support
- Interactive tooltips and crosshair
- Pan and zoom functionality
- Mobile-responsive design

## Usage

### Web (HTML)
```html
<iframe 
    src="/chart/widget?symbol=BTCUSDT&interval=1h&n_bars=50&theme=dark" 
    width="100%" 
    height="600px" 
    frameborder="0"
    style="border: none;">
</iframe>
```

### React
```jsx
const ChartWidget = ({ 
  symbol = 'BTCUSDT', 
  interval = '1h', 
  nBars = 50,
  theme = 'dark'
}) => {
  return (
    <iframe
      src={`/chart/widget?symbol=${symbol}&interval=${interval}&n_bars=${nBars}&theme=${theme}`}
      width="100%"
      height="600px"
      frameBorder="0"
      style={{ border: 'none' }}
    />
  );
};
```

### React Native
```jsx
import { WebView } from 'react-native-webview';

const ChartWidget = ({ 
  symbol = 'BTCUSDT', 
  interval = '1h', 
  nBars = 50,
  theme = 'dark'
}) => {
  return (
    <WebView
      source={{
        uri: `/chart/widget?symbol=${symbol}&interval=${interval}&n_bars=${nBars}&theme=${theme}`
      }}
      style={{ height: 600 }}
    />
  );
};
```

## Parameters

| Parameter | Type | Description | Default | Options |
|-----------|------|-------------|---------|----------|
| symbol | string | Trading pair to display | BTCUSDT | Any valid trading pair |
| interval | string | Time interval for candles | 1h | 15m, 30m, 1h, 4h, 1d, 1w |
| n_bars | number | Number of bars to display | 50 | 1-1000 |
| theme | string | Chart theme | light | light, dark |

## Technical Indicators

### Available Indicators
- SMA (Simple Moving Average)
  - 50-period SMA
  - 200-period SMA
- RSI (Relative Strength Index)
  - 14-period RSI
  - Overbought/Oversold levels at 70/30

## Examples

### Basic Usage
```jsx
// React - Dark theme
<ChartWidget 
  symbol="ETHUSDT" 
  interval="4h" 
  nBars={100}
  theme="dark"
/>

// React - Light theme with more bars
<ChartWidget 
  symbol="BTCUSDT" 
  interval="1d" 
  nBars={200}
  theme="light"
/>
```

## Notes
- Requires an active internet connection for real-time updates
- WebSocket connection automatically reconnects on disconnection
- Adjustable chart height based on container size
- Mobile-responsive design adapts to screen size
- For React Native, ensure `react-native-webview` is installed
- Supports both WebSocket and polling fallback for data updates

## Browser Compatibility
- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers

## Dependencies
- Bokeh.js (loaded automatically)
- Socket.IO (loaded automatically)