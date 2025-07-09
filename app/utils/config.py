"""
Utilitaires pour la gestion de la configuration de l'application.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "app": {
        "name": "Gmail Assistant IA",
        "version": "0.1.0",
        "theme": "light"
    },
    "email": {
        "max_emails_to_load": 50,
        "refresh_interval_minutes": 5,
        "signature": ""
    },
    "ai": {
        "enable_classification": True,
        "enable_spam_detection": True,
        "enable_response_generation": False,
        "response_model": "gpt-3.5-turbo"
    },
    "ui": {
        "font_size": 12,
        "show_preview_pane": True,
        "show_toolbar": True
    }
}

def load_config() -> Dict[str, Any]:
    """
    Charge la configuration depuis le fichier config.json.
    Si le fichier n'existe pas, crée une configuration par défaut.
    
    Returns:
        Dictionnaire de configuration.
    """
    config_path = Path("config.json")
    
    # Si le fichier de configuration n'existe pas, le créer avec les valeurs par défaut
    if not config_path.exists():
        logger.info("Aucun fichier de configuration trouvé. Création d'une configuration par défaut.")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        logger.info("Configuration chargée depuis le fichier.")
        
        # Mettre à jour la configuration avec les valeurs par défaut manquantes
        updated_config = update_missing_config(config, DEFAULT_CONFIG)
        
        # Si la configuration a été mise à jour, sauvegarder les changements
        if updated_config != config:
            logger.info("Mise à jour de la configuration avec les valeurs par défaut manquantes.")
            save_config(updated_config)
        
        return updated_config
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        logger.info("Utilisation de la configuration par défaut.")
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> bool:
    """
    Sauvegarde la configuration dans le fichier config.json.
    
    Args:
        config: Dictionnaire de configuration à sauvegarder.
        
    Returns:
        True si la sauvegarde a réussi, False sinon.
    """
    config_path = Path("config.json")
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        logger.info("Configuration sauvegardée dans le fichier.")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
        return False

def update_missing_config(config: Dict[str, Any], default_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Met à jour la configuration avec les valeurs par défaut manquantes.
    
    Args:
        config: Configuration actuelle.
        default_config: Configuration par défaut.
        
    Returns:
        Configuration mise à jour.
    """
    result = config.copy()
    
    for key, value in default_config.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = update_missing_config(result[key], value)
    
    return result

def get_config_value(config: Dict[str, Any], key_path: str, default_value: Any = None) -> Any:
    """
    Récupère une valeur de configuration à partir d'un chemin de clé.
    
    Args:
        config: Dictionnaire de configuration.
        key_path: Chemin de la clé (ex: "email.signature").
        default_value: Valeur par défaut si la clé n'existe pas.
        
    Returns:
        La valeur de configuration ou la valeur par défaut.
    """
    keys = key_path.split(".")
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default_value
    
    return current