"""
Système de réponse automatique intelligent.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

from models.email_model import Email
from gmail_client import GmailClient
from ai_processor import AIProcessor
from calendar_manager import CalendarManager

logger = logging.getLogger(__name__)

class AutoResponder:
    """Système de réponse automatique pour les emails."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor, 
                 calendar_manager: CalendarManager, config: Dict[str, Any]):
        """
        Initialise le répondeur automatique.
        
        Args:
            gmail_client: Client Gmail pour l'envoi d'emails.
            ai_processor: Processeur IA pour l'analyse des emails.
            calendar_manager: Gestionnaire de calendrier.
            config: Configuration de l'application.
        """
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.calendar_manager = calendar_manager
        self.config = config
        
        # Configuration du répondeur
        self.auto_respond_enabled = config.get('auto_respond', {}).get('enabled', False)
        self.response_delay = config.get('auto_respond', {}).get('delay_minutes', 5)
        self.user_name = config.get('user', {}).get('name', 'Assistant')
        self.user_signature = config.get('user', {}).get('signature', '')
        
        # Historique des réponses pour éviter les doublons
        self.response_history = {}
    
    def process_email(self, email: Email) -> bool:
        """
        Traite un email et envoie une réponse automatique si nécessaire.
        
        Args:
            email: L'email à traiter.
            
        Returns:
            True si une réponse a été envoyée, False sinon.
        """
        if not self.auto_respond_enabled:
            return False
        
        # Vérifier si on doit répondre automatiquement
        if not self.ai_processor.should_auto_respond(email):
            return False
        
        # Vérifier si on a déjà répondu récemment
        if self._has_recent_response(email):
            logger.info(f"Réponse automatique déjà envoyée récemment pour {email.id}")
            return False
        
        try:
            # Analyser l'email
            email_info = self.ai_processor.extract_key_information(email)
            
            # Générer la réponse appropriée
            response = self._generate_response(email, email_info)
            
            if response:
                # Envoyer la réponse
                subject = f"Re: {email.subject}"
                success = self.gmail_client.send_email(
                    email.get_sender_email(),
                    subject,
                    response
                )
                
                if success:
                    # Enregistrer dans l'historique
                    self._record_response(email)
                    logger.info(f"Réponse automatique envoyée pour {email.id}")
                    return True
                else:
                    logger.error(f"Échec de l'envoi de la réponse automatique pour {email.id}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'email {email.id}: {e}")
        
        return False
    
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

Le créneau que vous proposez me convient parfaitement. J'ai ajouté cet événement à mon calendrier et je vous enverrai une confirmation détaillée prochainement.

Cordialement,
{self.user_name}

{self.user_signature}"""
        else:
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
        sender_email = email.get_sender_email()
        
        if sender_email in self.response_history:
            last_response = self.response_history[sender_email]
            time_diff = datetime.now() - last_response
            
            # Éviter les réponses trop fréquentes (dans les 24h)
            return time_diff < timedelta(hours=24)
        
        return False
    
    def _record_response(self, email: Email):
        """
        Enregistre qu'une réponse a été envoyée.
        
        Args:
            email: L'email auquel on a répondu.
        """
        sender_email = email.get_sender_email()
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
        self.auto_respond_enabled = enabled
        logger.info(f"Réponses automatiques {'activées' if enabled else 'désactivées'}")
    
    def set_response_delay(self, delay_minutes: int):
        """
        Définit le délai avant envoi d'une réponse automatique.
        
        Args:
            delay_minutes: Délai en minutes.
        """
        self.response_delay = delay_minutes
        logger.info(f"Délai de réponse défini à {delay_minutes} minutes")
    
    def get_response_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques des réponses automatiques.
        
        Returns:
            Dictionnaire des statistiques.
        """
        return {
            'enabled': self.auto_respond_enabled,
            'delay_minutes': self.response_delay,
            'total_responses': len(self.response_history),
            'recent_responses': len([
                timestamp for timestamp in self.response_history.values()
                if datetime.now() - timestamp < timedelta(days=7)
            ])
        }