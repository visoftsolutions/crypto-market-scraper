import asyncio
import os
import ccxt.pro as ccxt
from logging import Logger
from db import InfluxDb
from handler import record_exchange
from utils import datetime_string_to_timestamp_ms, get_logger

ORG = os.getenv("DOCKER_INFLUXDB_INIT_ORG")
TOKEN = os.getenv("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN")
INFLUXDB_URL = os.getenv("CMS_INFLUXDB_URL")
DESIRED_AMOUNT = os.getenv("CMS_DESIRED_AMOUNT")
EXCHANGE_NAME = "binance"
MEASUREMENT_NAME = "trade"
SYMBOLS = ["BTC/USDT", "ETH/USDT", "MATIC/USDT"]
DATE_STR = "2023-09-13 08:05:00"
LIMIT = 1000


async def start(
    initial_sleep: float,
    logger: Logger,
    org: str,
    token: str,
    influxdb_url: str,
    exchange_name: str,
    measurement_name: str,
    tags: list[(str, str)],
    desired_amount: float,
    exchange: ccxt.Exchange,
    symbol: str,
    since: int | None = None,
    limit: int | None = None,
):
    await asyncio.sleep(initial_sleep)
    await record_exchange(
        logger,
        InfluxDb(
            org,
            token,
            influxdb_url,
            exchange_name,
            measurement_name,
            tags,
        ),
        desired_amount,
        exchange,
        symbol,
        since,
        limit,
    )


async def shutdown(loop, exchange: ccxt.Exchange):
    """Shutdown procedures."""
    logger.info("Shutting down gracefully...")
    await exchange.close()
    loop.stop()
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    logger = get_logger()

    loop = asyncio.get_event_loop()
    exchange: ccxt.Exchange = getattr(ccxt, EXCHANGE_NAME)()

    tasks = [
        start(
            5 * (i + 1),
            logger,
            ORG,
            TOKEN,
            INFLUXDB_URL,
            EXCHANGE_NAME,
            MEASUREMENT_NAME,
            [("symbol", symbol)],
            float(DESIRED_AMOUNT),
            exchange,
            symbol,
            datetime_string_to_timestamp_ms(DATE_STR),
            LIMIT,
        )
        for i, symbol in enumerate(SYMBOLS)
    ]

    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except KeyboardInterrupt:
        logger.info("Received exit signal, shutting down...")
        loop.run_until_complete(shutdown(loop, exchange))
    finally:
        loop.close()
