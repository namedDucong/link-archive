"""
테스트용 사용자 생성 api
"""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user = User(
        email=user_data.email,
        name=user_data.name,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists",
        )

    db.refresh(user)

    return user


@router.get("", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .all()
    )

    return users