from fastapi import APIRouter, HTTPException, Request
from app.database import SessionLocal
from app.models import TransactionModel, UserModel, ItemModel
from app.schemas import Transaction, TransactionAdd, TransactionEdit, ItemAdd, ItemEdit
from app.helpers import admin_required
from app.session import load_session

router = APIRouter()


@router.get("/admin/transactions")
def get_all_transactions(request: Request):
    db = SessionLocal()

    admin_required(db, request)

    try:
        transactions_db = db.query(TransactionModel).order_by(
            TransactionModel.id.desc()
        ).all()

        transactions = [Transaction.load_from_db(
            line) for line in transactions_db]

        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "shop_name": t.shop_name,
                "event_id": t.event_id,
                "owner_id": t.owner_id,

                "participants": [u.id for u in t.participants],

                "items": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "price": i.price
                    }
                    for i in t.items
                ]
            }
            for t in transactions
        ]

    finally:
        db.close()


@router.post("/admin/transactions")
def create_transaction(request: Request, transaction: TransactionAdd):
    db = SessionLocal()

    admin_required(db, request)

    try:
        participants = db.query(UserModel).filter(
            UserModel.id.in_(transaction.participants)
        ).all()

        new_transaction = TransactionModel(
            name=transaction.name,
            description=transaction.description,
            shop_name=transaction.shop_name,
            owner_id=transaction.owner_id,
            event_id=transaction.event_id,
            participants=participants,
            items=[
                ItemModel(name=i.name, price=i.price)
                for i in transaction.items
            ]
        )

        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

        return new_transaction

    finally:
        db.close()


@router.put("/admin/transactions/{transaction_id}")
def edit_transaction(request: Request, transaction_id: int, edited: TransactionEdit):
    db = SessionLocal()

    admin_required(db, request)

    try:
        transaction = db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id
        ).first()

        if not transaction:
            return {"error": "transaction not found"}

        if edited.name is not None:
            transaction.name = edited.name

        if edited.description is not None:
            transaction.description = edited.description

        if edited.shop_name is not None:
            transaction.shop_name = edited.shop_name

        if edited.participants is not None:
            transaction.participants = db.query(UserModel).filter(
                UserModel.id.in_(edited.participants)
            ).all()

        if edited.items is not None:
            transaction.items = [
                ItemModel(
                    name=i.name,
                    price=i.price
                )
                for i in edited.items
            ]

        db.commit()
        db.refresh(transaction)

        return transaction

    finally:
        db.close()


@router.delete("/admin/transactions/{transaction_id}")
def delete_transaction(request: Request, transaction_id: int):
    db = SessionLocal()

    admin_required(db, request)

    try:
        transaction = db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id).first()

        if not transaction:
            return {"error": "transaction not found"}

        db.delete(transaction)
        db.commit()
    finally:
        db.close()


@router.get("/transactions")
def get_all_transactions(request: Request):
    db = SessionLocal()

    jew_token = request.session.get("Session")
    user_id = load_session(jew_token)

    try:
        transactions_db = (db.query(TransactionModel)
                           .filter(TransactionModel.owner_id == user_id)
                           .order_by(TransactionModel.id.desc())
                           .all()
                           )

        transactions = [Transaction.load_from_db(
            line) for line in transactions_db]

        return transactions

    finally:
        db.close()


@router.post("/transactions")
def create_transaction(request: Request, transaction: TransactionAdd):
    db = SessionLocal()

    jew_token = request.session.get("Session")
    user_id = load_session(jew_token)

    try:
        participants = db.query(UserModel).filter(
            UserModel.id.in_(transaction.participants),
        ).all()

        new_transaction = TransactionModel(
            name=transaction.name,
            description=transaction.description,
            shop_name=transaction.shop_name,
            owner_id=user_id,
            event_id=transaction.event_id,
            participants=participants,
            items=[
                ItemModel(name=i.name, price=i.price)
                for i in transaction.items
            ]
        )

        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

        return new_transaction

    finally:
        db.close()


@router.put("/transactions/{transaction_id}")
def edit_transaction(request: Request, transaction_id: int, edited: TransactionEdit):
    db = SessionLocal()

    jew_token = request.session.get("Session")
    user_id = load_session(jew_token)

    try:
        transaction = db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id,
            TransactionModel.owner_id == user_id
        ).first()

        if not transaction:
            return {"error": "transaction not found"}

        if edited.name is not None:
            transaction.name = edited.name

        if edited.description is not None:
            transaction.description = edited.description

        if edited.shop_name is not None:
            transaction.shop_name = edited.shop_name

        if edited.participants is not None:
            transaction.participants = db.query(UserModel).filter(
                UserModel.id.in_(edited.participants)
            ).all()

        if edited.items is not None:
            transaction.items = [
                ItemModel(
                    name=i.name,
                    price=i.price
                )
                for i in edited.items
            ]

        db.commit()
        db.refresh(transaction)

        return transaction

    finally:
        db.close()


@router.delete("/admin/transactions/{transaction_id}")
def delete_transaction(request: Request, transaction_id: int):
    db = SessionLocal()

    jew_token = request.session.get("Session")
    user_id = load_session(jew_token)

    try:
        transaction = db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id, TransactionModel.owner_id == user_id).first()

        if not transaction:
            return {"error": "transaction not found"}

        db.delete(transaction)
        db.commit()
    finally:
        db.close()
