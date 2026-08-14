import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routes import customers

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Customer & CRM Service",
    description="Microservice quản lý thông tin khách hàng, điểm thưởng thành viên (Database-per-service: customer.db)",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "customer_service"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8007))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
