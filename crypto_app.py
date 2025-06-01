import streamlit as st
st.set_page_config(page_title="Crypto Price Comparison", layout="wide")

from streamlit_autorefresh import st_autorefresh
import asyncio
import aiohttp
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ========== CONFIG ==========
COINS = ['bitcoin', 'ethereum', 'bnb', 'solana', 'ripple', 'cardano', 'dogecoin', 'avalanche', 'polkadot', 'tron']
EXCHANGES = [
    'binance', 'coinbase', 'kraken', 'kucoin', 'bitfinex',
    'bybit', 'bitstamp', 'bittrex', 'gemini', 'mexc',
    'gate', 'okx', 'coincheck', 'bitmart', 'bitflyer'
]
UPDATE_INTERVAL = 30  # seconds

# ========== Автооновлення ==========
st_autorefresh(interval=UPDATE_INTERVAL * 1000, key="autorefresh")

# ========== Заголовок ==========
st.title("📊 Онлайн порівняння цін криптовалют між біржами")
st.info(f"Дані оновлюються кожні {UPDATE_INTERVAL} секунд. Поточний час: {datetime.now().strftime('%H:%M:%S')}")

# ========== Запит даних ==========
async def fetch_coin_data(session, coin):
    url = f'https://api.coingecko.com/api/v3/coins/{coin}/tickers'
    async with session.get(url) as resp:
        return await resp.json()

async def fetch_all():
    results = {}
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_coin_data(session, coin) for coin in COINS]
        raw_data = await asyncio.gather(*tasks)
        for coin, data in zip(COINS, raw_data):
            if 'tickers' in data:
                for ticker in data['tickers']:
                    exch = ticker['market']['name'].lower().replace(' ', '')
                    if exch in EXCHANGES:
                        price = ticker['converted_last']['usd']
                        if price is not None:
                            results.setdefault(coin, {})[exch] = price
    return results

# ========== Відображення ==========
async def main():
    data = await fetch_all()
    for coin, prices in data.items():
        st.subheader(coin.upper())

        df = pd.DataFrame.from_dict(prices, orient='index', columns=['Price'])
        df.index.name = 'Exchange'
        df = df.sort_values(by='Price')

        # Таблиця
        st.dataframe(df.style.format("${:.2f}"), use_container_width=True)

        # Різниця цін
        if len(df) > 1:
            min_ex, min_val = df['Price'].idxmin(), df['Price'].min()
            max_ex, max_val = df['Price'].idxmax(), df['Price'].max()
            diff = max_val - min_val
            diff_pct = (diff / min_val) * 100 if min_val > 0 else 0
            st.success(
                f"Найбільша різниця: **${diff:.2f}** ({diff_pct:.2f}%) між **{min_ex}** і **{max_ex}**"
            )

        # Графік
        fig, ax = plt.subplots()
        df['Price'].plot(kind='bar', ax=ax, color='skyblue')
        ax.set_ylabel('USD')
        ax.set_title(f"Ціни на {coin.upper()} по біржах")
        st.pyplot(fig)

# ========== Запуск ==========
asyncio.run(main())