import ccxt
import time
import pandas as pd
from datetime import datetime
from ta.trend import EMAIndicator, MACD
from sell import executesell_trade
from checkbuy import checkingactivepositionbuy
from checksell import checkingactivepositionsell
from losschecker import monitor_and_close_losing_positions

# Setup exchange
exchange = ccxt.binance({
    'enableRateLimit': True
})

symbol = 'BTC/USDT'
timeframe = '1m'
limit = 500

# Time sync
def get_time_difference():
    server_time = exchange.milliseconds()
    local_time = int(time.time() * 1000)
    return server_time - local_time

# Wait for the next candle to start
def wait_until_next_candle(time_diff):
    now = int(time.time() * 1000) + time_diff
    next_minute = ((now // 60000) + 1) * 60000
    sleep_time = (next_minute - now) / 1000
    print(f"🕒 Waiting {sleep_time:.2f}s for next candle...")
    time.sleep(sleep_time)

# Get recent candles
def fetch_candles(symbol, timeframe, limit):
    since = exchange.milliseconds() - limit * 60 * 1000
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def get_5m_ema200_and_close(exchange, symbol):
    """
    Fetches 5-minute candles and returns the latest EMA200 and closing price.
    
    Parameters:
    - exchange: ccxt exchange object
    - symbol: trading symbol, e.g., 'BTC/USDT'

    Returns:
    - tuple: (latest_ema200_5m, latest_close_5m)
    """
    df_5m = fetch_candles(symbol, '5m', 250)
    df_5m['ema200_5m'] = EMAIndicator(close=df_5m['close'], window=200).ema_indicator()
    ema200_5m_latest = df_5m['ema200_5m'].iloc[-1]
    close_5m_latest = df_5m['close'].iloc[-1]
    return ema200_5m_latest, close_5m_latest


# Add indicators
def apply_indicators(df):
    df['ema21'] = EMAIndicator(close=df['close'], window=21).ema_indicator()
    df['ema200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()

    macd = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()
    return df


# Main strategy
def run_bot_strategy():
    time_diff = get_time_difference()

    while True:
        df = fetch_candles(symbol, timeframe, limit)
        df = apply_indicators(df)
        ema200_5m, close_5m = get_5m_ema200_and_close(exchange, symbol)

        latest = df.iloc[-1]       # just-closed candle
        previous = df.iloc[-2]     # candle before that

        # Check that the latest candle is fresh
        now = int(time.time() * 1000)
        candle_time = int(latest['timestamp'].timestamp() * 1000)
        age = now - candle_time

        if age > 120000:
            print(f"⚠️ Skipping old candle from {latest['timestamp']} (Age: {age / 1000:.1f} sec)")
            wait_until_next_candle(time_diff)
            continue

        print(f"\n📊 Analyzing candle @ {latest['timestamp']}")

        # Long / Buy Logic
        if (
             latest['ema21'] > latest['ema200'] and
             latest['close'] > latest['ema21'] and
             previous['macd_hist'] < 0 and latest['macd_hist'] > 0 and
             close_5m > ema200_5m  # 5m filter
           ):
   
            print("📈 Buy conditions met!")
            checkingactivepositionbuy()
            print("🚀 Execute BUY trade!")

        # Short / Sell Logic
        elif   (
                latest['ema21'] < latest['ema200'] and
                latest['close'] < latest['ema21'] and
                previous['macd_hist'] > 0 and latest['macd_hist'] < 0 and
                close_5m < ema200_5m  # 5m filter
               ):

               print("📉 Sell conditions met!")
               checkingactivepositionsell()
               print("🚀 Execute SELL trade!")
        else:
            print("🛑 No buy signal detected")
            print("🛑 No sell signal detected")
            wait_until_next_candle(time_diff)
            continue

        print("⚪ No valid setup. Waiting...")
        wait_until_next_candle(time_diff)




def watchdog():
    
    while True:
        print("Hello Friend watch me trade for you")
        try:    
             # Run it
              run_bot_strategy()
              monitor_and_close_losing_positions()
    
        except Exception:
             print("OPPS NO INTERNET CONNECTION")
    
    
        
        
watchdog()