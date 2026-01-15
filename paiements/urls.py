# paiements/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'transactions', views.TransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Endpoints publics
    path('health/', views.health_check, name='api_health'),
    path('receive-sms/', views.receive_sms_webhook, name='receive_sms'),
    path('create-payment/', views.create_payment, name='create_payment'),
    path('check-payment/', views.check_payment_status, name='check_payment'),
    path('payment-details/<str:transaction_id>/', views.get_payment_details, name='payment_details'),
    
    # Endpoints admin
    path('statistics/', views.get_statistics, name='statistics'),
]
