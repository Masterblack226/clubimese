from django.db import models
from django.utils import timezone
import uuid
from django.core.validators import MinValueValidator
from formations.models import Formation

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En traitement'),
        ('completed', 'Complétée'),
        ('failed', 'Échouée'),
        ('expired', 'Expirée'),
        ('cancelled', 'Annulée'),
    ]
    
    OPERATOR_CHOICES = [
        ('orange', 'Orange Money'),
        ('moov', 'Moov Money'),
        ('wave', 'Wave'),
    ]
    
    # Identifiants
    transaction_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    reference_code = models.CharField(max_length=20)
    
    # Informations utilisateur
    user_name = models.CharField(max_length=200)
    user_phone = models.CharField(max_length=15)
    user_email = models.EmailField()
    
    # Informations paiement
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES)
    recipient_phone = models.CharField(max_length=15)  # Numéro qui a reçu le paiement
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Données SMS
    sms_content = models.TextField(blank=True, null=True)
    sms_sender = models.CharField(max_length=15, blank=True, null=True)
    sms_timestamp = models.DateTimeField(blank=True, null=True)
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user_phone']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} FCFA"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def mark_as_completed(self):
        from main.models import InscriptionFormation
        from django.utils import timezone as tz
        import logging
        
        logger = logging.getLogger(__name__)
        
        self.status = 'completed'
        self.completed_at = tz.now()
        self.save()
        
        logger.info(f"✅ Transaction complétée: {self.transaction_id} - Email: {self.user_email}")
        
        # Créer une inscription formation si la formation existe
        if self.formation:
            inscription, created = InscriptionFormation.objects.get_or_create(
                email=self.user_email,
                formation=self.formation,
                defaults={
                    'telephone': self.user_phone,
                    'nom': self.user_name,
                    'statut': 'completed',
                    'reference_code': self.reference_code,
                    'transaction_id': self.transaction_id,
                    'date_completion': tz.now(),
                }
            )
            
            if created:
                logger.info(f"✅ Nouvelle inscription créée: {self.user_email} -> {self.formation.titre}")
            else:
                logger.info(f"⚠️ Inscription existante mise à jour: {self.user_email} -> {self.formation.titre}")
                inscription.statut = 'completed'
                inscription.date_completion = tz.now()
                inscription.save()
        else:
            logger.warning(f"⚠️ Transaction sans formation: {self.transaction_id}")
    
    def get_time_remaining(self):
        if self.is_expired():
            return 0
        remaining = self.expires_at - timezone.now()
        return max(0, int(remaining.total_seconds()))
    
    def generate_payment_details(self):
        """Génère les détails de paiement pour l'utilisateur"""
        operator_numbers = {
            'orange': '+22654179369',
            'moov': '+22672689558',
        }
        
        return {
            'operator': self.get_operator_display(),
            'recipient_number': operator_numbers.get(self.operator, ''),
            'amount': float(self.amount),
            'reference_code': self.reference_code,
            'expires_in': self.get_time_remaining(),
            'transaction_id': self.transaction_id
        }

class PaymentAutoConfiguration(models.Model):
    """Configuration des paiements automatiques"""
    name = models.CharField(max_length=100)
    user_phone = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    operator = models.CharField(max_length=20, choices=Transaction.OPERATOR_CHOICES)
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.user_phone}"

class SMSParserLog(models.Model):
    """Log des SMS parsés"""
    sms_content = models.TextField()
    sender = models.CharField(max_length=15)
    parser_used = models.CharField(max_length=50)
    parsed_data = models.JSONField()
    is_success = models.BooleanField()
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class PaymentStatistic(models.Model):
    """Statistiques des paiements"""
    date = models.DateField(unique=True)
    total_transactions = models.IntegerField(default=0)
    successful_transactions = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    by_operator = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-date']
