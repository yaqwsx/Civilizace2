from __future__ import annotations
from typing import Optional
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from core.models.team import Team


class UserManager(BaseUserManager):
    def create_user(
        self, username: str, password: str, team: Optional[Team] = None
    ) -> User:
        assert isinstance(username, str)
        assert isinstance(password, str)

        user = self.model(username=username, team=team)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username: str, password: str) -> User:
        """
        Create and return a `User` with superuser (admin) permissions.
        """
        assert password is not None
        user = self.create_user(username, password)
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(db_index=True, max_length=255, unique=True)
    team: Optional[Team] = models.ForeignKey(
        "core.team", on_delete=models.PROTECT, default=None, null=True
    )  # type: ignore

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def isPlayer(self) -> bool:
        return not self.isOrg

    @property
    def isOrg(self) -> bool:
        return self.team is None

    @property
    def isSuperUser(self) -> bool:
        return self.is_superuser
