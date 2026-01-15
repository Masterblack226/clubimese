from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver



class CategorieFormation(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.nom

class Formateur(models.Model):
    nom = models.CharField(max_length=100)
    specialite = models.CharField(max_length=100)
    bio = models.TextField()
    photo = models.ImageField(upload_to='formateurs/', blank=True)
    
    def __str__(self):
        return self.nom

class Formation(models.Model):
    NIVEAU_CHOICES = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]
    
    titre = models.CharField(max_length=200)
    description = models.TextField()
    formateur = models.ForeignKey(Formateur, on_delete=models.CASCADE)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    date_debut = models.DateField()
    date_fin = models.DateField()
    categorie = models.ForeignKey(CategorieFormation, on_delete=models.CASCADE)
    lien_inscription = models.URLField(blank=True)
    image = models.ImageField(upload_to='formations/', blank=True)
    
    def __str__(self):
        return self.titre

class InscriptionFormation(models.Model):
    """Modèle pour tracker les inscriptions des utilisateurs aux formations"""
    from formations.models import Formation as FormationsFormation
    
    # L'utilisateur peut être anonyme (pas de User)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, 
                                   related_name='inscriptions_formations')
    
    # Informations de l'utilisateur (pour les paiements anonymes)
    email = models.EmailField()
    telephone = models.CharField(max_length=15)
    nom = models.CharField(max_length=200)
    
    # La formation (depuis formations.models)
    formation = models.ForeignKey('formations.Formation', on_delete=models.CASCADE, 
                                 related_name='inscriptions')
    
    # Statut et références
    statut = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente de paiement'),
            ('completed', 'Inscription complétée'),
            ('cancelled', 'Annulée'),
        ],
        default='pending'
    )
    
    # Référence de transaction/paiement
    reference_code = models.CharField(max_length=20, blank=True)
    transaction_id = models.CharField(max_length=50, blank=True, unique=True)
    
    # Dates
    date_inscription = models.DateTimeField(auto_now_add=True)
    date_completion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('email', 'formation')
        ordering = ['-date_inscription']
    
    def __str__(self):
        return f"{self.nom} - {self.formation.titre} ({self.statut})"

class CategorieActualite(models.Model):
    # Exactement les 6 catégories du template
    CATEGORIES_TEMPLATE = [
        ('TOUTES', 'Toutes les actualités'),
        ('FORMATIONS', 'Formations'),
        ('REUSSITES', 'Réussites'),
        ('EVENEMENTS', 'Événements'),
        ('PARTENARIATS', 'Partenariats'),
        ('ANNONCE', 'Annonce'),
    ]

    CATEGORIES_TEMPLATE = [
        ('TOUTES', 'Toutes les actualités'),  # Option d'affichage seulement
        ('FORMATIONS', 'Formations'),
        ('REUSSITES', 'Réussites'),
        ('EVENEMENTS', 'Événements'),
        ('PARTENARIATS', 'Partenariats'),
        ('ANNONCE', 'Annonce'),
    ]
    
    nom = models.CharField(max_length=100)
    type_categorie = models.CharField(
        max_length=20, 
        choices=CATEGORIES_TEMPLATE, 
        unique=True,  
        null=True, 
        blank=True
    )
    couleur = models.CharField(max_length=50, default='bg-primary-100 text-primary-600')
    icone = models.CharField(max_length=100, blank=True)
    ordre = models.IntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Catégorie d'Actualité"
        verbose_name_plural = "Catégories d'Actualité"

    def __str__(self):
        return self.nom
    
    @classmethod
    def get_categories_template(cls):
        """Retourne les 6 catégories exactes du template"""
        return cls.CATEGORIES_TEMPLATE
    
    
class Actualite(models.Model):
    TYPE_ACTUALITE_CHOICES = [
        ('FEATURED', 'À la une'),
        ('NORMAL', 'Normal'),
    ]

    CATEGORIES_TEMPLATE = [
        ('TOUTES', 'Toutes les actualités'),
        ('FORMATIONS', 'Formations'),
        ('REUSSITES', 'Réussites'),
        ('EVENEMENTS', 'Événements'),
        ('PARTENARIATS', 'Partenariats'),
        ('ANNONCE', 'Annonce'),
    ]
    
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    categorie = models.ForeignKey(CategorieActualite, on_delete=models.CASCADE)
    date_publication = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='actualites/', blank=True)
    auteur = models.CharField(max_length=100)
    vues = models.IntegerField(default=0)
    est_publie = models.BooleanField(default=True, verbose_name="Est publié")
    resume = models.TextField(max_length=300, blank=True, help_text="Résumé court pour l'affichage dans les listes")
    type_actualite = models.CharField(
        max_length=20, 
        choices=TYPE_ACTUALITE_CHOICES, 
        default='NORMAL',
        verbose_name="Type d'actualité"
    )
    def __str__(self):
        return self.titre
    def save(self, *args, **kwargs):
        # Auto-générer le résumé si vide
        if not self.resume and self.contenu:
            self.resume = self.contenu[:297] + "..." if len(self.contenu) > 300 else self.contenu
        super().save(*args, **kwargs)
    
