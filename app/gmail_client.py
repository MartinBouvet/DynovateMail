"""
Module pour interagir avec l'API Gmail.
"""
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import List, Dict, Any, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from models.email_model import Email

logger = logging.getLogger(__name__)

class GmailClient:
    """Client pour interagir avec l'API Gmail."""
    
    def __init__(self, credentials: Credentials):
        """
        Initialise le client Gmail avec les identifiants OAuth.
        
        Args:
            credentials: Les identifiants OAuth2 pour l'API Gmail.
        """
        self.service = build('gmail', 'v1', credentials=credentials)
        self.user_id = 'me'  # 'me' fait référence à l'utilisateur authentifié
    
    def list_messages(self, max_results: int = 20, query: str = "") -> List[Email]:
        """
        Récupère une liste d'emails depuis Gmail.
        
        Args:
            max_results: Nombre maximum d'emails à récupérer.
            query: Requête de recherche Gmail (ex: "is:unread").
            
        Returns:
            Liste d'objets Email.
        """
        try:
            # Récupérer les IDs des messages
            results = self.service.users().messages().list(
                userId=self.user_id,
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            
            # Si aucun message n'est trouvé
            if not messages:
                logger.info("Aucun message trouvé.")
                return []
            
            emails = []
            
            # Récupérer les détails de chaque message
            for message in messages:
                msg_id = message['id']
                email = self._get_email_details(msg_id)
                if email:
                    emails.append(email)
            
            return emails
        
        except HttpError as error:
            logger.error(f"Une erreur s'est produite lors de la récupération des emails: {error}")
            return []
    
    def _get_email_details(self, msg_id: str) -> Optional[Email]:
        """
        Récupère les détails d'un email spécifique.
        
        Args:
            msg_id: ID du message Gmail.
            
        Returns:
            Objet Email ou None en cas d'erreur.
        """
        try:
            message = self.service.users().messages().get(
                userId=self.user_id,
                id=msg_id,
                format='full'
            ).execute()
            
            # Extraire les en-têtes
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'Pas de sujet')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Inconnu')
            recipient = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'Inconnu')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Inconnu')
            
            # Extraire le corps du message
            body = self._get_email_body(message['payload'])
            
            # Créer un objet Email
            email = Email(
                id=msg_id,
                subject=subject,
                sender=sender,
                recipient=recipient,
                date=date,
                body=body,
                labels=message.get('labelIds', []),
                thread_id=message.get('threadId', ''),
                snippet=message.get('snippet', '')
            )
            
            return email
        
        except HttpError as error:
            logger.error(f"Une erreur s'est produite lors de la récupération des détails de l'email {msg_id}: {error}")
            return None
    
    def _get_email_body(self, payload: Dict[str, Any]) -> str:
        """
        Extrait le corps d'un email à partir de la charge utile.
        
        Args:
            payload: Charge utile du message Gmail.
            
        Returns:
            Corps de l'email sous forme de texte.
        """
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif 'parts' in part:
                    return self._get_email_body(part)
        
        elif 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return "Contenu non disponible"
    
    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> bool:
        """
        Envoie un email via Gmail.
        
        Args:
            to: Adresse email du destinataire.
            subject: Sujet de l'email.
            body: Corps de l'email.
            html: True si le corps est en HTML, False sinon.
            
        Returns:
            True si l'envoi a réussi, False sinon.
        """
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if html:
                msg = MIMEText(body, 'html')
            else:
                msg = MIMEText(body, 'plain')
            
            message.attach(msg)
            
            # Encoder le message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Envoyer le message
            self.service.users().messages().send(
                userId=self.user_id,
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email envoyé à {to} avec le sujet '{subject}'")
            return True
        
        except HttpError as error:
            logger.error(f"Une erreur s'est produite lors de l'envoi de l'email: {error}")
            return False