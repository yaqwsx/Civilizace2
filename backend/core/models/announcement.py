from __future__ import annotations

from datetime import datetime
from typing import Optional

from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone
from django_enumfield import enum

from core.models.team import Team
from core.models.user import User


class AnnouncementType(enum.Enum):
    normal = 1
    important = 2
    game = 3


class AnnouncementManager(models.Manager):
    def get_unread(self, user: User) -> QuerySet[Announcement]:
        return self.get_team(user.team).exclude(
            models.Exists(
                ReadEvent.objects.filter(announcement=models.OuterRef("pk"), user=user)
            )
        )

    def get_team_unread(self, team: Team) -> QuerySet[Announcement]:
        return self.get_team(team).exclude(
            models.Exists(
                ReadEvent.objects.filter(
                    announcement=models.OuterRef("pk"), user__team=team
                )
            )
        )

    def get_team(self, team: Optional[Team]) -> QuerySet[Announcement]:
        return self.get_visible().filter(teams=team).prefetch_related("readevent_set")

    def get_visible(self) -> QuerySet[Announcement]:
        return (
            self.get_queryset()
            .filter(appearDatetime__lte=timezone.now())
            .order_by("-appearDatetime")
        )

    def get_public(self) -> QuerySet[Announcement]:
        return self.get_visible().exclude(
            models.Exists(
                Team.objects.filter(visible=True).exclude(
                    announcement=models.OuterRef("pk")
                )
            )
        )


class Announcement(models.Model):
    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="createdAnnouncements",
        null=True,
        blank=True,
    )
    type: AnnouncementType = enum.EnumField(AnnouncementType, default=AnnouncementType.normal)  # type: ignore
    appearDatetime = models.DateTimeField("Time of public appearance")
    content = models.TextField("Message content")
    teams = models.ManyToManyField(Team)
    read = models.ManyToManyField(User, through="ReadEvent")

    objects = AnnouncementManager()

    def seenByTeamAt(self, team: Team) -> Optional[datetime]:
        try:
            event = (
                ReadEvent.objects.filter(
                    announcement=self, user__team=team, readAt__isnull=False
                )
                .order_by("readAt")
                .first()
            )
            return event.readAt if event is not None else None
        except ReadEvent.DoesNotExist:
            return None


class ReadEvent(models.Model):
    class Meta:
        unique_together = ("announcement", "user")

    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    readAt = models.DateTimeField(auto_now=True)
