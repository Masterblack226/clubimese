from django.contrib import admin
from .models import *

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

admin.site.register(CategorieActualite)

# Register your models here.
