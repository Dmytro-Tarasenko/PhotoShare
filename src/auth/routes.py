from datetime import datetime

from jose import jwt
from sqlalchemy import select, or_

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from starlette.requests import Request

from userprofile.model import TokenModel, UserAuthModel, UserDBModel
from database import get_db

from auth.service import auth as auth_service
from userprofile.orm import UserORM

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserDBModel,
    responses={
        409: {"description": "User already exists"},
        201: {"model": UserDBModel},
    },
)
async def new_user(
    user: UserAuthModel, db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    exists = await db.execute(
        select(UserORM).filter(
            or_(UserORM.email == user.email, UserORM.username == user.username)
        )
    )
    exists = exists.scalars().first()
    if exists:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "details": [
                    {"msg": "User with such email or username already registered"}
                ]
            },
        )

    hashed_pwd = auth_service.get_hash_password(user.password)
    user_orm = UserORM(email=user.email, username=user.username, password=hashed_pwd)
    db.add(user_orm)
    await db.commit()
    await db.refresh(user_orm)

    ret_user = await db.execute(select(UserORM).filter(UserORM.email == user.email))
    ret_user = ret_user.scalars().first()
    user_db_model = UserDBModel.from_orm(ret_user)
    user_db_model.registered_at = user_db_model.registered_at.isoformat()
    return JSONResponse(
        status_code=201,
        content={
            **UserDBModel.from_orm(ret_user).model_dump(
                exclude={"id", "password", "registered_at"}
            ),
            "registered_at": str(ret_user.registered_at),
        },
    )


@router.post("/login", response_model=TokenModel)
async def login(
    request: Request,
    user: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    db_response = await db.execute(
        select(UserORM).filter(UserORM.username == user.username)
    )
    user_db: UserORM = db_response.scalars().first()
    if not user_db:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "details": [{"msg": f"User with username: {user.username} not found"}]
            },
        )

    if not auth_service.verify_password(user.password, user_db.password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"details": [{"msg": "Invalid credentials"}]},
        )

    blacklisted_tokens = await auth_service.get_blacklisted_tokens(user.username, db)
    for blacklisted_token in blacklisted_tokens:
        if (
            blacklisted_token.token
            == request.headers.get("Authorization").split(" ")[1]
        ):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"details": "Token is blacklisted"},
            )

    access_token = auth_service.create_access_token(user_db.email)
    refresh_token = auth_service.create_refresh_token(user_db.email)
    email_token = auth_service.create_email_token(user_db.email)
    user_db.loggedin = True
    await db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "email_token": email_token,
            "token_type": "bearer",
        },
    )


@router.post("/refresh", response_model=TokenModel)
async def refresh(
    request: Request,
    user: Annotated[UserORM, Depends(auth_service.get_refresh_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    if not user.loggedin:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"details": "User not logged in. Use /auth/login"},
        )

    refresh_token = request.headers.get("Authorization").split(" ")[1]
    payload = jwt.decode(
        refresh_token,
        auth_service.SECRET_512,
        algorithms=[auth_service.REFRESH_ALGORITHM],
    )

    blacklisted_tokens = await auth_service.get_blacklisted_tokens(user.email, db)
    for blacklisted_token in blacklisted_tokens:
        if blacklisted_token.expire_refresh == datetime.fromtimestamp(payload["exp"]):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"details": "Token is blacklisted"},
            )

    access_token = await auth_service.create_access_token(user.email)
    email_token = await auth_service.create_email_token(user.email)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "email_token": email_token,
            "token_type": "bearer",
        },
    )


@router.get("/logout")
async def logout(
    token: Annotated[str, Depends(auth_service.oauth2_schema)],
    user_orm: Annotated[UserORM, Depends(auth_service.get_access_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    try:
        if not user_orm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_orm.loggedin = False

        payload = jwt.decode(
            token, auth_service.SECRET_256, algorithms=[auth_service.ACCESS_ALGORITHM]
        )
        expires_delta = payload["exp"] - payload["iat"]

        await auth_service.add_to_blacklist(
            token, user_orm.email, user_orm.username, expires_delta, db
        )
        await db.commit()

        return {"details": "User logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )
