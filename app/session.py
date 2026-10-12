from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jwt
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import settings
from app.schemas import Session

EXPIRY = timedelta(days=20)


def make_session(user_id):
    session = Session(
        user_id=user_id,
        created_at=datetime.now(ZoneInfo("Europe/Budapest")),
        expires_at=datetime.now(ZoneInfo("Europe/Budapest")) + EXPIRY,
    )
    jew_token = jwt.encode(
        session.model_dump(mode="json"), settings.jwt_secret, algorithm="HS256"
    )

    return jew_token


def load_session(jew_token):
    try:
        decoded = jwt.decode(jew_token, settings.jwt_secret, algorithms=["HS256"])

        session = Session.model_validate(decoded)

    except (jwt.InvalidTokenError, ValidationError) as exc:
        raise HTTPException(401, "Invalid token") from exc

    if datetime.now(ZoneInfo("Europe/Budapest")) > session.expires_at:
        raise HTTPException(404, "session expired")

    return session.user_id
