from typing import Annotated, List

from fastapi import APIRouter, BackgroundTasks, Body

from .models import DeribitSubscribe, DeribitUpdate
from .service import deribit_scraper, start, stop, update

router = APIRouter()


@router.post("/start")
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


@router.post("/update")
async def update_deribit(deribit_update: List[DeribitUpdate]):
    return await update(deribit_scraper, deribit_update)


@router.get("/stop")
async def stop_deribit():
    await stop(deribit_scraper)
    return str(deribit_scraper.state)


@router.get("/state")
async def deribit_task_state():
    return str(deribit_scraper.state)
