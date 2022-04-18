from rest_framework.routers import SimpleRouter
from game.views import AnnouncementView, AnnouncementsView, EntityView, TeamEntityView, TasksView, TaskView
from django.urls import path

routes = SimpleRouter()

urlpatterns = [
    *routes.urls,
    path("entity", EntityView.as_view(), name="entity"),
    path("entity/<str:teamId>", TeamEntityView.as_view(), name="team-entity"),
    path("task", TasksView.as_view(), name="tasks"),
    path("task/<str:taskId>", TaskView.as_view(), name="task"),
    path("announcement", AnnouncementsView.as_view(), name="announcements"),
    path("announcement/<int:announcementId>", AnnouncementView.as_view(), name="announcement")
]
