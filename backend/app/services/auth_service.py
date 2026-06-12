import hashlib
import hmac
import os

from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, create_session_token
from backend.app.repositories.master_repository import MasterRepository
from backend.app.schemas.auth import UserCreate, UserPasswordReset, UserUpdate
from backend.app.services.audit_service import AuditService

_PASSWORD_ALGORITHM = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 390_000


def _hash_password(raw_password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt, _PASSWORD_ITERATIONS)
    return f"{_PASSWORD_ALGORITHM}${_PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(raw_password: str, stored_hash: str) -> bool:
    if stored_hash.startswith(f"{_PASSWORD_ALGORITHM}$"):
        try:
            _, iterations_raw, salt_hex, digest_hex = stored_hash.split("$", 3)
            iterations = int(iterations_raw)
            salt = bytes.fromhex(salt_hex)
            expected_digest = bytes.fromhex(digest_hex)
        except (ValueError, TypeError):
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(candidate, expected_digest)

    legacy_hash = hashlib.sha256(raw_password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_hash, stored_hash)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MasterRepository(db)
        self.audit = AuditService(db)

    def ensure_default_user(self) -> None:
        if self.repo.get_user_by_username("admin") is not None:
            return
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
        self.repo.create_user(
            username="admin",
            password_hash=_hash_password(default_password),
            display_name="System Admin",
            role="admin",
            is_active=True,
        )
        self.db.commit()

    def list_users(self):
        return self.repo.list_users()

    def create_user(self, payload: UserCreate, actor: SessionContext | None = None):
        username = payload.username.strip()
        display_name = payload.display_name.strip()
        role = payload.role.strip()
        if self.repo.get_user_by_username(username) is not None:
            raise ValueError("username already exists")
        user = self.repo.create_user(
            username=username,
            password_hash=_hash_password(payload.password),
            display_name=display_name,
            role=role,
            is_active=payload.is_active,
        )
        self.audit.record(
            customer_id=None,
            entity_type="user",
            entity_key=user.username,
            action="create",
            summary=f"建立使用者 {user.username} / {user.display_name} / {user.role}",
            actor=actor,
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, payload: UserUpdate, actor: SessionContext | None = None):
        user = self.repo.get_user(user_id)
        if user is None:
            raise LookupError("user not found")
        before_display_name = user.display_name
        before_role = user.role
        before_active = user.is_active
        self.repo.update_user(
            user,
            display_name=payload.display_name.strip(),
            role=payload.role.strip(),
            is_active=payload.is_active,
        )
        self.audit.record(
            customer_id=None,
            entity_type="user",
            entity_key=user.username,
            action="update",
            summary=(
                f"更新使用者 {user.username}："
                f"{before_display_name} / {before_role} / {'啟用' if before_active else '停用'}"
                f" -> {user.display_name} / {user.role} / {'啟用' if user.is_active else '停用'}"
            ),
            actor=actor,
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def reset_password(self, user_id: int, payload: UserPasswordReset, actor: SessionContext | None = None) -> None:
        user = self.repo.get_user(user_id)
        if user is None:
            raise LookupError("user not found")
        user.password_hash = _hash_password(payload.password)
        self.audit.record(
            customer_id=None,
            entity_type="user",
            entity_key=user.username,
            action="reset_password",
            summary=f"重設使用者 {user.username} 密碼",
            actor=actor,
        )
        self.db.commit()

    def login(self, username: str, password: str):
        user = self.repo.get_user_by_username(username)
        if user is None or not user.is_active:
            raise ValueError("invalid credentials")
        if not _verify_password(password, user.password_hash):
            raise ValueError("invalid credentials")
        return user

    def guest_session(self) -> dict:
        return {
            "mode": "guest",
            "user": None,
            "display_name": "訪客",
            "token": create_session_token(mode="guest", display_name="訪客"),
            "role": "guest",
        }

    def build_session(self, user) -> dict:
        return {
            "mode": "user",
            "user": user,
            "display_name": user.display_name,
            "token": create_session_token(mode="user", user=user),
            "role": user.role,
        }
