import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import InscriptionForm, ConnexionForm
from django.utils import timezone
from django.shortcuts import render
from formations.models import Formation
import formations.models as formations_models
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import AbonnementVIP, TemoignageVIP, ProfilMembre, ActiviteMembre, Formation, Actualite, Evenement, Ressource, GalerieImage, Service, Paiement
from actualites.models import Actualite, Evenement, ReussiteMembre, CategorieActualite
from datetime import datetime, timedelta
from django.conf import settings
from datetime import date
from main.services.email_service import EmailService
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg
from django.views.decorators.csrf import csrf_exempt
import hashlib
from django.db.models import Q
import re
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from .models import Formation, Actualite, Evenement, ProfilMembre, AbonnementVIP, TemoignageVIP, ActiviteMembre, GalerieImage, Ressource, Paiement, Service, CategorieActualite
from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView

def actualite_detail(request, slug):
    """Vue pour afficher le détail d'une actualité"""
    actualite = get_object_or_404(Actualite, slug=slug, est_publie=True)
    
    # Incrémenter le compteur de vues
    actualite.vues += 1
    actualite.save()
    
    # Récupérer les actualités similaires (même catégorie)
    actualites_similaires = Actualite.objects.filter(
        categorie=actualite.categorie,
        est_publie=True
    ).exclude(id=actualite.id).order_by('-date_publication')[:3]
    
    # Récupérer les dernières actualités pour la sidebar
    dernieres_actualites = Actualite.objects.filter(
        est_publie=True
    ).exclude(id=actualite.id).order_by('-date_publication')[:5]
    
    context = {
        'actualite': actualite,
        'actualites_similaires': actualites_similaires,
        'dernieres_actualites': dernieres_actualites,
        'meta_titre': actualite.meta_titre or actualite.titre,
        'meta_description': actualite.meta_description or actualite.resume or actualite.contenu[:160],
    }
    
    return render(request, 'actualite_detail.html', context)