class Evenement(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    date_debut = models.DateTimeField()
    lieu = models.CharField(max_length=100)
    formateur = models.ForeignKey(Formateur, on_delete=models.CASCADE, null=True, blank=True)
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")
    
    def __str__(self):
        return self.titre
    
    class Meta:
        permissions = [
            ("can_publish_evenement", "Can publish evenement"),
            ("can_manage_evenement", "Can manage evenement"),
        ]

class Ressource(models.Model):
    CATEGORIE_CHOICES = [
        ('devoirs', 'Devoirs'),
        ('outils', 'Outils Statistiques'),
        ('bibliotheque', 'Bibliothèque'),
        ('performances', 'Performances'),
        ('economique', 'Données Économiques'),
        ('corrections', 'Corrections'),
    ]
    
    titre = models.CharField(max_length=200)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    fichier = models.FileField(upload_to='ressources/')
    description = models.TextField()
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.titre

class AbonnementVIP(models.Model):
    TYPE_CHOICES = [
        ('gratuit', 'Gratuit'),
        ('standard', 'Standard'), 
        ('premium', 'Premium'),
    ]
    
    nom = models.CharField(max_length=100)
    type_abonnement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    prix_annuel = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    avantages = models.TextField(help_text="Séparez les avantages par des points-virgules")
    est_populaire = models.BooleanField(default=False)
    couleur_principale = models.CharField(max_length=7, default='#3B82F6')  # Code couleur hex
    ordre_affichage = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['ordre_affichage', 'prix']
        verbose_name = "Abonnement VIP"
        verbose_name_plural = "Abonnements VIP"
    
    def __str__(self):
        return f"{self.nom} - {self.get_type_abonnement_display()}"
    
    def get_avantages_list(self):
        return [avantage.strip() for avantage in self.avantages.split(';') if avantage.strip()]
    
    def get_prix_mensuel(self):
        if self.prix_annuel:
            return self.prix_annuel / 12
        return self.prix
    
    def get_economie_annuelle(self):
        if self.prix_annuel:
            return (self.prix * 12) - self.prix_annuel
        return 0


class GalerieImage(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='galerie/')
    date_ajout = models.DateTimeField(auto_now_add=True)
    evenement_lie = models.ForeignKey(Evenement, on_delete=models.SET_NULL, null=True, blank=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-date_ajout']
    
    def __str__(self):
        return self.titre
    

class ProfilMembre(models.Model):
    NIVEAU_CHOICES = [
        ('licence1', 'Licence 1'),
        ('licence2', 'Licence 2'),
        ('licence3', 'Licence 3'),
        ('master1', 'Master 1'),
        ('master2', 'Master 2'),
        ('doctorat', 'Doctorat'),
    ]
    
    SPECIALISATION_CHOICES = [
        ('statistics', 'Statistiques'),
        ('economics', 'Économie'),
        ('econometrics', 'Économétrie'),
        ('data-science', 'Science des Données'),
        ('applied-economics', 'Économie Appliquée'),
        ('financial-economics', 'Économie Financière'),
        ('mathematiques', 'Mathématiques'),
    ]
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE)
    numero_etudiant = models.CharField(max_length=20, unique=True)
    telephone = models.CharField(max_length=20)
    niveau_academique = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    specialisation = models.CharField(max_length=30, choices=SPECIALISATION_CHOICES)
    date_inscription = models.DateTimeField(auto_now_add=True)
    est_vip = models.BooleanField(default=False)
    date_fin_vip = models.DateField(null=True, blank=True)
    newsletter_acceptee = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='profils/', blank=True, null=True)

    @classmethod
    def generate_unique_numero(cls, user_id,base_numero=None):
        
    
        if base_numero:
            numero = base_numero
            counter = 1
            while cls.objects.filter(numero_etudiant=numero).exists():
                numero = f"{base_numero}_{counter}"
                counter += 1
                if counter > 1000:  # Sécurité
                    break
            return numero
        else:
            # Générer un numéro basé sur l'ID utilisateur
            return f'ETU_{user_id}'
    
    def __str__(self):
        return f"{self.utilisateur.first_name} {self.utilisateur.last_name} ({self.numero_etudiant})"

