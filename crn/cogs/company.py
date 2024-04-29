from typing import Any, List, Optional

from line import Cog, Context, command
from line.models import (
    ButtonsTemplate,
    CarouselColumn,
    CarouselTemplate,
    PostbackAction,
    QuickReply,
    QuickReplyItem,
    TemplateMessage,
    TextMessage,
)

from ..bot import CompanyRevenueNotifier
from ..models import Stock, User
from ..utils import get_report_title, split_list


class CompanyCog(Cog):
    def __init__(self, bot: CompanyRevenueNotifier):
        super().__init__(bot)
        self.bot = bot

    @command
    async def add_company(
        self, ctx: Context, stock_id_or_name: Optional[str] = None
    ) -> Any:
        user = await User.get(id=ctx.user_id)
        if not user.line_notify_token:
            return await ctx.reply_text(
                "❌ 錯誤: 目前尚未設定 LINE Notify\n\n您將無法在月營收公佈時收到通知, 請先點擊「推播設定」進行設定"
            )

        template_msg = TemplateMessage(
            "追蹤新公司",
            template=ButtonsTemplate(
                "請輸入要追蹤的公司的股票代號或股票簡稱\n例如: 2330 或 台積電",
                [
                    PostbackAction(
                        "打開鍵盤",
                        data="cmd=open_keyboard",
                        input_option="openKeyboard",
                    ),
                    PostbackAction("查看已追蹤清單", data="cmd=list_companies"),
                    PostbackAction("取消", data="cmd=add_company_cancel"),
                ],
            ),
        )

        if stock_id_or_name is None:
            user.temp_data = "cmd=add_company&stock_id_or_name={text}"
            await user.save()

            return await ctx.reply_multiple([template_msg])

        if stock_id_or_name.isdigit():
            stock = await Stock.get_or_none(id=stock_id_or_name)
            if stock is None:
                async with self.bot.session.get(
                    f"https://stock-api.seriaati.xyz/stocks/{stock_id_or_name}"
                ) as resp:
                    if resp.status != 200:
                        return await ctx.reply_multiple(
                            [
                                TextMessage(
                                    f"❌ 錯誤: 找不到股票代號為 {stock_id_or_name} 的公司\n請檢查後重新輸入"
                                ),
                                template_msg,
                            ]
                        )

                    stock = await Stock.create(
                        id=stock_id_or_name, name=(await resp.json())["name"]
                    )
        else:
            stock = await Stock.get_or_none(name=stock_id_or_name)
            if stock is None:
                async with self.bot.session.get(
                    "https://stock-api.seriaati.xyz/stocks",
                    params={"name": stock_id_or_name},
                ) as resp:
                    if resp.status != 200:
                        return await ctx.reply_multiple(
                            [
                                TextMessage(
                                    f"❌ 錯誤: 找不到股票簡稱為 {stock_id_or_name} 的公司\n請檢查後重新輸入"
                                ),
                                template_msg,
                            ]
                        )

                    stock = await Stock.create(
                        id=(await resp.json())["id"], name=stock_id_or_name
                    )

        await user.stocks.add(stock)
        await user.save()

        if stock.revenue_report:
            return await ctx.reply_multiple(
                [
                    TextMessage(
                        f"已將 {stock} 加入追蹤清單\n\n在追蹤之前, {stock} 已公佈 {get_report_title()}, 點擊「已追蹤清單」即可查看"
                    ),
                    template_msg,
                ]
            )
        await ctx.reply_multiple(
            [
                TextMessage(
                    f"已將 {stock} 加入追蹤清單\n\n當 {stock} 公佈其上月營收時, 將會立即透過 LINE Notify 通知您"
                ),
                template_msg,
            ]
        )

    @command
    async def open_keyboard(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        user.temp_data = "cmd=add_company&stock_id_or_name={text}"
        await user.save()

    @command
    async def add_company_cancel(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        user.temp_data = None
        await user.save()
        await ctx.reply_text("已取消")

    @command
    async def search_company(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        user.temp_data = "cmd=list_companies&stock_id_or_name={text}"
        await user.save()
        await ctx.reply_text(
            "請輸入欲查詢的公司的股票代號或簡稱\n例如:「2330」或「台積電」",
            quick_reply=QuickReply(
                [QuickReplyItem(PostbackAction(label="✖️ 取消", data="cmd=cancel"))]
            ),
        )

    @command
    async def list_companies(
        self, ctx: Context, index: int = 0, stock_id_or_name: Optional[str] = None
    ) -> Any:
        user = await User.get(id=ctx.user_id)
        stocks = await user.stocks.all()
        if not stocks:
            return await ctx.reply_text("您尚未追蹤任何公司")

        if stock_id_or_name:
            stocks = [
                stock
                for stock in stocks
                if stock_id_or_name in stock.id or stock_id_or_name in stock.name
            ]

        split_stocks = split_list(stocks, 10)
        columns: List[CarouselColumn] = []
        for stock in split_stocks[index]:
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

        quick_reply_items: List[QuickReplyItem] = []
        if index > 0:
            quick_reply_items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label="⬅️ 上一頁", data=f"cmd=list_companies&index={index-1}"
                    )
                ),
            )
        if index < len(split_stocks) - 1:
            quick_reply_items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label="➡️ 下一頁", data=f"cmd=list_companies&index={index+1}"
                    )
                )
            )

        quick_reply_items.append(
            QuickReplyItem(
                action=PostbackAction(
                    label="🔎 搜尋公司",
                    data="cmd=search_company",
                    input_option="openKeyboard",
                )
            )
        )

        await ctx.reply_template(
            "追蹤清單",
            template=CarouselTemplate(columns=columns),
            quick_reply=QuickReply(items=quick_reply_items)
            if quick_reply_items
            else None,
        )

    @command
    async def remove_company(self, ctx: Context, stock_id: str) -> Any:
        user = await User.get(id=ctx.user_id)
        stock = await Stock.get(id=stock_id)
        await user.stocks.remove(stock)
        await user.save()
        await ctx.reply_text(f"已將 {stock} 移出追蹤清單")

    @command
    async def view_report(self, ctx: Context, stock_id: str) -> Any:
        stock = await Stock.get(id=stock_id).prefetch_related("revenue_report")
        report = stock.revenue_report
        if report is None:
            return await ctx.reply_text(f"{stock} 尚未公佈 {get_report_title()}")

        await ctx.reply_text(f"{stock} {get_report_title()}\n\n{report}")
