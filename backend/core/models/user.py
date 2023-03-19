from typing import Optional
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from core.models.team import Team


class UserManager(BaseUserManager):
    def create_user(self, username: str, password: Optional[str]=None, team: Optional[Team]=None) -> 'User':
        if username is None:
            raise TypeError('Users must have a username.')
        user = self.model(username=username, team=team)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username: str, password: Optional[str]) -> 'User':
        """
        Create and return a `User` with superuser (admin) permissions.
        """
        if password is None:
            raise TypeError('Superusers must have a password.')
        if username is None:
            raise TypeError('Superusers must have an username.')

        user = self.create_user(username, password)
        user.is_superuser = True
        user.save(using=self._db)

        return user



class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(db_index=True, max_length=255, unique=True)
    team: Optional[Team] = models.ForeignKey("core.team", on_delete=models.PROTECT,
                             default=None, null=True)  # type: ignore

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

