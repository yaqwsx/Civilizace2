from django.urls import path

from game.views import *

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("dashboard/", DashboardIndexView.as_view(), name="dashboardIndex"),
    path("dashboard/<int:teamId>", DashboardStatView.as_view(), name="dashboardStat"),
    path("action/", ActionIndexView.as_view(), name="actionIndex"),
    path("demo", DemoView.as_view(), name="demo")
]