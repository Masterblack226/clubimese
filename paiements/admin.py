from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Transaction, PaymentAutoConfiguration, SMSParserLog

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user_name', 'amount', 'operator', 'status_display', 'created_at', 'time_remaining']
    list_filter = ['status', 'operator', 'created_at']
    search_fields = ['transaction_id', 'user_name', 'user_phone', 'user_email']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at', 'completed_at', 'sms_timestamp']
    actions = ['mark_as_completed', 'mark_as_expired']
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'expired': 'gray',
            'cancelled': 'black'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Statut'
    
    def time_remaining(self, obj):
        if obj.status == 'pending':
            seconds = obj.get_time_remaining()
            if seconds <= 0:
                return 'Expiré'
            minutes = seconds // 60
            seconds = seconds % 60
            return f'{minutes}:{seconds:02d}'
        return '-'
    time_remaining.short_description = 'Temps restant'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} transactions marquées comme complétées.')
    mark_as_completed.short_description = "Marquer comme complété"
    
    def mark_as_expired(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='expired')
        self.message_user(request, f'{updated} transactions marquées comme expirées.')
    mark_as_expired.short_description = "Marquer comme expiré"

@admin.register(PaymentAutoConfiguration)
class PaymentAutoConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'user_phone', 'amount', 'operator', 'is_active', 'created_at']
    list_filter = ['operator', 'is_active', 'created_at']
    search_fields = ['name', 'user_phone']

@admin.register(SMSParserLog)
class SMSParserLogAdmin(admin.ModelAdmin):
    list_display = ['sender', 'parser_used', 'is_success', 'created_at']
    list_filter = ['parser_used', 'is_success', 'created_at']
    search_fields = ['sender', 'sms_content']
    readonly_fields = ['sms_content', 'parser_used', 'parsed_data', 'created_at']
