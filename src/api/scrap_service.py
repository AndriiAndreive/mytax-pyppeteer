from fastapi import APIRouter
from src.api.uri import URI
from src.payloads.account import Account
from src.controllers.tax_controller import TaxController

scrap_service_router = APIRouter()

@scrap_service_router.post(URI.TAXSTATUS.GET_STATUS)
async def get_tax_status(account: Account):
    return await TaxController().get_status(account)
