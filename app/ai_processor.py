#!/usr/bin/env python3
"""
Processeur IA principal avec classification intelligente et gestion contextuelle.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json

from ai.smart_classifier import SmartClassifier, EmailAnalysis
from models.email_model import Email
from utils.config import get_config_manager

logger = logging.getLogger(__name__)

class AIProcessor:
    """
    Processeur IA principal avec classification intelligente et context awareness.
    """
    
    def __init__(self):
        self.classifier = SmartClassifier()
        self.config_manager = get_config_manager()
        self.processing_queue = asyncio.Queue()
        self.context_history = {}  # Historique des conversations
        
        # Compteurs de performance
        self.stats = {
            'total_processed': 0,
            'correct_classifications': 0,
            'auto_responses_sent': 0,
            'last_reset': datetime.now()
        }
        
        logger.info("AIProcessor initialisé avec classification avancée")
    
    def process_email(self, email: Email) -> EmailAnalysis:
        """
        Traite un email avec analyse complète et context awareness.
        
        Args:
            email: L'email à analyser
            
        Returns:
            EmailAnalysis avec toutes les informations extraites
        """
        try:
            # Préparation des données pour l'IA
            email_data = {
                'subject': email.subject or '',
                'body': email.body or '',
                'sender': email.sender or '',
                'sender_name': email.get_sender_name(),
                'date': email.received_date,
                'thread_id': email.thread_id
            }
            
            # Ajouter le contexte de conversation si disponible
            email_data['conversation_context'] = self._get_conversation_context(email.thread_id)
            
            # Classification intelligente
            analysis = self.classifier.analyze_email(email_data)
            
            # Validation et ajustements contextuels
            analysis = self._validate_and_adjust_analysis(email, analysis)
            
            # Mise à jour des statistiques
            self.stats['total_processed'] += 1
            
            # Sauvegarder le contexte
            self._update_conversation_context(email.thread_id, analysis)
            
            logger.info(f"Email traité: {analysis.category} (confiance: {analysis.confidence:.2f})")
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur traitement email: {e}")
            return self._create_fallback_analysis(email)
    
    def _get_conversation_context(self, thread_id: str) -> Dict:
        """Récupère le contexte de la conversation."""
        if not thread_id:
            return {}
        
        context = self.context_history.get(thread_id, {
            'messages_count': 0,
            'last_category': None,
            'last_response_sent': None,
            'participants': [],
            'topics': []
        })
        
        return context
    
    def _update_conversation_context(self, thread_id: str, analysis: EmailAnalysis):
        """Met à jour le contexte de conversation."""
        if not thread_id:
            return
        
        if thread_id not in self.context_history:
            self.context_history[thread_id] = {
                'messages_count': 0,
                'last_category': None,
                'last_response_sent': None,
                'participants': [],
                'topics': []
            }
        
        context = self.context_history[thread_id]
        context['messages_count'] += 1
        context['last_category'] = analysis.category
        context['last_analysis'] = datetime.now()
        
        # Nettoyer l'historique ancien (> 30 jours)
        cutoff_date = datetime.now() - timedelta(days=30)
        self.context_history = {
            tid: ctx for tid, ctx in self.context_history.items()
            if ctx.get('last_analysis', datetime.now()) > cutoff_date
        }
    
    def _validate_and_adjust_analysis(self, email: Email, analysis: EmailAnalysis) -> EmailAnalysis:
        """Valide et ajuste l'analyse selon le contexte."""
        # Vérifications de cohérence
        
        # 1. Anti-boucle : éviter de répondre aux réponses automatiques
        if self._is_likely_auto_response(email):
            analysis.should_auto_respond = False
            analysis.reasoning += " [Auto-réponse détectée]"
        
        # 2. Limite de fréquence par expéditeur
        if self._sender_response_limit_reached(email.sender):
            analysis.should_auto_respond = False
            analysis.reasoning += " [Limite réponses atteinte]"
        
        # 3. Ajustement de confiance selon l'historique
        if hasattr(email, 'thread_id') and email.thread_id:
            context = self._get_conversation_context(email.thread_id)
            if context.get('last_category') == analysis.category:
                analysis.confidence *= 1.2  # Bonus cohérence
            
        # 4. Validation de la réponse suggérée
        if analysis.suggested_response:
            analysis.suggested_response = self._improve_suggested_response(
                analysis.suggested_response, email, analysis
            )
        
        return analysis
    
    def _is_likely_auto_response(self, email: Email) -> bool:
        """Détecte si l'email est probablement une réponse automatique."""
        indicators = [
            'noreply', 'no-reply', 'donotreply',
            'automatic', 'automatique', 'auto-generated',
            'out of office', 'absent du bureau'
        ]
        
        sender_lower = (email.sender or '').lower()
        subject_lower = (email.subject or '').lower()
        body_lower = (email.body or '').lower()[:500]
        
        return any(indicator in sender_lower or 
                  indicator in subject_lower or 
                  indicator in body_lower 
                  for indicator in indicators)
    
    def _sender_response_limit_reached(self, sender: str) -> bool:
        """Vérifie si la limite de réponses à cet expéditeur est atteinte."""
        # Logique simple : max 3 réponses auto par jour par expéditeur
        # TODO: Implémenter avec une vraie base de données
        return False
    
    def _improve_suggested_response(self, response: str, email: Email, analysis: EmailAnalysis) -> str:
        """Améliore la réponse suggérée avec des informations contextuelles."""
        # Personnalisation basée sur l'heure
        current_hour = datetime.now().hour
        if current_hour < 12:
            response = response.replace("Bonjour", "Bonjour")
        elif current_hour < 18:
            response = response.replace("Bonjour", "Bon après-midi")
        else:
            response = response.replace("Bonjour", "Bonsoir")
        
        # Ajouter des informations extraites si pertinentes
        if analysis.category == 'rdv' and analysis.extracted_info.get('potential_dates'):
            dates = analysis.extracted_info['potential_dates'][:2]
            if dates:
                response += f"\n\nP.S.: J'ai noté votre mention des dates suivantes : {', '.join(map(str, dates))}"
        
        return response
    
    def _create_fallback_analysis(self, email: Email) -> EmailAnalysis:
        """Crée une analyse de fallback en cas d'erreur."""
        return EmailAnalysis(
            category='general',
            confidence=0.1,
            priority=3,
            should_auto_respond=False,
            suggested_response=None,
            extracted_info={},
            reasoning="Analyse de fallback suite à une erreur"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de performance."""
        accuracy = 0.0
        if self.stats['total_processed'] > 0:
            accuracy = self.stats['correct_classifications'] / self.stats['total_processed']
        
        return {
            'total_processed': self.stats['total_processed'],
            'accuracy': accuracy,
            'auto_responses_sent': self.stats['auto_responses_sent'],
            'last_reset': self.stats['last_reset'],
            'context_history_size': len(self.context_history)
        }
    
    def report_classification_accuracy(self, was_correct: bool):
        """Rapporte la précision d'une classification pour les statistiques."""
        if was_correct:
            self.stats['correct_classifications'] += 1
    
    def learn_from_user_correction(self, email: Email, original_category: str, corrected_category: str):
        """Apprend d'une correction utilisateur."""
        email_data = {
            'subject': email.subject or '',
            'body': email.body or '',
            'sender': email.sender or ''
        }
        
        self.classifier.learn_from_correction(email_data, original_category, corrected_category)
        logger.info(f"Correction apprise: {original_category} -> {corrected_category}")