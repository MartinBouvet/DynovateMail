# Gmail Assistant IA

Une application Python locale pour gérer vos emails Gmail avec l'aide de l'intelligence artificielle.

## Fonctionnalités

- **Lecture et envoi d'emails**: Interface utilisateur pour lire et envoyer des emails via Gmail
- **Analyse d'emails par IA**: Classification des emails, détection de spam, analyse de sentiment
- **Réponses automatiques**: Génération de réponses aux emails à l'aide de l'IA
- **Interface intuitive**: Interface graphique conviviale basée sur PyQt6

## Prérequis

- Python 3.8 ou supérieur
- Compte Gmail
- Identifiants OAuth2 pour l'API Gmail

## Installation

1. Clonez ce dépôt:
```bash
git clone https://github.com/votre-nom/gmail-assistant.git
cd gmail-assistant
```

2. Créez un environnement virtuel:
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installez les dépendances:
```bash
pip install -r requirements.txt
```

4. Créez un projet sur [Google Cloud Console](https://console.cloud.google.com/):
   - Activez l'API Gmail
   - Créez des identifiants OAuth2
   - Téléchargez le fichier `client_secret.json` et placez-le à la racine du projet

5. Configurez le fichier `.env`:
```
GOOGLE_CLIENT_SECRET_FILE=client_secret.json
```

## Utilisation

1. Lancez l'application:
```bash
python app/main.py
```

2. Lors de la première exécution, une fenêtre de navigateur s'ouvrira pour vous authentifier auprès de Google.

3. Une fois authentifié, l'application affichera vos emails et vous pourrez commencer à les gérer.

## Configuration

Vous pouvez configurer l'application en modifiant le fichier `config.json` qui sera généré lors de la première exécution.

Options de configuration:
- `app`: Configuration générale de l'application (nom, version, thème)
- `email`: Configuration des emails (nombre d'emails à charger, intervalle de rafraîchissement)
- `ai`: Configuration des fonctionnalités d'IA (classification, détection de spam)
- `ui`: Configuration de l'interface utilisateur (taille de police, affichage des panneaux)

## Structure du projet

```
gmail-assistant/
│
├── app/
│   ├── main.py               # Point d'entrée de l'application
│   ├── gmail_client.py       # Client pour l'API Gmail
│   ├── email_processor.py    # Traitement et analyse des emails avec IA
│   ├── email_templates.py    # Templates pour les réponses automatiques
│   │
│   ├── models/
│   │   ├── email_model.py    # Modèles de données pour emails
│   │   └── ai_model.py       # Modèles d'IA (classification, NLP, etc.)
│   │
│   ├── utils/
│   │   ├── auth.py           # Authentification Google OAuth
│   │   ├── config.py         # Configuration de l'application
│   │   └── logger.py         # Logging
│   │
│   └── ui/
│       ├── app_window.py     # Interface utilisateur principale
│       ├── email_view.py     # Vue pour afficher les emails
│       └── compose_view.py   # Vue pour composer des emails
│
├── requirements.txt          # Dépendances Python
├── .env                      # Variables d'environnement
└── README.md                 # Documentation
```

## Extension future

Cette application constitue une base solide pour développer d'autres fonctionnalités avancées:

- **Classification avancée des emails**: Entraînement personnalisé selon vos habitudes
- **Automatisation complète**: Réponses automatiques basées sur des règles personnalisées
- **Intégration avec d'autres services**: Calendrier, tâches, etc.
- **Analyse du langage naturel**: Extraction d'informations clés des emails

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Auteur

[Votre Nom] - [votre.email@example.com]

---

Développé dans le cadre d'un projet entrepreneurial accrédité Pépite.