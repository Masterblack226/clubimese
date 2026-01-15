club_imese/
├── 📁 actualites/
│   ├── 📁 __pycache__/
│   ├── 📁 migrations/
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
│
├── 📁 formations/
│   ├── 📁 __pycache__/
│   ├── 📁 migrations/
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
│
├── 📁 main/                       # Application principale
│   ├── 📁 __pycache__/
│   ├── 📁 migrations/
│   │   └── __init__.py
│   ├── 📁 management/
│   ├── 📁 services/               # Services/logique métier
│   ├── 📁 templates/
│   │   ├── 📁 admin/
│   │   │   ├── dashboard.html
│   │   │   └── payments_dashboard.html
│   │   ├── 📁 emails/
│   │   │   ├── vip_activation.html
│   │   │   └── welcome_email.html
│   │   ├── formations_catalog.html
│   │   ├── homepage.html
│   │   ├── membership_portal.html
│   │   ├── my_payments.html
│   │   ├── news_activities.html
│   │   ├── paiement.html
│   │   ├── payment_confirmation.html
│   │   ├── ressources.html
│   │   ├── success.html
│   │   └── vip_membership.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── 📁 media/                      # Fichiers uploadés par les utilisateurs
│   ├── 📁 actualites/
│   ├── 📁 formations/
│   ├── 📁 formateurs/
│   ├── 📁 galerie/
│   ├── 📁 profils/
│   └── 📁 ressources/
│
├── 📁 static/                     # Fichiers statiques
│   ├── 📁 css/
│   │   ├── main.css
│   │   └── tailwind.css
│   ├── 📁 images/                 # Assets/images
│   └── 📁 js/                     # Fichiers JavaScript
│
├── 📁 ressources/
│   ├── 📁 __pycache__/
│   ├── 📁 migrations/
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
│
├── 📁 membres/
│   ├── 📁 __pycache__/
│   ├── 📁 migrations/
│   │   └── __init__.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
│
├── 📁 imese_site/                 # Configuration du projet
│   ├── 📁 __pycache__/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                # Fichier de configuration
│   ├── urls.py                    # URLs principaux
│   └── wsgi.py
│
├── 📄 manage.py                   # Script de gestion Django
└── 📄 db.sqlite3                  # Base de données (dev seulement)