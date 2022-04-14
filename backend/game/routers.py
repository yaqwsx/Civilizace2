from rest_framework.routers import SimpleRouter
from game.views import EntityView, TeamEntityView
from django.urls import path

routes = SimpleRouter()

urlpatterns = [
    *routes.urls,
    path("entity", EntityView.as_view(), name="entity"),
    path("entity/<str:teamId>", TeamEntityView.as_view(), name="team-entity")
]
