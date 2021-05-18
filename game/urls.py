from django.urls import path

from game.views import *
from game.views import messageBoard
from game.views import dashboard
from game.views import task
from game.views.generation import (GenerationConfigView, GenerationCountDownView, GenerationInfo)
from game.views import sticker

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("dashboard/", dashboard.DashboardIndexView.as_view(), name="dashboardIndex"),
    path("dashboard/<int:teamId>", dashboard.DashboardStatView.as_view(), name="dashboardStat"),
    path("dashboard/<int:teamId>/messages", dashboard.DashboardMessageView.as_view(), name="dashboardMessages"),
    path("dashboard/<int:teamId>/tasks", dashboard.DashboardTasksView.as_view(), name="dashboardTasks"),
    path("dashboard/<int:teamId>/stickers", dashboard.DashboardStickersView.as_view(), name="dashboardStickers"),

    path("action/", ActionIndexView.as_view(), name="actionIndex"),
    path("action/team/<int:teamId>/makemove/<int:moveId>", ActionInitiateView.as_view(), name="actionInitiate"),
    path("action/team/<int:teamId>/commitmove/<int:moveId>", ActionConfirmView.as_view(), name="actionConfirm"),
    path("action/throwdice/<int:actionId>", ActionDiceThrow.as_view(), name="actionDiceThrow"),

    path("messageBoard/", messageBoard.IndexView.as_view(), name="messageBoardIndex"),
    path("messageBoard/new", messageBoard.NewMessageView.as_view(), name="messageBoardNew"),
    path("messageBoard/edit/<int:messageId>", messageBoard.EditMessageView.as_view(), name="messageBoardEdit"),
    path("messageBoard/delete/<int:messageId>", messageBoard.DeleteMessageView.as_view(), name="messageBoardDelete"),
    path("messageBoard/dismiss/<int:messageId>", messageBoard.DismissMessageView.as_view(), name="messageBoardDismiss"),

    path("stickers/<int:stickerId>", sticker.StickerView.as_view(), name="stickerView"),

    path("generation/config", GenerationConfigView.as_view(), name="generationConfig"),
    path("generation/", GenerationCountDownView.as_view(), name="generationCountdown"),
    path("generation/info", GenerationInfo.as_view(), name="generationInfo"),

    path("tasks", task.TaskIndexView.as_view(), name="taskTaskIndex"),
    path("tasks/new", task.NewTaskView.as_view(), name="taskTaskNew"),
    path("tasks/<int:taskId>/edit", task.EditTaskView.as_view(), name="taskTaskEdit"),
    path("tasks/mapping", task.TaskMappingIndexView.as_view(), name="taskMappingIndex"),

    path("demo", DemoView.as_view(), name="demo")
]