# Ou en utilisant une Class-Based View
class ActualiteDetailView(DetailView):
    model = Actualite
    template_name = 'actualite_detail.html'
    context_object_name = 'actualite'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Actualite.objects.filter(est_publie=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actualite = self.get_object()
        
        # Incrémenter les vues
        actualite.vues += 1
        actualite.save()
        
        # Actualités similaires
        context['actualites_similaires'] = Actualite.objects.filter(
            categorie=actualite.categorie,
            est_publie=True
        ).exclude(id=actualite.id).order_by('-date_publication')[:3]
        
        # Dernières actualités
        context['dernieres_actualites'] = Actualite.objects.filter(
            est_publie=True
        ).exclude(id=actualite.id).order_by('-date_publication')[:5]
        
        # Métadonnées SEO
        context['meta_titre'] = actualite.meta_titre or actualite.titre
        context['meta_description'] = actualite.meta_description or actualite.resume or actualite.contenu[:160]
        
        return context



def homepage(request):
    # Données dynamiques
    formations_count = Formation.objects.count()
    dernieres_formations = Formation.objects.all().order_by('-date_debut')[:52]
    context = {
        'formations_count': formations_count,
        'member_count': ProfilMembre.objects.count(),
        'success_rate': ReussiteMembre.objects.filter(est_actif=True).count(),
        'dernieres_formations': dernieres_formations
    }
    return render(request, 'homepage.html', context)

def formations_catalog(request):
    formations = Formation.objects.all().select_related('formateur')
    context = {'formations': formations}
    #Ajout des données pour les statistiques
    stats = {
        'total_formations': formations.count(),
        'upcoming_formations': formations.filter(date_debut__gte=date.today()).count(),
        'completed_formations': formations.filter(date_fin__lt=date.today()).count(),
        
        'taux_satisfaction': 96
    }
    context.update(stats)
    return render(request, 'formations_catalog.html', context)

from ressources.models import Ressource

def ressources(request):
    devoirs = Ressource.objects.filter(categorie='DEVOIRS')
    ressources_statistiques = Ressource.objects.filter(categorie='STATISTIQUES')
    ressources_economie = Ressource.objects.filter(categorie='ECONOMIE')
    ressources_etudes = Ressource.objects.filter(categorie='ETUDES_CAS')
    
    # Statistiques
    stats = {
        'total_ressources': Ressource.objects.count(),
        'devoirs_actifs': devoirs.count(),
        'taux_reussite': ressources_statistiques.count(),  # Exemple fictif
    }
    
    context = {
        'devoirs': devoirs,
        'ressources_statistiques': ressources_statistiques,
        'ressources_economie': ressources_economie,
        'ressources_etudes': ressources_etudes,
        'stats': stats
    }
    return render(request, 'ressources.html', context)



def news_activities(request):
    # Récupère la catégorie sélectionnée depuis les paramètres GET
    categorie_slug = request.GET.get('categorie', 'toutes')
    
    print(f"=== DEBUG: Catégorie demandée: {categorie_slug} ===")
    
    # 1. Récupérer TOUTES les actualités publiées
    actualites_base = Actualite.objects.filter(est_publie=True).order_by('-date_publication')
    total_actualites = actualites_base.count()
    
    # 2. Filtrer par catégorie si spécifiée (et différente de "toutes")
    if categorie_slug == 'toutes' or categorie_slug == '':
        actualites = actualites_base
        categorie_active = None
        print("DEBUG: Affichage de TOUTES les actualités")
    else:
        # Cherche la catégorie par son type
        try:
            categorie_active = CategorieActualite.objects.get(type_categorie=categorie_slug.upper())
            actualites = actualites_base.filter(categorie=categorie_active)
            print(f"DEBUG: Filtrage par catégorie: {categorie_active.nom} ({actualites.count()} trouvées)")
        except CategorieActualite.DoesNotExist:
            actualites = actualites_base
            categorie_active = None
            categorie_slug = 'toutes'
            print(f"DEBUG: Catégorie {categorie_slug} non trouvée, affichage de toutes les actualités")

    # 3. L'actualité à la une
    actualite_une = actualites.filter(type_actualite='FEATURED').first()
    if not actualite_une and actualites.exists():
        actualite_une = actualites.first()
    
    # 4. Événements à venir
    evenements = Evenement.objects.filter(
        date_debut__gte=timezone.now(),
        est_actif=True
    ).order_by('date_debut')[:5]
    
    # 5. Réussites des membres
    reussites = ReussiteMembre.objects.filter(
        est_actif=True
    ).order_by('-date_reussite')[:5]
    
    # 6. Images galerie
    try:
        from main.models import GalerieImage
        images_galerie = GalerieImage.objects.filter(actif=True)[:12]
    except:
        images_galerie = []
    
    # 7. Calculer les statistiques pour la section Hero
    # Actualités ce mois (du 1er du mois à aujourd'hui)
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    actualites_ce_mois = Actualite.objects.filter(
        est_publie=True,
        date_publication__gte=debut_mois
    ).count()
    
    # Événements à venir (à partir d'aujourd'hui)
    evenements_a_venir = Evenement.objects.filter(
        est_actif=True,
        date_debut__gte=timezone.now()
    ).count()
    
    # Réussites célébrées (toutes les réussites actives)
    reussites_celebrees = ReussiteMembre.objects.filter(
        est_actif=True
    ).count()
    
    # 8. Statistiques par catégorie (pour les boutons de filtre)
    stats_categories = {
        'toutes': total_actualites,
        'formations': 0,
        'reussites': 0,
        'evenements': 0,
        'partenariats': 0,
        'annonce': 0,
    }
    
    # Compter pour chaque catégorie spécifique
    for key, cat_type in [
        ('toutes', 'TOUTES'),
        ('formations', 'FORMATIONS'),
        ('reussites', 'REUSSITES'),
        ('evenements', 'EVENEMENTS'),
        ('partenariats', 'PARTENARIATS'),
        ('annonce', 'ANNONCE'),
    ]:
        try:
            categorie = CategorieActualite.objects.get(type_categorie=cat_type)
            count = Actualite.objects.filter(est_publie=True, categorie=categorie).count()
            stats_categories[key] = count
            print(f"DEBUG: {cat_type}: {count} actualités")
        except CategorieActualite.DoesNotExist:
            stats_categories[key] = 0
            print(f"DEBUG: Catégorie {cat_type} non trouvée en base")
    
    # 9. Récupérer les catégories pour les boutons de filtre
    categories_template = CategorieActualite.objects.all().order_by('ordre')
    print(f"DEBUG: {categories_template.count()} catégories trouvées en base")
    
    # 10. Statistiques pour la section Hero
    hero_stats = {
        'actualites_ce_mois': actualites_ce_mois,
        'evenements_a_venir': evenements_a_venir,
        'reussites': reussites_celebrees,  # Utiliser reussites_celebrees
    }
    
    # DEBUG final
    print(f"=== RÉSUMÉ ===")
    print(f"Actualités à afficher: {actualites.count()}")
    print(f"Catégorie active: {categorie_slug}")
    print(f"Hero stats: {hero_stats}")
    print(f"Stats catégories: {stats_categories}")
    
    context = {
        # Actualités
        'actualite_une': actualite_une,
        'actualites_recentes': list(actualites[:8]),  # Limiter à 8 pour l'affichage
        'actualites': list(actualites[:8]),  # Pour compatibilité
        
        # Événements et réussites
        'evenements': evenements,
        'reussites': reussites,
        'images_galerie': images_galerie,
        
        # Catégories
        'categories_template': categories_template,
        'categorie_active': categorie_slug,
        
        # Statistiques
        'stats_categories': stats_categories,
        'hero_stats': hero_stats,
        'total_actualites': stats_categories['toutes'],
    }
    
    return render(request, 'news_activities.html', context)

def filtrer_actualites(request):
    """Vue pour filtrer les actualités via AJAX"""
    categorie_slug = request.GET.get('categorie', 'toutes')
    search_term = request.GET.get('search', '')
    
    # Filtrer par catégorie
    if categorie_slug == 'toutes':
        actualites = Actualite.objects.filter(est_publie=True)
    else:
        # Chercher par type_categorie directement
        actualites = Actualite.objects.filter(
            est_publie=True,
            categorie__type_categorie=categorie_slug.upper()
        )
    
    # Filtrer par recherche
    if search_term:
        actualites = actualites.filter(
            Q(titre__icontains=search_term) |
            Q(contenu__icontains=search_term) |
            Q(resume__icontains=search_term)
        )
    
    actualites = actualites.order_by('-date_publication')
    
    # Préparer les données pour la réponse AJAX
    data = []
    for act in actualites[:12]:  # Limiter à 12 pour la pagination
        data.append({
            'id': act.id,
            'titre': act.titre,
            'resume': act.resume or act.contenu[:150] + '...',
            'categorie': act.categorie.nom if act.categorie else 'Non catégorisé',
            'categorie_type': act.categorie.type_categorie.lower() if act.categorie else 'autre',
            'categorie_couleur': act.categorie.couleur if act.categorie else 'bg-gray-100 text-gray-600',
            'date': act.date_publication.strftime('%d %B %Y'),
            'auteur': act.auteur or 'Club IMESE',
            'vues': act.vues,
            'image_url': act.image.url if act.image else '/static/images/actualite-default.jpg',
            'has_image': bool(act.image),
        })
    
    return JsonResponse({
        'actualites': data,
        'total': actualites.count(),
        'categorie_active': categorie_slug
    })




def vip_membership(request):
    # Récupérer les abonnements disponibles
    abonnements = AbonnementVIP.objects.all()
    
    # Récupérer les témoignages approuvés
    temoignages = TemoignageVIP.objects.filter(est_approuve=True)[:6]
    
    # Statistiques VIP
    stats_vip = {
        'membres_vip': ProfilMembre.objects.filter(est_vip=True).count(),
        'satisfaction': 94,
        'economie_moyenne': 12000,  # Économie moyenne annuelle
    }
    
    # Vérifier si l'utilisateur connecté est VIP
    est_vip = False
    if request.user.is_authenticated:
        try:
            profil = request.user.profilmembre
            est_vip = profil.est_vip
        except ProfilMembre.DoesNotExist:
            pass
    
    contexte = {
        'abonnements': abonnements,
        'temoignages': temoignages,
        'stats_vip': stats_vip,
        'est_vip': est_vip,
        'user': request.user,
    }
    
    return render(request, 'vip_membership.html', contexte)

@login_required

def souscrire_vip(request, abonnement_id):
    if request.method == 'POST':
        try:
            abonnement = AbonnementVIP.objects.get(id=abonnement_id)
            methode_paiement = request.POST.get('methode_paiement')
            numero_telephone = request.POST.get('numero_telephone')
            
            #intégrer avec une API de paiement Forward sms
            
            # Mettre à jour le profil membre
            profil, created = ProfilMembre.objects.get_or_create(utilisateur=request.user)
            profil.est_vip = True
            profil.date_fin_vip = datetime.now() + timedelta(days=30)  # 1 mois
            profil.save()
            
            # Créer une activité
            ActiviteMembre.objects.create(
                membre=request.user,
                type_activite='certification_obtenue',
                titre=f'Abonnement VIP {abonnement.nom} Activé',
                description=f'Votre abonnement VIP {abonnement.nom} a été activé avec succès. Accès premium disponible.',
                lien='/vip/'
            )
            
            messages.success(request, f'Félicitations ! Votre abonnement VIP {abonnement.nom} a été activé avec succès.')
            return redirect('tableau_de_bord')
            
        except AbonnementVIP.DoesNotExist:
            messages.error(request, "L'abonnement sélectionné n'existe pas.")
            return redirect('vip_membership')
    
    return redirect('vip_membership')

@login_required
def annuler_vip(request):
    if request.method == 'POST':
        try:
            profil = request.user.profilmembre
            profil.est_vip = False
            profil.date_fin_vip = None
            profil.save()
            
            messages.success(request, 'Votre abonnement VIP a été annulé. Vous conservez l\'accès jusqu\'à la fin de la période payée.')
            return redirect('tableau_de_bord')
            
        except ProfilMembre.DoesNotExist:
            messages.error(request, "Profil membre non trouvé.")
    
    return redirect('vip_membership')


# API pour les fonctionnalités AJAX
def filter_news(request):
    categorie = request.GET.get('categorie', 'all')
    search_term = request.GET.get('search', '')
    
    actualites = Actualite.objects.all()
    
    if categorie != 'all':
        actualites = actualites.filter(categorie__nom=categorie)
    
    if search_term:
        actualites = actualites.filter(titre__icontains=search_term)
    
    # Retourner les données en JSON (simplifié)
    data = {
        'actualites': list(actualites.values('titre', 'contenu', 'categorie__nom', 'date_publication'))
    }
    return JsonResponse(data)


def galerie_complete(request):
    images_galerie = GalerieImage.objects.filter(actif=True).order_by('-date_ajout')
    return render(request, 'galerie_complete.html', {
        'images_galerie': images_galerie
    })


def membership_portal(request):
    # Récupère les événements pour tous les utilisateurs
    evenements = Evenement.objects.all().order_by('-date_debut')[:5]
    images_galerie = GalerieImage.objects.filter(actif=True).order_by('-date_ajout')[:12]
    
    context = {
        'evenements': evenements,
        'images_galerie': images_galerie,
        'active_tab': 'login'  # Par défaut
    }
    
    # Si l'utilisateur est connecté, afficher le dashboard
    if request.user.is_authenticated:
        # Pour les superutilisateurs, ne pas créer de profil
        if request.user.is_superuser:
            context.update({
                'profil': None,
                'stats': {
                    'formations_completees': 0,
                    'devoirs_rendus': 0,
                    'moyenne_generale': 0,
                    'points_xp': 0,
                },
                'activites_recentes': [],
            })
            return render(request, 'membership_portal.html', context)
        
        # Pour les utilisateurs normaux
        try:
            profil = request.user.profilmembre
        except ProfilMembre.DoesNotExist:
            # Créer un profil avec un numéro étudiant unique
            base_numero = f'ETU_{request.user.id}'
            numero_etudiant = base_numero
            counter = 1
            while ProfilMembre.objects.filter(numero_etudiant=numero_etudiant).exists():
                numero_etudiant = f'{base_numero}_{counter}'
                counter += 1
            
            profil = ProfilMembre.objects.create(
                utilisateur=request.user,
                numero_etudiant=numero_etudiant,
                telephone='',
                niveau_academique='licence1',
                specialisation='statistics',
                newsletter_acceptee=False
            )
        
        # DEBUG PHOTO - Maintenant profil est défini
        print("=== DEBUG PHOTO ===")
        print(f"Profil ID: {profil.id}")
        print(f"Profil a photo attribute: {hasattr(profil, 'photo')}")
        if hasattr(profil, 'photo'):
            print(f"Photo is not None: {profil.photo is not None}")
            if profil.photo:
                print(f"Photo name: {profil.photo.name}")
                print(f"Photo url: {profil.photo.url}")
                print(f"Photo path: {getattr(profil.photo, 'path', 'No path attribute')}")
            else:
                print("Photo is None")
        print("=== FIN DEBUG PHOTO ===")
        
        # ... reste du code pour stats et activités ...
        
        activites_recentes = ActiviteMembre.objects.filter(
            membre=request.user
        ).order_by('-date_activite')[:5]

        stats = {
            'formations_completees': 12,
            'devoirs_rendus': 28,
            'moyenne_generale': 87,
            'points_xp': 156,
        }
        
        context.update({
            'profil': profil,
            'stats': stats,
            'activites_recentes': activites_recentes,
        })
        
        # Traitement POST
        if request.method == 'POST':
            print("=== DEBUG PHOTO ===")
            print(f"Profil ID: {profil.id}")
            print(f"Profil a photo attribute: {hasattr(profil, 'photo')}")
            if hasattr(profil, 'photo'):
                photo_value = getattr(profil, 'photo', None)
                print(f"Photo value: {photo_value}")
                print(f"Photo is truthy: {bool(photo_value)}")
            if photo_value and hasattr(photo_value, 'url'):
                print(f"Photo name: {photo_value.name}")
                print(f"Photo url: {photo_value.url}")
            elif photo_value:
                print(f"Photo exists but no url: {photo_value}")
            else:
                print("Photo is None or empty")
                print("=== FIN DEBUG PHOTO ===")
            
            # Traitement de la photo
            if 'photo_profil' in request.FILES:
                try:
                    # Supprimer l'ancienne photo si elle existe
                    if profil.photo:
                        profil.photo.delete(save=False)
                    
                    profil.photo = request.FILES['photo_profil']
                    profil.save()
                    print(f"Photo sauvegardée: {profil.photo.url}")
                    messages.success(request, 'Photo de profil mise à jour avec succès.')
                except Exception as e:
                    print(f"Erreur sauvegarde photo: {e}")
                    messages.error(request, f'Erreur lors de l\'upload: {str(e)}')
                return redirect('membership_portal')
            
            elif 'supprimer_photo' in request.POST:
                if profil.photo:
                    try:
                        # Supprimer le fichier physique
                        if profil.photo and hasattr(profil.photo, 'delete'):
                            profil.photo.delete(save=False)
            
                        # Réinitialiser le champ photo
                        profil.photo = None
                        profil.save()
            
                        print("Photo supprimée avec succès")
                        messages.success(request, 'Photo de profil supprimée.')
                    except Exception as e:
                        print(f"Erreur suppression photo: {e}")
                        messages.error(request, f'Erreur lors de la suppression: {str(e)}')
                else:
                    print("Aucune photo à supprimer")
                    messages.info(request, 'Aucune photo à supprimer.')
                return redirect('membership_portal')
        
        

        activites_recentes = ActiviteMembre.objects.filter(
            membre=request.user
        ).order_by('-date_activite')[:5]

        # Statistiques dynamiques réelles
        formations_completees = Formation.objects.filter(
            # Ajoute ici la logique pour compter les formations complétées
            # Par exemple, si tu as un modèle d'inscription aux formations
        ).count()
        
        # Ou pour l'instant, utilise des valeurs de test qui changent :
        import random
        stats = {
            'formations_completees': random.randint(5, 20),
            'devoirs_rendus': random.randint(15, 40),
            'moyenne_generale': random.randint(75, 95),
            'points_xp': random.randint(100, 300),
        }
        
        context.update({
            'profil': profil,
            'stats': stats,
            'activites_recentes': activites_recentes,
        })
        
        
        try:
            profil = request.user.profilmembre
        except ProfilMembre.DoesNotExist:
            profil = ProfilMembre.objects.create(utilisateur=request.user)
        
        activites_recentes = ActiviteMembre.objects.filter(
            membre=request.user
        ).order_by('-date_activite')[:5]
        

        stats = {
            'formations_completees': 12,
            'devoirs_rendus': 28,
            'moyenne_generale': 87,
            'points_xp': 156,
        }
        
        context.update({
            'profil': profil,
            'stats': stats,
            'activites_recentes': activites_recentes,
        })
        
        return render(request, 'membership_portal.html', context)
    
    
    # Initialisation des formulaires
    context['form_inscription'] = InscriptionForm()
    context['form_connexion'] = ConnexionForm()
    
    # Debug - affiche les requêtes POST
    if request.method == 'POST':
        print("=== DEBUG POST ===")
        print("Method:", request.method)
        print("POST data:", request.POST)
        print("Active tab:", 'register' if 'inscription' in request.POST else 'login' if 'connexion' in request.POST else 'none')
        print("=== FIN DEBUG ===")
    
    # Gestion de l'inscription
    if request.method == 'POST' and 'inscription' in request.POST:
        print("=== TRAITEMENT INSCRIPTION ===")
        form_inscription = InscriptionForm(request.POST)
        context['form_inscription'] = form_inscription
        
        if form_inscription.is_valid():
            try:
                # Créer l'utilisateur
                utilisateur = form_inscription.save()
                
                # Créer le profil manuellement SANS SIGNAL
                numero_etudiant = form_inscription.cleaned_data['numero_etudiant']
                
                # Vérifier unicité et générer un numéro unique si nécessaire
                original_numero = numero_etudiant
                counter = 1
                while ProfilMembre.objects.filter(numero_etudiant=numero_etudiant).exists():
                    numero_etudiant = f"{original_numero}_{counter}"
                    counter += 1
                    if counter > 1000:
                        numero_etudiant = f"ETU_{utilisateur.id}_{counter}"
                        break
                
                if numero_etudiant != original_numero:
                    messages.warning(request, f"Numéro modifié: {numero_etudiant}")
                
                # Création DIRECTE sans signal
                profil = ProfilMembre.objects.create(
                    utilisateur=utilisateur,
                    numero_etudiant=numero_etudiant,
                    telephone=form_inscription.cleaned_data['telephone'],
                    niveau_academique=form_inscription.cleaned_data['niveau_academique'],
                    specialisation=form_inscription.cleaned_data['specialisation'],
                    newsletter_acceptee=form_inscription.cleaned_data.get('newsletter_acceptee', False)
                )
                
                login(request, utilisateur)
                messages.success(request, 'Inscription réussie!')
                return redirect('membership_portal')
                
            except Exception as e:
                messages.error(request, f'Erreur: {str(e)}')
                context['active_tab'] = 'register'
    
    # Gestion de la connexion
    elif request.method == 'POST' and 'connexion' in request.POST:
        print("=== TRAITEMENT CONNEXION ===")
        form_connexion = ConnexionForm(request.POST)
        context['form_connexion'] = form_connexion  # Toujours mettre à jour le formulaire dans le contexte
        
        if form_connexion.is_valid():
            print("Formulaire connexion valide")
            email = form_connexion.cleaned_data['email']
            password = form_connexion.cleaned_data['password']
            
            # Utiliser filter().first() pour éviter MultipleObjectsReturned
            utilisateur = User.objects.filter(email=email).first()
            if not utilisateur:
                messages.error(request, 'Aucun compte trouvé avec cette adresse email.')
                context['active_tab'] = 'login'
            else:
                user = authenticate(request, username=utilisateur.username, password=password)
                if user is not None:
                    login(request, user)
                    if not form_connexion.cleaned_data['remember_me']:
                        request.session.set_expiry(0)
                    messages.success(request, f'Bienvenue {user.first_name} !')
                    return redirect('membership_portal')
                else:
                    messages.error(request, 'Email ou mot de passe incorrect.')
                    context['active_tab'] = 'login'
        else:
            print("Erreurs formulaire connexion:", form_connexion.errors)
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
            context['active_tab'] = 'login'
    
    return render(request, 'membership_portal.html', context)



@login_required
def tableau_de_bord(request):
    try:
        profil = request.user.profilmembre
    except ProfilMembre.DoesNotExist:
        # Créer un profil si il n'existe pas (pour les utilisateurs existants)
        profil = ProfilMembre.objects.create(utilisateur=request.user)
    
    # Récupérer les activités récentes du membre
    activites_recentes = ActiviteMembre.objects.filter(
        membre=request.user
    ).order_by('-date_activite')[:5]

    # Statistiques du membre
    stats = {
        'formations_completees': 12,
        'devoirs_rendus': 28,
        'moyenne_generale': 87,
        'points_xp': 156,
    }
    
    return render(request, 'membership_portal.html', {
        'user': request.user,
        'profil': profil,
        'stats': stats,
        'activites_recentes': activites_recentes,
        'dashboard_active': True
    })

def deconnexion(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('membership_portal')


@staff_member_required
def admin_dashboard(request):
    """Dashboard administrateur avec rapports statistiques"""
    
    # Statistiques générales
    stats_generales = {
        'total_membres': ProfilMembre.objects.count(),
        'membres_vip': ProfilMembre.objects.filter(est_vip=True).count(),
        'total_formations': Formation.objects.count(),
        'total_evenements': Evenement.objects.count(),
        'total_actualites': Actualite.objects.count(),
    }
    
    # Membres par niveau académique
    membres_par_niveau = ProfilMembre.objects.values(
        'niveau_academique'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Membres par spécialisation
    membres_par_specialisation = ProfilMembre.objects.values(
        'specialisation'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Évolution des inscriptions (30 derniers jours)
    date_30_jours = timezone.now() - timedelta(days=30)
    inscriptions_30_jours = ProfilMembre.objects.filter(
        date_inscription__gte=date_30_jours
    ).extra(
        select={'date': 'date(date_inscription)'}
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Formations par catégorie
    formations_par_categorie = Formation.objects.values(
        'categorie__nom'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Événements à venir
    evenements_a_venir = Evenement.objects.filter(
        date_debut__gte=timezone.now()
    ).order_by('date_debut')[:10]
    
    context = {
        'stats_generales': stats_generales,
        'membres_par_niveau': membres_par_niveau,
        'membres_par_specialisation': membres_par_specialisation,
        'inscriptions_30_jours': list(inscriptions_30_jours),
        'formations_par_categorie': formations_par_categorie,
        'evenements_a_venir': evenements_a_venir,
    }
    
    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def rapport_membres(request):
    """Rapport détaillé sur les membres"""
    
    # Filtres
    niveau = request.GET.get('niveau')
    specialisation = request.GET.get('specialisation')
    est_vip = request.GET.get('vip')
    
    membres = ProfilMembre.objects.select_related('utilisateur')
    
    if niveau:
        membres = membres.filter(niveau_academique=niveau)
    if specialisation:
        membres = membres.filter(specialisation=specialisation)
    if est_vip:
        membres = membres.filter(est_vip=est_vip == 'true')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(membres.order_by('-date_inscription'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'niveaux': ProfilMembre.NIVEAU_CHOICES,
        'specialisations': ProfilMembre.SPECIALISATION_CHOICES,
        'filtres': {
            'niveau': niveau,
            'specialisation': specialisation,
            'vip': est_vip,
        }
    }
    
    return render(request, 'admin/rapport_membres.html', context)


def paiement_view(request):
    """Affiche la page de paiement"""
    # Récupérer le service depuis l'URL
    service_id = request.GET.get('service_id')
    formation_id = request.GET.get('formation')
    
    # Déterminer quel service est demandé
    service = None
    if service_id:
        service = get_object_or_404(Service, id=service_id, actif=True)
    elif formation_id:
        # Si c'est une formation, créer un service temporaire
        formation = get_object_or_404(formations_models.Formation, id=formation_id)
        service = {
            'name': formation.titre,
            'price': formation.prix,
            'type': 'formation'
        }
    
    # Configurations
    OPERATOR_NUMBERS = {
        'orange': "+226 54 17 93 69",
        'moov': "+226 72 68 95 58"
    }
    
    context = {
        'formation': service if isinstance(service, dict) else None,
        'service': service if not isinstance(service, dict) else None,
        'operator_numbers': OPERATOR_NUMBERS,
        'transaction_id': generate_transaction_id(),
    }
    
    return render(request, 'paiement.html', context)

def generate_transaction_id():
    """Génère un ID de transaction unique"""
    import uuid
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"CLUBIM{timestamp}{unique_id}"

@csrf_exempt
def submit_payment_api(request):
    """API pour soumettre un paiement"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validation des données
            required_fields = ['transactionId', 'phone', 'email', 'name', 
                              'referenceCode', 'operator', 'amount', 'service']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Champ manquant: {field}'
                    }, status=400)
            
            # Vérifier si la transaction existe déjà
            if Paiement.objects.filter(transaction_id=data['transactionId']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Transaction déjà existante'
                }, status=400)
            
            # Trouver ou créer le service
            service_name = data['service']
            service, created = Service.objects.get_or_create(
                nom=service_name,
                defaults={
                    'type_service': 'formation',
                    'prix': data['amount'],
                    'description': f'Service: {service_name}'
                }
            )
            
            # Créer l'enregistrement de paiement
            paiement = Paiement.objects.create(
                transaction_id=data['transactionId'],
                service=service,
                montant=data['amount'],
                user_phone=data['phone'],
                user_email=data['email'],
                user_name=data['name'],
                reference_code=data['referenceCode'],
                operator=data['operator'],
                submitted_at=timezone.now(),
                status='pending'
            )
            
            # TODO: Envoyer un email de confirmation
            
            return JsonResponse({
                'success': True,
                'transaction_id': paiement.transaction_id,
                'message': 'Paiement enregistré avec succès'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)



@csrf_exempt
def sms_webhook_api(request):
    """API pour recevoir et traiter les SMS de paiement"""
    if request.method == 'POST':
        try:
            # Parser les données
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            sms_text = data.get('message', '')
            sender = data.get('sender', '')
            timestamp = data.get('timestamp', '')
            
            print(f"📱 SMS reçu: {sms_text}")
            print(f"📞 Expéditeur: {sender}")
            
            # Analyser le SMS pour extraire montant et code
            parsed_data = parse_sms_for_payment(sms_text)
            
            if parsed_data:
                amount, reference_code = parsed_data
                print(f"✅ SMS analysé: {amount} FCFA, Code: {reference_code}")
                
                # Chercher les paiements en attente correspondants
                paiements = Paiement.objects.filter(
                    status='pending',
                    reference_code=reference_code,
                    montant=amount
                ).order_by('-created_at')
                
                if paiements.exists():
                    paiement = paiements.first()
                    
                    # Vérifier l'expiration
                    if paiement.is_expired():
                        paiement.expire()
                        return JsonResponse({
                            'success': False,
                            'message': 'Paiement expiré'
                        })
                    
                    # Confirmer le paiement
                    paiement.confirm(f"SMS reçu: {sms_text}")
                    
                    print(f"✅ Paiement confirmé: {paiement.transaction_id}")
                    
                    # TODO: Donner accès au service
                    # TODO: Envoyer email de confirmation
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Paiement confirmé avec succès',
                        'transaction_id': paiement.transaction_id,
                        'user': paiement.user_name,
                        'service': paiement.service.nom,
                        'amount': float(paiement.montant)
                    })
                else:
                    print(f"❌ Aucun paiement correspondant trouvé")
                    
                    # Enregistrer le SMS non matché pour analyse
                    with open('sms_non_matchés.log', 'a', encoding='utf-8') as f:
                        f.write(f"{datetime.now().isoformat()} | {sender} | {sms_text}\n")
            
            return JsonResponse({
                'success': False,
                'message': 'Aucun paiement correspondant trouvé'
            })
            
        except Exception as e:
            print(f"❌ Erreur webhook: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET pour tester
    return JsonResponse({
        'status': 'ready',
        'message': 'Webhook SMS opérationnel',
        'instructions': 'Configure SMS Forwarder pour forwarder vers cette URL'
    })

def parse_sms_for_payment(sms_text):
    """Parser un SMS Mobile Money pour extraire montant et code"""
    # Nettoyer le texte
    sms_text = sms_text.lower().replace('\n', ' ').replace('\r', ' ')
    
    # Patterns pour différents formats
    patterns = [
        # Format Orange: "vous avez reçu 15000 f de 70123456. ref: club2024"
        r'(\d+)\s*(?:f|fcfa|francs).*?ref[:\s]*(\w+)',
        
        # Format Moov: "transfert de 15000 f reçu. code: club2024"
        r'(\d+)\s*(?:f|fcfa|francs).*?code[:\s]*(\w+)',
        
        # Format générique: "15000f reçus. référence: club2024"
        r'(\d+)\s*(?:f|fcfa|francs).*?r[ée]f[ée]rence[:\s]*(\w+)',
        
        # Format avec "id:" ou "trx:"
        r'(\d+)\s*(?:f|fcfa|francs).*?(?:id|trx)[:\s]*(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sms_text)
        if match:
            return float(match.group(1)), match.group(2).upper()
    
    # Essayer de trouver juste un montant et un code séparé
    amount_match = re.search(r'(\d+)\s*(?:f|fcfa|francs)', sms_text)
    if amount_match:
        amount = float(amount_match.group(1))
        
        # Chercher un code 4+ caractères
        code_match = re.search(r'\b([a-z0-9]{4,20})\b', sms_text, re.IGNORECASE)
        if code_match:
            return amount, code_match.group(1).upper()
    
    return None


def check_payment_status_api(request, transaction_id):
    """API pour vérifier le statut d'un paiement"""
    try:
        paiement = Paiement.objects.get(transaction_id=transaction_id)
        
        # Vérifier expiration
        if paiement.status == 'pending' and paiement.is_expired():
            paiement.status = 'expired'
            paiement.save()
        
        if paiement.status == 'confirmed':
            return JsonResponse({
                'status': 'confirmed',
                'message': 'Paiement confirmé',
                'amount': float(paiement.montant),
                'service': paiement.service.nom,
                'redirect_url': f'/paiement/success/{paiement.transaction_id}/'
            })
        elif paiement.status == 'pending':
            return JsonResponse({
                'status': 'pending',
                'message': 'En attente de paiement'
            })
        else:
            return JsonResponse({
                'status': paiement.status,
                'message': f'Paiement {paiement.get_status_display().lower()}'
            })
            
    except Paiement.DoesNotExist:
        return JsonResponse({
            'status': 'not_found',
            'message': 'Transaction non trouvée'
        }, status=404)

def payment_success_view(request, transaction_id=None):
    """Page de succès après paiement"""
    paiement = None
    success = False
    
    if transaction_id:
        try:
            paiement = Paiement.objects.get(transaction_id=transaction_id)
            success = paiement.status == 'confirmed'
        except Paiement.DoesNotExist:
            pass
    
    # Récupérer depuis les paramètres GET
    if not paiement:
        transaction_id = request.GET.get('transaction_id')
        formation_name = request.GET.get('formation_name')
        formation_price = request.GET.get('formation_price')
        payment_method = request.GET.get('payment_method')
        
        if transaction_id:
            paiement = {
                'transaction_id': transaction_id,
                'service': {'nom': formation_name or 'Service'},
                'montant': formation_price or 0,
                'operator': payment_method or 'Mobile Money',
                'confirmed_at': timezone.now()
            }
            success = True
    
    context = {
        'paiement': paiement,
        'success': success,
    }
    
    return render(request, 'success.html', context)

# Vue admin pour gérer les paiements
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_payments_view(request):
    """Interface admin pour voir les paiements"""
    paiements = Paiement.objects.all().order_by('-created_at')
    
    # Filtres
    status = request.GET.get('status')
    if status:
        paiements = paiements.filter(status=status)
    
    operator = request.GET.get('operator')
    if operator:
        paiements = paiements.filter(operator=operator)
    
    # Statistiques
    stats = {
        'total': paiements.count(),
        'pending': paiements.filter(status='pending').count(),
        'confirmed': paiements.filter(status='confirmed').count(),
        'rejected': paiements.filter(status='rejected').count(),
        'expired': paiements.filter(status='expired').count(),
    }
    
    context = {
        'paiements': paiements,
        'stats': stats,
        'status_choices': Paiement.STATUS_CHOICES,
        'operator_choices': Paiement.OPERATOR_CHOICES,
    }
    
    return render(request, 'admin/payments.html', context)

@staff_member_required
def admin_confirm_payment(request, transaction_id):
    """Admin peut confirmer manuellement un paiement"""
    if request.method == 'POST':
        try:
            paiement = Paiement.objects.get(transaction_id=transaction_id)
            paiement.status = 'confirmed'
            paiement.confirmed_at = timezone.now()
            paiement.notes = f"Confirmé manuellement par {request.user.username}"
            paiement.save()
            
            messages.success(request, f"Paiement {transaction_id} confirmé")
        except Paiement.DoesNotExist:
            messages.error(request, "Paiement non trouvé")
    
    return redirect('admin_payments')


@staff_member_required
def admin_payments_dashboard(request):
    """Dashboard administrateur pour les paiements"""
    paiements = Paiement.objects.all().order_by('-created_at')
    
    # Statistiques
    stats = {
        'total': paiements.count(),
        'pending': paiements.filter(status='pending').count(),
        'confirmed': paiements.filter(status='confirmed').count(),
        'rejected': paiements.filter(status='rejected').count(),
        'total_amount': sum(p.montant for p in paiements.filter(status='confirmed')),
    }
    
    context = {
        'paiements': paiements[:50],  # 50 derniers
        'stats': stats,
    }
    
    return render(request, 'admin/payments_dashboard.html', context)




def send_payment_confirmation_email(paiement):
    """Envoyer un email de confirmation après paiement"""
    try:
        # Configuration email (à mettre dans settings.py)
        SMTP_CONFIG = {
            'host': getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com'),
            'port': getattr(settings, 'EMAIL_PORT', 587),
            'username': getattr(settings, 'EMAIL_HOST_USER', ''),
            'password': getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@clubimese.bf'),
        }
        
        # Créer le message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'✅ Confirmation de paiement - Club IMESE'
        msg['From'] = SMTP_CONFIG['from_email']
        msg['To'] = paiement.user_email
        
        # Contenu HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); padding: 30px; text-align: center; color: white;">
                <h1 style="margin: 0;">✅ Paiement Confirmé</h1>
                <p style="margin-top: 10px; opacity: 0.9;">Club IMESE - Université Thomas Sankara</p>
            </div>
            
            <div style="padding: 30px; background: #f8fafc;">
                <h2 style="color: #1e293b;">Bonjour {paiement.user_name},</h2>
                <p>Votre paiement a été confirmé avec succès. Voici les détails :</p>
                
                <div style="background: white; border-radius: 10px; padding: 20px; margin: 20px 0; border: 1px solid #e2e8f0;">
                    <h3 style="color: #3b82f6; margin-top: 0;">📋 Détails de la transaction</h3>
                    
                    <table style="width: 100%;">
                        <tr>
                            <td style="padding: 8px 0; color: #64748b;">ID Transaction :</td>
                            <td style="padding: 8px 0; font-weight: bold;">{paiement.transaction_id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #64748b;">Service :</td>
                            <td style="padding: 8px 0; font-weight: bold;">{paiement.service.nom}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #64748b;">Montant :</td>
                            <td style="padding: 8px 0; font-weight: bold; color: #059669;">{paiement.montant} FCFA</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #64748b;">Date :</td>
                            <td style="padding: 8px 0;">{paiement.confirmed_at.strftime('%d/%m/%Y %H:%M')}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 15px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #0369a1;">🎉 Prochaines étapes</h4>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Accédez à votre espace membre : <a href="https://ton-site.com/compte/">https://ton-site.com/compte/</a></li>
                        <li>Rejoignez notre groupe WhatsApp pour les annonces</li>
                        <li>Contactez-nous si vous avez des questions</li>
                    </ul>
                </div>
                
                <p style="color: #64748b; font-size: 14px;">
                    Cet email a été envoyé automatiquement. Veuillez ne pas y répondre.<br>
                    Pour toute assistance, contactez-nous à : contact@clubimese.bf
                </p>
            </div>
            
            <div style="background: #1e293b; color: #cbd5e1; text-align: center; padding: 20px; font-size: 12px;">
                <p>© 2024 Club IMESE - Université Thomas Sankara. Tous droits réservés.</p>
                <p>Ouagadougou, Burkina Faso</p>
            </div>
        </body>
        </html>
        """
        
        # Partie texte simple
        text = f"""
        Confirmation de paiement - Club IMESE
        
        Bonjour {paiement.user_name},
        
        Votre paiement a été confirmé avec succès.
        
        Détails :
        - ID Transaction : {paiement.transaction_id}
        - Service : {paiement.service.nom}
        - Montant : {paiement.montant} FCFA
        - Date : {paiement.confirmed_at.strftime('%d/%m/%Y %H:%M')}
        
        Accédez à votre espace membre : https://ton-site.com/compte/
        
        Pour toute assistance : contact@clubimese.bf
        
        © 2024 Club IMESE - Université Thomas Sankara
        """
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        # Envoyer l'email
        if all(SMTP_CONFIG.values()):  # Vérifier que la config est remplie
            with smtplib.SMTP(SMTP_CONFIG['host'], SMTP_CONFIG['port']) as server:
                server.starttls()
                server.login(SMTP_CONFIG['username'], SMTP_CONFIG['password'])
                server.send_message(msg)
            
            print(f"📧 Email envoyé à {paiement.user_email}")
            return True
        else:
            print("⚠️ Configuration email manquante - email non envoyé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        return False
    

@login_required
def my_payments_view(request):
    """Page pour voir ses propres paiements"""
    paiements = Paiement.objects.filter(
        user_email=request.user.email
    ).order_by('-created_at')
    
    context = {
        'paiements': paiements,
        'active_tab': 'payments'
    }
    
    return render(request, 'my_payments.html', context)
    


    