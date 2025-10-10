#!/usr/bin/env python3
"""
Point d'entrée principal - VERSION FINALE CORRIGÉE
"""
import sys
import logging
from pathlib import Path
import os

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
            logger.error(f"ERREUR: Fichier {credentials_file} non trouvé")
            print(f"❌ ERREUR: Le fichier {credentials_file} est requis")
            print("📥 Téléchargez vos credentials OAuth2 depuis:")
            print("🔗 https://console.cloud.google.com/apis/credentials")
            sys.exit(1)
        
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        
        from gmail_client import GmailClient
        from ai_processor import AIProcessor
        from calendar_manager import CalendarManager
        from auto_responder import AutoResponder
        from ui.main_window import MainWindow
        
        # Application Qt
        app = QApplication(sys.argv)
        app.setApplicationName("Dynovate Mail")
        app.setApplicationVersion("3.0")
        app.setOrganizationName("Dynovate")
        app.setStyle('Fusion')
        
        # Force le thème clair
        app.setStyleSheet("""
            * {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        logger.info("🚀 Démarrage Dynovate Mail...")
        
        # Authentification Gmail
        print("📧 Connexion à Gmail...")
        gmail_client = GmailClient(credentials_file=credentials_file, mock_mode=False)
        
        if not gmail_client.authenticated:
            logger.error("❌ Authentification Gmail échouée")
            print("❌ ERREUR: Impossible de s'authentifier")
            print("🔑 Vérifiez vos credentials et autorisations")
            sys.exit(1)
        
        print("✅ Gmail authentifié!")
        
        # Services
        ai_processor = AIProcessor()
        calendar_manager = CalendarManager()
        auto_responder = AutoResponder(ai_processor)
        
        # Interface
        main_window = MainWindow(
            gmail_client=gmail_client,
            ai_processor=ai_processor,
            calendar_manager=calendar_manager,
            auto_responder=auto_responder
        )
        
        main_window.show()
        
        logger.info("✅ Dynovate Mail lancé avec succès!")
        print("✅ Interface prête!")
        
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        print(f"❌ ERREUR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()