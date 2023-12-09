from typing import List, Tuple

import aiohttp
from fake_useragent import UserAgent

from .models import RevenueReport, Stock

ua = UserAgent()


async def crawl_monthly_revenue_reports(
    session: aiohttp.ClientSession,
    year: int,
    month: int,
) -> List[Tuple[Stock, RevenueReport]]:
    result: List[Tuple[Stock, RevenueReport]] = []
    for company_type in ("sii", "otc"):
        data = f"step=9&functionName=show_file2&filePath=%2Ft21%2F{company_type}%2F&fileName=t21sc03_{year}_{month}.csv"
        async with session.post(
            "https://mops.twse.com.tw/server-java/FileDownLoad",
            data=data,
            headers={"User-Agent": ua.random},
        ) as resp:
            text = await resp.text(encoding="utf-8")
            for row in text.split("\r\n")[1:-1]:
                strings = row.split(",")
                stock = await Stock.get_or_none(id=strings[2])
                if stock is None:
                    stock = await Stock.create(id=strings[2], name=strings[3])
                result.append((stock, RevenueReport.parse(strings)))

    return result
