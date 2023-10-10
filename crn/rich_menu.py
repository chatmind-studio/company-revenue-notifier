from line.models import PostbackAction, URIAction
from linebot.v3.messaging import (
    RichMenuArea,
    RichMenuBounds,
    RichMenuRequest,
    RichMenuSize,
)

RICH_MENU = RichMenuRequest(
    size=RichMenuSize(width=1200, height=810),
    selected=True,
    name="rich_menu",
    chatBarText="點擊開啟/關閉選單",
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=0, width=400, height=405),
            action=PostbackAction(
                data="cmd=set_line_notify", label="推播設定", input_option="closeRichMenu"
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=400, y=0, width=400, height=405),
            action=PostbackAction(data="cmd=add_company", label="追蹤新公司"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=800, y=0, width=400, height=405),
            action=PostbackAction(data="cmd=list_companies", label="已追蹤清單"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=405, width=400, height=405),
            action=URIAction(
                uri="https://line.me/R/nv/recommendOA/%40758svcdf", label="好用請分享"
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=400, y=405, width=400, height=405),
            action=PostbackAction(data="cmd=donate", label="支持贊助"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=800, y=405, width=400, height=405),
            action=PostbackAction(
                data="cmd=about", label="聯絡我們", input_option="closeRichMenu"
            ),
        ),
    ],
)
