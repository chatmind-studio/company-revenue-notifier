import datetime


def get_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))


def get_today() -> datetime.date:
    return get_now().date()


def remove_commas(s: str) -> str:
    return s.replace(",", "")


def get_report_title() -> str:
    today = get_today()
    if today.month == 1:
        return f"{today.year-1912} 年 12 月營收"
    return f"{today.year-1911} 年 {today.month-1} 月營收"
