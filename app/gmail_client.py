#!/usr/bin/env python3
"""
Client Gmail avec authentification et mode mock pour développement.
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from models.email_model import Email

logger = logging.getLogger(__name__)

class GmailClient:
    """Client Gmail avec mode mock pour développement."""
    
    def __init__(self, credentials: Optional[str] = None, mock_mode: bool = True):
        """
        Initialise le client Gmail.
        
        Args:
            credentials: Chemin vers le fichier de credentials (optionnel)
            mock_mode: Mode mock pour développement (par défaut True)
        """
        self.credentials = credentials
        self.mock_mode = mock_mode
        self.authenticated = False
        
        if mock_mode:
            logger.info("Client Gmail initialisé en mode mock")
            self.authenticated = True
        else:
            logger.info("Client Gmail initialisé en mode production")
            # TODO: Implémenter l'authentification réelle
    
    def authenticate(self) -> bool:
        """Authentifie l'utilisateur avec Gmail."""
        if self.mock_mode:
            self.authenticated = True
            return True
        
        # TODO: Implémenter l'authentification OAuth2 réelle
        logger.warning("Authentification réelle non implémentée")
        return False
    
    def get_recent_emails(self, limit: int = 50) -> List[Email]:
        """
        Récupère les emails récents.
        
        Args:
            limit: Nombre maximum d'emails à récupérer
            
        Returns:
            Liste des emails récents
        """
        if not self.authenticated:
            logger.error("Client Gmail non authentifié")
            return []
        
        if self.mock_mode:
            return self._generate_mock_emails(limit)
        
        # TODO: Implémenter la récupération réelle
        logger.warning("Récupération réelle d'emails non implémentée")
        return []
    
    def _generate_mock_emails(self, limit: int) -> List[Email]:
        """Génère des emails de test pour le développement."""
        mock_emails = []
        
        # Templates d'emails de test
        email_templates = [
            {
                'subject': 'Candidature pour le poste de développeur',
                'body': 'Bonjour, je vous envoie ma candidature pour le poste de développeur Python. Vous trouverez mon CV en pièce jointe.',
                'sender': 'john.doe@example.com',
                'category': 'cv'
            },
            {
                'subject': 'Demande de rendez-vous',
                'body': 'Bonjour, pourriez-vous me proposer un créneau pour un rendez-vous la semaine prochaine ? Je suis disponible mardi et mercredi.',
                'sender': 'client@entreprise.com',
                'category': 'rdv'
            },
            {
                'subject': 'Problème technique urgent',
                'body': 'Bonjour, nous rencontrons un problème critique sur notre site web. Pourriez-vous nous aider rapidement ?',
                'sender': 'support@client.com',
                'category': 'support'
            },
            {
                'subject': 'Facture N°2025-001',
                'body': 'Veuillez trouver ci-joint la facture pour les services du mois de janvier. Montant : 1 250€. Échéance : 30 jours.',
                'sender': 'comptabilite@fournisseur.com',
                'category': 'facture'
            },
            {
                'subject': 'URGENT: Offre spéciale limitée !',
                'body': 'CLIQUEZ ICI MAINTENANT ! Offre exceptionnelle valable 24h seulement ! Réduction de 90% !',
                'sender': 'promo@spam.com',
                'category': 'spam'
            },
            {
                'subject': 'Newsletter tech hebdomadaire',
                'body': 'Voici les dernières actualités tech de la semaine. Pour vous désabonner, cliquez ici.',
                'sender': 'newsletter@techblog.com',
                'category': 'newsletter'
            },
            {
                'subject': 'Proposition de partenariat',
                'body': 'Bonjour, nous aimerions vous proposer un partenariat commercial. Pouvons-nous planifier un appel ?',
                'sender': 'business@partner.com',
                'category': 'partenariat'
            },
            {
                'subject': 'Re: Votre commande',
                'body': 'Merci pour votre commande. Voici les détails de votre achat et le numéro de suivi.',
                'sender': 'commandes@boutique.com',
                'category': 'general'
            }
        ]
        
        # Générer les emails
        for i in range(min(limit, len(email_templates) * 3)):
            template = email_templates[i % len(email_templates)]
            
            # Varier les dates
            hours_ago = i * 2 + (i % 24)
            received_date = datetime.now() - timedelta(hours=hours_ago)
            
            email = Email(
                id=f"mock_email_{i+1}",
                subject=template['subject'],
                body=template['body'],
                sender=template['sender'],
                received_date=received_date,
                is_read=(i % 4 != 0),  # 75% des emails sont lus
                is_sent=False,
                thread_id=f"thread_{i//2}",  # Grouper par paires
                attachments=self._generate_mock_attachments(template.get('category'))
            )
            
            mock_emails.append(email)
        
        logger.info(f"{len(mock_emails)} emails de test générés")
        return mock_emails
    
    def _generate_mock_attachments(self, category: Optional[str] = None) -> List[dict]:
        """Génère des pièces jointes de test selon la catégorie."""
        if category == 'cv':
            return [
                {
                    'filename': 'CV_John_Doe.pdf',
                    'size': '245 KB',
                    'type': 'application/pdf'
                },
                {
                    'filename': 'Lettre_motivation.docx',
                    'size': '128 KB',
                    'type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                }
            ]
        elif category == 'facture':
            return [
                {
                    'filename': 'Facture_2025-001.pdf',
                    'size': '89 KB',
                    'type': 'application/pdf'
                }
            ]
        elif category == 'support':
            return [
                {
                    'filename': 'screenshot_erreur.png',
                    'size': '156 KB',
                    'type': 'image/png'
                }
            ]
        else:
            # Parfois pas de pièce jointe
            return [] if hash(str(category)) % 3 == 0 else []
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: Optional[List[str]] = None, 
                   bcc: Optional[List[str]] = None) -> bool:
        """
        Envoie un email.
        
        Args:
            to: Destinataire
            subject: Sujet
            body: Corps de l'email
            cc: Copie (optionnel)
            bcc: Copie cachée (optionnel)
            
        Returns:
            True si l'envoi a réussi
        """
        if not self.authenticated:
            logger.error("Client Gmail non authentifié")
            return False
        
        if self.mock_mode:
            logger.info(f"Email simulé envoyé à {to}: {subject}")
            return True
        
        # TODO: Implémenter l'envoi réel
        logger.warning("Envoi réel d'email non implémenté")
        return False
    
    def mark_as_read(self, email_id: str) -> bool:
        """Marque un email comme lu."""
        if self.mock_mode:
            logger.info(f"Email {email_id} marqué comme lu (simulé)")
            return True
        
        # TODO: Implémenter le marquage réel
        return False
    
    def archive_email(self, email_id: str) -> bool:
        """Archive un email."""
        if self.mock_mode:
            logger.info(f"Email {email_id} archivé (simulé)")
            return True
        
        # TODO: Implémenter l'archivage réel
        return False
    
    def delete_email(self, email_id: str) -> bool:
        """Supprime un email."""
        if self.mock_mode:
            logger.info(f"Email {email_id} supprimé (simulé)")
            return True
        
        # TODO: Implémenter la suppression réelle
        return False
    
    def get_email_details(self, email_id: str) -> Optional[Email]:
        """Récupère les détails d'un email spécifique."""
        if self.mock_mode:
            # Générer un email de test avec cet ID
            return Email(
                id=email_id,
                subject="Email de test détaillé",
                body="Ceci est un email de test avec plus de détails...",
                sender="test@example.com",
                received_date=datetime.now(),
                is_read=False
            )
        
        # TODO: Implémenter la récupération réelle
        return None
    
    def search_emails(self, query: str, max_results: int = 50) -> List[Email]:
        """
        Recherche des emails selon une requête.
        
        Args:
            query: Requête de recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste des emails correspondants
        """
        if self.mock_mode:
            # Simuler une recherche
            all_emails = self.get_recent_emails(max_results)
            query_lower = query.lower()
            
            matching_emails = []
            for email in all_emails:
                if (query_lower in (email.subject or '').lower() or
                    query_lower in (email.body or '').lower() or
                    query_lower in (email.sender or '').lower()):
                    matching_emails.append(email)
            
            logger.info(f"Recherche '{query}': {len(matching_emails)} résultats")
            return matching_emails
        
        # TODO: Implémenter la recherche réelle
        return []
    
    def get_connection_status(self) -> dict:
        """Retourne le statut de la connexion."""
        return {
            'authenticated': self.authenticated,
            'mock_mode': self.mock_mode,
            'credentials_loaded': self.credentials is not None,
            'last_sync': datetime.now().isoformat() if self.authenticated else None
        }