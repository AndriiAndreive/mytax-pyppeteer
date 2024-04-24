from fastapi import FastAPI
from src.api.scrap_service import scrap_service_router
from dotenv import load_dotenv
load_dotenv('.env')

app = FastAPI()

app.include_router(router=scrap_service_router, prefix="")
