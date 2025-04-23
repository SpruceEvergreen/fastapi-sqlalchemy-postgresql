import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.services.database import sessionmanager
from src.settings import DATABASE_URL, API_V1_PREFIX
from src.views import tb_res

@asynccontextmanager
async def lifespan(app: FastAPI):
    sessionmanager.init(DATABASE_URL)
    try:
        yield
    finally:
        if sessionmanager._engine is not None:
            await sessionmanager.close()

app = FastAPI(
    title="Restaurant Reservation APP",
    description="API For managing restaurant tables and reservations",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(tb_res.router, prefix=API_V1_PREFIX)

if __name__ == "__main__":
    print("Running Uvicorn directly for local development...")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

