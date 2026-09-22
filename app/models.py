from sqlalchemy import Column, Integer, Float, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

transaction_participants = Table(
    "transaction_participants",
    Base.metadata,
    Column("transaction_id", ForeignKey("transactions.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    account_number = Column(String)
    role = Column(String)

    pin_code = Column(String, nullable=False)


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    shop_name = Column(String, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))

    participants = relationship(
        "UserModel",
        secondary=transaction_participants,
    )

    items = relationship("ItemModel")


class ItemModel(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    parent_transaction_id = Column(Integer, ForeignKey("transactions.id"))


class EventModel(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)

    transactions = relationship("TransactionModel")
    owner_id = Column(Integer, ForeignKey("users.id"))
