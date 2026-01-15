from django.db import models

class Formateur(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom complet")
    bio = models.TextField(verbose_name="Biographie")
    photo = models.ImageField(upload_to='formateurs/', verbose_name="Photo de profil")
    email = models.EmailField(verbose_name="Email de contact")
    specialite = models.CharField(max_length=100, verbose_name="Spécialité")
    
    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Formateur"
        verbose_name_plural = "Formateurs"

class Formation(models.Model):
    NIVEAUX = [
        ('DEBUTANT', 'Débutant'),
        ('INTERMEDIAIRE', 'Intermédiaire'),
        ('AVANCE', 'Avancé'),
    ]
    
    titre = models.CharField(max_length=200, verbose_name="Titre de la formation")
    description = models.TextField(verbose_name="Description")
    formateur = models.ForeignKey(Formateur, on_delete=models.CASCADE, verbose_name="Formateur")
    niveau = models.CharField(max_length=20, choices=NIVEAUX, verbose_name="Niveau")
    prix = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (€)")
    date_debut = models.DateTimeField(verbose_name="Date de début")
    date_fin = models.DateTimeField(verbose_name="Date de fin")
    lien_inscription = models.URLField(verbose_name="Lien d'inscription")
    image = models.ImageField(upload_to='formations/', verbose_name="Image de la formation")
    duree = models.CharField(max_length=50, verbose_name="Durée", help_text="Ex: 4 semaines, 2 mois")
    
    def __str__(self):
        return f"{self.titre} - {self.formateur.nom}"
    
    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-date_debut']