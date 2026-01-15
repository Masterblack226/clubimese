from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('actualites/', include('actualites.urls')),
    path('formations/', include('formations.urls')),
    path('ressources/', views.ressources, name='ressources'),
    path('ressources/', include('ressources.urls')),
    path('vip/', views.vip_membership, name='vip_membership'),
    path('espace-membre/', views.membership_portal, name='membership_portal'),
    path('tableau-de-bord/', views.tableau_de_bord, name='tableau_de_bord'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('vip/souscrire/<int:abonnement_id>/', views.souscrire_vip, name='souscrire_vip'),
    path('vip/annuler/', views.annuler_vip, name='annuler_vip'),
    path('paiement/', views.paiement_view, name='paiement'),
    path('paiement/success/', views.payment_success_view, name='payment_success'),
    path('paiement/success/<str:transaction_id>/', views.payment_success_view, name='payment_success'),
    
    # API Paiement
    path('api/payment/submit/', views.submit_payment_api, name='submit_payment_api'),
    path('api/payment/check/<str:transaction_id>/', views.check_payment_status_api, name='check_payment_status_api'),
    path('api/payment/webhook/sms/', views.sms_webhook_api, name='sms_webhook_api'),
    
    # Admin Rapports
    path('admin/rapports/membres/', views.rapport_membres, name='rapport_membres'),
    
    # Admin Paiement
    path('admin/payments/', views.admin_payments_dashboard, name='admin_payments_dashboard'),
    path('admin/payments/confirm/<str:transaction_id>/', views.admin_confirm_payment, name='admin_confirm_payment'),
] 