from fastapi import FastAPI
from src.api.scrap_service import scrap_service_router
from dotenv import load_dotenv
load_dotenv('.env')

# Create FastAPI app
# app = FastAPI(
#     title="MyTax APIs",                              # Title for your API documentation
#     description="API to get tax status",    # Description for your API documentation
#     version="1.0",                                  # Version of your API
#     docs_url="/",                                   # URL endpoint for the Swagger UI
#     redoc_url="/redoc",                             # URL endpoint for the ReDoc UI
#     openapi_url="/openapi.json",                    # URL endpoint for the OpenAPI schema
# )
app = FastAPI()
# api_prefix = "/api"

# app.include_router(router=scrap_service_router, prefix=api_prefix)
app.include_router(router=scrap_service_router, prefix="")
