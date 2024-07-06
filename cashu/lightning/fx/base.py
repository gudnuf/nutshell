from abc import ABC, abstractmethod

from pydantic import BaseModel

from ...core.base import Unit


class ExchangeRateProvider(ABC):
    @abstractmethod
    async def from_sats(self, sats: int, unit: Unit) -> int:
        """
        Convert a given amount in satoshis to a specific unit.

        :param sats: The amount in satoshis.
        :param unit: The unit to convert to.
        :return: The equivalent amount in the specified unit.
        """
        pass

    @abstractmethod
    async def to_sats(self, amount: int, unit: Unit) -> int:
        """
        Convert a given amount in a specific unit to satoshis.

        :param amount: The amount to convert.
        :param unit: The unit of the amount.
        :return: The equivalent amount in satoshis.
        """
        pass
