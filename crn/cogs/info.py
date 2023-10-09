from typing import Any

from line import Cog, Context, command
from line.models import (
    ButtonsTemplate,
    ImageMessage,
    PostbackAction,
    TemplateMessage,
    TextMessage,
    URIAction,
)

from ..bot import CompanyRevenueNotifier


class AboutCog(Cog):
    def __init__(self, bot: CompanyRevenueNotifier):
        super().__init__(bot)
        self.bot = bot

    @command
    async def about(self, ctx: Context) -> Any:
        template = ButtonsTemplate(
            "本 LINE 機器人為聊思工作室所屬的產品。",
            [
                URIAction("一對一私訊", uri="https://line.me/R/ti/p/%40644rcaca"),
                # URIAction("查看其他作品", uri="https://line.me/R/ti/p/%40550sqmuw"),
            ],
            thumbnail_image_url="https://i.imgur.com/PUixVsA.png",
            title="聊思工作室",
        )
        await ctx.reply_multiple(
            [
                TemplateMessage("關於我們", template=template),
                TextMessage(
                    "聊思工作室致力於透過 LINE 官方帳號和網頁應用等數位服務, 幫助中小企業或商家減少人力和時間成本。\n\n我們同時也是資深的 LINE 機器人和網頁應用開發者, 如果您有任何問題或需求, 歡迎聯絡我們。"
                ),
            ]
        )

    @command
    async def donate(self, ctx: Context) -> Any:
        await ctx.reply_template(
            "支持贊助",
            template=ButtonsTemplate(
                "如果你覺得這個服務對您有幫助, 歡迎贊助我們。您的支持將會用於維持伺服器運作和開發新功能。",
                [
                    PostbackAction("街口支付", data="cmd=jkopay"),
                    URIAction(
                        "全支付",
                        uri="https://service.pxpayplus.com/pxplus_redirect/page_redirect/jumj?memberCode=MC14292876&amount=0",
                    ),
                    URIAction("信用卡或 PayPal", uri="https://ko-fi.com/chatmind"),
                ],
                title="捐款支持",
            ),
        )

    @command
    async def jkopay(self, ctx: Context) -> Any:
        await ctx.reply_multiple(
            [
                ImageMessage(
                    "https://i.imgur.com/tRfyIkv.png", "https://i.imgur.com/tRfyIkv.png"
                ),
                TextMessage(
                    "點擊連結或掃描 QR Code\n\nhttps://www.jkopay.com/transfer?j=Transfer:909280661"
                ),
            ]
        )
