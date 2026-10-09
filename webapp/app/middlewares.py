from http import HTTPStatus
from typing import Annotated

from fastapi import Cookie, HTTPException
from sqlalchemy import text

from .models import Chair, Owner, User
from .sql import engine

from .dictionary import chairs_by_token, users_by_token, owners_by_token, unsent_by_ride, latest_status_by_ride

def clear_auth_cache() -> None:
    chairs_by_token.clear()
    users_by_token.clear()
    owners_by_token.clear()
    unsent_by_ride.clear()
    latest_status_by_ride.clear()

def app_auth_middleware(app_session: Annotated[str | None, Cookie()] = None) -> User:
    if not app_session:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="app_session cookie is required"
        )
    
    user = users_by_token.get(app_session)
    if user is not None:
        return user

    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE access_token = :access_token"),
            {"access_token": app_session},
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail="invalid access token"
            )
        user = User.model_validate(row)
        users_by_token[app_session] = user
        return user


def owner_auth_middleware(
    owner_session: Annotated[str | None, Cookie()] = None,
) -> Owner:
    if not owner_session:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="owner_session cookie is required",
        )

    owner = owners_by_token.get(owner_session)
    if owner is not None:
        return owner

    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM owners WHERE access_token = :access_token"),
            {"access_token": owner_session},
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail="invalid access token"
            )

        owner = Owner.model_validate(row)
        owners_by_token[owner_session] = owner
        return owner


def chair_auth_middleware(
    chair_session: Annotated[str | None, Cookie()] = None,
) -> Chair:
    if not chair_session:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="chair_session cookie is required",
        )
    chair = chairs_by_token.get(chair_session)
    if chair is not None:
        return chair

    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM chairs WHERE access_token = :access_token"),
            {"access_token": chair_session},
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail="invalid access token"
            )

        chair = Chair.model_validate(row)
        chairs_by_token[chair_session] = chair
        return chair
