from rest_framework.routers import SimpleRouter
from core.viewsets.user import UserViewSet
from core.viewsets.team import TeamViewSet
from core.viewsets.auth import LoginViewSet, RefreshViewSet

routes = SimpleRouter()

routes.register(r'auth/login', LoginViewSet, basename="auth-login")
routes.register(r'auth/refresh', RefreshViewSet, basename="auth-refresh")

routes.register(r'user', UserViewSet, basename="user")
routes.register(r'team', TeamViewSet, basename="team")

urlpatterns = [
    *routes.urls
]