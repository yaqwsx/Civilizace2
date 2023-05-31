from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from core.models.team import Team


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(db_index=True, max_length=255, unique=True)
    team = models.ForeignKey(Team, on_delete=models.PROTECT, default=None, null=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = BaseUserManager()

    @property
    def is_org(self) -> bool:
        return self.team is None

    @staticmethod
    def update_or_create(
        *,
        username: str,
        password: str,
        superuser: bool = False,
        team: Optional[Team] = None,
    ) -> User:
        if superuser and team is not None:
            raise ValueError(f"Superuser {username!r} cannot have team {team!r}")

        assert isinstance(username, str)
        assert password, "Password cannot be empty"
        assert isinstance(password, str)

        user = User(username=username, team=team)
        user.set_password(password)
        user.is_superuser = superuser
        user.save()

        return user
