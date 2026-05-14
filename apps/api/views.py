# apps/api/views.py

from http import HTTPStatus

from dmr import Controller
from dmr.components import Path
from dmr.plugins.msgspec import MsgspecSerializer
from dmr.response import APIError
from dmr.security.django_session import DjangoSessionSyncAuth

from apps.users.models import User

from .schemas.user import UserPathParams, UserSchema


class UserListController(Controller[MsgspecSerializer]):
    """List all users."""

    auth = [DjangoSessionSyncAuth()]

    def get(self) -> list[UserSchema]:
        users = User.objects.all()
        return [
            UserSchema(
                id=u.id,
                username=u.username,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
            )
            for u in users
        ]


class UserDetailController(
    Controller[MsgspecSerializer],
    Path[UserPathParams],
):
    """Retrieve a single user by ID."""

    auth = [DjangoSessionSyncAuth()]

    def get(self) -> UserSchema:
        try:
            user = User.objects.get(id=self.parsed_path.user_id)
        except User.DoesNotExist:
            raise APIError(
                "User not found",
                status_code=HTTPStatus.NOT_FOUND,
            )
        return UserSchema(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )