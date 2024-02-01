import os
from contextlib import asynccontextmanager

import aiohttp
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from tortoise import Tortoise

from crn.models import Stock, User

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(
        db_url=os.getenv("DB_URL") or "sqlite://db.sqlite3",
        modules={"models": ["crn.models"]},
    )
    await Tortoise.generate_schemas()
    app.state.session = aiohttp.ClientSession()
    yield
    await Tortoise.close_connections()
    await app.state.session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index() -> Response:
    return Response(status_code=200, content="CRN API v1.0")


@app.get("/add-stock")
async def add_stock(user_id: str, stock_id: str) -> Response:
    async with app.state.session.get(
        f"https://stock-api.seriaati.xyz/stocks/{stock_id}"
    ) as resp:
        if resp.status != 200:
            raise HTTPException(status_code=404, detail="stock not found")
        data = await resp.json()

    stock_name = data["name"]
    user = await User.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    stock, _ = await Stock.get_or_create(id=stock_id, name=stock_name)
    await user.stocks.add(stock)
    return Response(status_code=200, content="stock added")


if __name__ == "__main__":
    uvicorn.run("api:app", port=4501, log_level="info")
