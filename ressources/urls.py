from django.urls import path
from . import views

urlpatterns = [
    path('ressources/', views.ressources_view, name='ressources'),
]