"""
Gestionnaire de configuration corrigé avec événements et mise à jour en temps réel.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Callable, List
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "app": {
        "name": "Dynovate Mail Assistant IA",
        "version": "1.0.0",
        "auto_refresh": True,
        "refresh_interval_minutes": 5
    },
    "user": {
        "name": "",
        "signature": ""
    },
    "email": {
        "max_emails_to_load": 50,
        "refresh_interval_minutes": 5
    },
    "ai": {
        "enable_classification": True,
        "enable_spam_detection": True,
        "enable_sentiment_analysis": True,
        "enable_meeting_extraction": True,
        "response_model": "local"
    },
    "auto_respond": {
        "enabled": False,
        "delay_minutes": 5,
        "respond_to_cv": True,
        "respond_to_rdv": True,
        "respond_to_support": True,
        "respond_to_partenariat": True,
        "avoid_loops": True
    },
    "ui": {
        "theme": "light",
        "font_size": 12,
        "show_preview_pane": True,
        "notifications": True,
        "minimize_to_tray": True
    }
}

class ConfigManager(QObject):
    """Gestionnaire de configuration avec signaux Qt pour les mises à jour."""
    
    config_changed = pyqtSignal(dict)  # Signal émis quand la config change
    
    def __init__(self, config_path: str = "config.json"):
        super().__init__()
        self.config_path = Path(config_path)
        self.config = {}
        self.observers = []  # Liste des callbacks pour les changements
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier."""
        if not self.config_path.exists():
            logger.info("Aucun fichier de configuration trouvé. Création d'une configuration par défaut.")
            self.config = DEFAULT_CONFIG.copy()
            self.save_config()
            return self.config
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
            
            # Merge avec la config par défaut pour ajouter les nouvelles clés
            self.config = self._merge_configs(DEFAULT_CONFIG, loaded_config)
            
            logger.info("Configuration chargée depuis le fichier.")
            return self.config
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            self.config = DEFAULT_CONFIG.copy()
            return self.config
    
    def save_config(self) -> bool:
        """Sauvegarde la configuration dans le fichier."""
        try:
            # Créer le répertoire parent si nécessaire
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.info("Configuration sauvegardée dans le fichier.")
            
            # Émettre le signal de changement
            self.config_changed.emit(self.config.copy())
            
            # Notifier les observers
            for callback in self.observers:
                try:
                    callback(self.config)
                except Exception as e:
                    logger.error(f"Erreur lors de la notification d'un observer: {e}")
            
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
    def get(self, key_path: str, default_value: Any = None) -> Any:
        """
        Récupère une valeur de configuration à partir d'un chemin de clé.
        
        Args:
            key_path: Chemin de la clé (ex: "email.signature").
            default_value: Valeur par défaut si la clé n'existe pas.
        """
        keys = key_path.split(".")
        current = self.config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default_value
        
        return current
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Définit une valeur de configuration à partir d'un chemin de clé.
        
        Args:
            key_path: Chemin de la clé (ex: "email.signature").
            value: Valeur à définir.
        """
        try:
            keys = key_path.split(".")
            current = self.config
            
            # Naviguer jusqu'au parent de la clé finale
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Définir la valeur
            current[keys[-1]] = value
            
            # Sauvegarder automatiquement
            return self.save_config()
        
        except Exception as e:
            logger.error(f"Erreur lors de la définition de la configuration: {e}")
            return False
    
    def update_section(self, section: str, values: Dict[str, Any]) -> bool:
        """
        Met à jour une section entière de la configuration.
        
        Args:
            section: Nom de la section (ex: "auto_respond").
            values: Dictionnaire des valeurs à mettre à jour.
        """
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section].update(values)
            return self.save_config()
        
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la section {section}: {e}")
            return False
    
    def add_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """Ajoute un callback qui sera appelé lors des changements de config."""
        self.observers.append(callback)
    
    def remove_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """Supprime un callback des observers."""
        if callback in self.observers:
            self.observers.remove(callback)
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Merge la configuration chargée avec les valeurs par défaut."""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def reset_to_defaults(self) -> bool:
        """Remet la configuration aux valeurs par défaut."""
        self.config = DEFAULT_CONFIG.copy()
        return self.save_config()
    
    def get_config(self) -> Dict[str, Any]:
        """Retourne une copie de la configuration complète."""
        return self.config.copy()

# Instance globale du gestionnaire de configuration
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Retourne l'instance globale du gestionnaire de configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def load_config() -> Dict[str, Any]:
    """Fonction de compatibilité - charge la configuration."""
    return get_config_manager().get_config()

def save_config(config: Dict[str, Any]) -> bool:
    """Fonction de compatibilité - sauvegarde la configuration."""
    manager = get_config_manager()
    manager.config = config
    return manager.save_config()