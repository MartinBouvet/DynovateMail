"""
Configuration du système de logging pour l'application.
"""
import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logger():
    """
    Configure et retourne un logger pour l'application.
    
    Returns:
        Le logger configuré.
    """
    # Créer le répertoire de logs s'il n'existe pas
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Nom du fichier de log avec la date
    log_filename = logs_dir / f"gmail_assistant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configurer le logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Formatter pour les logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler pour le fichier
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)  # Niveau plus détaillé pour les fichiers
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging configuré. Fichier de log: {log_filename}")
    
    return logger