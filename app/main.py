#!/usr/bin/env python3
"""
Point d'entrée principal corrigé.
"""
import sys
import logging
from pathlib import Path
import os
from ui.components.ai_suggestion_panel import AISuggestionPanel  # Assurer l'import
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.debug=false"

app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

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
        credentials_file = "client_secret.json"
        if not os.path.exists(credentials_file):
            logger.error(f"Fichier {credentials_file} non trouvé")
            print(f"ERREUR: Le fichier {credentials_file} est requis")
            sys.exit(1)
        
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        
        from gmail_client import GmailClient
        from ai_processor import AIProcessor
        from calendar_manager import CalendarManager
        from auto_responder import AutoResponder
        from pending_response_manager import PendingResponseManager
        from ui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("Dynovate Mail Assistant IA")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("Dynovate")
        app.setStyle('Fusion')
        
        logger.info("Initialisation des services...")
        
        # Services
        gmail_client = GmailClient(credentials_file=credentials_file, mock_mode=False)
        
        if not gmail_client.authenticated:
            logger.error("Impossible de s'authentifier avec Gmail")
            print("ERREUR: Authentification Gmail échouée")
            sys.exit(1)
        
        ai_processor = AIProcessor()
        calendar_manager = CalendarManager()
        pending_manager = PendingResponseManager()
        auto_responder = AutoResponder(ai_processor, pending_manager)
        
        # Interface principale
        main_window = MainWindow(
            gmail_client=gmail_client,
            ai_processor=ai_processor,
            calendar_manager=calendar_manager,
            auto_responder=auto_responder
        )
        
        main_window.show()
        
        logger.info("✅ Application lancée avec succès - Mode PRODUCTION")
        print("✅ Dynovate Mail avec IA fonctionnelle lancé !")
        
        sys.exit(app.exec())
        
    except ImportError as e:
        logger.error(f"Module manquant: {e}")
        print(f"ERREUR: Installez les dépendances - {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        print(f"Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()