import asyncio
from typing import List, Literal, Tuple

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from .models import RevenueReport
from .utils import get_today

ua = UserAgent()


async def crawl_monthly_revenue_reports(
    session: aiohttp.ClientSession,
    company_type: Literal["sii", "otc"],
    area: Literal["1", "0"],
) -> List[Tuple[str, RevenueReport]]:
    today = get_today()
    url = f"https://mops.twse.com.tw/nas/t21/{company_type}/t21sc03_{today.year-1911}_{today.month-1}_{area}.html"
    result: List[Tuple[str, RevenueReport]] = []

    async with session.get(url, headers={"User-Agent": ua.random}) as resp:
        soup = BeautifulSoup(await resp.text(), "lxml")

        # find tables with bgcolor="#FFFFFF" border="5" bordercolor="#FF6600" width="100%"
        for table in soup.find_all(
            "table", bgcolor="#FFFFFF", border="5", bordercolor="#FF6600"
        ):
            for tr in table.find_all("tr")[2:-1]:
                tds = tr.find_all("td")
                result.append(
                    (
                        tds[0].text.strip(),
                        RevenueReport.parse([td.text.strip() for td in tds]),
                    )
                )

    return result


async def crawl_all_monthly_revenue_reports(
    session: aiohttp.ClientSession,
) -> List[Tuple[str, RevenueReport]]:
    result: List[Tuple[str, RevenueReport]] = []
    for company_type in ("sii", "otc"):
        for area in ("1", "0"):
            result.extend(
                await crawl_monthly_revenue_reports(session, company_type, area)
            )
            await asyncio.sleep(1.0)
    return result
