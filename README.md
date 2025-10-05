# Dynovate Mail Assistant IA

![Dynovate Mail](https://img.shields.io/badge/Dynovate-Mail%20Assistant%20IA-black?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Powered-orange?style=for-the-badge)

Une solution complète de gestion d'emails avec intelligence artificielle. Interface moderne noir et blanc avec UX/UI optimisée pour une productivité maximale.

## 🚀 Fonctionnalités

### 📧 Gestion d'emails intelligente
- **Classification automatique** : Tri automatique des emails (CV, RDV, spam, factures, etc.)
- **Analyse de sentiment** : Détection du ton et de l'urgence des messages
- **Extraction d'entités** : Identification automatique des contacts, dates, lieux
- **Détection de spam** avancée avec IA

### 🤖 Réponses automatiques
- **Réponses contextuelles** : Génération automatique de réponses adaptées
- **Templates intelligents** : Réponses personnalisées selon le type d'email
- **Évitement des boucles** : Prévention des réponses automatiques en chaîne
- **Délais configurables** : Contrôle du timing des réponses

### 📅 Calendrier intégré
- **Extraction de rendez-vous** : Détection automatique des demandes de RDV
- **Gestion des conflits** : Vérification des créneaux disponibles
- **Confirmation automatique** : Réponses aux demandes de planning
- **Vue calendrier** : Interface moderne pour gérer les événements

### 🎨 Interface moderne
- **Design noir et blanc** : Interface élégante et professionnelle
- **UX/UI optimisée** : Navigation intuitive et efficace
- **Responsive** : Adaptation à toutes les tailles d'écran
- **Notifications** : Alertes discrètes dans la barre système

## 🔧 Installation

### Prérequis
- Python 3.8 ou supérieur
- Compte Gmail avec API activée
- Identifiants OAuth2 Google

### 1. Cloner le projet
```bash
git clone https://github.com/votre-nom/dynovate-mail-assistant.git
cd dynovate-mail-assistant
```

### 2. Environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Modèles spaCy
```bash
python -m spacy download fr_core_news_sm
python -m spacy download en_core_web_sm
```

### 5. Configuration Google API

#### Créer un projet Google Cloud
1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un existant
3. Activez l'API Gmail

#### Configurer OAuth2
1. Allez dans "Identifiants" → "Créer des identifiants" → "ID client OAuth 2.0"
2. Type d'application : "Application de bureau"
3. Téléchargez le fichier JSON
4. Renommez-le en `client_secret.json`
5. Placez-le à la racine du projet

#### Variables d'environnement
Créez un fichier `.env` :
```env
GOOGLE_CLIENT_SECRET_FILE=client_secret.json
OPENAI_API_KEY=your_openai_key_here  # Optionnel
```

## 🚦 Utilisation

### Démarrage
```bash
python app/main.py
```

### Interface en ligne de commande
```bash
python app/cli_main.py
```

### Premier démarrage
1. L'application ouvrira votre navigateur pour l'authentification Google
2. Accordez les permissions demandées
3. L'application se lance automatiquement

## 📱 Guide d'utilisation

### Navigation principale
- **📧 Boîte de réception** : Vue des emails entrants
- **📤 Envoyés** : Emails envoyés
- **⭐ Importants** : Messages marqués comme importants
- **🗓️ Calendrier** : Gestion des rendez-vous
- **📊 Statistiques** : Métriques et analyses
- **⚙️ Paramètres** : Configuration de l'application

### Filtres par catégorie
- **📄 CV/Candidatures** : Emails de recrutement
- **🤝 Rendez-vous** : Demandes de meetings
- **🛡️ Spam** : Messages indésirables
- **🧾 Factures** : Documents financiers
- **🔧 Support** : Demandes d'assistance
- **📰 Newsletters** : Informations périodiques

### Fonctionnalités avancées

#### Réponses automatiques
1. Activez dans **Paramètres** → **Réponse automatique**
2. Configurez les types d'emails à traiter
3. Personnalisez les templates de réponses
4. Définissez les délais d'envoi

#### Calendrier
1. Les RDV sont extraits automatiquement des emails
2. Confirmez ou modifiez dans l'onglet **Calendrier**
3. Gérez les conflits d'horaires
4. Synchronisez avec votre agenda

## ⚙️ Configuration

### Paramètres généraux
```json
{
    "app": {
        "name": "Dynovate Mail Assistant IA",
        "auto_refresh": true
    },
    "user": {
        "name": "Votre nom",
        "signature": "Votre signature"
    }
}
```

### Paramètres IA
```json
{
    "ai": {
        "enable_classification": true,
        "enable_spam_detection": true,
        "enable_sentiment_analysis": true,
        "enable_meeting_extraction": true,
        "response_model": "gpt-3.5-turbo"
    }
}
```

### Réponse automatique
```json
{
    "auto_respond": {
        "enabled": true,
        "delay_minutes": 5,
        "respond_to_cv": true,
        "respond_to_rdv": true,
        "respond_to_support": true,
        "avoid_loops": true
    }
}
```

## 🔧 Architecture technique

### Structure du projet
```
dynovate-mail-assistant/
├── app/
│   ├── main.py                 # Point d'entrée principal
│   ├── gmail_client.py         # Client Gmail API
│   ├── ai_processor.py         # Processeur IA principal
│   ├── calendar_manager.py     # Gestionnaire calendrier
│   ├── auto_responder.py       # Réponses automatiques
│   ├── models/
│   │   ├── email_model.py      # Modèle email
│   │   ├── calendar_model.py   # Modèle calendrier
│   │   └── ai_models.py        # Modèles IA
│   ├── ui/
│   │   ├── main_window.py      # Interface principale
│   │   ├── email_list_view.py  # Vue liste emails
│   │   ├── email_detail_view.py # Vue détail email
│   │   ├── calendar_view.py    # Vue calendrier
│   │   ├── compose_view.py     # Composition email
│   │   └── settings_view.py    # Paramètres
│   └── utils/
│       ├── auth.py             # Authentification
│       ├── config.py           # Configuration
│       ├── logger.py           # Logging
│       └── ai_utils.py         # Utilitaires IA
├── tests/                      # Tests unitaires
├── requirements.txt            # Dépendances
└── README.md                  # Documentation
```

### Technologies utilisées
- **Python 3.8+** : Langage principal
- **PyQt6** : Interface utilisateur
- **Gmail API** : Accès aux emails
- **Transformers** : Modèles IA
- **spaCy** : Traitement du langage naturel
- **SQLite** : Base de données locale
- **OpenAI API** : Génération de réponses (optionnel)

## 🧪 Tests

### Lancer les tests
```bash
python -m pytest tests/
```

### Tests de couverture
```bash
python -m pytest tests/ --cov=app
```

### Tests spécifiques
```bash
# Test du client Gmail
python -m pytest tests/test_gmail_client.py

# Test du processeur IA
python -m pytest tests/test_ai_processor.py

# Test du gestionnaire de calendrier
python -m pytest tests/test_calendar_manager.py
```

## 🚀 Déploiement

### Version portable
```bash
# Créer un exécutable
pip install pyinstaller
pyinstaller --onefile --windowed app/main.py
```

### Installation système
```bash
# Installer en mode développement
pip install -e .
```

## 📊 Performances

### Optimisations
- **Threading** : Traitement asynchrone des emails
- **Cache** : Mise en cache des analyses IA
- **Indexation** : Base de données optimisée
- **Pagination** : Chargement par lots

### Métriques
- **Vitesse de classification** : < 500ms par email
- **Mémoire** : < 200MB en usage normal
- **Latence de réponse** : < 2s pour les réponses automatiques

## 🔒 Sécurité

### Authentification
- **OAuth2** : Authentification sécurisée Google
- **Tokens** : Gestion automatique des tokens
- **Permissions** : Accès minimal nécessaire

### Données
- **Stockage local** : Aucune donnée n'est envoyée à des serveurs externes
- **Chiffrement** : Tokens stockés de manière sécurisée
- **Logs** : Pas de stockage des contenus d'emails

## 🛠️ Développement

### Environnement de développement
```bash
# Mode développement
pip install -e .

# Tests automatiques
python -m pytest tests/ --watch

# Linting
flake8 app/
black app/
```

### Contribuer
1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 🐛 Dépannage

### Problèmes courants

#### Erreur d'authentification
```
Erreur : Impossible de s'authentifier
Solution : Vérifiez client_secret.json et les permissions API
```

#### Modèles IA manquants
```
Erreur : Modèle spaCy non trouvé
Solution : python -m spacy download fr_core_news_sm
```

#### Permissions insuffisantes
```
Erreur : Accès refusé à Gmail
Solution : Revérifiez les scopes dans auth.py
```

### Logs de débogage
```bash
# Activer le mode verbose
python app/main.py --verbose

# Consulter les logs
tail -f logs/gmail_assistant_*.log
```

## 📞 Support

### Documentation
- **Wiki** : [Documentation complète](https://github.com/votre-nom/dynovate-mail-assistant/wiki)
- **API** : [Référence API](https://docs.dynovate.com/api)

### Contact
- **Email** : support@dynovate.com
- **Discord** : [Serveur communautaire](https://discord.gg/dynovate)
- **Issues** : [GitHub Issues](https://github.com/votre-nom/dynovate-mail-assistant/issues)

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🎯 Roadmap

### Version 1.1
- [ ] Intégration Outlook
- [ ] Synchronisation cloud
- [ ] Thèmes personnalisés
- [ ] Export des données

### Version 1.2
- [ ] Plugin système
- [ ] API REST
- [ ] Intégrations tierces
- [ ] Analytics avancées

### Version 2.0
- [ ] Version web
- [ ] Collaboration équipe
- [ ] IA conversationnelle
- [ ] Automatisation avancée

---

**Développé avec ❤️ par l'équipe Dynovate**

*Pour un avenir où l'IA simplifie votre gestion d'emails.*






