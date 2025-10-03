#!/usr/bin/env python3
"""
Point d'entrée principal CORRIGÉ - VRAIS EMAILS UNIQUEMENT.
"""
import sys
import logging
from pathlib import Path
import os

# Supprimer les warnings Qt inutiles
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
    """Fonction principale - VRAIS EMAILS UNIQUEMENT."""
    try:
        credentials_file = "client_secret.json"
        if not os.path.exists(credentials_file):
            logger.error(f"ERREUR FATALE: Fichier {credentials_file} non trouvé")
            print(f"❌ ERREUR: Le fichier {credentials_file} est OBLIGATOIRE")
            print("📥 Téléchargez vos credentials OAuth2 depuis Google Cloud Console")
            print("🔗 https://console.cloud.google.com/apis/credentials")
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
        
        logger.info("🚀 Initialisation des services...")
        
        # Services - FORCER MODE PRODUCTION
        print("📧 Connexion à Gmail (AUTHENTIFICATION REQUISE)...")
        gmail_client = GmailClient(credentials_file=credentials_file, mock_mode=False)
        
        if not gmail_client.authenticated:
            logger.error("❌ ERREUR FATALE: Impossible de s'authentifier avec Gmail")
            print("❌ ERREUR: Authentification Gmail échouée")
            print("🔑 Vérifiez vos credentials et autorisations")
            sys.exit(1)
        
        print("✅ Gmail authentifié avec succès!")
        
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
        
        logger.info("✅ Application lancée avec succès - MODE PRODUCTION UNIQUEMENT")
        print("✅ Dynovate Mail avec vrais emails lancé!")
        print("📧 AUCUN email de test - UNIQUEMENT vos vrais emails Gmail")
        print("📁 Navigation: Boîte de réception, Envoyés, Archives, Supprimés, Spam")
        print("💾 Sauvegarde de pièces jointes fonctionnelle")
        
        sys.exit(app.exec())
        
    except ImportError as e:
        logger.error(f"Module manquant: {e}")
        print(f"❌ ERREUR: Installez les dépendances - {e}")
        print("📦 Commande: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        print(f"💥 Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()