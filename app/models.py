from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

transaction_participants = Table(
    "transaction_participants",
    Base.metadata,
    Column("transaction_id", ForeignKey("transactions.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)

event_participants = Table(
    "event_participants",
    Base.metadata,
    Column("event_id", ForeignKey("events.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    account_number: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str | None] = mapped_column(String, nullable=True)

    pin_code: Mapped[str] = mapped_column(String, nullable=False)


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    shop_name: Mapped[str] = mapped_column(String, nullable=False)

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id"),
        nullable=True,
    )
    event: Mapped["EventModel | None"] = relationship(
        back_populates="transactions",
    )

    participants: Mapped[list["UserModel"]] = relationship(
        secondary=transaction_participants,
    )
    items: Mapped[list["ItemModel"]] = relationship(
        back_populates="parent_transaction",
    )


class ItemModel(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    parent_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id"),
        nullable=True,
    )

    parent_transaction: Mapped["TransactionModel"] = relationship(
        back_populates="items",
    )


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    transactions: Mapped[list["TransactionModel"]] = relationship(
        back_populates="event",
    )
    participants: Mapped[list["UserModel"]] = relationship(
        secondary=event_participants,
    )


class SettlementModel(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False,
    )
    debtor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    creditor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "debtor_id != creditor_id",
            name="different_settlement_users",
        ),
        CheckConstraint(
            "amount_minor > 0",
            name="positive_settlement_amount",
        ),
    )
