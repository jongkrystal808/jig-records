from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, require_permission
from backend.app.core.database import get_db
from backend.app.schemas.auth import (
    AuthSessionRead,
    LoginPayload,
    UserCreate,
    UserPasswordReset,
    UserRead,
    UserUpdate,
)
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthSessionRead)
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        user = service.login(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return service.build_session(user)


@router.post("/guest", response_model=AuthSessionRead)
def guest_entry(db: Session = Depends(get_db)):
    return AuthService(db).guest_session()


@router.get("/users", response_model=list[UserRead], dependencies=[Depends(require_permission("manage"))])
def list_users(db: Session = Depends(get_db)):
    return AuthService(db).list_users()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("manage"))])
def create_user(
    payload: UserCreate,
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        return service.create_user(payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/users/{user_id}", response_model=UserRead, dependencies=[Depends(require_permission("manage"))])
def update_user(
    user_id: int,
    payload: UserUpdate,
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        return service.update_user(user_id, payload, actor=session)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("manage"))])
def reset_password(
    user_id: int,
    payload: UserPasswordReset,
    session: SessionContext = Depends(require_permission("manage")),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        service.reset_password(user_id, payload, actor=session)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
