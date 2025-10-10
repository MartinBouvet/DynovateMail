#!/usr/bin/env python3
"""
Gestionnaire de configuration simple.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class ConfigManager(QObject):
    """Gestionnaire de configuration simple."""
    
    config_changed = pyqtSignal(dict)
    
    def __init__(self, config_file: str = "config/settings.json"):
        super().__init__()
        self.config_file = Path(config_file)
        self.config = self._load_default_config()
        
        # Créer le dossier de config si nécessaire
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Charger la config existante
        self._load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Charge la configuration par défaut."""
        return {
            'app': {
                'name': 'Dynovate Mail Assistant IA',
                'version': '2.0',
                'auto_refresh': True,
                'font_size': 12
            },
            'ai': {
                'auto_classify': True,
                'confidence_threshold': 0.75,
                'auto_respond': False,
                'response_delay': 5,
                'ai_model': 'Modèle local (rapide)',
                'enable_learning': True
            },
            'email': {
                'auto_refresh': True,
                'refresh_interval': 5,
                'max_emails': 100,
                'auto_mark_read': False,
                'default_signature': ''
            },
            'appearance': {
                'theme': 'Clair',
                'font_size': 12,
                'enable_animations': True,
                'enable_notifications': True,
                'enable_sounds': False
            }
        }
    
    def _load_config(self):
        """Charge la configuration depuis le fichier."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                
                # Fusionner avec la config par défaut
                self._merge_config(self.config, saved_config)
                logger.info("Configuration chargée")
        
        except Exception as e:
            logger.error(f"Erreur chargement configuration: {e}")
    
    def _merge_config(self, default: Dict[str, Any], saved: Dict[str, Any]):
        """Fusionne la configuration sauvegardée avec celle par défaut."""
        for key, value in saved.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
    
    def get_config(self) -> Dict[str, Any]:
        """Retourne la configuration actuelle."""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]):
        """Met à jour la configuration."""
        self._merge_config(self.config, updates)
        self._save_config()
        self.config_changed.emit(self.config)
    
    def _save_config(self):
        """Sauvegarde la configuration."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("Configuration sauvegardée")
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")

# Instance globale
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Retourne l'instance globale du gestionnaire de configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager