import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.helpers import admin_required
from app.models import EventModel, UserModel
from app.schemas import AdminEventCreate, AdminEventEdit, Event, EventCreate, EventEdit
from app.session import load_session

router = APIRouter()
logger = logging.getLogger(__name__)

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/admin/events")
def admin_get_events(request: Request, db: DbSession):

    admin_id = admin_required(db, request)

    try:
        events_db = db.query(EventModel).order_by(EventModel.id.desc()).all()

        logger.info("Admin %s retrieved %d events.", admin_id, len(events_db))
        events = [Event.load_from_db(line) for line in events_db]
        return JSONResponse(content=jsonable_encoder(events))

    except Exception:
        logger.exception("Failed to retrieve events. (Admin id: %s)", admin_id)

    finally:
        db.close()


@router.post("/admin/events")
def admin_create_event(request: Request, event: AdminEventCreate, db: DbSession):

    admin_id = admin_required(db, request)

    try:
        participants = (
            db.query(UserModel).filter(UserModel.id.in_(event.participants)).all()
        )

        new_event = EventModel(
            name=event.event_name,
            description=event.event_description,
            owner_id=event.owner_id,
            participants=participants,
        )

        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        logger.info("Event %s created by Admin %d.", new_event.id, admin_id)
        return new_event

    except Exception:
        db.rollback()
        logger.exception("Failed to create event. (Admin id: %s)", admin_id)
        raise

    finally:
        db.close()


@router.put("/admin/events/")
def admin_edit_event(request: Request, edited: AdminEventEdit, db: DbSession):

    admin_id = admin_required(db, request)

    try:
        event = db.query(EventModel).filter(EventModel.id == edited.event_id).first()

        if not event:
            logger.warning(
                "Admin %s attempted to edit a nonexistent Event (%d).",
                admin_id,
                edited.event_id,
            )
            raise HTTPException(404, "Event not found")

        if edited.event_name is not None:
            event.name = edited.event_name

        if edited.event_description is not None:
            event.description = edited.event_description

        if edited.participants is not None:
            event.participants = (
                db.query(UserModel).filter(UserModel.id.in_(edited.participants)).all()
            )

        db.commit()
        db.refresh(event)

        logger.info("Event %s edited by Admin %d.", edited.event_id, admin_id)
        return event

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to edit Event %s. (Admin id: %d)", edited.event_id, admin_id
        )
        raise

    finally:
        db.close()


@router.delete("/admin/events/{event_id}")
def admin_delete_event(request: Request, event_id: int, db: DbSession):

    admin_id = admin_required(db, request)

    try:
        event = db.query(EventModel).filter(EventModel.id == event_id).first()

        if not event:
            logger.warning(
                "Admin %s attempted to delete a nonexistent Event (%d).",
                admin_id,
                event_id,
            )
            raise HTTPException(404, "Event not found")

        db.delete(event)
        db.commit()

        logger.info("Event %s was deleted by Admin %d.", event_id, admin_id)

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to delete Event %s. (Admin id: %d)", event_id, admin_id
        )
        raise

    finally:
        db.close()


@router.get("/events")
def get_my_events(request: Request, db: DbSession):
    jew_token = request.cookies.get("Session")
    user_id = load_session(jew_token)

    try:
        events_db = db.query(EventModel).filter(EventModel.owner_id == user_id).all()
        events = [Event.load_from_db(event) for event in events_db]

        logger.info("User %s retrieved their Events.", user_id)
        return events

    except Exception:
        db.rollback()
        logger.exception("Failed to retrieve the Events of User %s.", user_id)
        raise

    finally:
        db.close()


@router.post("/events")
def create_event(request: Request, event: EventCreate, db: DbSession):
    jew_token = request.cookies.get("Session")
    user_id = load_session(jew_token)

    try:
        participants = (
            db.query(UserModel).filter(UserModel.id.in_(event.participants)).all()
        )

        new_event = EventModel(
            name=event.name,
            description=event.description,
            owner_id=user_id,
            participants=participants,
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        logger.info("User %s created a new Event: %s.", user_id, event.name)
        return new_event

    except Exception:
        db.rollback()
        logger.exception("User %s failed to create a new Event.", user_id)
        raise

    finally:
        db.close()


@router.put("/events/{event_id}")
def edit_event(request: Request, event_id: int, edited: EventEdit, db: DbSession):

    jew_token = request.cookies.get("Session")
    user_id = load_session(jew_token)

    try:
        event = (
            db.query(EventModel)
            .filter(EventModel.id == event_id, EventModel.owner_id == user_id)
            .first()
        )

        if not event:
            logger.warning(
                "User %s attempted to edit a nonexistent Event %d.", user_id, event_id
            )
            raise HTTPException(404, "Event not found")

        if edited.name is not None:
            event.name = edited.name

        if edited.description is not None:
            event.description = edited.description

        if edited.participants is not None:
            event.participants = (
                db.query(UserModel).filter(EventModel.id.in_(edited.participants)).all()
            )

        db.commit()
        db.refresh(event)

        logger.info("User %s edited Event %d.", user_id, event_id)
        return event

    except Exception:
        db.rollback()
        logger.exception("User %s failed to edit Event %d.", user_id, event_id)
        raise

    finally:
        db.close()


@router.delete("/events/{event_id}")
def delete_event(request: Request, event_id: int, db: DbSession):

    jew_token = request.cookies.get("Session")
    user_id = load_session(jew_token)

    try:
        event = (
            db.query(EventModel)
            .filter(EventModel.id == event_id, EventModel.owner_id == user_id)
            .first()
        )

        if not event:
            logger.warning(
                "User %s attempted to delete a nonexistent Event %d.", user_id, event_id
            )
            raise HTTPException(404, "Event not found")

        db.delete(event)
        db.commit()

        logger.info("User %s deleted Event %d.", user_id, event_id)

    except Exception:
        db.rollback()
        logger.exception("User %s failed to delete Event %d.", user_id, event_id)
        raise

    finally:
        db.close()
