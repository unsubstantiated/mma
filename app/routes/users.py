import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.database import SessionLocal
from app.helpers import admin_required
from app.models import UserModel
from app.schemas import User, UserCreate, UserEdit, UserLogin
from app.session import load_session, make_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/admin/users")
def admin_get_all_users(request: Request):
    db = SessionLocal()

    admin_id = admin_required(db, request)
    try:
        users_db = db.query(UserModel).order_by(UserModel.id.desc()).all()
        logger.info("Admin %s retrieved %d users.", admin_id, len(users_db))
        users = [User.load_from_db(user) for user in users_db]
        return users

    except Exception:
        logger.exception("Failed to retrieve users. (Admin id: %s)", admin_id)
        raise

    finally:
        db.close()


@router.post("/admin/users")
def admin_create_user(request: Request, user: UserCreate):
    db = SessionLocal()

    admin_id = admin_required(db, request)

    try:
        new_user = UserModel(name=user.name, account_number=user.account_number)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info("New User %s created by Admin %d.", new_user.id, admin_id)
        return {"message": "new user created"}

    except Exception:
        db.rollback()
        logger.exception("Failed to create user. (Admin id: %s)", admin_id)
        raise

    finally:
        db.close()


@router.put("/admin/users/{user_id}")
def admin_edit_user(request: Request, user_id: int, edited: UserEdit):
    db = SessionLocal()

    admin_id = admin_required(db, request)

    try:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            logger.warning(
                "Admin %s attempted to edit a nonexistent user (%d).", admin_id, user_id
            )
            raise HTTPException(404, "User not found")

        if edited.name is not None:
            user.name = edited.name

        if edited.account_number is not None:
            user.account_number = edited.account_number

        db.commit()
        db.refresh(user)

        logger.info("User %s edited by Admin %d.", user_id, admin_id)
        return user

    except Exception:
        db.rollback()
        logger.exception("Failed to edit user %s. (Admin id: %d)", user_id, admin_id)
        raise

    finally:
        db.close()


@router.delete("/admin/users/{user_id}")
def admin_delete_user(request: Request, user_id: int):
    db = SessionLocal()

    admin_id = admin_required(db, request)

    try:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            logger.warning(
                "Admin %s attempted to delete a nonexistent user (%d).",
                admin_id,
                user_id,
            )
            raise HTTPException(404, "User not found")

        db.delete(user)
        db.commit()

        logger.info("User %s was deleted by Admin %d.", user_id, admin_id)

    except Exception:
        db.rollback()
        logger.exception("Failed to delete user %s. (Admin id: %d)", user_id, admin_id)
        raise

    finally:
        db.close()


@router.post("/register")
def register(me: UserCreate):

    if not (me.pin_code.isnumeric() and len(me.pin_code) == 4):
        raise HTTPException(status_code=400, detail="pin code wrong format")

    db = SessionLocal()
    try:
        user_db = UserModel(
            name=me.name, account_number=me.account_number, pin_code=me.pin_code
        )

        db.add(user_db)
        db.commit()
        db.refresh(user_db)
        user = User.load_from_db(user_db)

        logger.info("New User registered: %s", user.id)
        return user

    except Exception:
        db.rollback()
        logger.exception("Failed to register new user.")
        raise

    finally:
        db.close()


@router.post("/login")
def login(me: UserLogin):

    if not (me.pin_code.isnumeric() and len(me.pin_code) == 4):
        raise HTTPException(status_code=400, detail="pin code wrong format")

    db = SessionLocal()

    try:
        user_db = (
            db.query(UserModel)
            .filter(UserModel.name == me.name, UserModel.pin_code == me.pin_code)
            .first()
        )

        if user_db is None:
            logger.warning("Failed login attempt for username='%s'.", me.name)
            raise HTTPException(status_code=403, detail="invalid credentials")

        user = User.load_from_db(user_db)

        jew_token = make_session(user.id)

        response = JSONResponse(user.model_dump(), 200)
        response.set_cookie("Session", jew_token)

        logger.info("User %s logged in.", user.id)

        return response

    except Exception:
        logger.exception("Failed to log in user: %s.", me.name)
        raise

    finally:
        db.close()


@router.get("/me")
def get_me(request: Request):
    jew_token = request.cookies.get("Session")
    user_id = load_session(jew_token)

    db = SessionLocal()
    try:
        user_db = db.query(UserModel).filter(UserModel.id == user_id).first()
        user = User.load_from_db(user_db)

        logger.info("User %s retrieved their data.", user_id)
        return user

    except Exception:
        logger.exception("Failed to get User %s data.", user_id)
        raise

    finally:
        db.close()


@router.delete("/me")
def delete_me(request: Request):
    jew_token = request.cookies.get("Session")
    user_id = load_session(jew_token)

    db = SessionLocal()
    try:
        user_db = db.query(UserModel).filter(UserModel.id == user_id).first()

        db.delete(user_db)
        db.commit()

        logger.info("User %s was deleted.", user_id)

    except Exception:
        db.rollback()
        logger.exception("Failed to delete User %s", user_id)
        raise

    finally:
        db.close()


@router.put("/me")
def edit_me(request: Request, edited: UserEdit):
    jew_token = request.cookies.get("Session")
    user_id = load_session(jew_token)

    db = SessionLocal()
    try:
        user_db = db.query(UserModel).filter(UserModel.id == user_id).first()

        if edited.name:
            user_db.name = edited.name

        if edited.account_number:
            user_db.account_number = edited.account_number

        if edited.pin_code:
            if not (edited.pin_code.isnumeric() and len(edited.pin_code) == 4):
                raise HTTPException(status_code=400, detail="pin code wrong format")

            user_db.pin_code = edited.pin_code

        db.commit()
        db.refresh(user_db)

        logger.info("User %s was edited.", user_id)

    except Exception:
        db.rollback()
        logger.warning("Failed to edit User %s", user_id)
        raise
    finally:
        db.close()
