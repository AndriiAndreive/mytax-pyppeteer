import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from src.api import app

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http*.+",
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)