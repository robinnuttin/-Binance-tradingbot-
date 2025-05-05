import time
import requests
import logging
import hmac
import hashlib
import sys
import io
import codecs

# === CONFIG ===
API_KEY = '8NSMWap7w6u1cVJdakBE3FTXGwXXrLKybNZ1HF4u3hjew5nuJIBquRAFxRXis97v'
API_SECRET = 'r3W29WxQq7YOl2bfpwgQfTT3R1jIXbZM9AagBQVZG0u40rbhRmA8ISoD6cSmC2c6'

BASE_URL = "https://fapi.binance.com"

headers = {
    "X-MBX-APIKEY": API_KEY
}

# Force UTF-8 output to console (even on Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
console_utf8 = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console handler with UTF-8 encoding
console_handler = logging.StreamHandler(console_utf8)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S"))

# File handler (local log file)
file_handler = logging.FileHandler("C:/Users/Administrator/Desktop/bot_signal.txt", encoding='utf-8')
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S"))

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


import time
import requests

BASE_URL = "https://fapi.binance.com"

def get_server_time():
    url = f"{BASE_URL}/fapi/v1/time"
    res = requests.get(url)
    return int(res.json()['serverTime'])


def sign(params: dict) -> str:
    query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params)])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return f"{query_string}&signature={signature}"

def get_server_time():
    try:
        response = requests.get(f"{BASE_URL}/fapi/v1/time")
        return response.json()['serverTime']
    except Exception as e:
        logger.error("Failed to sync time: %s", str(e))
        raise

timestamp = get_server_time()

def get_price(symbol: str):
    try:
        url = f"{BASE_URL}/fapi/v1/ticker/price?symbol={symbol}"
        response = requests.get(url)
        return float(response.json()['price'])
    except Exception as e:
        logger.error("Failed to fetch price: %s", str(e))
        raise


def executesell_trade():

    RATE_LIMIT = 0.2  # 5 requests per second = 1/5 = 0.2 seconds between requests
    logger.info("Starting sell order script...")

    symbol = "ETHUSDT"
    price = get_price(symbol)
    logger.info("Current %s price: %.2f", symbol, price)

    # Risk config
    sl_usdt = 5  # risk per trade
    leverage = 20

    sl_distance = 3.0  # in price units (e.g., $6.5 stop loss)
    tp_distance = sl_distance * 2.66
    sl_price = round(price + sl_distance, 1)
    tp_price = round(price - tp_distance, 1)

    timestamp = get_server_time()
    quantity = round(sl_usdt / sl_distance, 3)
    position_value = quantity * price
    required_margin = (position_value / leverage) + 0.2

    logger.info("SL Distance: %.1f | TP Distance: %.1f", sl_distance, tp_distance)
    logger.info("Quantity: %.3f | SL: %.1f | TP: %.1f", quantity, sl_price, tp_price)
    logger.info("Required Margin: %.2f USDT", required_margin)

    required_margin = position_value / leverage  # Apply buffer after leverage

    # Set leverage
    def set_leverage(symbol: str, leverage: int):
        try:
            server_time = get_server_time()
            params = {
                'symbol': symbol,
                'leverage': leverage,
                'timestamp': server_time
            }
            query = sign(params)
            url = f"{BASE_URL}/fapi/v1/leverage?{query}"
            response = requests.post(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Leverage set to %d for %s", data['leverage'], data['symbol'])
            else:
                logger.error("❌ Failed to set leverage: %s", response.text)

        except Exception as e:
            logger.error("❌ Error setting leverage: %s", str(e))
    set_leverage(symbol, leverage)

    timestamp = get_server_time()
    # Place market order
    order_data = {
        'symbol': symbol,
        'side': 'SELL',
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': timestamp
    }
    order_query = sign(order_data)
    order_url = f"{BASE_URL}/fapi/v1/order"
    order_res = requests.post(order_url, headers=headers, data=order_query)
    print(f"✅ Market order placed: {order_res.json()}")

    time.sleep(RATE_LIMIT)

    # SL
    sl_data = {
        'symbol': symbol,
        'side': 'BUY',
        'type': 'STOP_MARKET',
        'stopPrice': sl_price,
        'closePosition': True,
        'timestamp': timestamp
    }
    sl_query = sign(sl_data)
    sl_url = f"{BASE_URL}/fapi/v1/order"
    sl_res = requests.post(sl_url, headers=headers, data=sl_query)
    print(f"🛡️ SL set: {sl_res.json()}")

    time.sleep(RATE_LIMIT)

    # TP
    timestamp = get_server_time()
    tp_data = {
        'symbol': symbol,
        'side': 'BUY',
        'type': 'TAKE_PROFIT_MARKET',
        'stopPrice': tp_price,
        'closePosition': True,
        'timestamp': timestamp
    }
    tp_query = sign(tp_data)
    tp_url = f"{BASE_URL}/fapi/v1/order"
    tp_res = requests.post(tp_url, headers=headers, data=tp_query)
    print(f"🎯 TP set: {tp_res.json()}")

if __name__ == "__main__":
    executesell_trade()
