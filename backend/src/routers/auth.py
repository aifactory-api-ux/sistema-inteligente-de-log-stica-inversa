# backend/src/routers/auth.py

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from src.schemas import (
    LoginRequestSchema,
    TokenResponseSchema,
    AuthResponseSchema,
    UserSchema,
    RefreshTokenRequestSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.security.CORS_ORIGINS.split(',')[0]}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid4()),
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.JWT_SECRET,
        algorithm=settings.jwt.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid4()),
        "type": "refresh",
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.JWT_SECRET,
        algorithm=settings.jwt.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt.JWT_SECRET,
            algorithms=[settings.jwt.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_by_username(db: Session, username: str) -> Optional[dict]:
    query = text("""
        SELECT id, username, email, full_name, role, hashed_password,
               customer_id, is_active, created_at, updated_at
        FROM users
        WHERE username = :username AND is_active = true
    """)
    result = db.execute(query, {"username": username}).fetchone()

    if result:
        return {
            "user_id": str(result[0]),
            "username": result[1],
            "email": result[2],
            "full_name": result[3],
            "role": result[4],
            "hashed_password": result[5],
            "customer_id": result[6],
            "is_active": result[7],
            "created_at": result[8],
            "updated_at": result[9],
        }
    return None


def get_user_permissions(role: str) -> list:
    permissions_map = {
        "B2C_USER": ["returns:create", "returns:read_own"],
        "B2B_USER": ["returns:create", "returns:read_own", "batch:upload"],
        "SUPERVISOR": ["returns:read_all", "returns:update", "control_tower:read", "alerts:manage"],
        "KAM": ["returns:read_all", "returns:update", "batch:approve", "control_tower:read"],
        "ADMIN": ["*"],
    }
    return permissions_map.get(role, [])


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(lambda: None)
) -> UserSchema:
    payload = decode_token(token)
    username: str = payload.get("sub")

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    from src.db.database import SessionLocal
    db_session = SessionLocal()
    try:
        user = get_user_by_username(db_session, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return UserSchema(
            user_id=user["user_id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            permissions=get_user_permissions(user["role"]),
            customer_id=user["customer_id"],
            is_active=user["is_active"],
        )
    finally:
        db_session.close()


async def get_current_active_user(
    current_user: UserSchema = Depends(get_current_user)
) -> UserSchema:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


@router.post("/login", response_model=AuthResponseSchema)
async def login(
    login_data: LoginRequestSchema,
    db: Session = Depends(lambda: None)
):
    from src.db.database import SessionLocal
    db_session = SessionLocal()
    try:
        user = get_user_by_username(db_session, login_data.username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(login_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": user["username"]})
        refresh_token = create_refresh_token(data={"sub": user["username"]})

        logger.info(f"User {user['username']} logged in successfully")

        return AuthResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.jwt.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserSchema(
                user_id=user["user_id"],
                username=user["username"],
                email=user["email"],
                full_name=user["full_name"],
                role=user["role"],
                permissions=get_user_permissions(user["role"]),
                customer_id=user["customer_id"],
                is_active=user["is_active"],
            ),
        )
    finally:
        db_session.close()


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    logger.info("User logged out")
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponseSchema)
async def refresh_token(
    refresh_data: RefreshTokenRequestSchema,
    db: Session = Depends(lambda: None)
):
    payload = decode_token(refresh_data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type"
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    from src.db.database import SessionLocal
    db_session = SessionLocal()
    try:
        user = get_user_by_username(db_session, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        access_token = create_access_token(data={"sub": user["username"]})
        new_refresh_token = create_refresh_token(data={"sub": user["username"]})

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=settings.jwt.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    finally:
        db_session.close()


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: UserSchema = Depends(get_current_active_user)):
    return current_user
