#!/usr/bin/env python3
"""
Gestionnaire Ollama - VERSION FINALE
"""
import logging
import subprocess
import time
import os
import signal
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

class OllamaManager:
    """Gère le serveur Ollama."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "nchapman/ministral-8b-instruct-2410:8b"):
        self.base_url = base_url
        self.model_name = model_name
        self.process = None
        self.was_already_running = False
    
    def is_running(self) -> bool:
        """Vérifie si Ollama tourne."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def ensure_running(self) -> bool:
        """S'assure qu'Ollama tourne."""
        logger.info("🚀 Démarrage du serveur Ollama...")
        
        # Déjà en cours ?
        if self.is_running():
            logger.info("✅ Ollama est déjà en cours d'exécution")
            self.was_already_running = True
            
            # Vérifier le modèle
            if self.check_model():
                return True
            else:
                logger.warning("⚠️ Modèle non trouvé")
                return False
        
        # Démarrer Ollama
        logger.info("🔄 Lancement d'Ollama...")
        
        try:
            # Démarrer le serveur
            self.process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Attendre le démarrage (max 10s)
            for i in range(20):
                time.sleep(0.5)
                if self.is_running():
                    logger.info("✅ Ollama démarré avec succès")
                    
                    # Vérifier le modèle
                    if self.check_model():
                        return True
                    else:
                        logger.warning("⚠️ Modèle non trouvé")
                        return False
            
            logger.error("❌ Timeout démarrage Ollama")
            return False
        
        except FileNotFoundError:
            logger.error("❌ Ollama non installé")
            return False
        
        except Exception as e:
            logger.error(f"❌ Erreur démarrage: {e}")
            return False
    
    def check_model(self) -> bool:
        """Vérifie que le modèle est disponible."""
        logger.info(f"🔍 Vérification du modèle {self.model_name}...")
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                for model in models:
                    if model.get('name') == self.model_name:
                        logger.info(f"✅ Modèle {self.model_name} trouvé et prêt")
                        return True
                
                logger.warning(f"⚠️ Modèle {self.model_name} non trouvé")
                logger.info("📥 Téléchargez-le avec: ollama pull nchapman/ministral-8b-instruct-2410:8b")
                return False
            
            return False
        
        except Exception as e:
            logger.error(f"❌ Erreur vérification modèle: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Retourne le statut d'Ollama."""
        status = {
            'running': self.is_running(),
            'base_url': self.base_url,
            'model_name': self.model_name,
            'available_models': []
        }
        
        if status['running']:
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    status['available_models'] = [m['name'] for m in data.get('models', [])]
            except:
                pass
        
        return status
    
    def list_models(self) -> List[str]:
        """Liste les modèles disponibles."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                data = response.json()
                return [m['name'] for m in data.get('models', [])]
        except:
            pass
        
        return []
    
    def pull_model(self, model_name: str = None) -> bool:
        """Télécharge un modèle."""
        if model_name is None:
            model_name = self.model_name
        
        logger.info(f"📥 Téléchargement du modèle {model_name}...")
        
        try:
            subprocess.run(
                ["ollama", "pull", model_name],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info(f"✅ Modèle {model_name} téléchargé")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur téléchargement: {e}")
            return False
        
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return False
    
    def stop(self):
        """Arrête Ollama si on l'a démarré."""
        if self.process and not self.was_already_running:
            logger.info("🛑 Arrêt d'Ollama...")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
                logger.info("✅ Ollama arrêté")
            except:
                logger.warning("⚠️ Impossible d'arrêter Ollama proprement")
        else:
            logger.info("ℹ️ Ollama était déjà en cours, on ne l'arrête pas")
    
    def cleanup(self):
        """Nettoyage à la fermeture."""
        self.stop()
    
    def __del__(self):
        """Destructeur."""
        self.cleanup()