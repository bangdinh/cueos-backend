from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routes import products, tables

app = FastAPI(title="Inventory Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .redis_listener import start_redis_listener_thread

@app.on_event("startup")
def on_startup():
    init_db()
    start_redis_listener_thread()

app.include_router(products.router, tags=["Products"])
app.include_router(tables.router, tags=["Tables"])
