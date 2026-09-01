import hashlib
import hmac
import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.core.auth import SessionContext, create_session_token
from backend.app.core.config import settings
from backend.app.repositories.master_repository import MasterRepository
from backend.app.schemas.auth import OwnPasswordChange, UserCreate, UserPasswordReset, UserUpdate
from backend.app.services.audit_service import AuditService
from backend.app.utils.csv_tools import stream_csv_text

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
        if settings.is_production and settings.uses_default_admin_password:
            raise RuntimeError(
                "DEFAULT_ADMIN_PASSWORD must be set to a strong non-default value before bootstrapping the first Super Admin user in production"
            )
        default_password = settings.default_admin_password or "admin123"
        self.repo.create_user(
            username="admin",
            email=None,
            password_hash=_hash_password(default_password),
            display_name="System Admin",
            role="super_admin",
            is_active=True,
        )
        self.db.commit()

    def list_users(self):
        return self._serialize_users(self.repo.list_users())

    def list_users_page(self, *, page: int, page_size: int, keyword: str = "", is_active: bool | None = None) -> dict:
        users, total = self.repo.list_users_page(page=page, page_size=page_size, keyword=keyword, is_active=is_active)
        return {"items": self._serialize_users(users), "page": page, "page_size": page_size, "total": total}

    def stream_form_user_export_csv(self, *, keyword: str = "", is_active: bool | None = None):
        rows = (
            {
                "帳號": user.username,
                "顯示名稱": user.display_name,
                "Email": user.email or "",
                "角色": user.role,
                "狀態": "啟用" if user.is_active else "停用",
            }
            for user in self.repo.iter_users(keyword=keyword, is_active=is_active)
        )
        return stream_csv_text(["帳號", "顯示名稱", "Email", "角色", "狀態"], rows)

    def list_users_by_customer(self, customer_id: int):
        return self._serialize_users(self.repo.list_users_by_customer(customer_id))

    def _normalize_allowed_customer_ids(self, allowed_customer_ids: list[int]) -> list[int]:
        unique_ids = sorted({int(customer_id) for customer_id in allowed_customer_ids})
        if not unique_ids:
            return []
        customers = self.repo.list_customers_by_ids(unique_ids)
        found_ids = {customer.id for customer in customers}
        missing_ids = [customer_id for customer_id in unique_ids if customer_id not in found_ids]
        if missing_ids:
            raise ValueError(f"customer not found: {missing_ids[0]}")
        return unique_ids

    @staticmethod
    def _normalize_email(email: str | None) -> str | None:
        if email is None:
            return None
        stripped = email.strip()
        return stripped or None

    def _serialize_users(self, users) -> list[dict]:
        rows = list(users)
        allowed_ids_by_user = self.repo.list_allowed_customer_ids_for_users([user.id for user in rows])
        customer_ids = sorted({customer_id for ids in allowed_ids_by_user.values() for customer_id in ids})
        customer_by_id = {customer.id: customer for customer in self.repo.list_customers_by_ids(customer_ids)}
        return [
            self._serialize_user(
                user,
                allowed_customer_ids=allowed_ids_by_user[user.id],
                customer_by_id=customer_by_id,
            )
            for user in rows
        ]

    def _serialize_user(self, user, *, allowed_customer_ids: list[int] | None = None, customer_by_id=None):
        allowed_ids = self.repo.list_allowed_customer_ids_for_user(user.id) if allowed_customer_ids is None else allowed_customer_ids
        if customer_by_id is None:
            customer_by_id = {customer.id: customer for customer in self.repo.list_customers_by_ids(allowed_ids)}
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "is_active": user.is_active,
            "allowed_customer_ids": allowed_ids,
            "allowed_customers": [
                {
                    "id": customer.id,
                    "code": customer.code,
                    "name": customer.name,
                }
                for customer_id in allowed_ids
                if (customer := customer_by_id.get(customer_id)) is not None
            ],
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    def create_user(self, payload: UserCreate, actor: SessionContext | None = None):
        username = payload.username.strip()
        email = self._normalize_email(payload.email)
        display_name = payload.display_name.strip()
        role = payload.role.strip()
        if self.repo.get_user_by_username(username) is not None:
            raise ValueError("username already exists")
        allowed_customer_ids = self._normalize_allowed_customer_ids(payload.allowed_customer_ids)
        user = self.repo.create_user(
            username=username,
            email=email,
            password_hash=_hash_password(payload.password),
            display_name=display_name,
            role=role,
            is_active=payload.is_active,
        )
        self.repo.replace_allowed_customers_for_user(user.id, allowed_customer_ids)
        self.audit.record(
            customer_id=None,
            entity_type="user",
            entity_key=user.username,
            action="create",
            summary=f"建立使用者 {user.username} / {user.display_name} / {user.role} / {user.email or '-'}",
            actor=actor,
        )
        self.db.commit()
        return self._serialize_user(user)

    def update_user(self, user_id: int, payload: UserUpdate, actor: SessionContext | None = None):
        user = self.repo.get_user(user_id)
        if user is None:
            raise LookupError("user not found")
        before_email = user.email
        before_display_name = user.display_name
        before_role = user.role
        before_active = user.is_active
        before_allowed_customer_ids = self.repo.list_allowed_customer_ids_for_user(user.id)
        email = self._normalize_email(payload.email)
        normalized_role = payload.role.strip()
        if user.role == "super_admin" and (normalized_role != "super_admin" or not payload.is_active):
            if self.repo.count_active_users_by_role("super_admin") <= 1:
                raise ValueError("至少必須保留一位啟用中的 Super Admin")
        allowed_customer_ids = (
            before_allowed_customer_ids
            if payload.allowed_customer_ids is None
            else self._normalize_allowed_customer_ids(payload.allowed_customer_ids)
        )
        self.repo.update_user(
            user,
            email=email,
            display_name=payload.display_name.strip(),
            role=normalized_role,
            is_active=payload.is_active,
        )
        self.repo.replace_allowed_customers_for_user(user.id, allowed_customer_ids)
        self.audit.record(
            customer_id=None,
            entity_type="user",
            entity_key=user.username,
            action="update",
            summary=(
                f"更新使用者 {user.username}："
                f"{before_email or '-'} / {before_display_name} / {before_role} / {'啟用' if before_active else '停用'}"
                f" / 客戶 {','.join(str(customer_id) for customer_id in before_allowed_customer_ids) or '未分派'}"
                f" -> {user.email or '-'} / {user.display_name} / {user.role} / {'啟用' if user.is_active else '停用'}"
                f" / 客戶 {','.join(str(customer_id) for customer_id in allowed_customer_ids) or '未分派'}"
            ),
            actor=actor,
        )
        self.db.commit()
        return self._serialize_user(user)

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

    def change_own_password(
        self,
        user_id: int,
        payload: OwnPasswordChange,
        actor: SessionContext | None = None,
    ) -> None:
        user = self.repo.get_user(user_id)
        if user is None:
            raise LookupError("user not found")
        if not _verify_password(payload.current_password, user.password_hash):
            raise ValueError("目前密碼不正確")
        if hmac.compare_digest(payload.current_password, payload.new_password):
            raise ValueError("新密碼不可與目前密碼相同")
        user.password_hash = _hash_password(payload.new_password)
        self.audit.record(
            customer_id=None,
            entity_type="user",
            entity_key=user.username,
            action="change_own_password",
            summary=f"使用者 {user.username} 修改自己的密碼",
            actor=actor,
        )
        self.db.commit()

    @staticmethod
    def _serialize_model_shortcut(preference, model_code: str) -> dict:
        return {
            "model_id": preference.model_id,
            "model_code": model_code,
            "query_count": preference.query_count,
            "last_queried_at": preference.last_queried_at,
            "pinned": preference.is_pinned,
        }

    def list_model_shortcut_preferences(self, *, user_id: int, customer_id: int) -> list[dict]:
        return [
            self._serialize_model_shortcut(preference, model_code)
            for preference, model_code in self.repo.list_model_shortcut_preferences(
                user_id=user_id,
                customer_id=customer_id,
            )
        ]

    def record_model_shortcut_query(self, *, user_id: int, customer_id: int, model_id: int) -> dict:
        model = self.repo.get_model(model_id, customer_id)
        if model is None or not model.is_active:
            raise LookupError("model not found")
        preference = self.repo.get_model_shortcut_preference(
            user_id=user_id,
            customer_id=customer_id,
            model_id=model_id,
        )
        if preference is None:
            preference = self.repo.create_model_shortcut_preference(
                user_id=user_id,
                customer_id=customer_id,
                model_id=model_id,
            )
        preference.query_count += 1
        preference.last_queried_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(preference)
        return self._serialize_model_shortcut(preference, model.code)

    def set_model_shortcut_pin(
        self,
        *,
        user_id: int,
        customer_id: int,
        model_id: int,
        pinned: bool,
    ) -> dict:
        model = self.repo.get_model(model_id, customer_id)
        if model is None or not model.is_active:
            raise LookupError("model not found")
        preference = self.repo.get_model_shortcut_preference(
            user_id=user_id,
            customer_id=customer_id,
            model_id=model_id,
        )
        if preference is None:
            preference = self.repo.create_model_shortcut_preference(
                user_id=user_id,
                customer_id=customer_id,
                model_id=model_id,
            )
        preference.is_pinned = pinned
        self.db.commit()
        self.db.refresh(preference)
        return self._serialize_model_shortcut(preference, model.code)

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
            "user": self._serialize_user(user),
            "display_name": user.display_name,
            "token": create_session_token(mode="user", user=user),
            "role": user.role,
        }
