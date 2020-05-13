from django.urls import path

from game.views import *
from game.views import messageBoard
from game.views import dashboard

from service.views import ValidateEntities

urlpatterns = [
    path("validateEntity", ValidateEntities.as_view(), name="validateEntities")
]