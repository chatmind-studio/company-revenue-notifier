import logging
import os
import sys
from pathlib import Path

from aiohttp import web
from line import Bot
from line.ext.notify import LineNotifyAPI
from linebot.v3.webhooks import FollowEvent, MessageEvent
from tortoise import Tortoise
from tortoise.exceptions import IntegrityError

from .crawl import crawl_all_monthly_revenue_reports
from .models import Stock, User
from .rich_menu import RICH_MENU
from .utils import get_now, get_report_title, get_today


class CompanyRevenueNotifier(Bot):
    def _setup_line_notify(self):
        line_notify_client_id = os.getenv("LINE_NOTIFY_CLIENT_ID")
        if line_notify_client_id is None:
            raise RuntimeError("LINE_NOTIFY_CLIENT_ID is not set")
        line_notify_client_secret = os.getenv("LINE_NOTIFY_CLIENT_SECRET")
        if line_notify_client_secret is None:
            raise RuntimeError("LINE_NOTIFY_CLIENT_SECRET is not set")

        self.line_notify_api = LineNotifyAPI(
            client_id=line_notify_client_id,
            client_secret=line_notify_client_secret,
            redirect_uri="https://crn-linebot.seriaati.xyz/line-notify"
            if sys.platform == "linux"
            else "https://vastly-assuring-grub.ngrok-free.app/line-notify",
        )

    async def _line_notify_callback(self, request: web.Request) -> web.Response:
        params = await request.post()
        code = params.get("code")
        state = params.get("state")

        user = await User.get_or_none(line_notify_state=state)
        if user and isinstance(code, str):
            access_token = await self.line_notify_api.get_access_token(code)
            user.line_notify_token = access_token
            user.line_notify_state = None
            await user.save()

        return web.Response(
            status=302,
            headers={"Location": "https://line.me/R/oaMessage/%40758svcdf"},
        )

    async def on_follow(self, event: FollowEvent) -> None:
        try:
            await User.create(id=event.source.user_id)  # type: ignore
        except IntegrityError:
            pass

    async def on_message(self, event: MessageEvent) -> None:
        if event.message is None:
            return
        text: str = event.message.text  # type: ignore
        user = await User.get(id=event.source.user_id)  # type: ignore
        if user.temp_data:
            event.message.text = user.temp_data.format(text=text)  # type: ignore
            user.temp_data = None
            await user.save()

        await super().on_message(event)

    async def run_tasks(self) -> None:
        now = get_now()
        if now.hour == 0 and now.minute < 1 and now.day == 1:
            await self.reset_reports()
        elif now.minute == 30:
            await self.crawl_and_save_revenue_reports()

    async def reset_reports(self):
        stocks = await Stock.all()
        for stock in stocks:
            stock.revenue_report = None  # type: ignore
            await stock.save()

    async def crawl_and_save_revenue_reports(self):
        reports = await crawl_all_monthly_revenue_reports(self.session)
        for stock_id, report in reports:
            stock = await Stock.get_or_none(id=stock_id)
            if stock is None:
                async with self.session.get(
                    f"https://stock-api.seriaati.xyz/stocks/{stock_id}"
                ) as resp:
                    if resp.status != 200:
                        continue
                    stock = await Stock.create(
                        id=stock_id, name=(await resp.json())["name"]
                    )

            if stock.revenue_report:
                continue

            await report.save()
            stock.revenue_report = report
            await stock.save()

            users = await User.filter(stocks__id=stock_id)
            for user in users:
                if user.line_notify_token is None:
                    continue
                await self.line_notify_api.notify(
                    user.line_notify_token,
                    message=f"\n{stock} {get_report_title}\n\n{report}",
                )

    async def setup_hook(self) -> None:
        await Tortoise.init(
            db_url=os.getenv("DB_URL") or "sqlite://db.sqlite3",
            modules={"models": ["crn.models"]},
        )
        await Tortoise.generate_schemas()

        rich_menu_id = await self.create_rich_menu(RICH_MENU, "assets/rich_menu.png")
        await self.line_bot_api.set_default_rich_menu(rich_menu_id)

        self._setup_line_notify()
        self.app.add_routes([web.post("/line-notify", self._line_notify_callback)])

        for cog in Path("crn/cogs").glob("*.py"):
            logging.info("Loading cog %s", cog.stem)
            self.add_cog(f"crn.cogs.{cog.stem}")

    async def on_close(self) -> None:
        await Tortoise.close_connections()