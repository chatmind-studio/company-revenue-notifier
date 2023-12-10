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

from .crawl import crawl_monthly_revenue_reports
from .models import RevenueReport, User
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
            await self.line_notify_api.notify(
                access_token,
                message="\n✅ LINE Notify 設定成功\n點擊此連結返回機器人: https://line.me/R/oaMessage/%40758svcdf",
            )

        return web.Response(
            status=302,
            headers={"Location": "https://line.me/R/oaMessage/%40linenotify"},
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

        await super().on_message(event)

    async def run_tasks(self) -> None:
        now = get_now()
        if now.hour == 0 and now.minute < 1 and now.day == 1:
            await self.delete_reports()
        elif (now.minute == 30 or now.minute == 0) and now.day <= 15:
            await self.crawl_and_save_revenue_reports()

    async def delete_reports(self):
        logging.info("Deleting revenue reports")
        await RevenueReport.all().delete()
        logging.info("Deleted all revenue reports")

    async def crawl_and_save_revenue_reports(self):
        logging.info("Crawling revenue reports")
        today = get_today()
        reports = await crawl_monthly_revenue_reports(
            self.session, today.year - 1911, today.month - 1
        )
        logging.info(f"Crawled {len(reports)} revenue reports")
        for stock, report in reports:
            if stock.revenue_report:
                continue

            await report.save()
            stock.revenue_report = report
            await stock.save()

            users = await stock.users.all()
            for user in users:
                if user.line_notify_token is None:
                    continue
                await self.line_notify_api.notify(
                    user.line_notify_token,
                    message=f"\n{stock} {get_report_title()}\n\n{report}",
                )
        logging.info("Saved all revenue reports")

    async def setup_hook(self) -> None:
        await Tortoise.init(
            db_url=os.getenv("DB_URL") or "sqlite://db.sqlite3",
            modules={"models": ["crn.models"]},
        )
        await Tortoise.generate_schemas()

        await self.delete_all_rich_menus()
        rich_menu_id = await self.create_rich_menu(RICH_MENU, "assets/rich_menu.png")
        await self.line_bot_api.set_default_rich_menu(rich_menu_id)

        self._setup_line_notify()
        self.app.add_routes([web.post("/line-notify", self._line_notify_callback)])

        for cog in Path("crn/cogs").glob("*.py"):
            logging.info("Loading cog %s", cog.stem)
            self.add_cog(f"crn.cogs.{cog.stem}")

    async def on_close(self) -> None:
        await Tortoise.close_connections()
