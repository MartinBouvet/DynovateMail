#!/usr/bin/env python3
"""
Auto Responder - Réponses automatiques aux emails
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from app.gmail_client import GmailClient
from app.ai_processor import AIProcessor
from app.models.email_model import Email

logger = logging.getLogger(__name__)

class AutoResponder:
    """Gestionnaire de réponses automatiques."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        """
        Initialise l'auto-responder.
        
        Args:
            gmail_client: Client Gmail
            ai_processor: Processeur IA
        """
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.enabled = False
        self.responded_emails = set()
        self.last_check = datetime.now()
        
        logger.info("AutoResponder initialisé avec sécurité renforcée")
    
    def enable(self):
        """Active les réponses automatiques."""
        self.enabled = True
        logger.info("✅ Réponses automatiques activées")
    
    def disable(self):
        """Désactive les réponses automatiques."""
        self.enabled = False
        logger.info("⛔ Réponses automatiques désactivées")
    
    def should_respond(self, email: Email) -> bool:
        """
        Détermine si on doit répondre automatiquement à cet email.
        
        Args:
            email: Email à analyser
            
        Returns:
            True si on doit répondre, False sinon
        """
        if not self.enabled:
            return False
        
        # Ne pas répondre si déjà répondu
        if email.id in self.responded_emails:
            return False
        
        # Ne pas répondre aux emails envoyés
        if 'SENT' in email.labels:
            return False
        
        # Ne pas répondre aux newsletters
        sender_lower = (email.sender or '').lower()
        if 'noreply' in sender_lower or 'no-reply' in sender_lower:
            return False
        
        # Ne pas répondre au spam
        if 'SPAM' in email.labels:
            return False
        
        # Analyser avec l'IA
        try:
            analysis = self.ai_processor.analyze_email(email)
            category = analysis.get('category', '')
            
            # Répondre aux CVs et demandes de support
            if category in ['cv', 'support', 'meeting']:
                return True
        
        except Exception as e:
            logger.error(f"Erreur analyse pour auto-réponse: {e}")
        
        return False
    
    def generate_response(self, email: Email) -> Optional[str]:
        """
        Génère une réponse automatique.
        
        Args:
            email: Email auquel répondre
            
        Returns:
            Texte de la réponse ou None
        """
        try:
            # Analyser l'email
            analysis = self.ai_processor.analyze_email(email)
            category = analysis.get('category', 'work')
            
            # Templates selon la catégorie
            if category == 'cv':
                response = self._generate_cv_response(email)
            elif category == 'support':
                response = self._generate_support_response(email)
            elif category == 'meeting':
                response = self._generate_meeting_response(email)
            else:
                response = self._generate_generic_response(email)
            
            logger.info(f"✅ Réponse générée pour catégorie: {category}")
            return response
        
        except Exception as e:
            logger.error(f"Erreur génération réponse: {e}")
            return None
    
    def _generate_cv_response(self, email: Email) -> str:
        """Génère une réponse pour une candidature."""
        return f"""Bonjour,

Nous avons bien reçu votre candidature et nous vous en remercions.

Votre profil sera étudié avec attention par notre équipe et nous reviendrons vers vous dans les plus brefs délais.

Cordialement,
L'équipe de recrutement"""
    
    def _generate_support_response(self, email: Email) -> str:
        """Génère une réponse pour une demande de support."""
        return f"""Bonjour,

Nous avons bien reçu votre demande de support.

Notre équipe va l'examiner et vous apportera une réponse dans les meilleurs délais.

Merci de votre patience.

Cordialement,
L'équipe support"""
    
    def _generate_meeting_response(self, email: Email) -> str:
        """Génère une réponse pour une demande de réunion."""
        return f"""Bonjour,

Nous avons bien reçu votre demande de réunion.

Nous allons vérifier nos disponibilités et reviendrons vers vous rapidement pour convenir d'un créneau.

Cordialement"""
    
    def _generate_generic_response(self, email: Email) -> str:
        """Génère une réponse générique."""
        # Utiliser l'IA pour générer une réponse personnalisée
        try:
            response = self.ai_processor.generate_response(email, tone='professional')
            return response
        except:
            return f"""Bonjour,

Nous avons bien reçu votre message et nous vous en remercions.

Nous reviendrons vers vous dans les plus brefs délais.

Cordialement"""
    
    def send_auto_response(self, email: Email) -> bool:
        """
        Envoie une réponse automatique.
        
        Args:
            email: Email auquel répondre
            
        Returns:
            True si envoyé, False sinon
        """
        try:
            if not self.should_respond(email):
                return False
            
            # Générer la réponse
            response_body = self.generate_response(email)
            
            if not response_body:
                return False
            
            # Envoyer la réponse
            subject = f"Re: {email.subject}" if email.subject else "Re: Votre message"
            
            success = self.gmail_client.send_email(
                to=email.sender,
                subject=subject,
                body=response_body
            )
            
            if success:
                # Marquer comme répondu
                self.responded_emails.add(email.id)
                logger.info(f"✅ Réponse automatique envoyée à {email.sender}")
                return True
            else:
                logger.error(f"❌ Échec envoi réponse à {email.sender}")
                return False
        
        except Exception as e:
            logger.error(f"Erreur envoi auto-réponse: {e}")
            return False
    
    def check_and_respond(self, max_emails: int = 10) -> int:
        """
        Vérifie les nouveaux emails et répond automatiquement si nécessaire.
        
        Args:
            max_emails: Nombre maximum d'emails à traiter
            
        Returns:
            Nombre de réponses envoyées
        """
        if not self.enabled:
            return 0
        
        try:
            # Récupérer les emails récents non lus
            emails = self.gmail_client.list_emails(
                folder="INBOX",
                max_results=max_emails
            )
            
            # Filtrer les non lus
            unread_emails = [e for e in emails if not getattr(e, 'read', True)]
            
            responses_sent = 0
            
            for email in unread_emails:
                if self.send_auto_response(email):
                    responses_sent += 1
            
            self.last_check = datetime.now()
            
            if responses_sent > 0:
                logger.info(f"✅ {responses_sent} réponses automatiques envoyées")
            
            return responses_sent
        
        except Exception as e:
            logger.error(f"Erreur vérification auto-réponse: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """
        Récupère les statistiques des réponses automatiques.
        
        Returns:
            Dictionnaire avec les stats
        """
        return {
            'enabled': self.enabled,
            'total_responses': len(self.responded_emails),
            'last_check': self.last_check.isoformat() if self.last_check else None
        }
    
    def reset_stats(self):
        """Réinitialise les statistiques."""
        self.responded_emails.clear()
        logger.info("📊 Statistiques réinitialisées")
    
    def is_enabled(self) -> bool:
        """Vérifie si l'auto-responder est activé."""
        return self.enabled