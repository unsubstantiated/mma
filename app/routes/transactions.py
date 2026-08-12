from fastapi import APIRouter, HTTPException, Request, Response
from app.database import SessionLocal
from app.models import TransactionModel, UserModel, ItemModel
from app.schemas import Transaction, TransactionAdd, TransactionEdit, ItemAdd, ItemEdit
from app.helpers import admin_required
from app.session import load_session
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/admin/transactions")
def admin_get_all_transactions(request: Request):
    db = SessionLocal()

    admin_id = admin_required(db, request)

    try:
        transactions_db = db.query(TransactionModel).order_by(
            TransactionModel.id.desc()
        ).all()
        logger.info("Admin %s retrieved %d transactions.",
                    admin_id, len(transactions_db))
        transactions = [Transaction.load_from_db(
            line) for line in transactions_db]

        return Response(transactions, media_type="application/json")

    except Exception:
        logger.exception(
            "Failed to retrieve transactions. (Admin id: %s)", admin_id)
        raise

    finally:
        db.close()


@router.post("/admin/transactions")
def admin_create_transaction(request: Request, transaction: TransactionAdd):
    db = SessionLocal()

    admin_id = admin_required(db, request)

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

        logger.info("New Transaction %s created by Admin %d.",
                    new_transaction.id, admin_id)
        return Response(new_transaction, media_type="application/json")

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to create transaction. (Admin id: %s)", admin_id)
        raise

    finally:
        db.close()


@router.put("/admin/transactions/{transaction_id}")
def admin_edit_transaction(request: Request, transaction_id: int, edited: TransactionEdit):
    db = SessionLocal()

    admin_id = admin_required(db, request)

    try:
        transaction = db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id
        ).first()

        if not transaction:
            logger.warning(
                "Admin %s attempted to edit a nonexistent transaction (%d)", admin_id, transaction_id)
            raise HTTPException(404, "Transaction not found")

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

        logger.info("Transaction %s edited by Admin %d",
                    transaction_id, admin_id)
        return Response(transaction, media_type="application/json")

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to edit transaction %s. (Admin id: %d)", transaction_id, admin_id)
        raise

    finally:
        db.close()


@router.delete("/admin/transactions/{transaction_id}")
def admin_delete_transaction(request: Request, transaction_id: int):
    db = SessionLocal()

    admin_id = admin_required(db, request)

    try:
        transaction = db.query(TransactionModel).filter(
            TransactionModel.id == transaction_id).first()

        if not transaction:
            logger.warning(
                "Admin %s attempted to delete a nonexistent transaction (%d).", admin_id, transaction_id)
            raise HTTPException(404, "Transaction not found")

        db.delete(transaction)
        db.commit()
        logger.info("Transaction %s was deleted by Admin %d.",
                    transaction_id, admin_id)

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to delete transaction %s. (Admin id: %d)", transaction_id, admin_id)
        raise

    finally:
        db.close()


@router.get("/transactions")
def get_my_transactions(request: Request):
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
        logger.info("User %s retrieved their transactions.", user_id)
        return transactions

    except Exception:
        logger.exception(
            "Failed to retrieve the transactions of User %s.", user_id)
        raise

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

        logger.info("User %s created a new Transaction: %d.",
                    user_id, transaction.name)
        return new_transaction

    except Exception:
        db.rollback()
        logger.exception(
            "User %s failed to create a new Transaction.", user_id)
        raise

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
            logger.warning(
                "User %s attempted to edit a nonexistent Transaction %d.", user_id, transaction_id)
            raise HTTPException(404, "Transaction not found")

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

        logger.info("User %s edited Transaction %d.", user_id, transaction_id)
        return transaction

    except Exception:
        db.rollback()
        logger.exception(
            "User %s failed to edit Transaction %d.", user_id, transaction_id)
        raise

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
            logger.warning(
                "User %s attempted to delete a nonexistent Transaction %d.", user_id, transaction_id)
            raise HTTPException(404, "Transaction not found")

        db.delete(transaction)
        db.commit()
        logger.info("User %s deleted Transaction %d.",
                    user_id, transaction_id)

    except Exception:
        db.rollback()
        logger.exception(
            "User %s failed to delete Transaction %d.", user_id, transaction_id)
        raise

    finally:
        db.close()
