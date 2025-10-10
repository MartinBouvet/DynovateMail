#!/usr/bin/env python3
"""
Gestionnaire Ollama - Lance et arrête automatiquement le serveur
VERSION SIMPLIFIÉE sans psutil
"""
import logging
import subprocess
import time
import requests
import os
import signal
import platform
from typing import Optional

logger = logging.getLogger(__name__)

class OllamaManager:
    """Gère le cycle de vie du serveur Ollama."""
    
    def __init__(self, model_name: str = "nchapman/ministral-8b-instruct-2410:8b"):
        """
        Initialise le gestionnaire Ollama.
        
        Args:
            model_name: Nom du modèle à utiliser
        """
        self.model_name = model_name
        self.base_url = "http://localhost:11434"
        self.process: Optional[subprocess.Popen] = None
        self.was_already_running = False
        self.system = platform.system()
        
    def start(self) -> bool:
        """
        Démarre Ollama si nécessaire.
        
        Returns:
            True si Ollama est prêt, False sinon
        """
        logger.info("🚀 Démarrage du serveur Ollama...")
        
        # Vérifier si Ollama est déjà en cours d'exécution
        if self._is_running():
            logger.info("✅ Ollama est déjà en cours d'exécution")
            self.was_already_running = True
            return self._verify_model_loaded()
        
        # Lancer Ollama
        try:
            logger.info("🔄 Lancement du serveur Ollama...")
            
            # Déterminer la commande selon l'OS
            if self.system == 'Windows':
                # Windows
                self.process = subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            elif self.system == 'Darwin':
                # macOS
                self.process = subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            else:
                # Linux
                self.process = subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
            
            # Attendre que le serveur soit prêt (max 30 secondes)
            print("⏳ Attente du démarrage d'Ollama", end="", flush=True)
            for i in range(30):
                time.sleep(1)
                print(".", end="", flush=True)
                if self._is_running():
                    print(f" ✅ Démarré en {i+1}s")
                    logger.info(f"✅ Serveur Ollama démarré après {i+1}s")
                    return self._verify_model_loaded()
            
            print(" ❌ Timeout")
            logger.error("❌ Timeout: Ollama n'a pas démarré en 30s")
            return False
            
        except FileNotFoundError:
            logger.error("❌ Ollama n'est pas installé ou pas dans le PATH")
            print("\n❌ ERREUR: Ollama n'est pas installé")
            print("📥 Installez Ollama depuis: https://ollama.ai")
            print("\n💡 Sur macOS, utilisez: brew install ollama")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur lors du lancement d'Ollama: {e}")
            return False
    
    def _is_running(self) -> bool:
        """
        Vérifie si Ollama est en cours d'exécution.
        
        Returns:
            True si Ollama répond, False sinon
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _verify_model_loaded(self) -> bool:
        """
        Vérifie que le modèle est disponible.
        
        Returns:
            True si le modèle est prêt, False sinon
        """
        try:
            logger.info(f"🔍 Vérification du modèle {self.model_name}...")
            
            # Lister les modèles disponibles
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                # Vérifier si notre modèle est dans la liste
                if self.model_name in model_names:
                    logger.info(f"✅ Modèle {self.model_name} trouvé et prêt")
                    return True
                else:
                    logger.warning(f"⚠️ Modèle {self.model_name} non trouvé")
                    print(f"\n⚠️ Modèle {self.model_name} non trouvé")
                    print(f"📋 Modèles disponibles: {', '.join(model_names) if model_names else 'Aucun'}")
                    print(f"\n💡 Pour installer le modèle, lancez:")
                    print(f"   ollama pull {self.model_name}")
                    return False
            else:
                logger.error(f"❌ Impossible de lister les modèles: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification modèle: {e}")
            return False
    
    def stop(self):
        """Arrête Ollama s'il a été lancé par cette application."""
        if self.was_already_running:
            logger.info("ℹ️ Ollama était déjà en cours, on ne l'arrête pas")
            return
        
        if self.process is None:
            logger.info("ℹ️ Aucun processus Ollama à arrêter")
            return
        
        try:
            logger.info("🛑 Arrêt du serveur Ollama...")
            
            # Arrêt selon l'OS
            if self.system == 'Windows':
                self.process.terminate()
            else:
                # macOS et Linux
                try:
                    if self.system == 'Darwin':
                        # macOS - terminer le groupe de processus
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    else:
                        # Linux
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                except:
                    # Fallback: terminer juste le processus principal
                    self.process.terminate()
            
            # Attendre l'arrêt (max 5 secondes)
            try:
                self.process.wait(timeout=5)
                logger.info("✅ Ollama arrêté proprement")
            except subprocess.TimeoutExpired:
                # Forcer l'arrêt si nécessaire
                self.process.kill()
                logger.warning("⚠️ Ollama arrêté de force")
            
            self.process = None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'arrêt d'Ollama: {e}")
    
    def get_status(self) -> dict:
        """
        Obtient le statut d'Ollama.
        
        Returns:
            Dict avec les infos de statut
        """
        status = {
            "running": self._is_running(),
            "model_name": self.model_name,
            "base_url": self.base_url,
            "was_already_running": self.was_already_running,
            "system": self.system
        }
        
        if status["running"]:
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=2)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    status["available_models"] = [m.get('name', '') for m in models]
            except:
                pass
        
        return status
    
    def __enter__(self):
        """Support du context manager."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager."""
        self.stop()