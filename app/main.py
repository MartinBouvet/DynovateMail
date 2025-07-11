#!/usr/bin/env python3
"""
Point d'entrée principal pour Dynovate Mail Assistant IA.
Solution complète de gestion d'emails avec IA et configuration réactive.
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont

from ui.main_window import ModernMainWindow
from utils.auth import authenticate_gmail
from utils.logger import setup_logger
from utils.config import get_config_manager
from gmail_client import GmailClient
from ai_processor import AIProcessor
from calendar_manager import CalendarManager
from auto_responder import AutoResponder

# Configurer le logging
logger = setup_logger()

def create_splash_screen():
    """Crée un écran de démarrage moderne."""
    # Créer une image de splash simple
    pixmap = QPixmap(400, 200)
    pixmap.fill(QColor('#000000'))
    
    # Dessiner le texte
    painter = QPainter(pixmap)
    painter.setPen(QColor('#ffffff'))
    painter.setFont(QFont('Arial', 24, QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Dynovate Mail\nAssistant IA")
    painter.end()
    
    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
    return splash

def main():
    """Fonction principale pour démarrer l'application."""
    try:
        # Charger les variables d'environnement
        load_dotenv()
        
        # Initialiser l'application Qt
        app = QApplication(sys.argv)
        app.setApplicationName("Dynovate Mail Assistant IA")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Dynovate")
        
        # Écran de démarrage
        splash = create_splash_screen()
        splash.show()
        app.processEvents()
        
        def update_splash(message):
            splash.showMessage(
                message,
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                QColor('#ffffff')
            )
            app.processEvents()
        
        # Chargement des composants avec gestionnaire de configuration réactif
        update_splash("Chargement de la configuration...")
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        update_splash("Authentification Gmail...")
        credentials = authenticate_gmail()
        
        if not credentials:
            splash.close()
            QMessageBox.critical(
                None,
                "Erreur d'authentification",
                "Impossible de s'authentifier auprès de Gmail.\n"
                "Vérifiez votre fichier client_secret.json et votre connexion internet."
            )
            logger.error("Échec de l'authentification Gmail.")
            sys.exit(1)
        
        update_splash("Initialisation du client Gmail...")
        gmail_client = GmailClient(credentials)
        
        update_splash("Initialisation de l'IA...")
        ai_processor = AIProcessor(config)
        
        update_splash("Initialisation du calendrier...")
        calendar_manager = CalendarManager()
        
        update_splash("Initialisation du répondeur automatique...")
        # Le répondeur automatique utilise maintenant le gestionnaire de configuration directement
        auto_responder = AutoResponder(gmail_client, ai_processor, calendar_manager)
        
        update_splash("Chargement de l'interface...")
        
        # Créer la fenêtre principale avec configuration réactive
        window = ModernMainWindow(
            gmail_client,
            ai_processor,
            calendar_manager,
            auto_responder
        )
        
        # Fermer le splash et afficher la fenêtre
        splash.close()
        window.show()
        
        # Message de bienvenue
        logger.info("Dynovate Mail Assistant IA démarré avec succès")
        
        # Notification de démarrage avec statut de configuration
        auto_respond_enabled = config.get('auto_respond', {}).get('enabled', False)
        if hasattr(window, 'tray_icon') and window.tray_icon and window.tray_icon.isVisible():
            status_msg = "Réponse automatique activée" if auto_respond_enabled else "Réponse automatique désactivée"
            window.show_notification(
                "Dynovate Mail Assistant IA",
                f"Application démarrée avec succès!\n{status_msg}"
            )
        
        # Log du statut de configuration au démarrage
        logger.info(f"Configuration au démarrage:")
        logger.info(f"- Réponse automatique: {'activée' if auto_respond_enabled else 'désactivée'}")
        logger.info(f"- Rafraîchissement auto: {'activé' if config.get('app', {}).get('auto_refresh', True) else 'désactivé'}")
        logger.info(f"- Classification IA: {'activée' if config.get('ai', {}).get('enable_classification', True) else 'désactivée'}")
        logger.info(f"- Détection spam: {'activée' if config.get('ai', {}).get('enable_spam_detection', True) else 'désactivée'}")
        logger.info(f"- Analyse sentiment: {'activée' if config.get('ai', {}).get('enable_sentiment_analysis', True) else 'désactivée'}")
        logger.info(f"- Extraction RDV: {'activée' if config.get('ai', {}).get('enable_meeting_extraction', True) else 'désactivée'}")
        
        # Log des paramètres de réponse automatique
        auto_config = config.get('auto_respond', {})
        if auto_respond_enabled:
            logger.info(f"Paramètres de réponse automatique:")
            logger.info(f"- Délai: {auto_config.get('delay_minutes', 5)} minutes")
            logger.info(f"- Répondre aux CV: {'oui' if auto_config.get('respond_to_cv', True) else 'non'}")
            logger.info(f"- Répondre aux RDV: {'oui' if auto_config.get('respond_to_rdv', True) else 'non'}")
            logger.info(f"- Répondre au support: {'oui' if auto_config.get('respond_to_support', True) else 'non'}")
            logger.info(f"- Répondre aux partenariats: {'oui' if auto_config.get('respond_to_partenariat', True) else 'non'}")
            logger.info(f"- Éviter les boucles: {'oui' if auto_config.get('avoid_loops', True) else 'non'}")
        
        # Log des paramètres utilisateur
        user_config = config.get('user', {})
        user_name = user_config.get('name', '')
        if user_name:
            logger.info(f"Utilisateur configuré: {user_name}")
        else:
            logger.warning("Nom d'utilisateur non configuré - veuillez le définir dans les paramètres")
        
        # Vérifier la signature
        signature = user_config.get('signature', '')
        if signature:
            logger.info("Signature utilisateur configurée")
        else:
            logger.info("Aucune signature configurée")
        
        # Log des paramètres d'interface
        ui_config = config.get('ui', {})
        logger.info(f"Interface:")
        logger.info(f"- Thème: {ui_config.get('theme', 'light')}")
        logger.info(f"- Taille police: {ui_config.get('font_size', 12)}pt")
        logger.info(f"- Notifications: {'activées' if ui_config.get('notifications', True) else 'désactivées'}")
        logger.info(f"- Minimiser en barre système: {'oui' if ui_config.get('minimize_to_tray', True) else 'non'}")
        
        # Afficher un message de démarrage dans la console
        print("\n" + "="*60)
        print("🚀 DYNOVATE MAIL ASSISTANT IA - DÉMARRÉ AVEC SUCCÈS")
        print("="*60)
        print(f"📧 Client Gmail: Connecté")
        print(f"🤖 IA locale: Initialisée")
        print(f"📅 Calendrier: Disponible")
        print(f"⚙️  Réponse auto: {'✅ Activée' if auto_respond_enabled else '❌ Désactivée'}")
        print(f"🔄 Refresh auto: {'✅ Activé' if config.get('app', {}).get('auto_refresh', True) else '❌ Désactivé'}")
        print("="*60)
        print("💡 Conseil: Allez dans Paramètres pour configurer votre nom et signature")
        print("🎯 Pour activer la réponse automatique: Paramètres → Réponse automatique")
        print("="*60)
        
        # Exécuter l'application
        exit_code = app.exec()
        
        # Nettoyage avant fermeture
        logger.info("Fermeture de l'application")
        logger.info("Nettoyage des ressources...")
        
        # Sauvegarder la configuration finale
        try:
            config_manager.save_config()
            logger.info("Configuration finale sauvegardée")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde finale: {e}")
        
        # Log des statistiques finales si disponible
        if hasattr(auto_responder, 'get_response_stats'):
            final_stats = auto_responder.get_response_stats()
            logger.info(f"Statistiques finales des réponses automatiques:")
            logger.info(f"- Total réponses envoyées: {final_stats.get('total_responses', 0)}")
            logger.info(f"- Réponses récentes: {final_stats.get('recent_responses', 0)}")
        
        logger.info("Application fermée proprement")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("Interruption utilisateur (Ctrl+C)")
        print("\n🛑 Arrêt demandé par l'utilisateur")
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"Erreur critique lors du démarrage: {e}")
        
        # Afficher l'erreur à l'utilisateur
        if 'app' in locals():
            QMessageBox.critical(
                None,
                "Erreur critique",
                f"Une erreur critique s'est produite:\n\n{str(e)}\n\n"
                "Consultez les logs pour plus de détails.\n\n"
                "Solutions possibles:\n"
                "- Vérifiez votre connexion internet\n"
                "- Vérifiez le fichier client_secret.json\n"
                "- Redémarrez l'application\n"
                "- Consultez les logs dans le dossier logs/"
            )
        
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        print("📋 Consultez les logs pour plus de détails")
        print("🔧 Vérifiez votre configuration et redémarrez")
        
        sys.exit(1)

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées."""
    missing_deps = []
    
    try:
        import PyQt6
    except ImportError:
        missing_deps.append("PyQt6")
    
    try:
        import google.auth
    except ImportError:
        missing_deps.append("google-auth")
    
    try:
        import googleapiclient
    except ImportError:
        missing_deps.append("google-api-python-client")
    
    if missing_deps:
        print(f"❌ Dépendances manquantes: {', '.join(missing_deps)}")
        print("🔧 Installez avec: pip install -r requirements.txt")
        return False
    
    return True

def check_config_files():
    """Vérifie que les fichiers de configuration nécessaires existent."""
    required_files = {
        'client_secret.json': 'Fichier de configuration OAuth Google',
        '.env': 'Fichier de variables d\'environnement (optionnel)'
    }
    
    missing_files = []
    
    for file_path, description in required_files.items():
        if not os.path.exists(file_path):
            if file_path == 'client_secret.json':
                missing_files.append(f"{file_path} ({description})")
    
    if missing_files:
        print(f"❌ Fichiers manquants:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n🔧 Instructions:")
        print("   1. Allez sur https://console.cloud.google.com/")
        print("   2. Créez un projet et activez l'API Gmail")
        print("   3. Créez des identifiants OAuth 2.0")
        print("   4. Téléchargez le fichier JSON et renommez-le 'client_secret.json'")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Démarrage de Dynovate Mail Assistant IA...")
    
    # Vérifications préliminaires
    if not check_dependencies():
        sys.exit(1)
    
    if not check_config_files():
        sys.exit(1)
    
    # Démarrer l'application
    main()