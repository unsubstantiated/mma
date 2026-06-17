from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.database import SessionLocal
from app.models import UserModel
from app.schemas import User, UserCreate, UserEdit, UserLogin
from app.session import load_session, make_session
from app.helpers import admin_required


router = APIRouter()


@router.get("/admin/users")
def get_users(request: Request):
    db = SessionLocal()

    admin_required(db, request)
    try:
        users_db = db.query(UserModel).order_by(UserModel.id.desc()).all()
        users = [User.load_from_db(user) for user in users_db]
        return users

    finally:
        db.close()


@router.post("/admin/users")
def create_user(request: Request, user: UserCreate):
    db = SessionLocal()

    admin_required(db, request)

    try:
        new_user = UserModel(
            name=user.name,
            account_number=user.account_number
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "new user created"}
    finally:
        db.close()


@router.put("/admin/users/{user_id}")
def edit_user(request: Request, user_id: int, edited: UserEdit):
    db = SessionLocal()

    admin_required(db, request)

    try:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            return {"error": "user not found"}

        if edited.name is not None:
            user.name = edited.name

        if edited.account_number is not None:
            user.account_number = edited.account_number

        db.commit()
        db.refresh(user)

        return user

    finally:
        db.close()


@router.delete("/admin/users/{user_id}")
def delete_user(request: Request, user_id: int):
    db = SessionLocal()

    admin_required(db, request)

    try:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            return {"error": "user not found"}

        db.delete(user)
        db.commit()
    finally:
        db.close()


@router.post("/register")
def register(me: UserCreate):

    if me.pin_code.isnumeric() and len(me.pin_code) == 4:
        pass
    else:
        raise HTTPException(status_code=400, detail="pin code wrong format")

    db = SessionLocal()
    try:
        user = UserModel(
            name=me.name, account_number=me.account_number, pin_code=me.pin_code
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return User.load_from_db(user)
    finally:
        db.close()


@router.post("/login")
def login(me: UserLogin):

    if me.pin_code.isnumeric() and len(me.pin_code) == 4:
        pass
    else:
        raise HTTPException(status_code=400, detail="pin code wrong format")

    db = SessionLocal()

    try:
        user_db = db.query(UserModel).filter(
            UserModel.name == me.name,
            UserModel.pin_code == me.pin_code
        ).first()

    finally:
        db.close()

    if user_db is None:
        raise HTTPException(status_code=403, detail="invalid credentials")

    user = User.load_from_db(user_db)

    jew_token = make_session(user.id)

    response = JSONResponse(user.model_dump(), 200)
    response.set_cookie("Session", jew_token)
    return response


@router.get("/me")
def get_me(request: Request):
    jew_token = request.cookies.get("Session")
    user_id = load_session(jew_token)

    db = SessionLocal()
    try:
        user_db = db.query(UserModel).filter(UserModel.id == user_id).first()
        user = User.load_from_db(user_db)

        return user
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
            if edited.pin_code.isnumeric() and len(edited.pin_code) == 4:
                pass
            else:
                raise HTTPException(
                    status_code=400, detail="pin code wrong format")

            user_db.pin_code = edited.pin_code

    finally:
        db.close()
