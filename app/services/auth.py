import os
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

if JWT_SECRET_KEY is None:
    raise RuntimeError("JWT_SECRET_KEY is not set. Please check your .env file.")


password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    사용자가 입력한 비밀번호를 bcrypt hash로 변환한다.
    DB에는 원문 password가 아니라 이 hash만 저장한다.
    """
    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    로그인 시 입력한 비밀번호와 DB에 저장된 password_hash가 일치하는지 확인한다.
    """
    return password_context.verify(plain_password, password_hash)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    JWT access token을 생성한다.

    subject에는 보통 user_id를 문자열로 넣는다.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    return token


def decode_access_token(token: str) -> Optional[str]:
    """
    JWT access token을 검증하고, payload의 sub 값을 반환한다.

    token이 잘못되었거나 만료되었으면 None을 반환한다.
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        subject = payload.get("sub")

        if subject is None:
            return None

        return subject

    except JWTError:
        return None