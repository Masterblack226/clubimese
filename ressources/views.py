from django.shortcuts import render
from .models import Ressource

def ressources_view(request):
    # Récupère toutes les ressources
    ressources = Ressource.objects.all()
    
    # Filtre par catégorie pour les sections spécifiques
    ressources_statistiques = Ressource.objects.filter(categorie='STATISTIQUES')
    ressources_economie = Ressource.objects.filter(categorie='ECONOMIE')
    ressources_etudes = Ressource.objects.filter(categorie='ETUDES_CAS')
    
    # Récupère les "devoirs" (ressources avec échéance)
    devoirs = Ressource.objects.filter(echeance__isnull=False).order_by('echeance')
    
    # Statistiques pour le template
    stats = {
        'total_ressources': Ressource.objects.count(),
        'devoirs_actifs': devoirs.count(),
        'taux_reussite': 85,  # A remplacer par une vraie logique
    }
    
    context = {
        'ressources': ressources,
        'ressources_statistiques': ressources_statistiques,
        'ressources_economie': ressources_economie,
        'ressources_etudes': ressources_etudes,
        'devoirs': devoirs,
        'stats': stats,
    }
    
    return render(request, 'ressources.html', context)