from django.db import models

class Ressource(models.Model):
    CATEGORIES = [
        ('DEVOIRS', 'Devoirs'),
        ('STATISTIQUES', 'Statistiques'),
        ('ECONOMIE', 'Économie'),
        ('OUTILS', 'Outils'),
        ('ETUDES_CAS', 'Études de Cas'),
    ]
    
    NIVEAUX = [
        ('DEBUTANT', 'Débutant'),
        ('INTERMEDIAIRE', 'Intermédiaire'),
        ('AVANCE', 'Avancé'),
    ]
     
    titre = models.CharField(max_length=200)
    description = models.TextField()
    categorie = models.CharField(max_length=20, choices=CATEGORIES)
    niveau = models.CharField(max_length=20, choices=NIVEAUX)
    fichier = models.FileField(upload_to='ressources/')
    taille_fichier = models.CharField(max_length=50, blank=True)
    accessible_vip = models.BooleanField(default=False)
    date_ajout = models.DateTimeField(auto_now_add=True)
    echeance = models.DateField(null=True, blank=True)
    duree_estimee = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.titre
    
    class Meta:
        verbose_name = "Ressource"
        verbose_name_plural = "Ressources"