#!/usr/bin/env python3
"""
Point d'entrée principal pour l'application Gmail Assistant avec IA.
"""
import sys
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

from ui.app_window import MainWindow
from utils.auth import authenticate_gmail
from utils.logger import setup_logger
from utils.config import load_config
from gmail_client import GmailClient

# Configurer le logging
logger = setup_logger()

def main():
    """Fonction principale pour démarrer l'application."""
    try:
        # Charger les variables d'environnement
        load_dotenv()
        
        # Charger la configuration
        config = load_config()
        
        # S'authentifier auprès de Gmail
        credentials = authenticate_gmail()
        
        if not credentials:
            logger.error("Échec de l'authentification Gmail.")
            sys.exit(1)
        
        # Initialiser le client Gmail
        gmail_client = GmailClient(credentials)
        
        # Initialiser l'interface utilisateur
        app = QApplication(sys.argv)
        window = MainWindow(gmail_client, config)
        window.show()
        
        # Exécuter l'application
        sys.exit(app.exec())
    
    except Exception as e:
        logger.exception(f"Erreur lors du démarrage de l'application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()