from typing import Any

from line import Cog, Context, command
from line.models import ButtonsTemplate, PostbackAction, TemplateMessage

from ..bot import CompanyRevenueNotifier


class AdminCog(Cog):
    def __init__(self, bot: CompanyRevenueNotifier):
        super().__init__(bot)
        self.bot = bot
        self.admin_id = "Udfc687303c03a91398d74cbfd33dcea4"

    @command
    async def admin(self, ctx: Context) -> Any:
        if ctx.user_id != self.admin_id:
            return await ctx.reply_text("權限不足")

        template = ButtonsTemplate(
            "請選擇功能",
            [
                PostbackAction("reset reports", data="cmd=reset_reports"),
                PostbackAction(
                    "crawl reports", data="cmd=crawl_and_save_revenue_reports"
                ),
            ],
        )
        await ctx.reply_template("管理員功能", template=template)

    @command
    async def reset_reports(self, ctx: Context) -> None:
        await self.bot.reset_reports()
        await ctx.reply_text("已重置所有公司的營收報表")

    @command
    async def crawl_and_save_revenue_reports(self, ctx: Context) -> None:
        await self.bot.crawl_and_save_revenue_reports()
        await ctx.reply_text("已爬取並儲存所有公司的營收報表")
