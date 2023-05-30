from rest_framework.routers import SimpleRouter

from game.viewsets.action_no_init import NoInitActionViewSet
from game.viewsets.action_team import TeamActionViewSet
from game.viewsets.action_view_helper import ActionLogViewSet
from game.viewsets.armies import ArmiesViewSet
from game.viewsets.entity import EntityViewSet
from game.viewsets.map import MapViewSet
from game.viewsets.mapdiff import MapDiffViewSet
from game.viewsets.printers import PrinterViewSet
from game.viewsets.state import StateViewSet
from game.viewsets.stickers import StickerViewSet
from game.viewsets.tasks import TaskViewSet
from game.viewsets.team import TeamViewSet
from game.viewsets.tick import TickViewSet
from game.viewsets.turns import TurnsViewSet

routes = SimpleRouter()
routes.register(r"entities", EntityViewSet, basename="entities")
routes.register(r"teams", TeamViewSet, basename="gameteams")
routes.register(r"tasks", TaskViewSet, basename="tasks")
routes.register(r"actions/logs", ActionLogViewSet, basename="actionlogs")
routes.register(r"actions/team", TeamActionViewSet, basename="actionsteam")
routes.register(r"actions/noinit", NoInitActionViewSet, basename="actionsnoinit")
routes.register(r"turns", TurnsViewSet, basename="turns")
routes.register(r"printers", PrinterViewSet, basename="printers")
routes.register(r"stickers", StickerViewSet, basename="stickers")
routes.register(r"state", StateViewSet, basename="states")
routes.register(r"mapupdates", MapDiffViewSet, basename="mapdiff")
routes.register(r"map", MapViewSet, basename="map")
routes.register(r"armies", ArmiesViewSet, basename="armies")
routes.register(r"tick", TickViewSet, basename="tick")


urlpatterns = [*routes.urls]
