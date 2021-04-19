from django.urls import path

from game.views import *
from game.views import messageBoard
from game.views import dashboard
from game.views.autoGeneration import GenerationConfigView, GenerationParameters, GenerationCountDownView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("dashboard/", dashboard.DashboardIndexView.as_view(), name="dashboardIndex"),
    path("dashboard/<int:teamId>", dashboard.DashboardStatView.as_view(), name="dashboardStat"),
    path("dashboard/<int:teamId>/messages", dashboard.DashboardMessageView.as_view(), name="dashboardMessages"),

    path("action/", ActionIndexView.as_view(), name="actionIndex"),
    path("action/team/<int:teamId>/makemove/<int:moveId>", ActionInitiateView.as_view(), name="actionInitiate"),
    path("action/team/<int:teamId>/commitmove/<int:moveId>", ActionConfirmView.as_view(), name="actionConfirm"),
    path("action/throwdice/<int:actionId>", ActionDiceThrow.as_view(), name="actionDiceThrow"),

    path("messageBoard/", messageBoard.IndexView.as_view(), name="messageBoardIndex"),
    path("messageBoard/new", messageBoard.NewMessageView.as_view(), name="messageBoardNew"),
    path("messageBoard/edit/<int:messageId>", messageBoard.EditMessageView.as_view(), name="messageBoardEdit"),
    path("messageBoard/delete/<int:messageId>", messageBoard.DeleteMessageView.as_view(), name="messageBoardDelete"),
    path("messageBoard/dismiss/<int:messageId>", messageBoard.DismissMessageView.as_view(), name="messageBoardDismiss"),

    path("generation/params", GenerationParameters.as_view(), name="generationParams"),
    path("generation/config", GenerationConfigView.as_view(), name="generationConfig"),
    path("generation/", GenerationCountDownView.as_view(), name="generationCountdown"),

    path("demo", DemoView.as_view(), name="demo")
]