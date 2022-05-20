from rest_framework.routers import SimpleRouter
from game.views import AnnouncementView, AnnouncementsView, EntityView, RoundView, RoundsSentinelView, RoundsView, TeamEntityView, TasksView, TaskView
from django.urls import path

from game.viewsets.entity import EntityViewSet, TeamViewSet
from game.viewsets.tasks import TaskViewSet

routes = SimpleRouter()
routes.register(r'entities', EntityViewSet, basename="entities")
routes.register(r'teams', TeamViewSet, basename="gameteams")
routes.register(r'tasks', TaskViewSet, basename="tasks")

urlpatterns = [
    *routes.urls,
    # path("entity", EntityView.as_view(), name="entity"),
    #path("teamentity/<str:teamId>", TeamEntityView.as_view(), name="team-entity"),
    # path("task", TasksView.as_view(), name="tasks"),
    # path("task/<str:taskId>", TaskView.as_view(), name="task"),
    path("announcement", AnnouncementsView.as_view(), name="announcements"),
    path("announcement/<int:announcementId>", AnnouncementView.as_view(), name="announcement"),
    path("round", RoundsView.as_view(), name="rounds"),
    path("round/sentinel", RoundsSentinelView.as_view(), name="round-sentinel"),

]
