#!/usr/bin/env python3
"""
Gestionnaire de réponses automatiques - VERSION CORRIGÉE
Corrections: Validation, évitement de boucles, sécurité
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from ai_processor import AIProcessor
from models.email_model import Email

logger = logging.getLogger(__name__)


class AutoResponder:
    """Gestionnaire de réponses automatiques sécurisé - CORRIGÉ."""
    
    def __init__(self, ai_processor: AIProcessor):
        self.ai_processor = ai_processor
        
        # Configuration
        self.enabled = True
        self.delay_minutes = 5  # Délai avant envoi
        self.respond_to_cv = True
        self.respond_to_rdv = True
        self.respond_to_support = True
        self.respond_to_partenariat = False
        self.avoid_loops = True
        
        # Historique des réponses (pour éviter les boucles)
        self.response_history = defaultdict(list)  # sender -> [timestamps]
        self.max_responses_per_day = 2
        
        # Réponses en attente de validation
        self.pending_responses = {}  # response_id -> response_data
        
        logger.info("AutoResponder initialisé avec sécurité renforcée")
    
    def process_email_for_auto_response(self, email: Email) -> Optional[Dict]:
        """
        Traite un email pour une éventuelle réponse automatique - CORRIGÉ.
        
        Args:
            email: L'email à traiter
            
        Returns:
            Dict contenant les détails de la réponse suggérée, ou None
        """
        try:
            if not self.enabled:
                logger.debug("Réponses automatiques désactivées")
                return None
            
            # Vérifier que l'email a une analyse IA
            if not hasattr(email, 'ai_analysis') or not email.ai_analysis:
                logger.debug(f"Email {email.id} sans analyse IA")
                return None
            
            analysis = email.ai_analysis
            
            # Vérifier si une réponse auto est recommandée
            if not analysis.should_auto_respond:
                logger.debug(f"Email {email.id} ne nécessite pas de réponse auto")
                return None
            
            # Vérifier la catégorie
            if not self._is_category_enabled(analysis.category):
                logger.debug(f"Réponses auto désactivées pour catégorie: {analysis.category}")
                return None
            
            # === SÉCURITÉ: Éviter les boucles ===
            if self.avoid_loops:
                if self._is_response_loop_risk(email.sender):
                    logger.warning(f"Risque de boucle détecté pour {email.sender}")
                    return None
            
            # Vérifier qu'il y a une réponse suggérée
            if not analysis.suggested_response:
                logger.debug(f"Email {email.id} sans réponse suggérée")
                return None
            
            # Créer les données de la réponse
            response_data = {
                'email_id': email.id,
                'sender': email.sender,
                'subject': f"Re: {email.subject}" if email.subject else "Re: (sans sujet)",
                'body': analysis.suggested_response,
                'category': analysis.category,
                'confidence': analysis.confidence,
                'created_at': datetime.now(),
                'scheduled_send_time': datetime.now() + timedelta(minutes=self.delay_minutes),
                'status': 'pending'
            }
            
            logger.info(
                f"Réponse automatique suggérée pour email {email.id} "
                f"(catégorie: {analysis.category}, confiance: {analysis.confidence:.2f})"
            )
            
            return response_data
            
        except Exception as e:
            logger.error(f"Erreur traitement réponse auto: {e}")
            return None
    
    def _is_category_enabled(self, category: str) -> bool:
        """Vérifie si les réponses auto sont activées pour cette catégorie."""
        category_settings = {
            'cv': self.respond_to_cv,
            'rdv': self.respond_to_rdv,
            'support': self.respond_to_support,
            'partenariat': self.respond_to_partenariat
        }
        return category_settings.get(category, False)
    
    def _is_response_loop_risk(self, sender: str) -> bool:
        """
        Détecte un risque de boucle de réponses - CORRIGÉ.
        
        Args:
            sender: Adresse email de l'expéditeur
            
        Returns:
            True si risque de boucle détecté
        """
        if not sender:
            return True
        
        # Nettoyer l'historique (supprimer les anciennes entrées)
        cutoff_time = datetime.now() - timedelta(days=1)
        self.response_history[sender] = [
            timestamp for timestamp in self.response_history[sender]
            if timestamp > cutoff_time
        ]
        
        # Vérifier le nombre de réponses dans les dernières 24h
        response_count = len(self.response_history[sender])
        
        if response_count >= self.max_responses_per_day:
            logger.warning(
                f"Limite de réponses atteinte pour {sender}: "
                f"{response_count}/{self.max_responses_per_day}"
            )
            return True
        
        return False
    
    def register_response_sent(self, sender: str):
        """Enregistre qu'une réponse a été envoyée à cet expéditeur."""
        self.response_history[sender].append(datetime.now())
        logger.debug(f"Réponse enregistrée pour {sender}")
    
    def add_pending_response(self, response_id: str, response_data: Dict):
        """Ajoute une réponse en attente de validation."""
        self.pending_responses[response_id] = response_data
        logger.info(f"Réponse en attente ajoutée: {response_id}")
    
    def get_pending_responses(self) -> List[Dict]:
        """Retourne toutes les réponses en attente."""
        return list(self.pending_responses.values())
    
    def approve_response(self, response_id: str, 
                        modified_content: Optional[str] = None) -> bool:
        """
        Approuve une réponse pour envoi - CORRIGÉ.
        
        Args:
            response_id: ID de la réponse
            modified_content: Contenu modifié (optionnel)
            
        Returns:
            True si approuvée avec succès
        """
        if response_id not in self.pending_responses:
            logger.error(f"Réponse inconnue: {response_id}")
            return False
        
        response_data = self.pending_responses[response_id]
        
        # Appliquer les modifications si présentes
        if modified_content:
            response_data['body'] = modified_content
            response_data['modified'] = True
        
        response_data['status'] = 'approved'
        response_data['approved_at'] = datetime.now()
        
        logger.info(f"Réponse approuvée: {response_id}")
        return True
    
    def reject_response(self, response_id: str) -> bool:
        """
        Rejette une réponse suggérée.
        
        Args:
            response_id: ID de la réponse
            
        Returns:
            True si rejetée avec succès
        """
        if response_id not in self.pending_responses:
            logger.error(f"Réponse inconnue: {response_id}")
            return False
        
        response_data = self.pending_responses[response_id]
        response_data['status'] = 'rejected'
        response_data['rejected_at'] = datetime.now()
        
        # Retirer de la liste des réponses en attente
        del self.pending_responses[response_id]
        
        logger.info(f"Réponse rejetée: {response_id}")
        return True
    
    def get_response_by_email_id(self, email_id: str) -> Optional[Dict]:
        """Récupère une réponse par l'ID de l'email associé."""
        for response_id, response_data in self.pending_responses.items():
            if response_data.get('email_id') == email_id:
                return response_data
        return None
    
    def configure(self, settings: Dict[str, Any]):
        """
        Configure le gestionnaire de réponses automatiques.
        
        Args:
            settings: Dictionnaire de configuration
        """
        if 'enabled' in settings:
            self.enabled = settings['enabled']
        
        if 'delay_minutes' in settings:
            self.delay_minutes = max(0, int(settings['delay_minutes']))
        
        if 'respond_to_cv' in settings:
            self.respond_to_cv = settings['respond_to_cv']
        
        if 'respond_to_rdv' in settings:
            self.respond_to_rdv = settings['respond_to_rdv']
        
        if 'respond_to_support' in settings:
            self.respond_to_support = settings['respond_to_support']
        
        if 'respond_to_partenariat' in settings:
            self.respond_to_partenariat = settings['respond_to_partenariat']
        
        if 'avoid_loops' in settings:
            self.avoid_loops = settings['avoid_loops']
        
        if 'max_responses_per_day' in settings:
            self.max_responses_per_day = max(1, int(settings['max_responses_per_day']))
        
        logger.info("Configuration AutoResponder mise à jour")
    
    def get_configuration(self) -> Dict[str, Any]:
        """Retourne la configuration actuelle."""
        return {
            'enabled': self.enabled,
            'delay_minutes': self.delay_minutes,
            'respond_to_cv': self.respond_to_cv,
            'respond_to_rdv': self.respond_to_rdv,
            'respond_to_support': self.respond_to_support,
            'respond_to_partenariat': self.respond_to_partenariat,
            'avoid_loops': self.avoid_loops,
            'max_responses_per_day': self.max_responses_per_day
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques des réponses automatiques."""
        pending_count = len(self.pending_responses)
        
        # Compter par statut
        status_counts = defaultdict(int)
        for response_data in self.pending_responses.values():
            status = response_data.get('status', 'unknown')
            status_counts[status] += 1
        
        # Compter par catégorie
        category_counts = defaultdict(int)
        for response_data in self.pending_responses.values():
            category = response_data.get('category', 'unknown')
            category_counts[category] += 1
        
        return {
            'enabled': self.enabled,
            'pending_responses': pending_count,
            'status_breakdown': dict(status_counts),
            'category_breakdown': dict(category_counts),
            'delay_minutes': self.delay_minutes,
            'response_history_size': len(self.response_history)
        }