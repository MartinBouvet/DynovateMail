#!/usr/bin/env python3
"""
Point d'entrée principal - VERSION AVEC GESTION AUTOMATIQUE OLLAMA
"""
import sys
import logging
from pathlib import Path
import os
import atexit

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

# Gestionnaire Ollama global
ollama_manager = None

def cleanup_ollama():
    """Nettoie Ollama à la fermeture."""
    global ollama_manager
    if ollama_manager:
        logger.info("🧹 Nettoyage: arrêt d'Ollama...")
        ollama_manager.stop()

def main():
    """Fonction principale."""
    global ollama_manager
    
    try:
        credentials_file = "client_secret.json"
        if not os.path.exists(credentials_file):
            logger.error(f"ERREUR: Fichier {credentials_file} non trouvé")
            print(f"❌ ERREUR: Le fichier {credentials_file} est requis")
            print("📥 Téléchargez vos credentials OAuth2 depuis:")
            print("🔗 https://console.cloud.google.com/apis/credentials")
            sys.exit(1)
        
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtCore import Qt
        
        # === ÉTAPE 1: LANCER OLLAMA ===
        print("=" * 60)
        print("🤖 ÉTAPE 1/4: Démarrage du serveur Ollama...")
        print("=" * 60)
        
        from ollama_manager import OllamaManager
        ollama_manager = OllamaManager(model_name="nchapman/ministral-8b-instruct-2410:8b")
        
        # Enregistrer la fonction de nettoyage
        atexit.register(cleanup_ollama)
        
        if not ollama_manager.start():
            print("❌ ERREUR: Impossible de démarrer Ollama")
            print("📝 Vérifiez que:")
            print("   1. Ollama est installé (https://ollama.ai)")
            print("   2. Le modèle est téléchargé: ollama pull nchapman/ministral-8b-instruct-2410:8b")
            
            response = input("\n⚠️ Continuer sans IA ? (o/N): ")
            if response.lower() != 'o':
                sys.exit(1)
        else:
            print("✅ Ollama prêt!")
            status = ollama_manager.get_status()
            print(f"   📍 URL: {status['base_url']}")
            print(f"   🤖 Modèle: {status['model_name']}")
            if status.get('available_models'):
                print(f"   📚 Modèles disponibles: {', '.join(status['available_models'][:3])}")
        
        # === ÉTAPE 2: APPLICATION QT ===
        print("\n" + "=" * 60)
        print("🖥️  ÉTAPE 2/4: Initialisation de l'interface...")
        print("=" * 60)
        
        app = QApplication(sys.argv)
        app.setApplicationName("Dynovate Mail")
        app.setApplicationVersion("4.0 - Ollama Edition")
        app.setOrganizationName("Dynovate")
        app.setStyle('Fusion')
        
        app.setStyleSheet("""
            * {
                font-family: 'SF Pro Display', Arial, sans-serif;
            }
        """)
        
        # Gérer la fermeture de l'application
        app.aboutToQuit.connect(cleanup_ollama)
        
        print("✅ Interface initialisée!")
        
        # === ÉTAPE 3: AUTHENTIFICATION GMAIL ===
        print("\n" + "=" * 60)
        print("📧 ÉTAPE 3/4: Connexion à Gmail...")
        print("=" * 60)
        
        from gmail_client import GmailClient
        gmail_client = GmailClient(credentials_file=credentials_file, mock_mode=False)
        
        if not gmail_client.authenticated:
            logger.error("❌ Authentification Gmail échouée")
            print("❌ ERREUR: Impossible de s'authentifier à Gmail")
            print("🔑 Vérifiez vos credentials et autorisations")
            
            QMessageBox.critical(
                None,
                "Erreur d'authentification",
                "Impossible de se connecter à Gmail.\n\n"
                "Vérifiez votre fichier client_secret.json et vos autorisations."
            )
            
            cleanup_ollama()
            sys.exit(1)
        
        print("✅ Gmail authentifié!")
        
        # === ÉTAPE 4: SERVICES IA ===
        print("\n" + "=" * 60)
        print("🧠 ÉTAPE 4/4: Chargement des services IA...")
        print("=" * 60)
        
        from ai_processor import AIProcessor
        from calendar_manager import CalendarManager
        from auto_responder import AutoResponder
        from ui.main_window import MainWindow
        
        ai_processor = AIProcessor()
        calendar_manager = CalendarManager()
        auto_responder = AutoResponder(ai_processor)
        
        print("✅ Services IA chargés!")
        
        # === LANCEMENT DE L'INTERFACE ===
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
        
        # Lancer l'application
        exit_code = app.exec()
        
        # Nettoyage à la sortie
        logger.info("👋 Fermeture de l'application...")
        cleanup_ollama()
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("⚠️ Interruption clavier détectée")
        cleanup_ollama()
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"❌ Erreur fatale: {e}")
        print(f"\n❌ ERREUR FATALE: {e}")
        cleanup_ollama()
        sys.exit(1)

if __name__ == "__main__":
    main()