from typing import Annotated, List

from fastapi import APIRouter, BackgroundTasks, Body

from .models.deribit import DeribitSubscribe, DeribitUpdate
from .services.deribit import deribit_scraper, start, update

router = APIRouter()


@router.post("/deribit/start")
async def start_deribit(
    deribit_start: Annotated[
        DeribitSubscribe,
        Body(
            examples=[
                {
                    "channels": [
                        "incremental_ticker.BTC-PERPETUAL",
                        "incremental_ticker.BTC_USDT",
                    ]
                }
            ]
        ),
    ],
    background_task: BackgroundTasks,
):
    background_task.add_task(start, deribit_scraper, deribit_start.channels)
    return "attempting to start"


@router.post("/deribit/update")
async def update_deribit(deribit_update: List[DeribitUpdate]):
    return update(deribit_scraper, deribit_update)


@router.get("/deribit/stop")
async def stop_deribit():
    deribit_scraper.stop()
    return str(deribit_scraper.state)


@router.get("/deribit/state")
async def deribit_task_state():
    return str(deribit_scraper.state)
