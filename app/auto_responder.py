#!/usr/bin/env python3
"""
Gestionnaire de réponses automatiques avec IA avancée et gestion des réponses en attente.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ai_processor import AIProcessor
from pending_response_manager import PendingResponseManager
from models.email_model import Email
from models.pending_response_model import PendingResponse, ResponseStatus

logger = logging.getLogger(__name__)

class AutoResponder:
    """
    Gestionnaire de réponses automatiques avec validation utilisateur.
    """
    
    def __init__(self, ai_processor: AIProcessor, pending_manager: PendingResponseManager):
        self.ai_processor = ai_processor
        self.pending_manager = pending_manager
        
        # Configuration par défaut
        self.enabled = True
        self.delay_minutes = 5
        self.respond_to_cv = True
        self.respond_to_rdv = True
        self.respond_to_support = True
        self.respond_to_partenariat = False
        self.avoid_loops = True
        
        # Historique des réponses pour éviter les boucles
        self.recent_responses = {}  # sender -> last_response_time
        
        logger.info("AutoResponder initialisé avec IA avancée")
    
    def process_email_for_auto_response(self, email: Email) -> Optional[PendingResponse]:
        """
        Traite un email pour une éventuelle réponse automatique.
        
        Args:
            email: L'email à analyser
            
        Returns:
            PendingResponse si une réponse est suggérée, None sinon
        """
        try:
            if not self.enabled:
                return None
            
            # Vérifier si on doit répondre à cet email
            if not self._should_auto_respond(email):
                return None
            
            # Analyser l'email avec l'IA
            if not hasattr(email, 'ai_analysis'):
                email.ai_analysis = self.ai_processor.process_email(email)
            
            analysis = email.ai_analysis
            
            # Vérifier si l'IA recommande une réponse
            if not analysis.should_auto_respond:
                return None
            
            # Générer la réponse suggérée
            if analysis.suggested_response:
                # Ajouter aux réponses en attente
                pending_response = self.pending_manager.add_pending_response(
                    email=email,
                    suggested_response=analysis.suggested_response,
                    confidence=analysis.confidence
                )
                
                logger.info(f"Réponse automatique suggérée pour email {email.id}")
                return pending_response
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de réponse automatique: {e}")
            return None
    
    def _should_auto_respond(self, email: Email) -> bool:
        """
        Détermine si on doit proposer une réponse automatique pour cet email.
        
        Args:
            email: L'email à analyser
            
        Returns:
            True si une réponse automatique doit être proposée
        """
        try:
            # Ne pas répondre aux emails envoyés par l'utilisateur
            if email.is_sent:
                return False
            
            # Éviter les boucles de réponses
            if self.avoid_loops and self._is_likely_auto_response(email):
                return False
            
            # Vérifier la limite de fréquence par expéditeur
            if self._sender_response_limit_reached(email.sender):
                return False
            
            # Vérifier s'il y a déjà une réponse en attente pour cet email
            if self._has_pending_response(email):
                return False
            
            # Analyser le contenu avec l'IA si pas déjà fait
            if not hasattr(email, 'ai_analysis'):
                email.ai_analysis = self.ai_processor.process_email(email)
            
            analysis = email.ai_analysis
            category = analysis.category
            
            # Vérifier les préférences de catégorie
            category_preferences = {
                'cv': self.respond_to_cv,
                'rdv': self.respond_to_rdv,
                'support': self.respond_to_support,
                'partenariat': self.respond_to_partenariat
            }
            
            # Ne jamais répondre aux spams ou newsletters
            if category in ['spam', 'newsletter']:
                return False
            
            # Vérifier les préférences utilisateur pour cette catégorie
            return category_preferences.get(category, False)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de réponse automatique: {e}")
            return False
    
    def _is_likely_auto_response(self, email: Email) -> bool:
        """Détecte si l'email est probablement une réponse automatique."""
        indicators = [
            'noreply', 'no-reply', 'donotreply',
            'automatic', 'automatique', 'auto-generated',
            'out of office', 'absent du bureau',
            'vacation', 'vacances'
        ]
        
        sender_lower = (email.sender or '').lower()
        subject_lower = (email.subject or '').lower()
        body_lower = (email.body or '').lower()[:500]  # Premiers 500 caractères
        
        return any(indicator in sender_lower or 
                  indicator in subject_lower or 
                  indicator in body_lower 
                  for indicator in indicators)
    
    def _sender_response_limit_reached(self, sender: str) -> bool:
        """Vérifie si la limite de réponses à cet expéditeur est atteinte."""
        if not sender:
            return True
        
        # Limite : maximum 2 réponses automatiques par jour par expéditeur
        now = datetime.now()
        cutoff = now - timedelta(days=1)
        
        if sender in self.recent_responses:
            last_response = self.recent_responses[sender]
            if isinstance(last_response, list):
                # Compter les réponses dans les dernières 24h
                recent_count = len([t for t in last_response if t > cutoff])
                return recent_count >= 2
            elif isinstance(last_response, datetime):
                # Format ancien, convertir
                self.recent_responses[sender] = [last_response] if last_response > cutoff else []
                return len(self.recent_responses[sender]) >= 2
        
        return False
    
    def _has_pending_response(self, email: Email) -> bool:
        """Vérifie s'il y a déjà une réponse en attente pour cet email."""
        try:
            pending_responses = self.pending_manager.get_pending_responses()
            return any(response.email_id == email.id for response in pending_responses)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des réponses en attente: {e}")
            return False
    
    def approve_and_send_response(self, response_id: str, 
                                 modified_content: Optional[str] = None,
                                 user_notes: str = "") -> bool:
        """
        Approuve et envoie une réponse.
        
        Args:
            response_id: ID de la réponse à approuver
            modified_content: Contenu modifié (optionnel)
            user_notes: Notes de l'utilisateur
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            # Approuver la réponse
            if not self.pending_manager.approve_response(response_id, modified_content):
                logger.error(f"Impossible d'approuver la réponse {response_id}")
                return False
            
            # TODO: Implémenter l'envoi réel via Gmail API
            # Pour l'instant, on simule l'envoi
            logger.info(f"Réponse {response_id} envoyée (simulé)")
            
            # Marquer comme envoyée
            self.pending_manager.mark_as_sent(response_id)
            
            # Mettre à jour l'historique des réponses
            # TODO: Récupérer l'expéditeur original
            # self._update_response_history(sender)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la réponse {response_id}: {e}")
            return False
    
    def reject_response(self, response_id: str) -> bool:
        """
        Rejette une réponse suggérée.
        
        Args:
            response_id: ID de la réponse à rejeter
            
        Returns:
            True si le rejet a réussi
        """
        try:
            success = self.pending_manager.reject_response(response_id)
            if success:
                logger.info(f"Réponse {response_id} rejetée")
            return success
        except Exception as e:
            logger.error(f"Erreur lors du rejet de la réponse {response_id}: {e}")
            return False
    
    def get_pending_responses(self) -> List[PendingResponse]:
        """Retourne toutes les réponses en attente."""
        return self.pending_manager.get_pending_responses()
    
    def get_responses_since(self, since: datetime) -> List[PendingResponse]:
        """Retourne les réponses depuis une date donnée."""
        all_responses = []
        for response in self.pending_manager.pending_responses.values():
            if response.created_at >= since:
                all_responses.append(response)
        return all_responses
    
    def _update_response_history(self, sender: str):
        """Met à jour l'historique des réponses pour un expéditeur."""
        now = datetime.now()
        
        if sender not in self.recent_responses:
            self.recent_responses[sender] = []
        
        if isinstance(self.recent_responses[sender], datetime):
            # Convertir l'ancien format
            old_time = self.recent_responses[sender]
            self.recent_responses[sender] = [old_time, now]
        else:
            self.recent_responses[sender].append(now)
        
        # Nettoyer les entrées anciennes (> 7 jours)
        cutoff = now - timedelta(days=7)
        self.recent_responses[sender] = [
            t for t in self.recent_responses[sender] if t > cutoff
        ]
    
    def cleanup_expired_responses(self):
        """Nettoie les réponses expirées."""
        self.pending_manager.cleanup_expired()
    
    def update_config(self, config: Dict[str, Any]):
        """Met à jour la configuration du répondeur automatique."""
        self.enabled = config.get('enabled', self.enabled)
        self.delay_minutes = config.get('delay_minutes', self.delay_minutes)
        self.respond_to_cv = config.get('respond_to_cv', self.respond_to_cv)
        self.respond_to_rdv = config.get('respond_to_rdv', self.respond_to_rdv)
        self.respond_to_support = config.get('respond_to_support', self.respond_to_support)
        self.respond_to_partenariat = config.get('respond_to_partenariat', self.respond_to_partenariat)
        self.avoid_loops = config.get('avoid_loops', self.avoid_loops)
        
        logger.info("Configuration AutoResponder mise à jour")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du répondeur automatique."""
        pending_count = len(self.get_pending_responses())
        
        # Compter les réponses par statut
        status_counts = {}
        for response in self.pending_manager.pending_responses.values():
            status = response.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'enabled': self.enabled,
            'pending_responses': pending_count,
            'total_responses': len(self.pending_manager.pending_responses),
            'status_breakdown': status_counts,
            'delay_minutes': self.delay_minutes
        }
    def get_ai_response_for_email(self, email: Email) -> Optional[str]:
        """Génère une réponse IA pour un email donné."""
        try:
            if not hasattr(email, 'ai_analysis') or not email.ai_analysis:
            # Analyser l'email d'abord
                email.ai_analysis = self.ai_processor.process_email(email)
        
            analysis = email.ai_analysis
        
            if (hasattr(analysis, 'should_auto_respond') and analysis.should_auto_respond and
                hasattr(analysis, 'suggested_response') and analysis.suggested_response):
                return analysis.suggested_response
        
            return None
        
        except Exception as e:
            logger.error(f"Erreur génération réponse IA: {e}")
            return None