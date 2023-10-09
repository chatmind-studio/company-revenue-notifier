import datetime
from typing import List, TypeVar


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


T = TypeVar("T")


def split_list(input_list: List[T], n: int) -> List[List[T]]:
    """
    Split a list into sublists of length n

    Parameters:
        input_list: The input list
        n: The length of each sublist
    """
    if n <= 0:
        raise ValueError("Parameter n must be a positive integer")

    return [input_list[i : i + n] for i in range(0, len(input_list), n)]
