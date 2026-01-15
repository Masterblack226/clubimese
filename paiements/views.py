from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum, Q
from django.db import transaction as db_transaction

from .models import Transaction, PaymentAutoConfiguration, SMSParserLog
from .serializers import *
from .services.sms_parser import SMSParser
from formations.models import Formation

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Endpoint de santé"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def receive_sms_webhook(request):
    """
    Webhook pour recevoir les SMS de Forward SMS
    Format attendu: {"from": "10", "text": "...", "timestamp": "...", "device": "..."}
    Sécurisé par clé API dans le header X-API-Key
    """
    try:
        # ============================================
        # VÉRIFICATION DE LA CLÉ API (SÉCURITÉ)
        # ============================================
        api_key = request.headers.get('X-API-Key', '')
        expected_key = getattr(settings, 'FORWARD_SMS_WEBHOOK_KEY', 'dev-secret-key')
        
        if api_key != expected_key:
            logger.warning(f"❌ Tentative d'accès webhook avec clé API invalide. IP: {request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Clé API invalide'
            }, status=status.HTTP_403_FORBIDDEN)
        
        logger.info(f"✅ Webhook SMS reçu avec clé API valide")
        
        data = request.data
        
        # Validation des données
        if not data or 'text' not in data:
            return Response({
                'success': False,
                'message': 'Données SMS invalides'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        sms_content = data['text']
        sender = data.get('from', '')
        device = data.get('device', 'unknown')
        timestamp = data.get('timestamp')
        
        # Parser le SMS
        operator, parsed_data, log_entry = SMSParser.parse_sms(sms_content, sender)
        
        # Enregistrer le log
        SMSParserLog.objects.create(
            sms_content=sms_content,
            sender=sender,
            parser_used=operator,
            parsed_data=parsed_data or {},
            is_success=parsed_data is not None,
            error_message=None if parsed_data else 'SMS non reconnu'
        )
        
        if not parsed_data:
            logger.info(f"SMS non reconnu - Expéditeur: {sender}")
            return Response({
                'success': False,
                'message': 'SMS non reconnu comme transaction valide'
            }, status=status.HTTP_200_OK)
        
        # Vérifier si une transaction correspond
        transaction_obj = None
        
        # Recherche par numéro et montant
        if parsed_data.get('sender_phone') and parsed_data.get('amount'):
            # Nettoyer le numéro pour la recherche
            phone = parsed_data['sender_phone']
            if phone.startswith('+226'):
                phone_clean = phone[4:]  # Enlever +226
            elif phone.startswith('226'):
                phone_clean = phone[3:]  # Enlever 226
            else:
                phone_clean = phone
            
            # Chercher une transaction en attente correspondante
            transactions = Transaction.objects.filter(
                Q(user_phone__endswith=phone_clean) | 
                Q(user_phone__contains=phone_clean),
                amount=parsed_data['amount'],
                status='pending',
                operator=operator,
                expires_at__gt=timezone.now()
            ).order_by('-created_at')
            
            if transactions.exists():
                transaction_obj = transactions.first()
        
        # Si transaction trouvée, la marquer comme complétée
        if transaction_obj:
            transaction_obj.status = 'processing'
            transaction_obj.sms_content = sms_content
            transaction_obj.sms_sender = sender
            transaction_obj.sms_timestamp = timezone.now()
            transaction_obj.recipient_phone = get_operator_phone(operator)
            transaction_obj.save()
            
            # Vérifier les paiements automatiques
            auto_configs = PaymentAutoConfiguration.objects.filter(
                user_phone=transaction_obj.user_phone,
                amount=transaction_obj.amount,
                operator=transaction_obj.operator,
                is_active=True
            )
            
            if auto_configs.exists():
                auto_config = auto_configs.first()
                transaction_obj.metadata['auto_config'] = auto_config.name
                transaction_obj.mark_as_completed()
                
                logger.info(f"Paiement automatique traité: {transaction_obj.transaction_id}")
            else:
                logger.info(f"Paiement trouvé, en attente de validation: {transaction_obj.transaction_id}")
            
            return Response({
                'success': True,
                'message': 'Transaction trouvée et traitée',
                'data': {
                    'transaction_id': transaction_obj.transaction_id,
                    'status': transaction_obj.status,
                    'user_name': transaction_obj.user_name,
                    'amount': float(transaction_obj.amount),
                    'operator': transaction_obj.get_operator_display()
                }
            })
        
        # Si pas de transaction trouvée, créer une transaction orpheline
        orphan_transaction = Transaction.objects.create(
            transaction_id=f"ORPHAN_{timezone.now().strftime('%Y%m%d%H%M%S')}",
            reference_code='AUTO_DETECTED',
            user_name=parsed_data.get('sender_name', 'Inconnu'),
            user_phone=parsed_data.get('sender_phone', ''),
            user_email='auto-detected@system.com',
            amount=parsed_data.get('amount', 0),
            operator=operator,
            recipient_phone=get_operator_phone(operator),
            status='processing',
            sms_content=sms_content,
            sms_sender=sender,
            sms_timestamp=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=24),
            metadata={
                'auto_detected': True,
                'parsed_data': parsed_data,
                'device': device
            }
        )
        
        logger.info(f"Transaction orpheline créée: {orphan_transaction.transaction_id}")
        
        return Response({
            'success': True,
            'message': 'Transaction détectée mais non liée à un paiement en attente',
            'data': {
                'transaction_id': orphan_transaction.transaction_id,
                'status': 'orphan'
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur traitement webhook SMS: {str(e)}")
        return Response({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_operator_phone(operator):
    """Retourne le numéro de téléphone de l'opérateur"""
    operator_numbers = {
        'orange': '+22654179369',
        'moov': '+22672689558',
        'wave': '+22600000000'
    }
    return operator_numbers.get(operator, '')

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def create_payment(request):
    """Créer une nouvelle transaction de paiement"""
    try:
        data = request.data
        
        # Validation des données
        required_fields = ['user_name', 'user_phone', 'user_email', 
                          'reference_code', 'operator', 'amount', 'formation_id']
        
        for field in required_fields:
            if field not in data:
                return Response({
                    'success': False,
                    'message': f'Champ manquant: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier la formation
        try:
            formation = Formation.objects.get(id=data['formation_id'])
        except Formation.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Formation non trouvée ou inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier si le montant correspond
        if float(data['amount']) != float(formation.prix):
            return Response({
                'success': False,
                'message': f'Le montant doit être {formation.prix} FCFA'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Générer un ID de transaction unique
        import uuid
        transaction_id = f"CLUBIM{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        
        # Créer la transaction
        transaction_obj = Transaction.objects.create(
            transaction_id=transaction_id,
            reference_code=data['reference_code'],
            user_name=data['user_name'],
            user_phone=data['user_phone'],
            user_email=data['user_email'],
            formation=formation,
            amount=data['amount'],
            operator=data['operator'],
            recipient_phone=get_operator_phone(data['operator']),
            status='pending',
            expires_at=timezone.now() + timedelta(minutes=15),
            metadata={
                'ip_address': request.META.get('REMOTE_ADDR', ''),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'created_via': 'web_form'
            }
        )
        
        # Sauvegarder l'email dans la session pour tracker les inscriptions
        request.session['user_email'] = data['user_email']
        request.session['formation_id'] = data['formation_id']
        request.session.modified = True  # Force la sauvegarde de la session
        
        logger.info(f"💾 Session sauvegardée: email={data['user_email']}, formation={data['formation_id']}")
        
        # Générer les détails de paiement
        payment_details = transaction_obj.generate_payment_details()
        
        return Response({
            'success': True,
            'message': 'Transaction créée avec succès',
            'data': {
                'transaction': TransactionSerializer(transaction_obj).data,
                'payment_details': payment_details
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur création paiement: {str(e)}")
        return Response({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def check_payment_status(request):
    """Vérifier le statut d'une transaction"""
    try:
        data = request.data
        
        if 'transaction_id' not in data:
            return Response({
                'success': False,
                'message': 'transaction_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transaction_obj = Transaction.objects.get(transaction_id=data['transaction_id'])
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Transaction non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier si la transaction a expiré
        if transaction_obj.is_expired() and transaction_obj.status == 'pending':
            transaction_obj.status = 'expired'
            transaction_obj.save()
        
        # Vérifier si un SMS a été reçu
        if transaction_obj.sms_content and transaction_obj.status == 'processing':
            # Vérifier si le paiement correspond à une configuration automatique
            auto_configs = PaymentAutoConfiguration.objects.filter(
                user_phone=transaction_obj.user_phone,
                amount=transaction_obj.amount,
                operator=transaction_obj.operator,
                is_active=True
            )
            
            if auto_configs.exists():
                transaction_obj.mark_as_completed()
        
        return Response({
            'success': True,
            'data': TransactionSerializer(transaction_obj).data
        })
        
    except Exception as e:
        logger.error(f"Erreur vérification statut: {str(e)}")
        return Response({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_payment_details(request, transaction_id):
    """Obtenir les détails d'une transaction"""
    try:
        transaction_obj = Transaction.objects.get(transaction_id=transaction_id)
        return Response({
            'success': True,
            'data': {
                'transaction': TransactionSerializer(transaction_obj).data,
                'payment_details': transaction_obj.generate_payment_details(),
                'time_remaining': transaction_obj.get_time_remaining()
            }
        })
    except Transaction.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Transaction non trouvée'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_statistics(request):
    """Obtenir les statistiques des paiements"""
    try:
        # Statistiques globales
        total_transactions = Transaction.objects.count()
        successful_transactions = Transaction.objects.filter(status='completed').count()
        total_amount = Transaction.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Par opérateur
        by_operator = Transaction.objects.filter(status='completed').values(
            'operator'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # 24 dernières heures
        last_24h = Transaction.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Dernières transactions
        recent_transactions = Transaction.objects.order_by('-created_at')[:10]
        
        return Response({
            'success': True,
            'data': {
                'global': {
                    'total_transactions': total_transactions,
                    'successful_transactions': successful_transactions,
                    'total_amount': float(total_amount),
                    'success_rate': (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
                },
                'by_operator': list(by_operator),
                'last_24h': last_24h,
                'recent_transactions': TransactionSerializer(recent_transactions, many=True).data
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur statistiques: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Viewsets pour l'administration
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Transactions en attente"""
        pending_transactions = Transaction.objects.filter(
            status='pending',
            expires_at__gt=timezone.now()
        ).order_by('expires_at')
        
        serializer = self.get_serializer(pending_transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def orphans(self, request):
        """Transactions orphelines (détectées automatiquement)"""
        orphan_transactions = Transaction.objects.filter(
            metadata__auto_detected=True
        ).order_by('-created_at')
        
        serializer = self.get_serializer(orphan_transactions, many=True)
        return Response(serializer.data)
