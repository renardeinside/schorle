from pydantic import BaseModel


class StatsProps(BaseModel):
    total_users: int
    last_updated_at: str


class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: str
    updated_at: str


class Users(BaseModel):
    users: list[User]
