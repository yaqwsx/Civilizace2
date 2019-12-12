from django.urls import path

from .views import DashboardView, DemoView

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('demo', DemoView.as_view(), name='demo')
]