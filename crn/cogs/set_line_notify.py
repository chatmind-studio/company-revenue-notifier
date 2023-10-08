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

        if not user.line_notify_token:
            state = secrets.token_urlsafe()
            user.line_notify_state = state
            await user.save()

            template = ButtonsTemplate(
                "請點擊下方按鈕後按照下圖指示完成設定",
                [
                    URIAction(
                        label="前往設定", uri=self.bot.line_notify_api.get_oauth_uri(state)
                    )
                ],
                title="通知設定",
            )
            image = ImageMessage(
                original_content_url="https://i.imgur.com/9k26h5s.png",
                preview_image_url="https://i.imgur.com/9k26h5s.png",
            )
            await ctx.reply_multiple(
                [
                    TemplateMessage("通知設定", template=template),
                    image,
                ]
            )
        else:
            template = ButtonsTemplate(
                "✅ 設定完成",
                [
                    PostbackAction("發送測試訊息", data="cmd=send_test_message"),
                    PostbackAction("重新設定", data="cmd=reset_line_notify"),
                ],
                title="通知設定",
            )
            await ctx.reply_template("通知設定", template=template)

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
            "確定要重新設定 LINE Notify 嗎?",
            [
                PostbackAction("確定", data="cmd=set_line_notify&reset=True"),
                PostbackAction("取消", data="cmd=cancel"),
            ],
        )
        await ctx.reply_template("確認設定", template=template)
