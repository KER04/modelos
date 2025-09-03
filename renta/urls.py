from django.urls import path
from .views import *
urlpatterns = [
    path('renta/', renta_view, name='renta'),
]