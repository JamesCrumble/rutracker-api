from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .v1 import router

app = FastAPI(title='RutrackerApi')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"]
)

app.include_router(router)
