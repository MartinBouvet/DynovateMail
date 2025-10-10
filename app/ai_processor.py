#!/usr/bin/env python3
"""
Processeur IA avec intégration Ollama - VERSION SANS spaCy
"""
import logging
from typing import Dict, List, Optional
import re
from datetime import datetime

from ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class AIProcessor:
    """Processeur IA utilisant Ollama pour toutes les tâches."""
    
    def __init__(self):
        """Initialise le processeur IA."""
        self.ollama = OllamaClient()
        
        # spaCy désactivé - on utilise uniquement Ollama
        self.nlp_fr = None
        self.nlp_en = None
        
        logger.info("✅ AIProcessor initialisé avec Ollama (mode sans spaCy)")
    
    def analyze_email(self, subject: str, body: str, sender: str) -> Dict:
        """
        Analyse complète d'un email avec Ollama.
        
        Returns:
            Dict avec toutes les métadonnées IA
        """
        logger.info(f"🔍 Analyse IA de: {subject}")
        
        # Analyse principale avec Ollama
        analysis = self.ollama.analyze_email(subject, body, sender)
        
        # Enrichir avec extraction basique d'entités (regex simple)
        entities = self._extract_entities_basic(body)
        analysis["entities"] = entities
        
        return analysis
    
    def generate_response(self, email_subject: str, email_body: str, sender: str, context: str = "") -> str:
        """
        Génère une réponse automatique avec Ollama.
        
        Returns:
            Texte de réponse
        """
        logger.info(f"✍️ Génération réponse pour: {email_subject}")
        
        response = self.ollama.generate_email_response(email_subject, email_body, sender, context)
        
        if not response:
            # Fallback
            response = f"""Bonjour,

Merci pour votre message concernant: {email_subject}

Nous avons bien reçu votre email et nous reviendrons vers vous dans les meilleurs délais.

Cordialement,
L'équipe Dynovate"""
        
        return response
    
    def extract_meeting_request(self, email_body: str) -> Optional[Dict]:
        """
        Détecte et extrait les demandes de rendez-vous avec Ollama.
        
        Returns:
            Dict avec infos du RDV ou None
        """
        meeting_info = self.ollama.extract_meeting_info(email_body)
        return meeting_info
    
    def categorize_email(self, subject: str, body: str) -> str:
        """
        Catégorise un email.
        
        Returns:
            Catégorie (cv, rendez-vous, spam, facture, etc.)
        """
        analysis = self.ollama.analyze_email(subject, body, "")
        return analysis.get("category", "autre")
    
    def detect_spam(self, subject: str, body: str, sender: str) -> bool:
        """
        Détecte si un email est un spam.
        
        Returns:
            True si spam détecté
        """
        analysis = self.ollama.analyze_email(subject, body, sender)
        return analysis.get("is_spam", False)
    
    def get_priority(self, subject: str, body: str) -> str:
        """
        Détermine la priorité d'un email.
        
        Returns:
            'haute', 'moyenne', ou 'basse'
        """
        analysis = self.ollama.analyze_email(subject, body, "")
        return analysis.get("priority", "moyenne")
    
    def summarize_email(self, body: str) -> str:
        """
        Génère un résumé de l'email.
        
        Returns:
            Résumé en 1-2 phrases
        """
        analysis = self.ollama.analyze_email("", body, "")
        return analysis.get("summary", "Résumé non disponible")
    
    def suggest_actions(self, email_data: Dict) -> List[str]:
        """
        Suggère des actions pour un email.
        
        Returns:
            Liste d'actions suggérées
        """
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        
        analysis = self.ollama.analyze_email(subject, body, "")
        return analysis.get("suggested_actions", ["Lire l'email"])
    
    def _extract_entities_basic(self, text: str) -> Dict:
        """
        Extrait les entités nommées avec regex (version basique sans spaCy).
        
        Returns:
            Dict avec emails, téléphones, URLs
        """
        entities = {
            "emails": [],
            "phones": [],
            "urls": [],
            "dates": []
        }
        
        try:
            # Extraire emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            entities["emails"] = list(set(re.findall(email_pattern, text)))
            
            # Extraire téléphones (formats français et internationaux)
            phone_patterns = [
                r'(?:\+33|0)[1-9](?:[0-9]{2}){4}',  # France
                r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'  # International
            ]
            for pattern in phone_patterns:
                entities["phones"].extend(re.findall(pattern, text))
            entities["phones"] = list(set(entities["phones"]))
            
            # Extraire URLs
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            entities["urls"] = list(set(re.findall(url_pattern, text)))
            
            # Extraire dates simples (formats courants)
            date_patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # JJ/MM/AAAA
                r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',     # AAAA-MM-JJ
            ]
            for pattern in date_patterns:
                entities["dates"].extend(re.findall(pattern, text))
            entities["dates"] = list(set(entities["dates"]))
            
        except Exception as e:
            logger.error(f"Erreur extraction entités: {e}")
        
        return entities
    
    def chat_with_assistant(self, user_message: str, history: List[Dict] = None) -> str:
        """
        Chatbot assistant avec Ollama.
        
        Args:
            user_message: Message de l'utilisateur
            history: Historique de conversation
            
        Returns:
            Réponse du chatbot
        """
        return self.ollama.chat_assistant(user_message, history)