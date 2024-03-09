import asyncio
import logging
import os

from dotenv import load_dotenv
from seria.logging import setup_logging

from crn.bot import CompanyRevenueNotifier

load_dotenv()


async def run() -> None:
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    if channel_secret is None:
        raise ValueError("LINE_CHANNEL_SECRET is not set")
    access_token = os.getenv("LINE_ACCESS_TOKEN")
    if access_token is None:
        raise ValueError("LINE_ACCESS_TOKEN is not set")

    bot = CompanyRevenueNotifier(
        channel_secret=channel_secret, access_token=access_token
    )
    await bot.run(port=7060)


with setup_logging(logging.INFO, log_filename="crn.log"):
    asyncio.run(run())
