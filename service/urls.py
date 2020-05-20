from django.urls import path

from game.views import *
from game.views import messageBoard
from game.views import dashboard

from service.views import ValidateEntities, DownloadTechTree, ViewTechTree, ViewVyrobas

urlpatterns = [
    path("validateEntity", ValidateEntities.as_view(), name="validateEntities"),
    path("techTree", DownloadTechTree.as_view(), name="downloadTechTree"),
    path("techTree/view", ViewTechTree.as_view(), name="viewTechTree"),
    path("vyrobas/view", ViewVyrobas.as_view(), name="viewVyrobas")
]