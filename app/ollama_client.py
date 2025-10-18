#!/usr/bin/env python3
"""
Client Ollama pour génération de texte.
"""
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client pour interagir avec Ollama."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nchapman/ministral-8b-instruct-2410:8b"):
        """
        Initialise le client Ollama.
        
        Args:
            base_url: URL de base du serveur Ollama
            model: Nom du modèle à utiliser
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
        
        # Tester la connexion
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Ollama connecté sur {self.base_url}")
            else:
                logger.warning(f"⚠️ Ollama répond mais avec code {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Impossible de se connecter à Ollama: {e}")
    
    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Génère du texte avec Ollama.
        
        Args:
            prompt: Le prompt à envoyer
            max_tokens: Nombre maximum de tokens
            temperature: Température de génération (0-1)
            
        Returns:
            Le texte généré
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                logger.info(f"✅ Réponse générée ({len(generated_text)} caractères)")
                return generated_text
            else:
                logger.error(f"❌ Erreur Ollama: {response.status_code}")
                return ""
        
        except requests.exceptions.Timeout:
            logger.error("⏱️ Timeout Ollama")
            return ""
        
        except Exception as e:
            logger.error(f"❌ Erreur génération: {e}")
            return ""
    
    def chat(self, messages: list, max_tokens: int = 500) -> str:
        """
        Conversation avec Ollama.
        
        Args:
            messages: Liste de messages [{"role": "user", "content": "..."}]
            max_tokens: Nombre maximum de tokens
            
        Returns:
            La réponse générée
        """
        try:
            # Construire le prompt depuis les messages
            prompt = ""
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                if role == 'system':
                    prompt += f"[SYSTEM] {content}\n\n"
                elif role == 'user':
                    prompt += f"[USER] {content}\n\n"
                elif role == 'assistant':
                    prompt += f"[ASSISTANT] {content}\n\n"
            
            prompt += "[ASSISTANT] "
            
            return self.generate(prompt, max_tokens=max_tokens)
        
        except Exception as e:
            logger.error(f"❌ Erreur chat: {e}")
            return ""
    
    def is_available(self) -> bool:
        """Vérifie si Ollama est disponible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False