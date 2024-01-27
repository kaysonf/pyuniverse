from enum import Enum
from typing import List

from pydantic import BaseModel


class DeribitSubscribe(BaseModel):
    channels: List[str]


class DeribitOperation(Enum):
    subscribe = "public/subscribe"
    unsubscribe = "public/unsubscribe"


class DeribitUpdate(BaseModel):
    operation: DeribitOperation
    channel: str
