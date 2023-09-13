import asyncio
import os
import ccxt.pro as ccxt
from db import InfluxDb
from handler import record_exchange
from utils import datetime_string_to_timestamp_ms, get_logger

ORG = os.getenv("DOCKER_INFLUXDB_INIT_ORG")
TOKEN = os.getenv("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN")
URL = os.getenv("INFLUXDB_URL")
EXCHANGE_NAME = "binance"
MEASUREMENT_NAME = "trade"
SYMBOL = "BTC/USDT"
DATE_STR = "2023-09-13 07:30:00"
LIMIT = 1000
DESIRED_AMOUNT = 400.0


if __name__ == "__main__":
    logger = get_logger()

    loop = asyncio.get_event_loop()
    exchange: ccxt.Exchange = getattr(ccxt, EXCHANGE_NAME)()

    try:
        influxdb = InfluxDb(
            ORG, TOKEN, URL, EXCHANGE_NAME, MEASUREMENT_NAME, [("symbol", SYMBOL)]
        )
        loop.run_until_complete(
            record_exchange(
                logger,
                influxdb,
                DESIRED_AMOUNT,
                exchange,
                SYMBOL,
                datetime_string_to_timestamp_ms(DATE_STR),
                LIMIT,
            )
        )
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(exchange.close())
