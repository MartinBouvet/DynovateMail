#!/usr/bin/env python3
"""
Point d'entrée principal pour Dynovate Mail Assistant IA.
Version compatible avec l'architecture existante
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

import logging
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont

# Imports compatibles avec l'architecture existante
from ui.main_window import ModernMainWindow
from utils.auth import authenticate_gmail
from utils.logger import setup_logger
from utils.config import get_config_manager
from gmail_client import GmailClient
from calendar_manager import CalendarManager
from auto_responder import AutoResponder

# Import de l'IA avec fallback
try:
    from ai_processor import AdvancedAIProcessor as AIProcessor
    AI_MODE = "advanced"
except ImportError:
    try:
        from ai_processor import AIProcessor
        AI_MODE = "standard"
    except ImportError:
        # Fallback vers une version très simple
        class AIProcessor:
            def __init__(self, config=None):
                self.config = config or {}
                
            def extract_key_information(self, email):
                return {
                    'category': 'general',
                    'priority': 1,
                    'should_auto_respond': False,
                    'sentiment': 'neutral',
                    'confidence': 0.5
                }
            
            def classify_email(self, email):
                return 'general'
            
            def should_auto_respond(self, email):
                return False
        
        AI_MODE = "fallback"

# Configurer le logging
logger = setup_logger()

def create_splash_screen():
    """Crée un écran de démarrage moderne."""
    pixmap = QPixmap(400, 200)
    pixmap.fill(QColor('#000000'))
    
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
        
        # Créer l'application Qt
        app = QApplication(sys.argv)
        app.setApplicationName("Dynovate Mail Assistant IA")
        app.setApplicationVersion("2.0")
        
        # Écran de démarrage
        splash = create_splash_screen()
        splash.show()
        app.processEvents()
        
        def update_splash(message):
            splash.showMessage(
                f"{message}...", 
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                QColor('#ffffff')
            )
            app.processEvents()
        
        # Configuration
        update_splash("Chargement de la configuration")
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        logger.info(f"Mode IA: {AI_MODE}")
        
        # Authentification Gmail
        update_splash("Authentification Gmail")
        try:
            credentials = authenticate_gmail()
            if not credentials:
                splash.close()
                QMessageBox.critical(None, "Erreur", "Échec de l'authentification Gmail.")
                sys.exit(1)
        except Exception as e:
            splash.close()
            QMessageBox.critical(None, "Erreur d'authentification", f"Erreur: {str(e)}")
            sys.exit(1)
        
        # Initialisation des composants
        update_splash("Initialisation du client Gmail")
        gmail_client = GmailClient(credentials)
        
        update_splash("Initialisation de l'IA")
        ai_processor = AIProcessor(config)
        
        update_splash("Initialisation du calendrier")
        calendar_manager = CalendarManager()
        
        update_splash("Initialisation du répondeur automatique")
        auto_responder = AutoResponder(gmail_client, ai_processor, calendar_manager)
        
        update_splash("Chargement de l'interface")
        
        # Créer la fenêtre principale
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
        logger.info(f"Dynovate Mail Assistant IA démarré avec succès (Mode: {AI_MODE})")
        
        # Notification de démarrage
        auto_respond_enabled = config.get('auto_respond', {}).get('enabled', False)
        if hasattr(window, 'tray_icon') and window.tray_icon and window.tray_icon.isVisible():
            status_msg = f"Mode IA: {AI_MODE} - Réponse auto: {'ON' if auto_respond_enabled else 'OFF'}"
            window.show_notification(
                "Dynovate Mail Assistant IA",
                f"Application démarrée!\n{status_msg}"
            )
        
        # Log de l'état de configuration
        logger.info(f"Configuration au démarrage:")
        logger.info(f"- Mode IA: {AI_MODE}")
        logger.info(f"- Réponse automatique: {'activée' if auto_respond_enabled else 'désactivée'}")
        
        # Démarrer la boucle d'événements
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Erreur fatale lors du démarrage: {e}")
        if 'app' in locals():
            QMessageBox.critical(None, "Erreur fatale", f"Impossible de démarrer l'application:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()