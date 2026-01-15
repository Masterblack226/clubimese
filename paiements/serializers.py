# paiements/serializers.py
from rest_framework import serializers
from .models import Transaction, PaymentAutoConfiguration, SMSParserLog
from formations.models import Formation
from django.utils import timezone

class FormationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = ['id', 'titre', 'description', 'prix', 'duree']

class TransactionSerializer(serializers.ModelSerializer):
    formation = FormationSerializer(read_only=True)
    formation_id = serializers.PrimaryKeyRelatedField(
        queryset=Formation.objects.all(),
        write_only=True,
        source='formation'
    )
    time_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'reference_code', 'user_name', 'user_phone', 
            'user_email', 'formation', 'formation_id', 'amount', 'operator',
            'recipient_phone', 'status', 'sms_content', 'sms_sender',
            'sms_timestamp', 'metadata', 'expires_at', 'created_at',
            'updated_at', 'completed_at', 'time_remaining', 'is_expired',
            'payment_details'
        ]
        read_only_fields = ['transaction_id', 'created_at', 'updated_at', 'completed_at']
    
    def get_time_remaining(self, obj):
        return obj.get_time_remaining()
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_payment_details(self, obj):
        return obj.generate_payment_details()
    
    def validate(self, data):
        # Vérifier que la transaction n'expire pas dans le passé
        if 'expires_at' in data and data['expires_at'] <= timezone.now():
            raise serializers.ValidationError("La date d'expiration doit être dans le futur")
        
        # Vérifier le numéro de téléphone
        if 'user_phone' in data:
            phone = data['user_phone']
            # Nettoyer le numéro
            phone = phone.replace(' ', '').replace('+', '')
            if len(phone) < 8 or len(phone) > 12:
                raise serializers.ValidationError("Numéro de téléphone invalide")
            data['user_phone'] = phone
        
        return data

class PaymentAutoConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAutoConfiguration
        fields = ['id', 'name', 'user_phone', 'amount', 'operator', 'formation', 'is_active', 'created_at']
    
    def validate(self, data):
        # Vérifier si une configuration similaire existe déjà
        existing = PaymentAutoConfiguration.objects.filter(
            user_phone=data['user_phone'],
            amount=data['amount'],
            operator=data['operator'],
            formation=data['formation'],
            is_active=True
        ).exists()
        
        if existing:
            raise serializers.ValidationError("Une configuration similaire existe déjà")
        
        return data

class SMSParserLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSParserLog
        fields = '__all__'
