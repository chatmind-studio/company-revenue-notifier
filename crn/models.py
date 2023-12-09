from typing import List, Optional, Self

from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.CharField(max_length=33, pk=True)
    line_notify_token: fields.Field[Optional[str]] = fields.CharField(
        max_length=255, null=True
    )  # type: ignore
    line_notify_state: fields.Field[Optional[str]] = fields.CharField(
        max_length=255, null=True
    )  # type: ignore
    stocks: fields.ManyToManyRelation["Stock"] = fields.ManyToManyField(
        "models.Stock", related_name="users", through="user_stock"
    )
    temp_data: fields.Field[Optional[str]] = fields.TextField(null=True)  # type: ignore


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
    stock: fields.BackwardOneToOneRelation[Stock]
    industry = fields.CharField(max_length=100)
    current_month_revenue = fields.BigIntField()
    last_month_revenue = fields.BigIntField()
    last_year_current_month_revenue = fields.BigIntField()
    last_month_diff = fields.FloatField()
    last_year_current_month_diff = fields.FloatField()
    current_month_accum_revenue = fields.BigIntField()
    last_year_accum_revenue = fields.BigIntField()
    last_season_diff = fields.FloatField()
    notes: fields.Field[Optional[str]] = fields.TextField(null=True)  # type: ignore

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

    @classmethod
    def parse(cls, strings: List[str]) -> Self:
        return cls(
            industry=strings[4],
            current_month_revenue=int(strings[5]),
            last_month_revenue=int(strings[6]),
            last_year_current_month_revenue=int(strings[7]),
            last_month_diff=float(strings[8]) if strings[8] else 0,
            last_year_current_month_diff=float(strings[9]) if strings[9] else 0,
            current_month_accum_revenue=int(strings[10]) if strings[10] else 0,
            last_year_accum_revenue=int(strings[11]) if strings[11] else 0,
            last_season_diff=float(strings[12]) if strings[12] else 0,
            notes=strings[13] if strings[13] != "-" else None,
        )
