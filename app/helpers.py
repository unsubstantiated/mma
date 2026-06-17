from fastapi import HTTPException, Request
from app.session import load_session
from app.models import UserModel


def admin_required(db, request: Request):

    jew_token = request.cookies.get("Session")

    if not jew_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    is_admin_id = load_session(jew_token)

    if not is_admin_id:
        raise HTTPException(status_code=401, detail="Invalid session")

    role = db.query(UserModel.role).filter(
        UserModel.id == is_admin_id).scalar()

    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return is_admin_id
