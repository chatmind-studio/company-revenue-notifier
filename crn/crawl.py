from typing import List, Tuple

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from .models import RevenueReport, Stock

ua = UserAgent()


async def crawl_monthly_revenue_reports(
    session: aiohttp.ClientSession,
    year: int,
    month: int,
) -> List[Tuple[Stock, RevenueReport]]:
    found_stock_ids: set[str] = set()
    result: List[Tuple[Stock, RevenueReport]] = []
    for company_type in ("sii", "otc"):
        for area in (0, 1):
            url = f"https://mops.twse.com.tw/nas/t21/{company_type}/t21sc03_{year}_{month}_{area}.html"
            async with session.get(url) as resp:
                text = await resp.text(encoding="big5hkscs")
                soup = BeautifulSoup(text, "html.parser")
                big_table = soup.find("table")
                tables = big_table.tr.td.find_all("table")  # type: ignore
                for table in tables:
                    rows = table.find_all("tr")[4:-1]
                    for row in rows:
                        strings = [s.strip().replace(",", "") for s in row.strings]
                        stock_id, stock_name = strings[0], strings[1]
                        if stock_id in found_stock_ids:
                            continue

                        stock = await Stock.get_or_none(id=stock_id)
                        if stock is None:
                            stock = await Stock.create(id=stock_id, name=stock_name)
                        result.append((stock, RevenueReport.parse(strings)))
                        found_stock_ids.add(stock_id)
    return result
