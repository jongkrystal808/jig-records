from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, require_permission, resolve_customer_scope
from backend.app.core.database import get_db
from backend.app.schemas.auth import (
    AuthSessionRead,
    LoginPayload,
    ModelShortcutPinUpdate,
    ModelShortcutPreferenceRead,
    OwnPasswordChange,
    UserCreate,
    UserPasswordReset,
    UserRead,
    UserPageRead,
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


@router.get(
    "/preferences/model-shortcuts",
    response_model=list[ModelShortcutPreferenceRead],
    dependencies=[Depends(require_permission("write"))],
)
def list_model_shortcut_preferences(
    customer_id: int = Query(..., ge=1),
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolved_customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    if session.user_id is None or resolved_customer_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="signed-in user required")
    return AuthService(db).list_model_shortcut_preferences(
        user_id=session.user_id,
        customer_id=resolved_customer_id,
    )


@router.post(
    "/preferences/model-shortcuts/{model_id}/query",
    response_model=ModelShortcutPreferenceRead,
    dependencies=[Depends(require_permission("write"))],
)
def record_model_shortcut_query(
    model_id: int,
    customer_id: int = Query(..., ge=1),
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolved_customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    if session.user_id is None or resolved_customer_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="signed-in user required")
    try:
        return AuthService(db).record_model_shortcut_query(
            user_id=session.user_id,
            customer_id=resolved_customer_id,
            model_id=model_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/preferences/model-shortcuts/{model_id}/pin",
    response_model=ModelShortcutPreferenceRead,
    dependencies=[Depends(require_permission("write"))],
)
def set_model_shortcut_pin(
    model_id: int,
    payload: ModelShortcutPinUpdate,
    customer_id: int = Query(..., ge=1),
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    resolved_customer_id = resolve_customer_scope(session, db, customer_id, allow_empty=False)
    if session.user_id is None or resolved_customer_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="signed-in user required")
    try:
        return AuthService(db).set_model_shortcut_pin(
            user_id=session.user_id,
            customer_id=resolved_customer_id,
            model_id=model_id,
            pinned=payload.pinned,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/users", response_model=list[UserRead], dependencies=[Depends(require_permission("super_manage"))])
def list_users(db: Session = Depends(get_db)):
    return AuthService(db).list_users()


@router.get("/users/page", response_model=UserPageRead, dependencies=[Depends(require_permission("super_manage"))])
def list_users_page(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    keyword: str = Query("", max_length=160),
    status_filter: str = Query("all", pattern="^(all|active|inactive)$"),
    db: Session = Depends(get_db),
):
    is_active = None if status_filter == "all" else status_filter == "active"
    return AuthService(db).list_users_page(page=page, page_size=page_size, keyword=keyword, is_active=is_active)


@router.get("/users/form-export", dependencies=[Depends(require_permission("super_manage"))])
def export_form_users(
    keyword: str = Query("", max_length=160),
    status_filter: str = Query("all", pattern="^(all|active|inactive)$"),
    db: Session = Depends(get_db),
):
    is_active = None if status_filter == "all" else status_filter == "active"
    return StreamingResponse(
        content=AuthService(db).stream_form_user_export_csv(keyword=keyword, is_active=is_active),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="form-users.csv"'},
    )


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("super_manage"))])
def create_user(
    payload: UserCreate,
    session: SessionContext = Depends(require_permission("super_manage")),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        return service.create_user(payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/users/{user_id}", response_model=UserRead, dependencies=[Depends(require_permission("super_manage"))])
def update_user(
    user_id: int,
    payload: UserUpdate,
    session: SessionContext = Depends(require_permission("super_manage")),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        return service.update_user(user_id, payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("super_manage"))])
def reset_password(
    user_id: int,
    payload: UserPasswordReset,
    session: SessionContext = Depends(require_permission("super_manage")),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        service.reset_password(user_id, payload, actor=session)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("write"))])
def change_own_password(
    payload: OwnPasswordChange,
    session: SessionContext = Depends(require_permission("write")),
    db: Session = Depends(get_db),
):
    if session.user_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="signed-in user required")
    try:
        AuthService(db).change_own_password(session.user_id, payload, actor=session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
