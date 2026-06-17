from fastapi import APIRouter, Request, HTTPException
from app.database import SessionLocal
from app.models import EventModel
from app.schemas import Event, EventCreate, EventEdit
from app.session import load_session
from app.helpers import admin_required


router = APIRouter()


@router.get("/admin/events")
def admin_get_events(request: Request):
    db = SessionLocal()

    admin_required(db, request)

    try:
        events = db.query(EventModel).order_by(EventModel.id.desc()).all()

        return [
            {
                "id": e.id,
                "name": e.name,
                "description": e.description,

                "transactions": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "description": t.description,
                        "shop_name": t.shop_name,
                        "event_id": t.event_id,
                        "owner_id": t.owner_id,

                        "participants": [
                            u.id for u in t.participants
                        ],

                        "items": [
                            {
                                "id": i.id,
                                "name": i.name,
                                "price": i.price
                            }
                            for i in t.items
                        ]
                    }
                    for t in e.transactions
                ]
            }
            for e in events
        ]

    finally:
        db.close()


@router.post("/admin/events")
def admin_create_event(request: Request, event: EventCreate):
    db = SessionLocal()

    admin_required(db, request)

    try:
        new_event = EventModel(
            name=event.name,
            description=event.description,
            owner_id=event.owner_id,

        )

        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event

    finally:
        db.close()


@router.put("/admin/events/{event_id}")
def admin_edit_event(request: Request, event_id: int, edited: EventEdit):
    db = SessionLocal()

    admin_required(db, request)

    try:
        event = db.query(EventModel).filter(EventModel.id == event_id).first()

        if not event:
            return {"error": "event not found"}

        if edited.name is not None:
            event.name = edited.name

        if edited.description is not None:
            event.description = edited.description

        db.commit()
        db.refresh(event)

        return event

    finally:
        db.close()


@router.delete("/admin/events/{event_id}")
def admin_delete_event(request: Request, event_id: int):
    db = SessionLocal()

    admin_required(db, request)

    try:
        event = db.query(EventModel).filter(EventModel.id == event_id).first()

        if not event:
            return {"error": "event not found"}

        db.delete(event)
        db.commit()
    finally:
        db.close()


@router.get("/events")
def get_my_events(request: Request):
    jew_token = request.session.get("Session")
    user_id = load_session(jew_token)

    db = SessionLocal()
    try:
        events_db = db.query(EventModel).filter(
            EventModel.owner_id == user_id).all()
        events = [Event.load_from_db(event) for event in events_db]

        return events
    finally:
        db.close()


@router.post("/events")
def create_event(request: Request, event: EventCreate):
    jew_token = request.session.get("Session")
    user_id = load_session(jew_token)

    db = SessionLocal()
    try:
        new_event = EventModel(
            name=event.name,
            description=event.description,
            owner_id=user_id
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event

    finally:
        db.close()


@router.put("/events/{event_id}")
def edit_event(request: Request, event_id: int, edited: EventEdit):

    jew_token = request.session.get("Session")
    user_id = load_session(jew_token)

    db = SessionLocal()

    try:
        event = db.query(EventModel).filter(
            EventModel.id == event_id, EventModel.owner_id == user_id).first()

        if not event:
            return {"error": "event not found"}

        if edited.name is not None:
            event.name = edited.name

        if edited.description is not None:
            event.description = edited.description

        db.commit()
        db.refresh(event)

        return event

    finally:
        db.close()


@router.delete("/admin/events/{event_id}")
def delete_event(request: Request, event_id: int):

    jew_token = request.session.get("Session")
    user_id = load_session(jew_token)

    db = SessionLocal()

    try:
        event = db.query(EventModel).filter(
            EventModel.id == event_id, EventModel.owner_id == user_id).first()

        if not event:
            return {"error": "event not found"}

        db.delete(event)
        db.commit()
    finally:
        db.close()
