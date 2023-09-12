import asyncio
import os
import ccxt.pro as ccxt
import numpy as np
from datetime import datetime
import logging
from dataclasses import dataclass
from db import InfluxDb

ORG = os.getenv("DOCKER_INFLUXDB_INIT_ORG")
TOKEN = os.getenv("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN")
URL = os.getenv("INFLUXDB_URL")
BUCKET_NAME = "binance"
MEASUREMENT_NAME = "trade"
SYMBOL = "BTC/USDT"
DATE_STR = "2023-09-12 00:00:00"
LIMIT = 1000
START_INTERVAL = 5
DESIRED_AMOUNT = 400


@dataclass
class Trade:
    timestamp: int
    datetime: datetime
    symbol: str
    id: int
    side: str
    price: float
    amount: float
    cost: float


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


async def record_binance(
    logger: logging.Logger,
    binance: ccxt.binance,
    bucket_name: str,
    measurement_name: str,
    symbol: str,
    since: int | None = None,
    limit: int | None = None,
):
    influxdb = InfluxDb(ORG, TOKEN, URL)
    logger.info(influxdb.create_bucket_if_not_exist(bucket_name))
    wait_interval = 1
    desired_amount = float(DESIRED_AMOUNT)

    last = influxdb.get_last(
        bucket=bucket_name, measurement_name=measurement_name, symbol=symbol
    )
    if last:
        from_id = last["id"]
    else:
        while True:
            trades = list(
                map(
                    lambda trade: Trade(
                        trade["timestamp"],
                        trade["datetime"],
                        trade["symbol"],
                        trade["id"],
                        trade["side"],
                        trade["price"],
                        trade["amount"],
                        trade["cost"],
                    ),
                    await binance.fetch_trades(symbol=symbol, since=since, limit=limit),
                )
            )
            for trade in trades:
                influxdb.write(
                    bucket_name,
                    measurement_name,
                    [("symbol", trade.symbol)],
                    [
                        ("id", trade.id),
                        ("side", trade.side),
                        ("price", trade.price),
                        ("amount", trade.amount),
                        ("cost", trade.cost),
                    ],
                    trade.datetime,
                )
            last = influxdb.get_last(
                bucket=bucket_name, measurement_name=measurement_name, symbol=symbol
            )
            if last:
                from_id = last["id"]
                break
            else:
                logger.info("waiting for trades...")
                asyncio.sleep(10)

    while True:
        trades = list(
            map(
                lambda trade: Trade(
                    trade["timestamp"],
                    trade["datetime"],
                    trade["symbol"],
                    trade["id"],
                    trade["side"],
                    trade["price"],
                    trade["amount"],
                    trade["cost"],
                ),
                await binance.fetch_trades(
                    symbol=symbol, limit=limit, params={"fromId": from_id}
                ),
            )
        )
        trades_len = float(len(trades))
        wait_interval = max(
            0.1,
            (
                wait_interval
                + wait_interval * 2.0 * sigmoid((desired_amount - trades_len) / 100.0)
            )
            / 2.0,
        )
        logger.info(f"{wait_interval} --> {len(trades)}")
        for trade in trades:
            influxdb.write(
                bucket_name,
                measurement_name,
                [("symbol", trade.symbol)],
                [
                    ("id", trade.id),
                    ("side", trade.side),
                    ("price", trade.price),
                    ("amount", trade.amount),
                    ("cost", trade.cost),
                ],
                trade.datetime,
            )
        from_id = influxdb.get_last(
            bucket=bucket_name, measurement_name=measurement_name, symbol=symbol
        )["id"]
        await asyncio.sleep(wait_interval)


def get_logger():
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    return logger


def datetime_string_to_timestamp_ms(
    date_str: str, date_format: str = "%Y-%m-%d %H:%M:%S"
):
    """
    Convert a datetime string to a timestamp in milliseconds.

    Parameters:
    - date_str: the datetime string to be converted.
    - date_format: the format of the datetime string. Default is '%Y-%m-%d %H:%M:%S'.

    Returns:
    - Timestamp in milliseconds.
    """
    dt_object = datetime.strptime(date_str, date_format)
    timestamp_ms = int(dt_object.timestamp() * 1000)
    return timestamp_ms


if __name__ == "__main__":
    logger = get_logger()

    loop = asyncio.get_event_loop()
    binance = ccxt.binance()

    try:
        loop.run_until_complete(
            record_binance(
                logger,
                binance,
                BUCKET_NAME,
                MEASUREMENT_NAME,
                SYMBOL,
                datetime_string_to_timestamp_ms(DATE_STR),
                LIMIT,
            )
        )
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(binance.close())
