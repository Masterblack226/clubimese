from django.contrib import admin
from .models import Formateur, Formation

@admin.register(Formateur)
class FormateurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'email', 'specialite']
    search_fields = ['nom', 'specialite']
    list_filter = ['specialite']

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'formateur', 'niveau', 'prix', 'date_debut']
    list_filter = ['niveau', 'formateur', 'date_debut']
    search_fields = ['titre', 'description']
    date_hierarchy = 'date_debut' 