from datetime import datetime, timedelta
import jwt
import os
from app.schemas import Session
from fastapi import HTTPException

EXPIRY = timedelta(days=20)
SECRET = os.urandom(128)


def make_session(user_id):
    session = Session(user_id=user_id, created_at=datetime.now(),
                      expires_at=datetime.now()+EXPIRY
                      )
    jew_token = jwt.encode(session.model_dump(), SECRET, algorithm="HS256")

    return jew_token


def load_session(jew_token):
    try:
        decoded = jwt.decode(jew_token, SECRET, algorithms=["HS256"])

        session = Session.model_validate(decoded)

        if datetime.now() > session.expires_at:
            raise HTTPException(404, "session expired")

        return session.user_id

    except Exception:
        raise HTTPException(401, "Invalid token")
