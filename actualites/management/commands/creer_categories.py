from django.core.management.base import BaseCommand
from actualites.models import CategorieActualite

class Command(BaseCommand):
    help = 'Crée les 6 catégories d\'actualités correspondant au template'

    def handle(self, *args, **kwargs):
        # Les 6 catégories exactes du template news_activities.html
        categories = [
            {
                'type_categorie': 'TOUTES',
                'nom': 'Toutes les actualités',
                'couleur': 'bg-gray-100 text-gray-700 hover:bg-gray-200',
                'icone': 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
                'ordre': 1,
                'description': 'Toutes les actualités du Club IMESE'
            },
            {
                'type_categorie': 'FORMATIONS',
                'nom': 'Formations',
                'couleur': 'bg-blue-100 text-blue-600 hover:bg-blue-200',
                'icone': 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
                'ordre': 2,
                'description': 'Actualités sur les formations et ateliers'
            },
            {
                'type_categorie': 'REUSSITES', 
                'nom': 'Réussites',
                'couleur': 'bg-green-100 text-green-600 hover:bg-green-200',
                'icone': 'M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z',
                'ordre': 3,
                'description': 'Réussites et accomplissements des membres'
            },
            {
                'type_categorie': 'EVENEMENTS',
                'nom': 'Événements',
                'couleur': 'bg-purple-100 text-purple-600 hover:bg-purple-200',
                'icone': 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
                'ordre': 4,
                'description': 'Événements et activités du club'
            },
            {
                'type_categorie': 'PARTENARIATS',
                'nom': 'Partenariats',
                'couleur': 'bg-orange-100 text-orange-600 hover:bg-orange-200',
                'icone': 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
                'ordre': 5,
                'description': 'Partenariats et collaborations'
            },
            {
                'type_categorie': 'ANNONCE',
                'nom': 'Annonce',
                'couleur': 'bg-red-100 text-red-600 hover:bg-red-200',
                'icone': 'M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z',
                'ordre': 6,
                'description': 'Annonces importantes et urgences'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for cat_data in categories:
            # Crée ou met à jour chaque catégorie
            cat, created = CategorieActualite.objects.update_or_create(
                type_categorie=cat_data['type_categorie'],
                defaults={
                    'nom': cat_data['nom'],
                    'couleur': cat_data['couleur'],
                    'icone': cat_data['icone'],
                    'ordre': cat_data['ordre'],
                    'description': cat_data['description']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Catégorie créée: {cat.nom}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ Catégorie mise à jour: {cat.nom}'))
        
        # Supprime les catégories qui ne font pas partie des 6 du template
        types_template = [cat['type_categorie'] for cat in categories]
        categories_a_supprimer = CategorieActualite.objects.exclude(type_categorie__in=types_template)
        deleted_count = categories_a_supprimer.count()
        
        if deleted_count > 0:
            categories_a_supprimer.delete()
            self.stdout.write(self.style.ERROR(f'🗑️ {deleted_count} catégories obsolètes supprimées'))
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 RÉSUMÉ:'))
        self.stdout.write(self.style.SUCCESS(f'   • {created_count} catégories créées'))
        self.stdout.write(self.style.SUCCESS(f'   • {updated_count} catégories mises à jour'))
        self.stdout.write(self.style.SUCCESS(f'   • {deleted_count} catégories supprimées'))
        self.stdout.write(self.style.SUCCESS(f'   • Total: {CategorieActualite.objects.count()} catégories (sur 6 attendues)'))
        
        # Vérification finale
        categories_finales = CategorieActualite.objects.all().order_by('ordre')
        self.stdout.write(self.style.SUCCESS(f'\n📋 LISTE DES CATÉGORIES:'))
        for cat in categories_finales:
            self.stdout.write(self.style.SUCCESS(f'   {cat.ordre}. {cat.nom} ({cat.type_categorie})'))