#!/usr/bin/env python3
"""
Point d'entrée principal de Dynovate Mail Assistant IA.
Application de gestion d'emails avec intelligence artificielle.
"""
import sys
import logging
from pathlib import Path
import os
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.debug=false"
# Ajouter le dossier app au chemin Python
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dynovate_mail.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Fonction principale."""
    try:
        # Imports après configuration du chemin
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QIcon
        
        # Services
        from gmail_client import GmailClient
        from ai_processor import AIProcessor
        from calendar_manager import CalendarManager
        from auto_responder import AutoResponder
        from pending_response_manager import PendingResponseManager
        
        # Interface
        from ui.main_window import MainWindow
        
        # Créer l'application
        app = QApplication(sys.argv)
        app.setApplicationName("Dynovate Mail Assistant IA")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("Dynovate")
        
        # Configuration du style
        app.setStyle('Fusion')  # Style moderne
        
        # Initialiser les services
        logger.info("Initialisation des services...")
        
        # Initialisation sans credentials (mode mock)
        gmail_client = GmailClient(mock_mode=False)
        ai_processor = AIProcessor()
        calendar_manager = CalendarManager()
        pending_manager = PendingResponseManager()
        auto_responder = AutoResponder(ai_processor, pending_manager)
        
        # Créer l'interface principale
        main_window = MainWindow(
            gmail_client=gmail_client,
            ai_processor=ai_processor,
            calendar_manager=calendar_manager,
            auto_responder=auto_responder
        )
        
        # Afficher la fenêtre
        main_window.show()
        
        logger.info("Application démarrée avec succès")
        
        # Lancer la boucle d'événements
        sys.exit(app.exec())
        
    except ImportError as e:
        logger.error(f"Erreur d'import: {e}")
        print(f"Erreur: Module manquant - {e}")
        print("Installez les dépendances manquantes")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        print(f"Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()