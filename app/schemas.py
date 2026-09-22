from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Literal
from app.models import UserModel, ItemModel, TransactionModel, EventModel


class Session(BaseModel):
    user_id: int
    created_at: datetime
    expires_at: datetime


class UserCreate(BaseModel):
    name: str
    account_number: Optional[str] = None
    pin_code: str


class UserEdit(BaseModel):
    name: Optional[str] = None
    account_number: Optional[str] = None
    pin_code: Optional[str] = None


class UserLogin(BaseModel):
    name: str
    pin_code: str


class ItemAdd(BaseModel):
    name: str
    price: float


class ItemEdit(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None


class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: int


class EventEdit(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TransactionAdd(BaseModel):
    name: str
    description: Optional[str] = None
    shop_name: str
    event_id: int
    owner_id: int
    participants: list[int]
    items: list[ItemAdd]


class TransactionEdit(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    shop_name: Optional[str] = None
    participants: Optional[list[int]] = None


class User(BaseModel):
    id: int
    name: str
    account_number: str
    role: Literal["slave", "woman", "member", "jew"] = "member"

    pin_code: str

    @classmethod
    def load_from_db(cls, line: UserModel):
        return cls(id=line.id, name=line.name, account_number=line.account_number, role=line.role, pin_code=line.pin_code)


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
    description: Optional[str] = None
    shop_name: str

    owner_id: int
    participants: list[User]
    items: list[Item]

    @classmethod
    def load_from_db(cls, line: TransactionModel):
        return cls(id=line.id, name=line.name, description=line.description, shop_name=line.shop_name, owner_id=line.owner_id, participants=line.participants, items=line.items)


class Event(BaseModel):
    id: int
    name: str
    description: str
    transactions: list[Transaction]
    owner_id: int

    @classmethod
    def load_from_db(cls, line: EventModel):
        return cls(id=line.id, name=line.name, description=line.description, transactions=line.transactions, owner_id=line.owner_id)
