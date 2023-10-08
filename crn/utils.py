import datetime


def get_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))


def get_today() -> datetime.date:
    return get_now().date()


def remove_commas(s: str) -> str:
    return s.replace(",", "")
