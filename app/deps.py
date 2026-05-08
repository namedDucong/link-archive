"""
인증이 필요한 API에서 현재 로그인한 사용자를 가져오는 역할
Authorization header 확인
→ JWT 검증
→ token의 sub에서 user_id 추출
→ DB에서 User 조회
→ 현재 로그인한 사용자 반환
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.services.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Authorization: Bearer <token> 에서 JWT를 꺼내 검증하고,
    현재 로그인한 User 객체를 반환한다.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    subject = decode_access_token(token)

    if subject is None:
        raise credentials_exception

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise credentials_exception

    return user