import secrets
from typing import Any

from line import Cog, Context, command
from line.models import (
    ButtonsTemplate,
    ConfirmTemplate,
    ImageMessage,
    PostbackAction,
    TemplateMessage,
    URIAction,
)

from ..bot import CompanyRevenueNotifier
from ..models import User


class SetNotifyCog(Cog):
    def __init__(self, bot: CompanyRevenueNotifier):
        super().__init__(bot)
        self.bot = bot

    @command
    async def set_line_notify(self, ctx: Context, reset: bool = False) -> Any:
        user = await User.get(id=ctx.user_id)
        if reset:
            await self.bot.session.post(
                "https://notify-api.line.me/api/revoke",
                headers={"Authorization": f"Bearer {user.line_notify_token}"},
            )

            user.line_notify_token = None
            user.line_notify_state = None
            await user.save()
            return await ctx.reply_text("✅ 已解除綁定 LINE Notify")

        if not user.line_notify_token:
            state = secrets.token_urlsafe()
            user.line_notify_state = state
            await user.save()

            template = ButtonsTemplate(
                "目前尚未設定 LINE Notify\n\n請參考上方圖示步驟, 點擊下方按鈕後進行設定",
                [
                    URIAction(
                        label="前往設定", uri=self.bot.line_notify_api.get_oauth_uri(state)
                    )
                ],
                title="推播設定",
            )
            image = ImageMessage(
                original_content_url="https://i.imgur.com/3lUM6ow.png",
                preview_image_url="https://i.imgur.com/3lUM6ow.png",
            )
            await ctx.reply_multiple(
                [
                    image,
                    TemplateMessage("推播設定", template=template),
                ]
            )
        else:
            template = ButtonsTemplate(
                "✅ 已完成設定",
                [
                    PostbackAction("發送測試訊息", data="cmd=send_test_message"),
                    PostbackAction("解除綁定", data="cmd=reset_line_notify"),
                ],
                title="推播設定",
            )
            await ctx.reply_template("推播設定", template=template)

    @command
    async def send_test_message(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        assert user.line_notify_token

        await self.bot.line_notify_api.notify(
            user.line_notify_token, message="這是一則測試訊息"
        )
        template = ButtonsTemplate(
            "已發送測試訊息",
            [
                URIAction(
                    label="點我前往查看", uri="https://line.me/R/oaMessage/%40linenotify"
                )
            ],
        )
        await ctx.reply_template("已發送測試訊息", template=template)

    @command
    async def reset_line_notify(self, ctx: Context) -> Any:
        template = ConfirmTemplate(
            "確定要解除綁定 LINE Notify 嗎?\n您將無法收到任何來自此機器人的推播訊息",
            [
                PostbackAction("確定", data="cmd=set_line_notify&reset=True"),
                PostbackAction("取消", data="cmd=cancel_line_notify"),
            ],
        )
        await ctx.reply_template("確認取消設定", template=template)

    @command
    async def cancel_line_notify(self, ctx: Context) -> Any:
        await ctx.reply_text("已取消")
