#!/usr/bin/env python3
"""
Point d'entrée principal pour Dynovate Mail Assistant IA.
Version corrigée pour éviter les bus errors sur macOS
"""
import sys
import os
from pathlib import Path

# Configuration AVANT tout import pour éviter bus errors
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''  # Fix potential Qt issues

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

import logging
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont
import gc

# Imports compatibles avec l'architecture existante
from utils.auth import authenticate_gmail
from utils.logger import setup_logger
from utils.config import get_config_manager
from gmail_client import GmailClient
from calendar_manager import CalendarManager
from auto_responder import AutoResponder

# Import de l'IA avec fallback SANS configuration torch (sera fait dans ai_processor)
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
    app = None
    try:
        # Charger les variables d'environnement
        load_dotenv()
        
        # Créer l'application Qt avec configuration spéciale pour macOS
        app = QApplication(sys.argv)
        app.setApplicationName("Dynovate Mail Assistant IA")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("Dynovate")
        
        # Configuration Qt pour macOS (PyQt6 compatible)
        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            pass  # Ignoré si l'attribut n'existe pas
        
        # Créer et afficher le splash screen
        splash = create_splash_screen()
        splash.show()
        app.processEvents()
        
        def update_splash(message):
            splash.showMessage(
                message, 
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                QColor('#ffffff')
            )
            app.processEvents()
        
        # Charger la configuration
        update_splash("Chargement de la configuration...")
        config_manager = get_config_manager()
        config = config_manager.get_config()
        logger.info(f"Mode IA: {AI_MODE}")
        
        # Authentification Gmail
        update_splash("Authentification Gmail...")
        try:
            credentials = authenticate_gmail()
            if not credentials:
                splash.close()
                QMessageBox.critical(None, "Erreur d'authentification", 
                                   "Impossible de s'authentifier auprès de Gmail.\n"
                                   "Vérifiez votre fichier client_secret.json.")
                sys.exit(1)
        except Exception as e:
            splash.close()
            QMessageBox.critical(None, "Erreur d'authentification", f"Erreur: {str(e)}")
            sys.exit(1)
        
        # Initialisation des composants
        update_splash("Initialisation du client Gmail...")
        gmail_client = GmailClient(credentials)
        
        update_splash("Initialisation du calendrier...")
        calendar_manager = CalendarManager()
        
        update_splash("Initialisation de l'IA...")
        app.processEvents()
        
        # Initialisation de l'IA avec gestion d'erreurs
        try:
            ai_processor = AIProcessor(config)
            logger.info("IA initialisée avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'IA: {e}")
            # Fallback vers un processeur simple
            class SimpleAIProcessor:
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
            
            ai_processor = SimpleAIProcessor(config)
            logger.warning("Utilisation de l'IA simplifiée en raison d'une erreur")
        
        update_splash("Initialisation du répondeur automatique...")
        auto_responder = AutoResponder(gmail_client, ai_processor, calendar_manager)
        
        # Nettoyer la mémoire avant d'initialiser l'interface
        update_splash("Optimisation mémoire...")
        gc.collect()
        
        update_splash("Chargement de l'interface...")
        app.processEvents()
        
        # IMPORT DE L'INTERFACE SEULEMENT ICI pour éviter les conflits
        from ui.main_window import ModernMainWindow
        
        # Créer la fenêtre principale directement (sans délai)
        try:
            window = ModernMainWindow(
                gmail_client,
                ai_processor,
                calendar_manager,
                auto_responder
            )
            
            splash.close()
            window.show()
            
            # Message de bienvenue
            logger.info(f"Dynovate Mail Assistant IA démarré avec succès (Mode: {AI_MODE})")
            
            # Log de l'état de configuration
            auto_respond_enabled = config.get('auto_respond', {}).get('enabled', False)
            logger.info(f"Configuration au démarrage:")
            logger.info(f"- Mode IA: {AI_MODE}")
            logger.info(f"- Réponse automatique: {'activée' if auto_respond_enabled else 'désactivée'}")
            
        except Exception as e:
            splash.close()
            logger.error(f"Erreur lors de la création de l'interface: {e}")
            QMessageBox.critical(None, "Erreur interface", 
                               f"Erreur lors de la création de l'interface:\n{str(e)}")
            sys.exit(1)
        
        # Démarrer la boucle d'événements
        result = app.exec()
        
        # Nettoyage final
        try:
            gc.collect()
        except:
            pass
        
        sys.exit(result)
        
    except Exception as e:
        logger.error(f"Erreur fatale lors du démarrage: {e}")
        if app:
            QMessageBox.critical(None, "Erreur fatale", f"Impossible de démarrer l'application:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()