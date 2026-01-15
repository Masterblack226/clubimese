from django.contrib import admin
from .models import Ressource

@admin.register(Ressource)
class RessourceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'categorie', 'niveau', 'accessible_vip', 'date_ajout', 'fichier')
    list_filter = ('categorie', 'niveau', 'accessible_vip')
    search_fields = ('titre', 'description')
    date_hierarchy = 'date_ajout'
    list_per_page = 20
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'description', 'categorie', 'niveau')
        }),
        ('Fichier', {
            'fields': ('fichier', 'taille_fichier', 'accessible_vip')
        }),
        ('Dates et durée', {
            'fields': ('echeance', 'duree_estimee'),
            'classes': ('collapse',)
        }),
    ) 