#@receiver(post_save, sender=User)
#def creer_profil_membre(sender, instance, created, **kwargs):
#    if created:
#        # Utiliser get_or_create pour éviter les doublons
#        ProfilMembre.objects.get_or_create(
#            utilisateur=instance,
#            defaults={
                #'numero_etudiant': f'ETU_{instance.id}',
                #'telephone': '',
                #'niveau_academique': 'licence1',
                #'specialisation': 'statistics',
                #'newsletter_acceptee': False
            #}
        #)


@receiver(post_save, sender=User)
def creer_profil_membre(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        # Générer un numéro étudiant unique
        base_numero = f'ETU_{instance.id}'
        numero_etudiant = base_numero
        counter = 1
        while ProfilMembre.objects.filter(numero_etudiant=numero_etudiant).exists():
            numero_etudiant = f'{base_numero}_{counter}'
            counter += 1
            
        try:
            ProfilMembre.objects.create(
                utilisateur=instance,
                numero_etudiant=numero_etudiant,
                telephone='',
                niveau_academique='licence1',
                specialisation='statistics',
                newsletter_acceptee=False
            )
        except Exception as e:
            # En cas d'erreur, ne pas bloquer la création de l'utilisateur
            print(f"Erreur lors de la création du profil: {e}")
            pass        

#@receiver(post_save, sender=User)
#def sauvegarder_profil_membre(sender, instance, **kwargs):
#    if hasattr(instance, 'profilemembre'):
#        instance.profilmembre.save()


class ActiviteMembre(models.Model):
    TYPE_ACTIVITE_CHOICES = [
        ('devoir_corrige', 'Devoir Corrigé'),
        ('nouvelle_formation', 'Nouvelle Formation'),
        ('rappel_devoir', 'Rappel Devoir'),
        ('certification_obtenue', 'Certification Obtenue'),
        ('progression', 'Progression'),
        ('annonce', 'Annonce'),
    ]
    
    membre = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activites')
    type_activite = models.CharField(max_length=30, choices=TYPE_ACTIVITE_CHOICES)
    titre = models.CharField(max_length=200)
    description = models.TextField()
    date_activite = models.DateTimeField(auto_now_add=True)
    lien = models.URLField(blank=True, null=True)
    est_lue = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_activite']
        verbose_name = "Activité Membre"
        verbose_name_plural = "Activités Membres"
    
    def __str__(self):
        return f"{self.membre.username} - {self.titre}"
    
    def get_icon_class(self):
        icons = {
            'devoir_corrige': 'success',
            'nouvelle_formation': 'primary', 
            'rappel_devoir': 'secondary',
            'certification_obtenue': 'accent',
            'progression': 'info',
            'annonce': 'warning',
        }
        return icons.get(self.type_activite, 'primary')
    
    def get_icon_svg(self):
        icons = {
            'devoir_corrige': '''
                <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                </svg>
            ''',
            'nouvelle_formation': '''
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
            ''',
            'rappel_devoir': '''
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            ''',
            'certification_obtenue': '''
                <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732L14.146 12.8l-1.179 4.456a1 1 0 01-1.934 0L9.854 12.8 6.5 10.866a1 1 0 010-1.732L9.854 7.2l1.179-4.456A1 1 0 0112 2z" clip-rule="evenodd"/>
                </svg>
            ''',
            'progression': '''
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                </svg>
            ''',
            'annonce': '''
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"/>
                </svg>
            ''',
        }
        return icons.get(self.type_activite, icons['annonce'])
    
    def get_bg_color_class(self):
        colors = {
            'devoir_corrige': 'success-50',
            'nouvelle_formation': 'primary-50',
            'rappel_devoir': 'secondary-50',
            'certification_obtenue': 'accent-50',
            'progression': 'info-50',
            'annonce': 'warning-50',
        }
        return colors.get(self.type_activite, 'primary-50')
    
    def get_icon_bg_class(self):
        colors = {
            'devoir_corrige': 'success',
            'nouvelle_formation': 'primary',
            'rappel_devoir': 'secondary',
            'certification_obtenue': 'accent',
            'progression': 'info',
            'annonce': 'warning',
        }
        return colors.get(self.type_activite, 'primary')
    
    def get_temps_ecoule(self):
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        return f"Il y a {timesince(self.date_activite)}"


class TemoignageVIP(models.Model):
    membre = models.ForeignKey(User, on_delete=models.CASCADE)
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    note = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    date_creation = models.DateTimeField(auto_now_add=True)
    est_approuve = models.BooleanField(default=False)
    image_url = models.URLField(blank=True, null=True)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Témoignage VIP"
        verbose_name_plural = "Témoignages VIP"
    
    def __str__(self):
        return f"{self.membre.username} - {self.titre}"
    
    def get_note_etoiles(self):
        return "★" * int(self.note) + "☆" * (5 - int(self.note)) 
    
    
# ============================================
# MODÈLES DE PAIEMENT
# ============================================

class Service(models.Model):
    """Modèle pour les services payants (formations, abonnements, etc.)"""
    TYPE_CHOICES = [
        ('formation', 'Formation'),
        ('abonnement', 'Abonnement VIP'),
        ('vip', 'Membre VIP'),
        ('ressource', 'Ressource Premium'),
    ]
    
    nom = models.CharField(max_length=200)
    type_service = models.CharField(max_length=20, choices=TYPE_CHOICES)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    duree_jours = models.IntegerField(default=30, help_text="Durée en jours")
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['type_service', 'prix']
        verbose_name = "Service"
        verbose_name_plural = "Services"
    
    def __str__(self):
        return f"{self.nom} - {self.prix} FCFA"
    
    def get_type_display_color(self):
        colors = {
            'formation': 'primary',
            'abonnement': 'success', 
            'vip': 'warning',
            'ressource': 'info',
        }
        return colors.get(self.type_service, 'secondary')

class Paiement(models.Model):
    """Modèle pour enregistrer les paiements"""
    STATUS_CHOICES = [
        ('pending', '⏳ En attente'),
        ('confirmed', '✅ Confirmé'),
        ('rejected', '❌ Rejeté'),
        ('expired', '⌛ Expiré'),
    ]
    
    OPERATOR_CHOICES = [
        ('orange', 'Orange Money'),
        ('moov', 'Moov Money'),
    ]
    
    # === Information transaction ===
    transaction_id = models.CharField(max_length=50, unique=True, verbose_name="ID Transaction")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, blank=True, null=True, verbose_name="Service")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (FCFA)")
    
    # === Information utilisateur ===
    user_phone = models.CharField(max_length=20, verbose_name="Téléphone utilisateur")
    user_email = models.EmailField(verbose_name="Email utilisateur")
    user_name = models.CharField(max_length=100, verbose_name="Nom complet")
    reference_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Code de référence")
    
    # === Information paiement ===
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES, verbose_name="Opérateur")
    operator_number = models.CharField(max_length=20, default="", verbose_name="Numéro opérateur")
    
    # === Statut et dates ===
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date création")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="Date soumission")
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="Date confirmation")
    
    # === Métadonnées ===
    sms_received = models.TextField(blank=True, verbose_name="SMS reçu")
    admin_notes = models.TextField(blank=True, verbose_name="Notes admin")
    is_processed = models.BooleanField(default=False, verbose_name="Traité")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user_phone']),
        ]
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user_name} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Si c'est une nouvelle création, générer un ID
        if not self.transaction_id:
            from datetime import datetime
            import uuid
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:6].upper()
            self.transaction_id = f"CLUBIM{timestamp}{unique_id}"
        
        # Si confirmé, mettre à jour la date de confirmation
        if self.status == 'confirmed' and not self.confirmed_at:
            from django.utils import timezone
            self.confirmed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Vérifie si le paiement a expiré (15 minutes)"""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.status in ['confirmed', 'rejected', 'expired']:
            return False
        
        expiration_time = self.created_at + timedelta(minutes=15)
        return timezone.now() > expiration_time
    
    def get_time_left(self):
        """Retourne le temps restant avant expiration"""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.status != 'pending':
            return 0
        
        expiration_time = self.created_at + timedelta(minutes=15)
        time_left = expiration_time - timezone.now()
        return max(0, int(time_left.total_seconds()))
    
    def confirm(self, sms_text=""):
        """Confirme le paiement"""
        from django.utils import timezone
        
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        if sms_text:
            self.sms_received = sms_text
        self.save()
        return True
    
    def reject(self, reason=""):
        """Rejette le paiement"""
        self.status = 'rejected'
        if reason:
            self.admin_notes = reason
        self.save()
        return True
    
    def expire(self):
        """Marque le paiement comme expiré"""
        self.status = 'expired'
        self.save()
        return True
    
    def get_status_badge(self):
        """Retourne le badge HTML pour le statut"""
        badges = {
            'pending': '<span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs">⏳ En attente</span>',
            'confirmed': '<span class="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">✅ Confirmé</span>',
            'rejected': '<span class="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs">❌ Rejeté</span>',
            'expired': '<span class="bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs">⌛ Expiré</span>',
        }
        return badges.get(self.status, '')