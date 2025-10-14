#!/usr/bin/env python3
"""
Client Ollama - VERSION COMPLÈTE CORRIGÉE
"""
import logging
import requests
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client pour interagir avec le serveur Ollama.
    
    Permet de générer du texte avec des modèles IA locaux via l'API Ollama.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model: str = "nchapman/ministral-8b-instruct-2410:8b"):
        """
        Initialise le client Ollama.
        
        Args:
            base_url: URL du serveur Ollama
            model: Nom du modèle à utiliser
        """
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        logger.info(f"✅ Ollama connecté sur {base_url}")
    
    def is_available(self) -> bool:
        """
        Vérifie si le serveur Ollama est disponible.
        
        Returns:
            True si Ollama est accessible, False sinon
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=2
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ollama non disponible: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur inattendue: {e}")
            return False
    
    def get_models(self) -> List[str]:
        """
        Récupère la liste des modèles disponibles.
        
        Returns:
            Liste des noms de modèles disponibles
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                logger.info(f"📚 {len(models)} modèles disponibles")
                return models
            else:
                logger.error(f"❌ Erreur récupération modèles: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"❌ Erreur get_models: {e}")
            return []
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
        """
        Génère une réponse avec Ollama.
        
        Args:
            prompt: Texte d'entrée pour la génération
            system_prompt: Instructions système optionnelles
            temperature: Contrôle la créativité (0.0 = déterministe, 1.0 = créatif)
            max_tokens: Nombre maximum de tokens à générer
            
        Returns:
            Texte généré ou None en cas d'erreur
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            logger.debug(f"🤖 Génération avec {self.model}...")
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                
                if generated_text:
                    logger.info(f"✅ Réponse générée ({len(generated_text)} caractères)")
                    return generated_text
                else:
                    logger.warning("⚠️ Réponse vide de Ollama")
                    return None
            else:
                logger.error(f"❌ Erreur API Ollama: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout lors de la génération")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur réseau: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur génération Ollama: {e}")
            return None
    
    def chat(self, messages: List[Dict[str, str]], 
             temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
        """
        Mode chat avec historique de conversation.
        
        Args:
            messages: Liste de messages au format [{"role": "user/assistant", "content": "..."}]
            temperature: Contrôle la créativité
            max_tokens: Nombre maximum de tokens
            
        Returns:
            Réponse de l'assistant ou None en cas d'erreur
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            logger.debug(f"💬 Chat avec {len(messages)} messages")
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", {})
                content = message.get("content", "")
                
                if content:
                    logger.info(f"✅ Réponse chat générée ({len(content)} caractères)")
                    return content
                else:
                    logger.warning("⚠️ Réponse chat vide")
                    return None
            else:
                logger.error(f"❌ Erreur chat Ollama: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout lors du chat")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur réseau chat: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur chat Ollama: {e}")
            return None
    
    def analyze_email(self, email_subject: str, email_body: str, sender: str) -> Dict:
        """
        Analyse un email avec l'IA.
        
        Args:
            email_subject: Sujet de l'email
            email_body: Corps de l'email
            sender: Expéditeur
            
        Returns:
            Dictionnaire contenant l'analyse
        """
        try:
            # Tronquer le body pour éviter les timeouts
            body_truncated = email_body[:500] if len(email_body) > 500 else email_body
            
            prompt = f"""Analyse cet email et réponds UNIQUEMENT avec un JSON valide (pas de markdown, pas de backticks):

Sujet: {email_subject}
Expéditeur: {sender}
Corps: {body_truncated}

Retourne exactement ce format JSON:
{{
    "category": "cv|meeting|invoice|newsletter|support|spam|general",
    "sentiment": "positive|neutral|negative",
    "urgent": true|false,
    "spam_score": 0.5,
    "summary": "résumé en une phrase",
    "confidence": 0.8
}}"""

            response = self.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200
            )
            
            if response:
                # Nettoyer la réponse (enlever markdown si présent)
                response_clean = response.strip()
                
                # Enlever les backticks si présents
                if response_clean.startswith('```'):
                    lines = response_clean.split('\n')
                    response_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_clean
                
                # Parser le JSON
                import json
                analysis = json.loads(response_clean)
                
                logger.info(f"✅ Email analysé: {analysis.get('category')}")
                return analysis
            else:
                logger.warning("⚠️ Pas de réponse pour l'analyse email")
                return self._default_analysis()
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur parsing JSON: {e}")
            return self._default_analysis()
        except Exception as e:
            logger.error(f"❌ Erreur analyse email: {e}")
            return self._default_analysis()
    
    def _default_analysis(self) -> Dict:
        """
        Retourne une analyse par défaut en cas d'erreur.
        
        Returns:
            Analyse par défaut
        """
        return {
            "category": "general",
            "sentiment": "neutral",
            "urgent": False,
            "spam_score": 0.0,
            "summary": "Analyse non disponible",
            "confidence": 0.0
        }
    
    def test_connection(self) -> bool:
        """
        Teste la connexion avec Ollama et le modèle.
        
        Returns:
            True si tout fonctionne, False sinon
        """
        try:
            if not self.is_available():
                logger.error("❌ Serveur Ollama non accessible")
                return False
            
            # Test simple de génération
            response = self.generate(
                prompt="Dis bonjour en un mot.",
                temperature=0.1,
                max_tokens=10
            )
            
            if response:
                logger.info("✅ Test de connexion Ollama réussi")
                return True
            else:
                logger.error("❌ Test de génération échoué")
                return False
        
        except Exception as e:
            logger.error(f"❌ Erreur test connexion: {e}")
            return False
    
    def __str__(self) -> str:
        """Représentation textuelle du client."""
        return f"OllamaClient(url={self.base_url}, model={self.model})"
    
    def __repr__(self) -> str:
        """Représentation détaillée du client."""
        return f"OllamaClient(base_url={self.base_url}, model={self.model})"