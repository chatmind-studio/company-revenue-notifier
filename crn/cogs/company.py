from typing import List, Optional

from line import Cog, Context, command
from line.models import (
    ButtonsTemplate,
    CarouselColumn,
    CarouselTemplate,
    PostbackAction,
    TemplateMessage,
    TextMessage,
)

from ..bot import CompanyRevenueNotifier
from ..models import Stock, User
from ..utils import get_report_title


class CompanyCog(Cog):
    def __init__(self, bot: CompanyRevenueNotifier):
        super().__init__(bot)
        self.bot = bot

    @command
    async def add_company(self, ctx: Context, stock_id: Optional[str] = None) -> None:
        template_message = TemplateMessage(
            "追蹤新公司",
            template=ButtonsTemplate(
                "請輸入要追蹤的公司的股票代號或股票簡稱\n\n例如: 2330 或 台積電",
                [PostbackAction("打開鍵盤", data="ignore", input_option="openKeyboard")],
            ),
        )
        user = await User.get(id=ctx.user_id)
        if stock_id is None:
            user.temp_data = "cmd=add_company&stock_id={text}"
            await user.save()
            return await ctx.reply_multiple([template_message])

        if stock_id.isdigit():
            stock = await Stock.get_or_none(id=stock_id)
            if stock is None:
                async with self.bot.session.get(
                    f"https://stock-api.seriaati.xyz/stocks/{stock_id}"
                ) as resp:
                    if resp.status != 200:
                        user.temp_data = "cmd=add_company&stock_id={text}"
                        await user.save()

                        return await ctx.reply_multiple(
                            [
                                TextMessage(f"查無股票代號為 {stock_id} 的公司, 請確認後重新輸入"),
                                template_message,
                            ]
                        )
                    stock = await Stock.create(
                        id=stock_id, name=(await resp.json())["name"]
                    )
        else:
            stock = await Stock.get_or_none(name=stock_id)
            if stock is None:
                async with self.bot.session.get(
                    "https://stock-api.seriaati.xyz/stocks",
                    params={"name": stock_id},
                ) as resp:
                    if resp.status != 200:
                        user.temp_data = "cmd=add_company&stock_id={text}"
                        await user.save()

                        return await ctx.reply_multiple(
                            [
                                TextMessage(f"查無股票簡稱為 {stock_id} 的公司, 請確認後重新輸入"),
                                template_message,
                            ]
                        )
                    stock = await Stock.create(
                        id=(await resp.json())["id"], name=stock_id
                    )

        user = await User.get(id=ctx.user_id)
        await user.stocks.add(stock)
        await user.save()
        if stock.revenue_report:
            return await ctx.reply_text(
                f"已將 {stock} 加入追蹤清單\n\n在追蹤之前, {stock} 已公佈 {get_report_title()}, 點擊「已追蹤清單」即可查看"
            )
        await ctx.reply_text(f"已將 {stock} 加入追蹤清單")

    @command
    async def list_companies(self, ctx: Context) -> None:
        user = await User.get(id=ctx.user_id)
        stocks = await user.stocks.all()
        if not stocks:
            return await ctx.reply_text("您尚未追蹤任何公司")

        columns: List[CarouselColumn] = []
        for stock in stocks:
            await stock.fetch_related("revenue_report")
            column = CarouselColumn(
                title=str(stock),
                text=f"{'已' if stock.revenue_report else '尚未'}公佈 {get_report_title()}",
                actions=[
                    PostbackAction(
                        "取消追蹤", data=f"cmd=remove_company&stock_id={stock.id}"
                    ),
                    PostbackAction(
                        f"{'尚無法' if stock.revenue_report is None else ''}查看營收",
                        data=f"cmd=view_report&stock_id={stock.id}",
                    ),
                ],
            )
            columns.append(column)

        await ctx.reply_template(
            "追蹤清單",
            template=CarouselTemplate(columns=columns),
        )

    @command
    async def remove_company(self, ctx: Context, stock_id: str) -> None:
        user = await User.get(id=ctx.user_id)
        stock = await Stock.get(id=stock_id)
        await user.stocks.remove(stock)
        await user.save()
        await ctx.reply_text(f"已將 {stock} 移出追蹤清單")

    @command
    async def view_report(self, ctx: Context, stock_id: str) -> None:
        stock = await Stock.get(id=stock_id).prefetch_related("revenue_report")
        report = stock.revenue_report
        if report is None:
            return await ctx.reply_text(f"{stock} 尚未公佈 {get_report_title()}")

        await ctx.reply_text(f"{stock} {get_report_title()}\n\n{report}")