
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

class EmailService:
    @staticmethod
    def send_welcome_email(user, profil):
        """Envoyer email de bienvenue"""
        context = {
            'user': user,
            'profil': profil,
            'site_name': 'Club IMESE',
        }
        
        subject = 'Bienvenue sur Club IMESE!'
        html_content = render_to_string('emails/welcome_email.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        return email.send()
    
    @staticmethod
    def send_vip_activation_email(user, abonnement):
        """Envoyer email d'activation VIP"""
        context = {
            'user': user,
            'abonnement': abonnement,
            'site_name': 'Club IMESE',
        }
        
        subject = 'Votre abonnement VIP est activé!'
        html_content = render_to_string('emails/vip_activation.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        return email.send()
    
    @staticmethod
    def send_event_notification(user, evenement):
        """Envoyer notification d'événement"""
        context = {
            'user': user,
            'evenement': evenement,
            'site_name': 'Club IMESE',
        }
        
        subject = f'Nouvel événement: {evenement.titre}'
        html_content = render_to_string('emails/event_notification.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        return email.send()
