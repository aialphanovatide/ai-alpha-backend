# Chart Widget Documentation

This widget allows you to embed interactive charts in your application. It supports both web and mobile implementations.

## Usage

### Web (HTML)
```html
<iframe 
    src="/chart/widget?symbol=BTCUSDT&interval=1h&n_bars=50" 
    width="100%" 
    height="600px" 
    frameborder="0"
    style="border: none;">
</iframe>
```

### React
```jsx
const ChartWidget = ({ symbol = 'BTCUSDT', interval = '1h', nBars = 50 }) => {
  return (
    <iframe
      src={`/chart/widget?symbol=${symbol}&interval=${interval}&n_bars=${nBars}`}
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

const ChartWidget = ({ symbol = 'BTCUSDT', interval = '1h', nBars = 50 }) => {
  return (
    <WebView
      source={{
        uri: `/chart/widget?symbol=${symbol}&interval=${interval}&n_bars=${nBars}`
      }}
      style={{ height: 600 }}
    />
  );
};
```

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| symbol | string | Trading pair to display | BTCUSDT |
| interval | string | Time interval for candles | 1h, 4h, 1d |
| n_bars | number | Number of bars to display | 50 |

## Examples

### Basic Usage
```jsx
// React
<ChartWidget symbol="ETHUSDT" interval="4h" nBars={100} />

// React Native
<ChartWidget symbol="ETHUSDT" interval="4h" nBars={100} />
```

## Notes
- Ensure your application has the necessary dependencies installed (`react-native-webview` for React Native)
- The widget requires an active internet connection
- Adjust the height parameter based on your application's needs