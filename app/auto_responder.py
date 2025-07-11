"""
Système de réponse automatique avec validation utilisateur.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta  # <-- Ajoutez timedelta ici
import json

from models.email_model import Email
from models.pending_response_model import PendingResponse, ResponseStatus
from gmail_client import GmailClient
from ai_processor import AIProcessor
from calendar_manager import CalendarManager
from pending_response_manager import PendingResponseManager
from utils.config import get_config_manager

logger = logging.getLogger(__name__)

class AutoResponder:
    """Système de réponse automatique avec validation utilisateur."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor, 
                 calendar_manager: CalendarManager):
        """
        Initialise le répondeur automatique.
        
        Args:
            gmail_client: Client Gmail pour l'envoi d'emails.
            ai_processor: Processeur IA pour l'analyse des emails.
            calendar_manager: Gestionnaire de calendrier.
        """
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.calendar_manager = calendar_manager
        
        # Gestionnaire de configuration
        self.config_manager = get_config_manager()
        
        # Gestionnaire des réponses en attente
        self.pending_manager = PendingResponseManager()
        
        # Configuration actuelle (mise à jour en temps réel)
        self._update_config()
        
        # S'abonner aux changements de configuration
        self.config_manager.add_observer(self._on_config_changed)
        
        # Historique des réponses pour éviter les doublons
        self.response_history = {}
        
        logger.info("AutoResponder initialisé avec validation utilisateur")
    
    def _update_config(self):
        """Met à jour la configuration interne."""
        config = self.config_manager.get_config()
        
        auto_respond_config = config.get('auto_respond', {})
        user_config = config.get('user', {})
        
        # Configuration du répondeur
        self.auto_respond_enabled = auto_respond_config.get('enabled', False)
        self.response_delay = auto_respond_config.get('delay_minutes', 5)
        self.respond_to_cv = auto_respond_config.get('respond_to_cv', True)
        self.respond_to_rdv = auto_respond_config.get('respond_to_rdv', True)
        self.respond_to_support = auto_respond_config.get('respond_to_support', True)
        self.respond_to_partenariat = auto_respond_config.get('respond_to_partenariat', True)
        self.avoid_loops = auto_respond_config.get('avoid_loops', True)
        
        # Informations utilisateur
        self.user_name = user_config.get('name', 'Assistant')
        self.user_signature = user_config.get('signature', '')
        
        logger.info(f"Configuration mise à jour - Auto-réponse: {'activée' if self.auto_respond_enabled else 'désactivée'}")
    
    def _on_config_changed(self, new_config: Dict[str, Any]):
        """Callback appelé quand la configuration change."""
        logger.info("Configuration changée, mise à jour de l'auto-répondeur")
        self._update_config()
    
    def process_email(self, email: Email) -> bool:
        """
        Traite un email et crée une réponse en attente si nécessaire.
        
        Args:
            email: L'email à traiter.
            
        Returns:
            True si une réponse en attente a été créée, False sinon.
        """
        if not self.auto_respond_enabled:
            logger.debug("Réponse automatique désactivée")
            return False
        
        # Vérifier si on doit répondre automatiquement
        if not self.should_auto_respond(email):
            return False
        
        # Vérifier si on a déjà une réponse en attente pour cet email
        if self._has_pending_response(email):
            logger.info(f"Réponse déjà en attente pour {email.id}")
            return False
        
        # Vérifier si on a déjà répondu récemment
        if self._has_recent_response(email):
            logger.info(f"Réponse automatique déjà envoyée récemment pour {email.id}")
            return False
        
        try:
            # Analyser l'email
            email_info = self.ai_processor.extract_key_information(email)
            
            # Générer la réponse proposée
            proposed_response = self._generate_response(email, email_info)
            
            if proposed_response:
                # Créer une réponse en attente
                pending_response = PendingResponse(
                    email_id=email.id,
                    original_subject=email.subject,
                    original_sender=email.get_sender_name(),
                    original_sender_email=email.get_sender_email(),
                    original_body=email.body[:500] + "..." if len(email.body) > 500 else email.body,
                    category=email_info.get('category', 'general'),
                    proposed_response=proposed_response,
                    reason=self._get_response_reason(email_info),
                    confidence_score=self._calculate_confidence(email_info),
                    status=ResponseStatus.PENDING
                )
                
                # Ajouter à la base de données
                success = self.pending_manager.add_pending_response(pending_response)
                
                if success:
                    logger.info(f"Réponse en attente créée pour {email.id}")
                    return True
                else:
                    logger.error(f"Échec de la création de réponse en attente pour {email.id}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'email {email.id}: {e}")
        
        return False
    
    def should_auto_respond(self, email: Email) -> bool:
        """
        Détermine si un email doit recevoir une réponse automatique.
        
        Args:
            email: L'email à analyser.
            
        Returns:
            True si une réponse automatique doit être proposée.
        """
        try:
            # Ne pas répondre aux emails envoyés par l'utilisateur
            if email.is_sent:
                return False
            
            # Vérifier la catégorie de l'email
            if hasattr(email, 'ai_info') and email.ai_info:
                category = email.ai_info.get('category', 'general')
                
                # Vérifier si on doit répondre à cette catégorie
                if category == 'cv' and not self.respond_to_cv:
                    return False
                elif category == 'rdv' and not self.respond_to_rdv:
                    return False
                elif category == 'support' and not self.respond_to_support:
                    return False
                elif category == 'partenariat' and not self.respond_to_partenariat:
                    return False
                elif category == 'newsletter':
                    return False  # Ne jamais répondre aux newsletters
                elif category == 'spam':
                    return False  # Ne jamais répondre aux spams
                
                # Si l'IA recommande une réponse
                return email.ai_info.get('should_auto_respond', False)
            
            # Fallback sur l'analyse simple
            return self.ai_processor.should_auto_respond(email)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de réponse automatique: {e}")
            return False
    
    def _has_pending_response(self, email: Email) -> bool:
        """
        Vérifie s'il y a déjà une réponse en attente pour cet email.
        
        Args:
            email: L'email à vérifier.
            
        Returns:
            True si une réponse est déjà en attente.
        """
        pending_responses = self.pending_manager.get_pending_responses()
        return any(response.email_id == email.id for response in pending_responses)
    
    def approve_and_send_response(self, response_id: int, 
                                 modified_content: Optional[str] = None,
                                 user_notes: str = "") -> bool:
        """
        Approuve et envoie une réponse.
        
        Args:
            response_id: ID de la réponse à approuver.
            modified_content: Contenu modifié (optionnel).
            user_notes: Notes de l'utilisateur.
            
        Returns:
            True si l'envoi a réussi, False sinon.
        """
        try:
            # Récupérer la réponse
            response = self.pending_manager.get_response_by_id(response_id)
            if not response:
                logger.error(f"Réponse {response_id} introuvable")
                return False
            
            # Utiliser le contenu modifié si fourni
            final_content = modified_content if modified_content else response.proposed_response
            
            # Envoyer l'email
            subject = f"Re: {response.original_subject}"
            success = self.gmail_client.send_email(
                response.original_sender_email,
                subject,
                final_content
            )
            
            if success:
                # Mettre à jour le statut
                if modified_content:
                    self.pending_manager.update_response_content(response_id, modified_content)
                
                self.pending_manager.update_response_status(
                    response_id, 
                    ResponseStatus.SENT, 
                    user_notes
                )
                
                # Enregistrer dans l'historique
                self._record_response_from_pending(response)
                
                logger.info(f"Réponse {response_id} approuvée et envoyée")
                return True
            else:
                logger.error(f"Échec de l'envoi de la réponse {response_id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'approbation de la réponse: {e}")
            return False
    
    def reject_response(self, response_id: int, user_notes: str = "") -> bool:
        """
        Rejette une réponse.
        
        Args:
            response_id: ID de la réponse à rejeter.
            user_notes: Raison du rejet.
            
        Returns:
            True si le rejet a réussi, False sinon.
        """
        try:
            success = self.pending_manager.update_response_status(
                response_id,
                ResponseStatus.REJECTED,
                user_notes
            )
            
            if success:
                logger.info(f"Réponse {response_id} rejetée: {user_notes}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors du rejet de la réponse: {e}")
            return False
    
    def get_pending_responses(self) -> list:
        """Récupère toutes les réponses en attente."""
        return self.pending_manager.get_pending_responses()
    
    def get_response_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques des réponses automatiques.
        
        Returns:
            Dictionnaire des statistiques.
        """
        db_stats = self.pending_manager.get_stats()
        
        return {
            'enabled': self.auto_respond_enabled,
            'delay_minutes': self.response_delay,
            'total_responses': len(self.response_history),
            'pending_count': db_stats['pending'],
            'approved_count': db_stats['approved'],
            'rejected_count': db_stats['rejected'],
            'sent_count': db_stats['sent'],
            'today_count': db_stats['today'],
            'categories': {
                'cv': self.respond_to_cv,
                'rdv': self.respond_to_rdv,
                'support': self.respond_to_support,
                'partenariat': self.respond_to_partenariat
            },
            'avoid_loops': self.avoid_loops
        }
    
    def _generate_response(self, email: Email, email_info: Dict[str, Any]) -> Optional[str]:
        """
        Génère une réponse appropriée basée sur l'analyse de l'email.
        
        Args:
            email: L'email original.
            email_info: Informations extraites par l'IA.
            
        Returns:
            La réponse générée ou None.
        """
        category = email_info.get('category', 'general')
        sender_name = email.get_sender_name()
        
        # Générer des réponses spécialisées par catégorie
        if category == 'cv':
            return self._generate_cv_response(email, sender_name)
        elif category == 'rdv':
            return self._generate_meeting_response(email, sender_name, email_info)
        elif category == 'support':
            return self._generate_support_response(email, sender_name)
        elif category == 'facture':
            return self._generate_invoice_response(email, sender_name)
        elif category == 'partenariat':
            return self._generate_partnership_response(email, sender_name)
        else:
            return self._generate_general_response(email, sender_name)
    
    def _get_response_reason(self, email_info: Dict[str, Any]) -> str:
        """Génère une explication de pourquoi l'IA propose cette réponse."""
        category = email_info.get('category', 'general')
        
        reasons = {
            'cv': "Email identifié comme une candidature",
            'rdv': "Demande de rendez-vous détectée",
            'support': "Demande d'assistance technique",
            'facture': "Document comptable reçu",
            'partenariat': "Proposition de collaboration",
            'general': "Email nécessitant une réponse de courtoisie"
        }
        
        return reasons.get(category, "Email analysé par l'IA")
    
    def _calculate_confidence(self, email_info: Dict[str, Any]) -> float:
        """Calcule un score de confiance pour la réponse."""
        confidence = 0.5  # Base
        
        # Bonus selon la catégorie
        category = email_info.get('category', 'general')
        if category in ['cv', 'rdv', 'support']:
            confidence += 0.3
        
        # Bonus selon la priorité
        priority = email_info.get('priority', 1)
        if priority >= 2:
            confidence += 0.1
        
        # Bonus si l'email est professionnel
        if email_info.get('is_professional', False):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_cv_response(self, email: Email, sender_name: str) -> str:
        """Génère une réponse pour une candidature."""
        return f"""Bonjour {sender_name},

Merci pour votre candidature que nous avons bien reçue.

Notre équipe RH va examiner votre profil dans les plus brefs délais. Nous vous contacterons prochainement si votre candidature correspond à nos besoins actuels.

Nous vous remercions pour l'intérêt que vous portez à notre entreprise.

Cordialement,
{self.user_name}
Service des Ressources Humaines

{self.user_signature}"""
    
    def _generate_meeting_response(self, email: Email, sender_name: str, 
                                  email_info: Dict[str, Any]) -> str:
        """Génère une réponse pour une demande de rendez-vous."""
        meeting_info = email_info.get('meeting_info')
        
        if meeting_info:
            # Vérifier les conflits de planning
            try:
                conflicts = self.calendar_manager.get_conflicting_events(meeting_info)
                
                if conflicts:
                    return f"""Bonjour {sender_name},

Merci pour votre demande de rendez-vous.

Malheureusement, le créneau que vous proposez n'est pas disponible. Pouvez-vous me proposer d'autres créneaux qui vous conviendraient ?

Je vous recontacterai rapidement pour convenir d'un moment qui nous convient à tous les deux.

Cordialement,
{self.user_name}

{self.user_signature}"""
                else:
                    return f"""Bonjour {sender_name},

Merci pour votre demande de rendez-vous.

Le créneau que vous proposez me convient parfaitement. Je vais ajouter cet événement à mon calendrier et vous enverrai une confirmation détaillée prochainement.

Cordialement,
{self.user_name}

{self.user_signature}"""
            except Exception as e:
                logger.error(f"Erreur lors de la vérification du calendrier: {e}")
        
        return f"""Bonjour {sender_name},

Merci pour votre demande de rendez-vous.

Je vais vérifier mes disponibilités et vous recontacterai rapidement avec plusieurs créneaux possibles.

Cordialement,
{self.user_name}

{self.user_signature}"""
    
    def _generate_support_response(self, email: Email, sender_name: str) -> str:
        """Génère une réponse pour une demande de support."""
        return f"""Bonjour {sender_name},

Merci pour votre message.

J'ai bien reçu votre demande d'assistance et je vais l'examiner attentivement. Je vous répondrai dans les plus brefs délais avec une solution appropriée.

Si votre demande est urgente, n'hésitez pas à me contacter directement.

Cordialement,
{self.user_name}
Service Support

{self.user_signature}"""
    
    def _generate_invoice_response(self, email: Email, sender_name: str) -> str:
        """Génère une réponse pour une facture."""
        return f"""Bonjour {sender_name},

Merci pour votre facture que nous avons bien reçue.

Elle va être transmise à notre service comptable pour traitement. Le règlement sera effectué selon nos conditions de paiement habituelles.

Cordialement,
{self.user_name}
Service Comptabilité

{self.user_signature}"""
    
    def _generate_partnership_response(self, email: Email, sender_name: str) -> str:
        """Génère une réponse pour une proposition de partenariat."""
        return f"""Bonjour {sender_name},

Merci pour votre proposition de partenariat.

Nous sommes toujours intéressés par de nouvelles opportunités de collaboration. Je vais examiner votre proposition et la transmettre aux personnes concernées.

Nous vous recontacterons prochainement pour discuter des possibilités de collaboration.

Cordialement,
{self.user_name}
Direction Commerciale

{self.user_signature}"""
    
    def _generate_general_response(self, email: Email, sender_name: str) -> str:
        """Génère une réponse générale."""
        return f"""Bonjour {sender_name},

Merci pour votre email.

J'ai bien reçu votre message et je vous répondrai dans les plus brefs délais.

Cordialement,
{self.user_name}

{self.user_signature}"""
    
    def _has_recent_response(self, email: Email) -> bool:
        """
        Vérifie si une réponse automatique a été envoyée récemment.
        
        Args:
            email: L'email à vérifier.
            
        Returns:
            True si une réponse récente existe, False sinon.
        """
        if not self.avoid_loops:
            return False
        
        sender_email = email.get_sender_email()
        
        if sender_email in self.response_history:
            last_response = self.response_history[sender_email]
            time_diff = datetime.now() - last_response
            
            # Éviter les réponses trop fréquentes (dans les 24h)
            return time_diff < timedelta(hours=24)
        
        return False
    
    def _record_response_from_pending(self, response: PendingResponse):
        """
        Enregistre qu'une réponse a été envoyée depuis une réponse en attente.
        
        Args:
            response: La réponse qui a été envoyée.
        """
        sender_email = response.original_sender_email
        self.response_history[sender_email] = datetime.now()
        
        # Nettoyer l'historique (garder seulement les 30 derniers jours)
        cutoff_date = datetime.now() - timedelta(days=30)
        self.response_history = {
            email: timestamp for email, timestamp in self.response_history.items()
            if timestamp > cutoff_date
        }
    
    def set_auto_respond_enabled(self, enabled: bool):
        """
        Active ou désactive les réponses automatiques.
        
        Args:
            enabled: True pour activer, False pour désactiver.
        """
        self.config_manager.set('auto_respond.enabled', enabled)
        logger.info(f"Réponses automatiques {'activées' if enabled else 'désactivées'} via API")
    
    def set_response_delay(self, delay_minutes: int):
        """
        Définit le délai avant envoi d'une réponse automatique.
        
        Args:
            delay_minutes: Délai en minutes.
        """
        self.config_manager.set('auto_respond.delay_minutes', delay_minutes)
        logger.info(f"Délai de réponse défini à {delay_minutes} minutes via API")
    
    def set_category_response(self, category: str, enabled: bool):
        """
        Active/désactive la réponse automatique pour une catégorie.
        
        Args:
            category: Catégorie (cv, rdv, support, partenariat).
            enabled: True pour activer, False pour désactiver.
        """
        config_key = f'auto_respond.respond_to_{category}'
        self.config_manager.set(config_key, enabled)
        logger.info(f"Réponse automatique pour {category}: {'activée' if enabled else 'désactivée'}")
    
    def cleanup_old_data(self):
        """Nettoie les anciennes données."""
        try:
            # Nettoyer les réponses en attente anciennes
            deleted_count = self.pending_manager.cleanup_old_responses(30)
            logger.info(f"Nettoyage automatique: {deleted_count} anciennes réponses supprimées")
            
            # Nettoyer l'historique local
            cutoff_date = datetime.now() - timedelta(days=30)
            old_count = len(self.response_history)
            self.response_history = {
                email: timestamp for email, timestamp in self.response_history.items()
                if timestamp > cutoff_date
            }
            cleaned_count = old_count - len(self.response_history)
            
            if cleaned_count > 0:
                logger.info(f"Historique local nettoyé: {cleaned_count} entrées supprimées")
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
    
    def __del__(self):
        """Nettoie les observers lors de la destruction."""
        try:
            self.config_manager.remove_observer(self._on_config_changed)
        except:
            pass