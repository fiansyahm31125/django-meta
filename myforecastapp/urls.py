# myforecastapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('sarima', views.forecast, name='forecast'),
]
