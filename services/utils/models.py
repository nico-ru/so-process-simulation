from typing import List
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    quantity: int


class Order(BaseModel):
    items: List[Item]


class Availability(BaseModel):
    available: List[Item]
    inavailable: List[Item]
