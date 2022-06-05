from rest_framework.routers import SimpleRouter
from game.views import AnnouncementView, AnnouncementsView, EntityView, RoundView, RoundsSentinelView, RoundsView, TeamEntityView, TasksView, TaskView
from django.urls import path

from game.viewsets.entity import EntityViewSet, TeamViewSet
from game.viewsets.printers import PrinterViewSet
from game.viewsets.stickers import StickerViewSet
from game.viewsets.tasks import TaskViewSet
from game.viewsets.action import ActionViewSet
from game.viewsets.turns import TurnsViewSet
from game.viewsets.voucher import VoucherViewSet
from game.viewsets.state import StateViewSet

routes = SimpleRouter()
routes.register(r'entities', EntityViewSet, basename="entities")
routes.register(r'teams', TeamViewSet, basename="gameteams")
routes.register(r'tasks', TaskViewSet, basename="tasks")
routes.register(r'actions', ActionViewSet, basename="actions")
routes.register(r'turns', TurnsViewSet, basename="turns")
routes.register(r'vouchers', VoucherViewSet, basename="vouchers")
routes.register(r'printers', PrinterViewSet, basename="printers")
routes.register(r'stickers', StickerViewSet, basename="stickers")
routes.register(r'state', StateViewSet, basename="states")

urlpatterns = [
    *routes.urls
]
