from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from main.models import Evenement, Formation, Actualite, CategorieActualite, CategorieFormation, Formateur, Ressource

class Command(BaseCommand):
    help = 'Crée les groupes d\'utilisateurs avec permissions appropriées'
    
    def handle(self, *args, **options):
        # Créer le groupe Administrateurs
        admin_group, created = Group.objects.get_or_create(name='Administrateurs')
        
        if created:
            self.stdout.write('Groupe Administrateurs créé')
        else:
            # Vider les permissions existantes
            admin_group.permissions.clear()
        
        # Modèles auxquels les administrateurs peuvent accéder
        models_admin_access = [
            Evenement,
            Formation, 
            Actualite,
            CategorieActualite,
            CategorieFormation,
            Formateur,
            Ressource
        ]
        
        # Ajouter les permissions pour chaque modèle
        for model in models_admin_access:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)
            for perm in permissions:
                admin_group.permissions.add(perm)
                self.stdout.write(f'Permission ajoutée: {perm}')
        
        self.stdout.write(
            self.style.SUCCESS('Groupe Administrateurs configuré avec succès')
        )
        
        # Informations sur les superutilisateurs
        self.stdout.write('\nPour créer des superadministrateurs:')
        self.stdout.write('python manage.py createsuperuser')
        self.stdout.write('\nPour créer des administrateurs:')
        self.stdout.write('1. Créez un utilisateur normal dans l\'admin')
        self.stdout.write('2. Assignez-le au groupe "Administrateurs"')
