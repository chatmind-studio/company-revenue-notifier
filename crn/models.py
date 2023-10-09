from typing import List, Optional, Self

from tortoise import fields
from tortoise.models import Model

from .utils import remove_commas


class User(Model):
    id = fields.CharField(max_length=33, pk=True)
    line_notify_token: Optional[str] = fields.CharField(max_length=255, null=True)  # type: ignore
    line_notify_state: Optional[str] = fields.CharField(max_length=255, null=True)  # type: ignore
    stocks: fields.ManyToManyRelation["Stock"] = fields.ManyToManyField(
        "models.Stock", related_name="users", through="user_stock"
    )
    temp_data: Optional[str] = fields.TextField(null=True)  # type: ignore


class Stock(Model):
    id = fields.CharField(max_length=10, pk=True)
    name = fields.CharField(max_length=255)
    users: fields.ManyToManyRelation[User]
    revenue_report: fields.OneToOneNullableRelation[
        "RevenueReport"
    ] = fields.OneToOneField("models.RevenueReport", related_name="stock", null=True)

    def __str__(self) -> str:
        return f"[{self.id}] {self.name}"


class RevenueReport(Model):
    current_month_revenue = fields.IntField()
    """當月營收"""
    last_month_revenue = fields.IntField()
    """上月營收"""
    last_year_current_month_revenue = fields.IntField()
    """去年當月營收"""
    last_month_diff = fields.FloatField()
    """上月比較增減(%)"""
    last_year_current_month_diff = fields.FloatField()
    """去年同月增減(%)"""

    current_month_accum_revenue = fields.IntField()
    """當月累計營收"""
    last_year_accum_revenue = fields.IntField()
    """去年累計營收"""
    last_season_diff = fields.FloatField()
    """前期比較增減(%)"""

    notes: Optional[str] = fields.TextField(null=True)  # type: ignore
    """備註"""

    stock: fields.OneToOneRelation[Stock]

    @classmethod
    def parse(cls, strings: List[str]) -> Self:
        return cls(
            current_month_revenue=int(remove_commas(strings[2])) if strings[2] else 0,
            last_month_revenue=int(remove_commas(strings[3])) if strings[3] else 0,
            last_year_current_month_revenue=int(remove_commas(strings[4]))
            if strings[4]
            else 0,
            last_month_diff=float(remove_commas(strings[5])) if strings[5] else 0.0,
            last_year_current_month_diff=float(remove_commas(strings[6]))
            if strings[6]
            else 0.0,
            current_month_accum_revenue=remove_commas(strings[7]) if strings[7] else 0,
            last_year_accum_revenue=remove_commas(strings[8]) if strings[8] else 0,
            last_season_diff=float(remove_commas(strings[9])) if strings[9] else 0.0,
            notes=strings[10] if strings[10] != "-" else None,
        )

    def __str__(self) -> str:
        return (
            f"當月營收: {self.current_month_revenue:,}\n"
            f"上月營收: {self.last_month_revenue:,}\n"
            f"去年當月營收: {self.last_year_current_month_revenue:,}\n"
            f"上月比較增減: {self.last_month_diff:+.2f}%\n"
            f"去年同月增減: {self.last_year_current_month_diff:+.2f}%\n"
            f"當月累計營收: {self.current_month_accum_revenue:,}\n"
            f"去年累計營收: {self.last_year_accum_revenue:,}\n"
            f"前期比較增減: {self.last_season_diff:+.2f}%\n"
            f"備註: {self.notes or '無'}"
        )
