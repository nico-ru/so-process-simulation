from enum import Enum
from typing import List
from pydantic import BaseModel


class Location(str, Enum):
    DE = "DE"
    AT = "AT"
    CH = "CH"


class Success(BaseModel):
    success: bool


class ItemBase(BaseModel):
    id: str


class Item(ItemBase):
    qty: int


class InavailibleItem(ItemBase):
    missing: int


class InvoiceItem(ItemBase):
    price: float


class RestockItem(ItemBase):
    date: str


class Order(BaseModel):
    items: List[Item]
    location: Location


class OrderInternal(BaseModel):
    items: List[Item]


class Availability(BaseModel):
    available: List[str]
    inavailable: List[InavailibleItem]


class Rejection(BaseModel):
    inavailable: List[InavailibleItem]


class Confirmation(BaseModel):
    date: str


class Resotck(BaseModel):
    items: List[RestockItem]


class Invoice(BaseModel):
    items: List[InvoiceItem]
    total: float


class ReorderRequest(OrderInternal):
    items: List[ItemBase]


class AvailabilityRequest(OrderInternal):
    pass


class InvoiceRequest(OrderInternal):
    pass
