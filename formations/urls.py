from django.urls import path
from . import views

urlpatterns = [
    path('', views.formations_catalog, name='formations_catalog'),
    path('filtrer/', views.filtrer_formations, name='filtrer_formations'),
    path('<int:id>/detail-json/', views.formation_detail_json, name='formation_detail_json'),
    path('debug/inscriptions/', views.debug_inscriptions, name='debug_inscriptions'),
    path('debug/complete-payment/<str:transaction_id>/', views.debug_complete_payment, name='debug_complete_payment'),
]
