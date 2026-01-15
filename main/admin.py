from django.contrib import admin
from .models import *
from .models import Paiement, Service
 
# Supprimez l'ancien enregistrement si il existe et gardez seulement celui-ci :
@admin.register(ProfilMembre)
class ProfilMembreAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'numero_etudiant', 'niveau_academique', 'specialisation', 'est_vip']
    list_filter = ['niveau_academique', 'specialisation', 'est_vip']
    search_fields = ['utilisateur__first_name', 'utilisateur__last_name', 'numero_etudiant']

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'formateur', 'niveau', 'prix', 'date_debut']
    list_filter = ['niveau', 'categorie', 'date_debut']
    search_fields = ['titre', 'description']

@admin.register(InscriptionFormation)
class InscriptionFormationAdmin(admin.ModelAdmin):
    list_display = ['nom', 'email', 'formation', 'statut', 'date_inscription', 'date_completion']
    list_filter = ['statut', 'formation', 'date_inscription', 'date_completion']
    search_fields = ['nom', 'email', 'telephone', 'transaction_id', 'reference_code']
    readonly_fields = ['date_inscription', 'date_completion', 'transaction_id']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('nom', 'email', 'telephone', 'utilisateur')
        }),
        ('Formation', {
            'fields': ('formation',)
        }),
        ('Paiement', {
            'fields': ('reference_code', 'transaction_id', 'statut')
        }),
        ('Dates', {
            'fields': ('date_inscription', 'date_completion'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Actualite)
class ActualiteAdmin(admin.ModelAdmin):
    list_display = ['titre', 'categorie', 'date_publication', 'auteur']
    list_filter = ['categorie', 'date_publication']
    search_fields = ['titre', 'contenu']

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ['titre', 'lieu', 'date_debut']
    list_filter = ['date_debut']
    search_fields = ['titre', 'description']
    search_fields = ('titre', 'lieu')
    date_hierarchy = 'date_debut'
    ordering = ('-date_debut',)
@admin.register(Ressource)
class RessourceAdmin(admin.ModelAdmin):
    list_display = ['titre', 'categorie', 'date_ajout']
    list_filter = ['categorie']
    search_fields = ['titre', 'description']

@admin.register(AbonnementVIP)
class AbonnementVIPAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_abonnement', 'prix']
    list_filter = ['type_abonnement']
    search_fields = ['nom']

@admin.register(GalerieImage)
class GalerieImageAdmin(admin.ModelAdmin):
    list_display = ['titre', 'evenement_lie', 'date_ajout', 'actif']
    list_filter = ['evenement_lie', 'date_ajout', 'actif']
    list_editable = ['actif']
    search_fields = ['titre', 'description']

@admin.register(ActiviteMembre)
class ActiviteMembreAdmin(admin.ModelAdmin):
    list_display = ['membre', 'type_activite', 'titre', 'date_activite', 'est_lue']
    list_filter = ['type_activite', 'date_activite', 'est_lue']
    search_fields = ['titre', 'description', 'membre__username']
    list_editable = ['est_lue']
    readonly_fields = ['date_activite']    


# ============================================
# ADMIN POUR PAIEMENTS
# ============================================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_service', 'prix', 'duree_jours', 'actif', 'date_creation']
    list_filter = ['type_service', 'actif', 'date_creation']
    search_fields = ['nom', 'description']
    list_editable = ['prix', 'actif', 'duree_jours']
    list_per_page = 20
    
    fieldsets = (
        ('Information Service', {
            'fields': ('nom', 'type_service', 'prix', 'duree_jours', 'description')
        }),
        ('Activation', {
            'fields': ('actif',)
        }),
    )

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'get_service_nom', 'montant', 'user_name', 
                   'user_phone', 'get_status_display_colored', 'created_at', 'time_left', 'status']
    list_filter = ['status', 'operator', 'created_at', 'service__type_service']
    search_fields = ['transaction_id', 'user_name', 'user_phone', 'user_email', 'reference_code']
    readonly_fields = ['created_at', 'submitted_at', 'confirmed_at', 'transaction_id']
    list_editable = ['status']
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['confirm_selected', 'reject_selected', 'expire_selected']
    
    # Méthodes pour affichage
    def get_service_nom(self, obj):
        return obj.service.nom if obj.service else "N/A"
    get_service_nom.short_description = 'Service'
    get_service_nom.admin_order_field = 'service__nom'
    
    def get_status_display_colored(self, obj):
        from django.utils.html import format_html
        colors = {
            'pending': 'warning',
            'confirmed': 'success',
            'rejected': 'danger',
            'expired': 'secondary',
        }
        color = colors.get(obj.status, 'info')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_display_colored.short_description = 'Statut'
    
    def time_left(self, obj):
        if obj.status == 'pending':
            minutes = obj.get_time_left() // 60
            seconds = obj.get_time_left() % 60
            return f"{minutes:02d}:{seconds:02d}"
        return "-"
    time_left.short_description = 'Temps restant'
    
    # Actions admin
    def confirm_selected(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} paiement(s) confirmé(s).")
    confirm_selected.short_description = "Confirmer les paiements sélectionnés"
    
    def reject_selected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} paiement(s) rejeté(s).")
    reject_selected.short_description = "Rejeter les paiements sélectionnés"
    
    def expire_selected(self, request, queryset):
        updated = queryset.update(status='expired')
        self.message_user(request, f"{updated} paiement(s) marqué(s) comme expiré(s).")
    expire_selected.short_description = "Marquer comme expiré"
    
    fieldsets = (
        ('Transaction', {
            'fields': ('transaction_id', 'service', 'montant', 'status', 'is_processed')
        }),
        ('Utilisateur', {
            'fields': ('user_name', 'user_phone', 'user_email', 'reference_code')
        }),
        ('Paiement', {
            'fields': ('operator', 'operator_number')
        }),
        ('SMS & Notes', {
            'fields': ('sms_received', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'submitted_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )

# Enregistrement des modèles simples (sans configuration admin personnalisée)
admin.site.register(CategorieFormation)
admin.site.register(Formateur)
admin.site.register(CategorieActualite)
