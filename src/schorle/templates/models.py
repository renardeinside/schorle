from pydantic import BaseModel
from datetime import datetime


class User(BaseModel):
    name: str


class UsageStats(BaseModel):
    count: int
    last_usage_date: datetime
