import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EventModel, TransactionModel
from app.schemas import (
    EventSettlements,
    SettlementSuggestion,
    UserBalance,
)
from app.services.settlements import (
    calculate_balances,
    calculate_settlements,
)
from app.session import load_session

router = APIRouter()
logger = logging.getLogger(__name__)

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/events/{event_id}/settlements",
    response_model=EventSettlements,
)
def get_event_settlements(event_id: int, request: Request, db: DbSession):
    session_token = request.cookies.get("Session")
    user_id = load_session(session_token)

    try:
        event = db.query(EventModel).filter(EventModel.id == event_id).first()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Event not found",
            )

        is_participant = any(
            participant.id == user_id for participant in event.participants
        )

        if event.owner_id != user_id and not is_participant:
            raise HTTPException(
                status_code=403,
                detail="You are not a participant of this event",
            )

        transactions = (
            db.query(TransactionModel)
            .filter(TransactionModel.event_id == event_id)
            .all()
        )

        balances = calculate_balances(transactions)

        # Include event members even if they have no transactions.
        balances.setdefault(event.owner_id, 0)

        for participant in event.participants:
            balances.setdefault(participant.id, 0)

        suggestions = calculate_settlements(balances)

        response = EventSettlements(
            event_id=event_id,
            balances=[
                UserBalance(
                    user_id=member_id,
                    balance_minor=balance,
                )
                for member_id, balance in sorted(balances.items())
            ],
            settlements=[
                SettlementSuggestion(
                    from_user_id=settlement["from_user_id"],
                    to_user_id=settlement["to_user_id"],
                    amount_minor=settlement["amount_cents"],
                )
                for settlement in suggestions
            ],
        )

        logger.info(
            "User %s retrieved settlements for event %s.",
            user_id,
            event_id,
        )

        return response

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to calculate settlements for event %s.",
            event_id,
        )
        raise
