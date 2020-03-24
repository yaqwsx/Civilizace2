from django.urls import path

from game.views import *

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("dashboard/", DashboardIndexView.as_view(), name="dashboardIndex"),
    path("dashboard/<int:teamId>", DashboardStatView.as_view(), name="dashboardStat"),
    path("action/", ActionIndexView.as_view(), name="actionIndex"),
    path("action/team/<int:teamId>/makemove/<int:moveId>", ActionMoveView.as_view(), name="actionMove"),
    path("action/team/<int:teamId>/commitmove/<int:moveId>", ActionConfirmView.as_view(), name="actionConfirm"),
    path("demo", DemoView.as_view(), name="demo")
]