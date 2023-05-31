from __future__ import annotations
from datetime import datetime
from typing import Optional
from django.db import models
from core.models.user import User
from core.models.team import Team
from django.db.models import Count
from django.db.models.query import QuerySet
from django.utils import timezone


class AnnouncementType(models.IntegerChoices):
    normal = 1
    important = 2
    game = 3


class AnnouncementManager(models.Manager):
    def getUnread(self, user: User) -> QuerySet[Announcement]:
        return self.getTeam(user.team).filter(
            ~models.Exists(
                ReadEvent.objects.filter(user=user, announcement=models.OuterRef("pk"))
            )
        )

    def getTeamUnread(self, team: Team) -> QuerySet[Announcement]:
        return self.getTeam(team).filter(
            ~models.Exists(
                ReadEvent.objects.filter(
                    announcement=models.OuterRef("pk"), user__team=team
                )
            )
        )

    def getTeam(self, team: Optional[Team]) -> QuerySet[Announcement]:
        return self.getVisible().filter(teams=team).prefetch_related("readevent_set")

    def getVisible(self) -> QuerySet[Announcement]:
        return (
            self.get_queryset()
            .filter(appearDatetime__lte=timezone.now())
            .order_by("-appearDatetime")
        )

    def getPublic(self) -> QuerySet[Announcement]:
        tCount = Team.objects.filter(visible=True).count()
        return (
            self.get_queryset()
            .annotate(teams_count=Count("teams"))
            .filter(teams_count__gte=tCount)
        )


class Announcement(models.Model):
    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="announcementsFrom", null=True
    )
    appearDatetime = models.DateTimeField("Time of appearance the message")
    type = models.IntegerField(
        choices=AnnouncementType.choices, default=AnnouncementType.normal
    )
    content = models.TextField("Message content")
    teams = models.ManyToManyField(Team)
    read = models.ManyToManyField(User, through="ReadEvent")

    objects = AnnouncementManager()

    def typeString(self):
        return AnnouncementType(self.type).name

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
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    readAt = models.DateTimeField(auto_now=True)
