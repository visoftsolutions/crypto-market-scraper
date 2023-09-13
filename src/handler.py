from ccxt.pro import Exchange
import logging
from asyncio import sleep
from datetime import datetime
from dataclasses import dataclass
from db import InfluxDb
from utils import sigmoid


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


async def record_exchange(
    logger: logging.Logger,
    influxdb: InfluxDb,
    desired_amount: float,
    exchange: Exchange,
    symbol: str,
    since: int | None = None,
    limit: int | None = None,
):
    influxdb.create_bucket_if_not_exist()
    wait_interval = 5

    last = influxdb.get_last()
    if last:
        from_id = last["id"]
    else:
        while True:
            while True:
                try:
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
                            await exchange.fetch_trades(
                                symbol=symbol, since=since, limit=limit
                            ),
                        )
                    )
                    break
                except Exception as e:
                    logger.error(e)
                    await sleep(5)
            for trade in trades:
                influxdb.write(
                    [
                        ("id", trade.id),
                        ("side", trade.side),
                        ("price", trade.price),
                        ("amount", trade.amount),
                        ("cost", trade.cost),
                    ],
                    trade.datetime,
                )
            last = influxdb.get_last()
            if last:
                from_id = last["id"]
                break
            else:
                logger.info(f"symbol: {symbol} waiting for trades...")
                await sleep(60)

    while True:
        while True:
            try:
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
                        await exchange.fetch_trades(
                            symbol=symbol, limit=limit, params={"fromId": from_id}
                        ),
                    )
                )
                break
            except Exception as e:
                logger.error(e)
                await sleep(5)
        trades_len = float(len(trades))
        wait_interval = max(
            0.1,
            (
                wait_interval
                + wait_interval * 2.0 * sigmoid((desired_amount - trades_len) / 100.0)
            )
            / 2.0,
        )
        logger.info(f"{wait_interval} --> symbol: {symbol} lenght: {len(trades)}")
        for trade in trades:
            influxdb.write(
                [
                    ("id", trade.id),
                    ("side", trade.side),
                    ("price", trade.price),
                    ("amount", trade.amount),
                    ("cost", trade.cost),
                ],
                trade.datetime,
            )
        from_id = influxdb.get_last()["id"]
        await sleep(wait_interval)
