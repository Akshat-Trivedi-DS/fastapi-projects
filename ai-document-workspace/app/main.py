from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routes import router

app = FastAPI()
app.include_router(router,tags=["Workspaces"])

@app.on_event("startup")
async def startup():

    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )

@app.get("/")
async def home():
    return {"Helth check":"Success"}