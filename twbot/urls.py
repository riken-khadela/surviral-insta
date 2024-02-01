from django.urls import path, include
from .views import *
urlpatterns = [
    path('api/run-command/', run_commandss.as_view(), name='api-register'),
]