from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from datetime import date
from datetime import timedelta
from formations.models import Formation
import json

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

def filtrer_formations(request):
    """Retourne les formations filtrées par catégorie et recherche en JSON"""
    niveau = request.GET.get('niveau', 'all')
    search = request.GET.get('search', '')
    
    # Commencer avec toutes les formations
    formations = Formation.objects.all().select_related('formateur')
    
    # Filtrer par niveau
    if niveau and niveau != 'all':
        formations = formations.filter(niveau=niveau)
    
    # Filtrer par recherche
    if search:
        formations = formations.filter(
            titre__icontains=search
        ) | formations.filter(
            description__icontains=search
        )
    
    # Compter les formations par niveau
    compteurs = {
        'toutes': Formation.objects.count(),
        'debutant': Formation.objects.filter(niveau='DEBUTANT').count(),
        'intermediaire': Formation.objects.filter(niveau='INTERMEDIAIRE').count(),
        'avance': Formation.objects.filter(niveau='AVANCE').count(),
    }
    
    # Formater les données pour JSON
    data = {
        'formations': [
            {
                'id': f.id,
                'titre': f.titre,
                'description': f.description[:150] + '...' if len(f.description) > 150 else f.description,
                'prix': float(f.prix),
                'formateur': f.formateur.nom,
                'specialite': f.formateur.specialite,
                'date_debut': f.date_debut.strftime('%d %B %Y'),
                'duree': f.duree,
                'niveau': f.get_niveau_display(),
                'image_url': f.image.url if f.image else '/static/images/formation-default.jpg',
                'formateur_photo': f.formateur.photo.url if f.formateur.photo else '/static/images/formateur-default.jpg',
            }
            for f in formations[:12]
        ],
        'total': formations.count(),
        'niveau_actif': niveau,
        'compteurs': compteurs,
    }
    
    return JsonResponse(data)

def formation_detail_json(request, id):
    """Retourne les détails complets d'une formation en JSON"""
    from main.models import InscriptionFormation
    from paiements.models import Transaction
    import logging
    
    logger = logging.getLogger(__name__)
    formation = get_object_or_404(Formation, id=id)
    
    # Vérifier si l'utilisateur est inscrit
    user_email = None
    is_inscribed = False
    debug_messages = []
    
    if request.user.is_authenticated:
        user_email = request.user.email
        debug_messages.append(f"Utilisateur authentifié: {user_email}")
        logger.info(f"✅ Utilisateur authentifié: {user_email}")
    else:
        # Pour les utilisateurs anonymes, on vérifie la session
        user_email = request.session.get('user_email')
        debug_messages.append(f"Email depuis session: {user_email}")
        logger.info(f"✅ Email depuis session: {user_email}")
    
    # Vérifier l'inscription par plusieurs méthodes
    if user_email:
        debug_messages.append(f"Recherche pour email: {user_email}, formation: {formation.id}")
        
        # Méthode 1: Chercher une inscription complétée
        try:
            inscription_query = InscriptionFormation.objects.filter(
                email__iexact=user_email.lower(),
                formation_id=formation.id,  # Utilise formation_id au lieu de formation
                statut='completed'
            )
            debug_messages.append(f"Inscriptions trouvées: {inscription_query.count()}")
            
            inscription = inscription_query.first()
            
            if inscription:
                is_inscribed = True
                debug_messages.append(f"✅ Inscription trouvée!")
                logger.info(f"✅ Inscription trouvée: {user_email} pour {formation.titre}")
            else:
                debug_messages.append(f"❌ Pas d'inscription trouvée")
                logger.info(f"❌ Pas d'inscription trouvée pour {user_email} et formation {formation.id}")
                
                # Méthode 2: Chercher une transaction complétée
                transaction = Transaction.objects.filter(
                    user_email__iexact=user_email.lower(),
                    formation_id=formation.id,
                    status='completed'
                ).first()
                
                if transaction:
                    is_inscribed = True
                    debug_messages.append(f"✅ Transaction trouvée!")
                    logger.info(f"✅ Transaction complétée trouvée: {user_email} pour {formation.titre}")
                else:
                    debug_messages.append(f"❌ Pas de transaction trouvée")
        except Exception as e:
            debug_messages.append(f"❌ Erreur lors de la recherche: {str(e)}")
            logger.error(f"❌ Erreur lors de la recherche d'inscription: {str(e)}")
    else:
        debug_messages.append("❌ Pas d'email trouvé")
        logger.info("❌ Pas d'email trouvé (utilisateur anonyme)")
    
    data = {
        'id': formation.id,
        'titre': formation.titre,
        'description': formation.description,
        'prix': float(formation.prix),
        'formateur': formation.formateur.nom,
        'specialite': formation.formateur.specialite,
        'bio_formateur': formation.formateur.bio,
        'date_debut': formation.date_debut.strftime('%d %B %Y à %H:%M'),
        'date_fin': formation.date_fin.strftime('%d %B %Y'),
        'duree': formation.duree,
        'niveau': formation.get_niveau_display(),
        'image_url': formation.image.url if formation.image else '/static/images/formation-default.jpg',
        'formateur_photo': formation.formateur.photo.url if formation.formateur.photo else '/static/images/formateur-default.jpg',
        'lien_inscription': formation.lien_inscription,
        'is_inscribed': is_inscribed,
        'user_email': user_email,
        'debug_info': {
            'user_email_found': user_email is not None,
            'is_authenticated': request.user.is_authenticated,
            'formation_id': formation.id,
            'messages': debug_messages,
        }
    }
    
    return JsonResponse(data)

