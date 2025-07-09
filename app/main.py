#!/usr/bin/env python3
"""
Point d'entrée principal pour Dynovate Mail Assistant IA.
Solution complète de gestion d'emails avec IA.
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
from utils.config import load_config
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
        
        # Chargement des composants
        update_splash("Chargement de la configuration...")
        config = load_config()
        
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
        auto_responder = AutoResponder(gmail_client, ai_processor, calendar_manager, config)
        
        update_splash("Chargement de l'interface...")
        
        # Créer la fenêtre principale
        window = ModernMainWindow(
            gmail_client,
            ai_processor,
            calendar_manager,
            auto_responder,
            config
        )
        
        # Fermer le splash et afficher la fenêtre
        splash.close()
        window.show()
        
        # Message de bienvenue
        logger.info("Dynovate Mail Assistant IA démarré avec succès")
        
        # Notification de démarrage
        if window.tray_icon and window.tray_icon.isVisible():
            window.show_notification(
                "Dynovate Mail Assistant IA",
                "Application démarrée avec succès!"
            )
        
        # Exécuter l'application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.exception(f"Erreur critique lors du démarrage: {e}")
        
        # Afficher l'erreur à l'utilisateur
        if 'app' in locals():
            QMessageBox.critical(
                None,
                "Erreur critique",
                f"Une erreur critique s'est produite:\n\n{str(e)}\n\n"
                "Consultez les logs pour plus de détails."
            )
        
        sys.exit(1)

if __name__ == "__main__":
    main()