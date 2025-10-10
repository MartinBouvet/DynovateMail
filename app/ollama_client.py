#!/usr/bin/env python3
"""
Client Ollama pour intégration IA locale
"""
import logging
import requests
import json
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client pour communiquer avec Ollama en local."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nchapman/ministral-8b-instruct-2410:8b"):
        """
        Initialise le client Ollama.
        
        Args:
            base_url: URL de base d'Ollama (par défaut localhost:11434)
            model: Nom du modèle à utiliser
        """
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Vérifier la connexion
        if not self._check_connection():
            logger.warning("⚠️ Ollama n'est pas accessible, vérifiez qu'il est lancé")
    
    def _check_connection(self) -> bool:
        """Vérifie que Ollama est accessible."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Ollama connecté sur {self.base_url}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Impossible de se connecter à Ollama: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """
        Génère une réponse avec le modèle Ollama.
        
        Args:
            prompt: Texte d'entrée
            system_prompt: Instructions système (optionnel)
            temperature: Créativité (0-1)
            max_tokens: Nombre maximum de tokens
            
        Returns:
            Réponse générée ou None en cas d'erreur
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
            
            logger.info(f"🤖 Génération avec Ollama ({self.model})...")
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                logger.info(f"✅ Réponse générée ({len(generated_text)} caractères)")
                return generated_text
            else:
                logger.error(f"❌ Erreur API Ollama: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur génération Ollama: {e}")
            return None
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """
        Mode chat avec historique de conversation.
        
        Args:
            messages: Liste de messages [{"role": "user/assistant", "content": "..."}]
            temperature: Créativité
            
        Returns:
            Réponse de l'assistant
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                logger.error(f"❌ Erreur chat Ollama: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur chat Ollama: {e}")
            return None
    
    def analyze_email(self, email_subject: str, email_body: str, sender: str) -> Dict:
        """
        Analyse un email avec l'IA.
        
        Returns:
            Dict avec category, priority, sentiment, summary, suggested_actions
        """
        system_prompt = """Tu es un assistant IA expert en analyse d'emails professionnels.
Ton rôle est d'analyser les emails et de fournir des informations structurées.
Réponds UNIQUEMENT en JSON valide sans texte supplémentaire."""

        prompt = f"""Analyse cet email et retourne un JSON avec ces champs:
- category: une catégorie parmi [cv, rendez-vous, spam, facture, newsletter, important, personnel, autre]
- priority: un niveau parmi [haute, moyenne, basse]
- sentiment: un sentiment parmi [positif, neutre, négatif, urgent]
- summary: un résumé en 1-2 phrases
- suggested_actions: liste de 2-3 actions suggérées
- is_spam: true/false

Email à analyser:
De: {sender}
Sujet: {email_subject}
Contenu: {email_body[:1000]}

Réponds en JSON uniquement."""

        try:
            response = self.generate(prompt, system_prompt=system_prompt, temperature=0.3)
            if response:
                # Nettoyer la réponse pour extraire le JSON
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.endswith("```"):
                    response = response[:-3]
                response = response.strip()
                
                analysis = json.loads(response)
                logger.info(f"✅ Email analysé: {analysis.get('category', 'autre')}")
                return analysis
            else:
                return self._default_analysis()
        except Exception as e:
            logger.error(f"❌ Erreur analyse email: {e}")
            return self._default_analysis()
    
    def generate_email_response(self, email_subject: str, email_body: str, sender: str, context: str = "") -> Optional[str]:
        """
        Génère une réponse automatique à un email.
        
        Args:
            email_subject: Sujet de l'email
            email_body: Corps de l'email
            sender: Expéditeur
            context: Contexte supplémentaire
            
        Returns:
            Réponse générée
        """
        system_prompt = """Tu es un assistant IA professionnel qui génère des réponses par email.
Tes réponses doivent être:
- Polies et professionnelles
- Concises (2-4 paragraphes maximum)
- Adaptées au contexte
- En français correct
- Signées "L'équipe Dynovate" """

        prompt = f"""Génère une réponse professionnelle à cet email:

De: {sender}
Sujet: {email_subject}
Message: {email_body[:800]}

{f'Contexte: {context}' if context else ''}

Génère une réponse appropriée, claire et professionnelle."""

        return self.generate(prompt, system_prompt=system_prompt, temperature=0.7, max_tokens=500)
    
    def extract_meeting_info(self, email_body: str) -> Optional[Dict]:
        """
        Extrait les informations de rendez-vous d'un email.
        
        Returns:
            Dict avec date, heure, durée, sujet, participants ou None
        """
        system_prompt = """Tu extrais les informations de rendez-vous des emails.
Réponds UNIQUEMENT en JSON valide."""

        prompt = f"""Extrait les informations de rendez-vous de cet email.
Retourne un JSON avec: date, heure, duree_minutes, sujet, participants (liste), lieu

Email: {email_body[:1000]}

Si aucun rendez-vous détecté, retourne {{"has_meeting": false}}
Sinon retourne {{"has_meeting": true, ...autres champs...}}

JSON uniquement:"""

        try:
            response = self.generate(prompt, system_prompt=system_prompt, temperature=0.2)
            if response:
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.endswith("```"):
                    response = response[:-3]
                response = response.strip()
                
                meeting_info = json.loads(response)
                if meeting_info.get("has_meeting"):
                    logger.info("✅ Rendez-vous détecté dans l'email")
                    return meeting_info
            return None
        except Exception as e:
            logger.error(f"❌ Erreur extraction rendez-vous: {e}")
            return None
    
    def chat_assistant(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """
        Chatbot assistant intelligent.
        
        Args:
            user_message: Message de l'utilisateur
            conversation_history: Historique de la conversation
            
        Returns:
            Réponse du chatbot
        """
        if conversation_history is None:
            conversation_history = []
        
        # Ajouter un message système au début
        messages = [{
            "role": "system",
            "content": """Tu es l'assistant IA Dynovate, expert en gestion d'emails et productivité.
Tu aides les utilisateurs à gérer leurs emails, organiser leur travail et automatiser leurs tâches.
Sois amical, concis et efficace. Réponds en français."""
        }]
        
        # Ajouter l'historique
        messages.extend(conversation_history)
        
        # Ajouter le nouveau message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        response = self.chat(messages, temperature=0.8)
        return response if response else "Désolé, je n'ai pas pu générer de réponse."
    
    def _default_analysis(self) -> Dict:
        """Retourne une analyse par défaut en cas d'erreur."""
        return {
            "category": "autre",
            "priority": "moyenne",
            "sentiment": "neutre",
            "summary": "Analyse non disponible",
            "suggested_actions": ["Lire l'email"],
            "is_spam": False
        }