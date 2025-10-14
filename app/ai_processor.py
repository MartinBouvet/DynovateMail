#!/usr/bin/env python3
"""
Processeur IA - ULTRA-RAPIDE ET OPTIMISÉ
"""
import logging
import json
from typing import Dict, Optional
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)

class AIProcessor:
    """IA ultra-rapide avec cache."""
    
    def __init__(self):
        self.ollama_client = None
        self.cache = {}
        self.cache_duration = timedelta(hours=24)
        
        try:
            from app.ollama_client import OllamaClient
            self.ollama_client = OllamaClient()
            if self.ollama_client.is_available():
                logger.info("✅ Ollama OK")
            else:
                logger.warning("⚠️ Ollama indisponible")
                self.ollama_client = None
        except:
            self.ollama_client = None
    
    def analyze_email_fast(self, subject: str, body: str, sender: str) -> Optional[Dict]:
        """
        Analyse ULTRA-RAPIDE (< 100ms).
        """
        try:
            # Cache
            cache_key = self._cache_key(subject, sender)
            if cache_key in self.cache:
                cached, timestamp = self.cache[cache_key]
                if datetime.now() - timestamp < self.cache_duration:
                    logger.info(f"📦 Cache hit: {subject[:30]}")
                    return cached
            
            # Analyse basique (RAPIDE)
            analysis = self._basic_analysis(subject, body, sender)
            
            # Cache
            self.cache[cache_key] = (analysis, datetime.now())
            
            return analysis
        
        except:
            return None
    
    def _basic_analysis(self, subject: str, body: str, sender: str) -> Dict:
        """Analyse par règles - INSTANTANÉE."""
        analysis = {
            'category': 'general',
            'sentiment': 'neutral',
            'urgent': False,
            'spam_score': 0.0,
            'confidence': 0.85
        }
        
        subject_lower = (subject or '').lower()
        body_lower = (body or '').lower()
        combined = subject_lower + ' ' + body_lower
        
        # Catégories
        if any(w in combined for w in ['cv', 'candidature', 'curriculum', 'postule']):
            analysis['category'] = 'cv'
        
        elif any(w in combined for w in ['rendez-vous', 'rdv', 'réunion', 'meeting', 'disponibilité']):
            analysis['category'] = 'meeting'
        
        elif any(w in combined for w in ['facture', 'invoice', 'paiement', 'montant']):
            analysis['category'] = 'invoice'
        
        elif any(w in combined for w in ['newsletter', 'abonnement', 'désabonner']):
            analysis['category'] = 'newsletter'
        
        elif any(w in combined for w in ['support', 'aide', 'problème', 'assistance']):
            analysis['category'] = 'support'
        
        elif any(w in combined for w in ['casino', 'viagra', 'lottery', 'winner', 'urgent money']):
            analysis['category'] = 'spam'
            analysis['spam_score'] = 0.95
        
        # Sentiment
        positive = ['merci', 'excellent', 'super', 'bravo', 'parfait']
        negative = ['problème', 'erreur', 'bug', 'mécontent', 'déçu']
        
        pos_count = sum(1 for w in positive if w in combined)
        neg_count = sum(1 for w in negative if w in combined)
        
        if pos_count > neg_count:
            analysis['sentiment'] = 'positive'
        elif neg_count > pos_count:
            analysis['sentiment'] = 'negative'
        
        # Urgence
        if any(w in combined for w in ['urgent', 'asap', 'immédiat', 'important', 'prioritaire']):
            analysis['urgent'] = True
        
        return analysis
    
    def analyze_email_detailed(self, subject: str, body: str, sender: str) -> Optional[Dict]:
        """Analyse détaillée avec IA."""
        try:
            cache_key = self._cache_key(subject, sender)
            if cache_key in self.cache:
                cached, timestamp = self.cache[cache_key]
                if datetime.now() - timestamp < self.cache_duration:
                    return cached
            
            # IA si disponible
            if self.ollama_client and self.ollama_client.is_available():
                analysis = self._ai_analysis(subject, body, sender)
            else:
                analysis = self._basic_analysis(subject, body, sender)
            
            # Résumé
            if 'summary' not in analysis and body:
                analysis['summary'] = self._summary(body)
            
            self.cache[cache_key] = (analysis, datetime.now())
            
            return analysis
        except:
            return None
    
    def _ai_analysis(self, subject: str, body: str, sender: str) -> Dict:
        """Analyse IA."""
        try:
            body_truncated = body[:400] if len(body) > 400 else body
            
            prompt = f"""Analyse email, réponds JSON pur (pas de markdown):

Sujet: {subject}
De: {sender}
Corps: {body_truncated}

JSON:
{{
    "category": "cv|meeting|invoice|newsletter|support|spam|general",
    "sentiment": "positive|neutral|negative",
    "urgent": true|false,
    "spam_score": 0.5,
    "summary": "résumé court",
    "confidence": 0.8
}}"""

            response = self.ollama_client.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=150
            )
            if response:
                # Nettoyer
                response_clean = response.strip()
                if response_clean.startswith('```'):
                    lines = response_clean.split('\n')
                    response_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_clean
                
                analysis = json.loads(response_clean)
                logger.info(f"✅ IA: {analysis.get('category')}")
                return analysis
            
        except Exception as e:
            logger.error(f"Erreur IA: {e}")
        
        return self._basic_analysis(subject, body, sender)
    
    def _summary(self, body: str) -> str:
        """Génère résumé."""
        if not body:
            return "Email sans contenu"
        
        summary = body.strip()[:120]
        summary = summary.replace('\n', ' ').replace('\r', '')
        
        if len(body) > 120:
            summary += "..."
        
        return summary
    
    def _cache_key(self, subject: str, sender: str) -> str:
        """Clé cache."""
        return f"{sender}:{subject}"
    
    def clear_cache(self):
        """Efface cache."""
        self.cache.clear()
        logger.info("Cache effacé")
    
    def generate_response(self, email_content: str, context: str = "") -> Optional[str]:
        """Génère réponse."""
        try:
            if not self.ollama_client or not self.ollama_client.is_available():
                return None
            
            prompt = f"""Rédige réponse professionnelle:

Email:
{email_content[:400]}

{context}

Réponds courtoisement."""

            response = self.ollama_client.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=250
            )
            
            return response
        
        except:
            return None