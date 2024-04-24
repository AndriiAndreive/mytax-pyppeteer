from fastapi import APIRouter
from src.api.uri import URI
from src.payloads.account import Account
from src.controllers.tax_controller import TaxController

scrap_service_router = APIRouter()

@scrap_service_router.post(URI.TAXSTATUS.GET_STATUS)
async def get_tax_status(account: Account):
    return await TaxController().get_status(account)

@scrap_service_router.get(URI.TAXSTATUS.GET_ALL)
async def get_root():
    return 'Root'

@scrap_service_router.get(URI.TAXSTATUS.GET_ICO)
async def get_favicorn():
    return 'Favicorn'