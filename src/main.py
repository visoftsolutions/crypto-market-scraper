import argparse
import asyncio
import os
import ccxt.pro as ccxt
from logging import Logger
from db import InfluxDb
from datetime import datetime
from handler import record_exchange
from utils import datetime_string_to_timestamp_ms, get_logger

ORG = os.getenv("DOCKER_INFLUXDB_INIT_ORG")
TOKEN = os.getenv("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN")
INFLUXDB_URL = os.getenv("CMS_INFLUXDB_URL")


async def start(
    initial_sleep: float,
    logger: Logger,
    org: str,
    token: str,
    influxdb_url: str,
    exchange_name: str,
    measurement_name: str,
    tags: list[(str, str)],
    batch: float,
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
        batch,
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


def setup_args():
    parser = argparse.ArgumentParser(description="Arguments for exchange record task.")
    parser.add_argument(
        "-x",
        "--exchange-name",
        dest="exchange_name",
        type=str,
        help="Name of the exchange",
    )
    parser.add_argument(
        "-m",
        "--measurement-name",
        dest="measurement_name",
        type=str,
        help="Name of the measurement",
    )
    parser.add_argument(
        "-s",
        "--symbols",
        dest="symbols",
        nargs="+",
        type=str,
        help="List of symbols (e.g., BTC/USDT ETH/USDT)",
    )
    parser.add_argument(
        "-d",
        "--date-str",
        dest="date_str",
        type=str,
        default=datetime.now().strftime(r"%Y-%m-%d %H:%M:%S"),
        help='Date in string format (e.g., "2023-01-01 00:00:00")',
    )
    parser.add_argument(
        "-b", "--batch", dest="batch", type=float, help="Batch as an float"
    )
    parser.add_argument(
        "-l", "--limit", dest="limit", type=int, help="Limit as an integer"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = setup_args()

    logger = get_logger()
    loop = asyncio.get_event_loop()
    exchange: ccxt.Exchange = getattr(ccxt, args.exchange_name)()

    tasks = [
        start(
            5 * (i + 1),
            logger,
            ORG,
            TOKEN,
            INFLUXDB_URL,
            args.exchange_name,
            args.measurement_name,
            [("symbol", symbol)],
            args.batch,
            exchange,
            symbol,
            datetime_string_to_timestamp_ms(args.date_str),
            args.limit,
        )
        for i, symbol in enumerate(args.symbols)
    ]

    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except KeyboardInterrupt:
        logger.info("Received exit signal, shutting down...")
        loop.run_until_complete(shutdown(loop, exchange))
    finally:
        loop.close()
