import math
import time
from typing import Dict, Optional

import httpx
from pydantic import BaseModel

from ...core.base import Unit
from .base import ExchangeRateProvider


class ExchangeDataCache(BaseModel):
    time: int
    rates: Dict[Unit, Optional[int]]


class MempoolExchangeRateProvider(ExchangeRateProvider):
    url = "https://mempool.space/api/v1/prices"
    supported_units = [Unit.sat, Unit.usd]
    cache_timeout = 60  # 1 minute
    cache: ExchangeDataCache = ExchangeDataCache(time=0, rates={})

    unit_map = {
        Unit.sat: "sat",
        Unit.usd: "USD",
        # Unit.eur: "EUR",
        # Unit.gbp: "GBP",
        # Unit.jpy: "JPY",
        # Unit.aud: "AUD",
        # Unit.cad: "CAD",
        # Unit.chf: "CHF",
    }

    def __init__(self):
        self.client = httpx.AsyncClient()

    def _update_cache(self, data: dict) -> None:
        rates = {
            unit: data.get(symbol)
            for unit, symbol in self.unit_map.items()
            if symbol in data
        }
        self.cache = ExchangeDataCache(time=int(time.time()), rates=rates)

    def _check_cache(self) -> Optional[ExchangeDataCache]:
        now = int(time.time())
        if now - self.cache.time > self.cache_timeout:
            return None
        return self.cache

    async def _fetch_exchange_rate(self) -> dict:
        res = await self.client.get(self.url)
        res.raise_for_status()
        return res.json()

    async def fetch_unit_per_satoshi(self, unit: Unit) -> float:
        if unit not in self.supported_units:
            raise ValueError(f"Unsupported unit: {unit}")

        if unit == Unit.sat:
            return 1.0

        cached_data = self._check_cache()
        if not cached_data:
            data = await self._fetch_exchange_rate()
            self._update_cache(data)
            rate_btc = data[self.unit_map[unit]]
        else:
            rate_btc = cached_data.rates[unit]

        rate_sats = rate_btc / 1e8
        return rate_sats * 100  # convert to cents/sat because Unit.usd is cents

    async def from_sats(self, sats: int, unit: Unit) -> int:
        rate = await self.fetch_unit_per_satoshi(unit)
        if unit == Unit.usd:
            # round to nearest
            return round(sats * rate)
        return sats

    async def to_sats(self, amount: int, unit: Unit) -> int:
        rate = await self.fetch_unit_per_satoshi(unit)
        if unit == Unit.usd:
            return round(amount / rate)
        return amount
