from fastapi import APIRouter

from pyuniverse.deribit.views import router as historical_router

api_router = APIRouter()

api_router.include_router(historical_router, prefix="/deribit")
