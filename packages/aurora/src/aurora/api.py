from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

api = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)


class Item(BaseModel):
    id: int
    name: str


fake_items_db = [Item(id=1, name="Item 1"), Item(id=2, name="Item 2")]


@api.get("/", response_model=list[Item])
async def read_items():
    return fake_items_db


@api.get("/{item_id}", response_model=Item)
async def read_item(item_id: int):
    if item_id not in [item.id for item in fake_items_db]:
        raise HTTPException(status_code=404, detail="Item not found")
    return fake_items_db[item_id]
