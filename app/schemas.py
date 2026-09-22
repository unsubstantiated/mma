from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models import EventModel, ItemModel, TransactionModel, UserModel


class Session(BaseModel):
    user_id: int
    created_at: datetime
    expires_at: datetime


class UserCreate(BaseModel):
    name: str
    account_number: str | None = None
    pin_code: str


class UserEdit(BaseModel):
    name: str | None = None
    account_number: str | None = None
    pin_code: str | None = None


class UserLogin(BaseModel):
    name: str
    pin_code: str


class ItemAdd(BaseModel):
    name: str
    price: float


class ItemEdit(BaseModel):
    name: str | None = None
    price: float | None = None


class EventCreate(BaseModel):
    name: str
    description: str | None = None


class EventEdit(BaseModel):
    name: str | None = None
    description: str | None = None


class TransactionAdd(BaseModel):
    name: str
    description: str | None = None
    shop_name: str
    event_id: int
    owner_id: int
    participants: list[int]
    items: list[ItemAdd]


class TransactionEdit(BaseModel):
    name: str | None = None
    description: str | None = None
    shop_name: str | None = None
    participants: list[int] | None = None


class User(BaseModel):
    id: int
    name: str
    account_number: str
    role: Literal["slave", "woman", "member", "jew"]

    pin_code: str

    @classmethod
    def load_from_db(cls, line: UserModel):
        return cls(
            id=line.id,
            name=line.name,
            account_number=line.account_number,
            role=line.role,
            pin_code=line.pin_code,
        )


class Item(BaseModel):
    id: int
    name: str
    price: float

    @classmethod
    def load_from_db(cls, line: ItemModel):
        return cls(id=line.id, name=line.name, price=line.price)


class Transaction(BaseModel):
    id: int
    name: str
    description: str | None = None
    shop_name: str

    owner_id: int
    participants: list[User]
    items: list[Item]

    @classmethod
    def load_from_db(cls, line: TransactionModel):
        return cls(
            id=line.id,
            name=line.name,
            description=line.description,
            shop_name=line.shop_name,
            owner_id=line.owner_id,
            participants=line.participants,
            items=line.items,
        )


class Event(BaseModel):
    id: int
    name: str
    description: str
    transactions: list[Transaction]
    owner_id: int

    @classmethod
    def load_from_db(cls, line: EventModel):
        return cls(
            id=line.id,
            name=line.name,
            description=line.description,
            transactions=line.transactions,
            owner_id=line.owner_id,
        )