def debug_inscriptions(request):
    """Endpoint de debug pour voir toutes les inscriptions"""
    from main.models import InscriptionFormation
    from paiements.models import Transaction
    
    # Récupérer toutes les inscriptions
    inscriptions = InscriptionFormation.objects.select_related('formation').all()
    
    # Récupérer TOUTES les transactions, pas juste les complétées
    transactions = Transaction.objects.select_related('formation').all()
    
    inscriptions_data = []
    for ins in inscriptions:
        inscriptions_data.append({
            'id': ins.id,
            'email': ins.email,
            'nom': ins.nom,
            'formation_id': ins.formation_id,
            'formation_title': ins.formation.titre if ins.formation else 'N/A',
            'statut': ins.statut,
            'transaction_id': ins.transaction_id,
            'date_inscription': ins.date_inscription.isoformat(),
            'date_completion': ins.date_completion.isoformat() if ins.date_completion else None,
        })
    
    transactions_data = []
    for trans in transactions:
        transactions_data.append({
            'id': trans.id,
            'transaction_id': trans.transaction_id,
            'user_email': trans.user_email,
            'user_name': trans.user_name,
            'formation_id': trans.formation_id,
            'formation_title': trans.formation.titre if trans.formation else 'N/A',
            'status': trans.status,  # ⭐ Peut être pending, completed, etc.
            'created_at': trans.created_at.isoformat() if hasattr(trans, 'created_at') else 'N/A',
        })
    
    # Obtenir l'email actuellement en session
    session_email = request.session.get('user_email', 'Aucun')
    
    return JsonResponse({
        'inscriptions': {
            'count': len(inscriptions_data),
            'data': inscriptions_data,
        },
        'transactions': {
            'count': len(transactions_data),
            'data': transactions_data,
        },
        'session': {
            'user_email': session_email,
            'formation_id': request.session.get('formation_id', 'Aucun'),
        },
        'message': 'Inscriptions vides? Cela signifie que aucun paiement n\'a été marqué comme "completed". Les paiements doivent passer par le webhook SMS pour être complétés.',
    }, safe=False)

def debug_complete_payment(request, transaction_id):
    """Endpoint de TEST pour marquer une transaction comme complétée"""
    from paiements.models import Transaction
    
    try:
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        transaction.mark_as_completed()
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Transaction {transaction_id} marquée comme complétée!',
            'data': {
                'transaction_id': transaction.transaction_id,
                'status': transaction.status,
                'user_email': transaction.user_email,
                'formation_id': transaction.formation_id,
            }
        })
    except Transaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'❌ Transaction {transaction_id} non trouvée',
            'all_transactions': list(Transaction.objects.values_list('transaction_id', flat=True))
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'❌ Erreur: {str(e)}',
        }, status=500)
