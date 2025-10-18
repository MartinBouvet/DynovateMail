#!/usr/bin/env python3
"""
Dynovate Mail - Point d'entrée principal
VERSION FINALE OPTIMISÉE
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration du logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"gmail_assistant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def cleanup_ollama():
    """Nettoyage Ollama à la sortie."""
    try:
        from ollama_manager import OllamaManager
        manager = OllamaManager()
        manager.cleanup()
    except:
        pass

def main():
    """Fonction principale."""
    try:
        # === ÉTAPE 1: OLLAMA ===
        print("\n" + "=" * 60)
        print("🤖 ÉTAPE 1/4: Démarrage du serveur Ollama...")
        print("=" * 60)
        
        from ollama_manager import OllamaManager
        ollama_manager = OllamaManager()
        
        if not ollama_manager.ensure_running():
            logger.warning("⚠️ Ollama non disponible")
            print("\n⚠️ Ollama n'est pas disponible.")
            print("   L'application fonctionnera sans IA.")
            print("   Pour activer l'IA:")
            print("   1. Installez Ollama (https://ollama.ai)")
            print("   2. Téléchargez le modèle: ollama pull nchapman/ministral-8b-instruct-2410:8b")
            
            response = input("\n⚠️ Continuer sans IA ? (o/N): ")
            if response.lower() != 'o':
                sys.exit(1)
        else:
            print("✅ Ollama prêt!")
            status = ollama_manager.get_status()
            print(f"   📍 URL: {status['base_url']}")
            print(f"   🤖 Modèle: {status['model_name']}")
            if status.get('available_models'):
                print(f"   📚 Modèles: {', '.join(status['available_models'][:3])}")
        
        # === ÉTAPE 2: INTERFACE QT ===
        print("\n" + "=" * 60)
        print("🖥️  ÉTAPE 2/4: Initialisation de l'interface...")
        print("=" * 60)
        
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        
        app = QApplication(sys.argv)
        app.setApplicationName("Dynovate Mail")
        app.setApplicationVersion("4.0 - Final Edition")
        app.setOrganizationName("Dynovate")
        app.setStyle('Fusion')
        
        # Font par défaut
        font = QFont("Arial", 11)
        app.setFont(font)
        
        # Style global
        app.setStyleSheet("""
            * {
                font-family: Arial, sans-serif;
            }
        """)
        
        # Gérer fermeture
        app.aboutToQuit.connect(cleanup_ollama)
        
        print("✅ Interface initialisée!")
        
        # === ÉTAPE 3: GMAIL ===
        print("\n" + "=" * 60)
        print("📧 ÉTAPE 3/4: Connexion à Gmail...")
        print("=" * 60)
        
        # Vérifier credentials
        credentials_file = "client_secret.json"
        if not os.path.exists(credentials_file):
            logger.error("❌ Fichier client_secret.json introuvable")
            print("❌ ERREUR: Fichier client_secret.json introuvable")
            print("\n📋 Pour configurer Gmail:")
            print("   1. Allez sur https://console.cloud.google.com")
            print("   2. Créez un projet et activez l'API Gmail")
            print("   3. Créez des identifiants OAuth 2.0")
            print("   4. Téléchargez le fichier JSON")
            print("   5. Renommez-le en 'client_secret.json'")
            print("   6. Placez-le à la racine du projet")
            
            QMessageBox.critical(
                None,
                "Erreur configuration",
                "Fichier client_secret.json introuvable.\n\n"
                "Consultez la documentation pour configurer Gmail."
            )
            
            cleanup_ollama()
            sys.exit(1)
        
        from gmail_client import GmailClient
        gmail_client = GmailClient(credentials_file=credentials_file, mock_mode=False)
        
        if not gmail_client.authenticated:
            logger.error("❌ Authentification Gmail échouée")
            print("❌ ERREUR: Impossible de s'authentifier à Gmail")
            print("🔑 Vérifiez vos credentials et autorisations")
            
            QMessageBox.critical(
                None,
                "Erreur authentification",
                "Impossible de se connecter à Gmail.\n\n"
                "Vérifiez:\n"
                "- Le fichier client_secret.json est correct\n"
                "- L'API Gmail est activée\n"
                "- Les autorisations sont accordées"
            )
            
            cleanup_ollama()
            sys.exit(1)
        
        print("✅ Gmail authentifié!")
        
        # === ÉTAPE 4: SERVICES IA ===
        print("\n" + "=" * 60)
        print("🧠 ÉTAPE 4/4: Chargement des services IA...")
        print("=" * 60)

        # Imports
        from app.ollama_client import OllamaClient
        from ai_processor import AIProcessor
        from calendar_manager import CalendarManager
        from auto_responder import AutoResponder
        from ui.main_window import MainWindow
        
        # Initialiser le client Ollama
        ollama_client = OllamaClient(
            base_url="http://localhost:11434",
            model="nchapman/ministral-8b-instruct-2410:8b"
        )
        
        # Initialiser AIProcessor avec le client
        ai_processor = AIProcessor(ollama_client=ollama_client)
        
        # Initialiser les autres services
        calendar_manager = CalendarManager()
        auto_responder = AutoResponder(
            gmail_client=gmail_client,
            ai_processor=ai_processor
        )
        
        print("✅ Services IA chargés!")
        
        # === LANCEMENT ===
        print("\n" + "=" * 60)
        print("🚀 DYNOVATE MAIL 4.0 - PRÊT!")
        print("=" * 60)
        print("✨ Propulsé par Ollama + Ministral-8B")
        print("📧 Gmail connecté")
        print("🤖 Assistant IA actif")
        print("💡 Fermez l'application pour arrêter Ollama automatiquement")
        print("=" * 60 + "\n")
        
        main_window = MainWindow(
            gmail_client=gmail_client,
            ai_processor=ai_processor,
            calendar_manager=calendar_manager,
            auto_responder=auto_responder
        )
        
        main_window.show()
        
        logger.info("✅ Dynovate Mail lancé avec succès!")
        
        # Lancer
        exit_code = app.exec()
        
        # Nettoyage
        logger.info("👋 Fermeture de l'application...")
        cleanup_ollama()
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("⚠️ Interruption clavier")
        cleanup_ollama()
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"❌ Erreur fatale: {e}")
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        cleanup_ollama()
        sys.exit(1)

if __name__ == "__main__":
    main()