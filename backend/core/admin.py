from typing import Type

from django.contrib import admin
from django.db import models

from core.models import announcement, team, user


def get_list_display_all(model: Type[models.Model]) -> list[str]:
    return ["__str__"] + [field.name for field in model._meta.fields]


@admin.register(user.User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "username",
        "team",
        "is_org_display",
        "is_superuser",
        "last_login",
    ]

    @admin.display(boolean=True, description="Org")
    def is_org_display(self, obj: user.User):
        return obj.is_org


@admin.register(team.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = get_list_display_all(team.Team)


@admin.register(announcement.Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    class DbStateInline(admin.TabularInline):
        model = announcement.ReadEvent
        readonly_fields = ["readAt"]
        show_change_link = True
        extra = 0

    inlines = [DbStateInline]
    list_display = get_list_display_all(announcement.Announcement)


@admin.register(announcement.ReadEvent)
class ReadEventAdmin(admin.ModelAdmin):
    list_display = ["__str__", "user", "announcement", "announcement_content", "readAt"]
    readonly_fields = ["readAt"]

    @admin.display(ordering="announcement__content")
    def announcement_content(self, obj: announcement.ReadEvent):
        return obj.announcement.content
