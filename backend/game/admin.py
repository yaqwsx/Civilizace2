from typing import Any, Type

from django.contrib import admin
from django.db import models

from game.models import (
    DbAction,
    DbEntities,
    DbInteraction,
    DbMapDiff,
    DbMapState,
    DbScheduledAction,
    DbState,
    DbSticker,
    DbTask,
    DbTaskAssignment,
    DbTaskPreference,
    DbTeamState,
    DbTurn,
    DbWorldState,
    Printer,
)


def get_list_display_all(model: Type[models.Model]) -> list[str]:
    return ["__str__"] + [field.name for field in model._meta.fields]


@admin.register(DbAction)
class DbActionAdmin(admin.ModelAdmin):
    class InteractionsInline(admin.TabularInline):
        model = DbInteraction
        show_change_link = True
        extra = 0

    class CreatedScheduledActionsInline(admin.TabularInline):
        model = DbScheduledAction
        fk_name = "created_from"
        verbose_name = "Created Scheduled Action"
        show_change_link = True
        extra = 0

    class ActionSchedulingInline(admin.TabularInline):
        model = DbScheduledAction
        fk_name = "action"
        verbose_name = "Action Scheduling"
        show_change_link = True
        extra = 0

    inlines = [
        InteractionsInline,
        CreatedScheduledActionsInline,
        ActionSchedulingInline,
    ]
    list_display = [
        "id",
        "actionType",
        "description",
        "args",
        "last_interaction_type",
        "entities",
    ]

    @admin.display(ordering="entitiesRevision")
    def entities(self, obj: DbAction):
        return DbEntities.objects.get(id=obj.entitiesRevision)

    # @admin.display(ordering="interactions__phase")
    def last_interaction_type(self, obj: DbAction):
        return obj.lastInteraction().phase


@admin.register(DbEntities)
class DbEntitiesAdmin(admin.ModelAdmin):
    list_display = ["__str__", "id"]


@admin.register(DbMapState, DbWorldState)
class DbJsonStateAdmin(admin.ModelAdmin):
    class DbStateInline(admin.TabularInline):
        model = DbState
        verbose_name = "Parent State"
        show_change_link = True
        extra = 0

    inlines = [DbStateInline]
    list_display = ["__str__", "id"]


@admin.register(DbTeamState)
class DbTeamStateAdmin(admin.ModelAdmin):
    list_display = ["__str__", "id", "team"]


@admin.register(DbInteraction)
class DbInteractionAdmin(admin.ModelAdmin):
    list_display = get_list_display_all(DbInteraction)


@admin.register(DbMapDiff)
class DbMapDiffAdmin(admin.ModelAdmin):
    list_display = get_list_display_all(DbMapDiff)


@admin.register(DbScheduledAction)
class DbScheduledActionAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "id",
        "action",
        "created",
        "author",
        "created_from",
        "start_game_time",
        "delay_s",
        "target_game_time",
        "performed",
    ]

    @admin.display(
        ordering=models.functions.Concat(
            "start_round", models.Value(" "), "start_time_s"
        )
    )
    def start_game_time(self, obj: DbScheduledAction):
        return str(obj.startGameTime)

    def target_game_time(self, obj: DbScheduledAction):
        return str(target) if (target := obj.targetGameTime()) is not None else None


@admin.register(DbState)
class DbStateAdmin(admin.ModelAdmin):
    class CreatedByInline(admin.TabularInline):
        model = DbInteraction
        verbose_name = "Created By"
        show_change_link = True
        extra = 0

    inlines = [CreatedByInline]
    list_display = ["__str__", "id", "created_by_display", "mapState", "worldState"]

    @admin.display(ordering="interaction", description="Created By")
    def created_by_display(self, obj: DbState):
        return obj.get_interaction()


@admin.register(DbSticker)
class DbStickerAdmin(admin.ModelAdmin):
    list_display = get_list_display_all(DbSticker)


@admin.register(DbTask)
class DbTaskAdmin(admin.ModelAdmin):
    class AssignmentsInline(admin.TabularInline):
        model = DbTaskAssignment
        show_change_link = True
        extra = 0

    class PreferencesInline(admin.StackedInline):
        model = DbTaskPreference
        show_change_link = True
        extra = 0

    inlines = [AssignmentsInline, PreferencesInline]
    list_display = [
        "__str__",
        "id",
        "name",
        "capacity",
        "assignments_count_display",
        "free_count_display",
        "orgDescription",
        "teamDescription",
    ]

    @admin.display(description="Assigned Spots")
    def assignments_count_display(self, obj: DbTask):
        return obj.assignments.count()  # type: ignore

    @admin.display(description="Free Spots")
    def free_count_display(self, obj: DbTask):
        return obj.capacity - obj.assignments.count()  # type: ignore


@admin.register(DbTaskAssignment)
class DbTaskAssignmentAdmin(admin.ModelAdmin):
    list_display = get_list_display_all(DbTaskAssignment)


@admin.register(DbTaskPreference)
class DbTaskPreferenceAdmin(admin.ModelAdmin):
    list_display = get_list_display_all(DbTaskPreference)


@admin.register(DbTurn)
class DbTurnAdmin(admin.ModelAdmin):
    list_display = get_list_display_all(DbTurn)
    ordering = ["id"]


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = get_list_display_all(Printer)
