import time
import requests
import logging
import hmac
import hashlib
import sys
import io
import codecs
import asyncio
import aiohttp

# === CONFIG ===
API_KEY = '8NSMWap7w6u1cVJdakBE3FTXGwXXrLKybNZ1HF4u3hjew5nuJIBquRAFxRXis97v'
API_SECRET = 'r3W29WxQq7YOl2bfpwgQfTT3R1jIXbZM9AagBQVZG0u40rbhRmA8ISoD6cSmC2c6'
BASE_URL = "https://fapi.binance.com"

# Session for reusing connections
session = requests.Session()
session.headers.update({"X-MBX-APIKEY": API_KEY})

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", handlers=[
    logging.StreamHandler(sys.stdout),
    logging.FileHandler("C:/Users/Administrator/Desktop/bot_signal.txt", encoding='utf-8')
])

logger = logging.getLogger()

# Sign parameters
def sign(params: dict) -> str:
    params['recvWindow'] = 5000
    query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params)])
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return f"{query_string}&signature={signature}"

# Get server time once
def get_server_time():
    url = f"{BASE_URL}/fapi/v1/time"
    response = session.get(url)
    if response.status_code == 200:
        return int(response.json().get('serverTime', time.time() * 1000))
    else:
        logger.error("Failed to fetch server time: %s", response.text)
        return int(time.time() * 1000)

# Get price
async def get_price(symbol: str):
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/fapi/v1/ticker/price?symbol={symbol}"
        async with session.get(url) as response:
            data = await response.json()
            return float(data['price'])

# Set leverage
async def set_leverage(symbol: str, leverage: int):
    params = {'symbol': symbol, 'leverage': leverage, 'timestamp': get_server_time()}
    query = sign(params)
    url = f"{BASE_URL}/fapi/v1/leverage?{query}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers={"X-MBX-APIKEY": API_KEY}) as response:
            return await response.json()

# Place order
async def place_order(order_data):
    query = sign(order_data)
    url = f"{BASE_URL}/fapi/v1/order?{query}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers={"X-MBX-APIKEY": API_KEY}) as response:
            return await response.json()

async def executesell_trade():
    symbol = "ETHUSDT"
    price = await get_price(symbol)

    # Risk config
    sl_usdt = 5
    leverage = 20
    sl_distance = 3.0
    tp_distance = sl_distance * 2.66
    sl_price = round(price + sl_distance, 1)
    tp_price = round(price - tp_distance, 1)
    quantity = round(sl_usdt / sl_distance, 3)

    # Set leverage and place market order
    leverage_res = await set_leverage(symbol, leverage)
    logger.info(f"Leverage set: {leverage_res}")

    order_data = {
        'symbol': symbol, 'side': 'SELL', 'type': 'MARKET', 'quantity': quantity, 'timestamp': get_server_time()
    }
    order_res = await place_order(order_data)
    logger.info(f"SELL Market order placed: {order_res}")

    # SL and TP orders
    sl_data = {'symbol': symbol, 'side': 'BUY', 'type': 'STOP_MARKET', 'stopPrice': sl_price, 'closePosition': True, 'timestamp': get_server_time()}
    tp_data = {'symbol': symbol, 'side': 'BUY', 'type': 'TAKE_PROFIT_MARKET', 'stopPrice': tp_price, 'closePosition': True, 'timestamp': get_server_time()}
    sl_res, tp_res = await asyncio.gather(place_order(sl_data), place_order(tp_data))
    logger.info(f"SL order: {sl_res}")
    logger.info(f"TP order: {tp_res}")

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(executesell_trade())
