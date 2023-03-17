from enum import Enum
from typing import List, Optional
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
    size: str


class InavailibleItem(ItemBase):
    missing: Optional[int]


class InvoiceItem(ItemBase):
    price: float


class RestockItem(ItemBase):
    restock_info: str


class Order(BaseModel):
    items: List[Item]
    location: Location


class OrderInternal(BaseModel):
    items: List[Item]


class Availability(BaseModel):
    available: List[str]
    inavailable: List[ItemBase]


class Rejection(BaseModel):
    inavailable: List[ItemBase]


class Confirmation(BaseModel):
    info: str


class Resotck(BaseModel):
    items: List[RestockItem]


class Invoice(BaseModel):
    items: List[InvoiceItem]
    total: float


class ReorderRequest(BaseModel):
    items: List[ItemBase]


class AvailabilityRequest(OrderInternal):
    pass


class InvoiceRequest(OrderInternal):
    pass
