import logging

from fastapi import HTTPException, Request

from app.models import UserModel
from app.session import load_session

logger = logging.getLogger(__name__)


def admin_required(db, request: Request):

    jew_token = request.cookies.get("Session")

    if not jew_token:
        logger.warning("Access denied: missing jew-token.")
        raise HTTPException(status_code=401, detail="Not authenticated")

    is_admin_id = load_session(jew_token)

    if not is_admin_id:
        logger.warning("Access denied: invalid jew-token.")
        raise HTTPException(status_code=401, detail="Invalid session")

    role = db.query(UserModel.role).filter(UserModel.id == is_admin_id).scalar()

    if role != "jew":
        logger.warning("Access denied: user %s is not an admin.", is_admin_id)
        raise HTTPException(status_code=403, detail="Admin access required")

    return is_admin_id
