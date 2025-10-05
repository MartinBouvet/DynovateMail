#!/usr/bin/env python3
"""
Client Gmail API - VERSION COMPLÈTE CORRIGÉE
"""
import logging
import pickle
import os.path
import base64
from typing import List, Optional, Dict, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from models.email_model import Email, EmailAttachment

logger = logging.getLogger(__name__)

# Scopes nécessaires
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailClient:
    """Client Gmail API - PRODUCTION UNIQUEMENT."""
    
    def __init__(self, credentials_file: str = 'client_secret.json', mock_mode: bool = False):
        """
        Initialise le client Gmail.
        
        Args:
            credentials_file: Chemin vers le fichier credentials OAuth2
            mock_mode: IGNORÉ - toujours en mode production
        """
        self.credentials_file = credentials_file
        self.token_file = 'token.pickle'
        self.service = None
        self.authenticated = False
        
        logger.info("Client Gmail PRODUCTION UNIQUEMENT initialisé")
        self._authenticate()
    
    def _authenticate(self):
        """Authentifie avec l'API Gmail."""
        creds = None
        
        # Charger les credentials sauvegardés
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Si pas de credentials ou expirés
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Token Gmail rafraîchi")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Fichier credentials introuvable: {self.credentials_file}")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Sauvegarder les credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
                logger.info("Credentials Gmail sauvegardés")
        
        # Créer le service
        self.service = build('gmail', 'v1', credentials=creds)
        self.authenticated = True
        logger.info("✅ Service Gmail authentifié avec succès")
    
    def get_recent_emails(self, max_results: int = 50) -> List[Email]:
        """
        Récupère les emails récents.
        
        Args:
            max_results: Nombre maximum d'emails
            
        Returns:
            List[Email]: Liste des emails
        """
        try:
            if not self.authenticated:
                logger.error("Service Gmail non authentifié")
                return []
            
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info("Aucun email trouvé")
                return []
            
            logger.info(f"Récupération de {len(messages)} emails...")
            
            emails = []
            for msg in messages:
                email = self.get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            return emails
            
        except Exception as e:
            logger.error(f"Erreur récupération emails: {e}")
            return []
    
    def get_email_by_id(self, email_id: str) -> Optional[Email]:
        """
        Récupère un email par son ID.
        
        Args:
            email_id: ID de l'email
            
        Returns:
            Email ou None
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            return self._parse_email(message)
            
        except Exception as e:
            logger.error(f"Erreur récupération email {email_id}: {e}")
            return None
    
    def _parse_email(self, message: Dict) -> Optional[Email]:
        """Parse un message Gmail en objet Email."""
        try:
            headers = message['payload'].get('headers', [])
            
            # Extraire les headers
            subject = self._get_header(headers, 'Subject') or '(Sans sujet)'
            sender = self._get_header(headers, 'From') or 'unknown@unknown.com'
            to = self._get_header(headers, 'To') or ''
            date_str = self._get_header(headers, 'Date') or ''
            
            # Parser la date
            try:
                from email.utils import parsedate_to_datetime
                received_date = parsedate_to_datetime(date_str)
            except:
                received_date = datetime.now()
            
            # Corps du message
            body, is_html = self._get_body(message['payload'])
            
            # Snippet
            snippet = message.get('snippet', '')
            
            # Labels (pour déterminer si lu)
            label_ids = message.get('labelIds', [])
            is_read = 'UNREAD' not in label_ids
            
            # Pièces jointes
            attachments = self._get_attachments(message['payload'], message['id'])
            
            email = Email(
                id=message['id'],
                sender=sender,
                to=to,
                subject=subject,
                body=body,
                snippet=snippet,
                received_date=received_date,
                is_read=is_read,
                is_html=is_html,
                attachments=attachments,
                has_attachments=len(attachments) > 0
            )
            
            return email
            
        except Exception as e:
            logger.error(f"Erreur parsing email: {e}")
            return None
    
    def _get_header(self, headers: List[Dict], name: str) -> Optional[str]:
        """Récupère un header spécifique."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return None
    
    def _get_body(self, payload: Dict) -> tuple[str, bool]:
        """Extrait le corps du message."""
        body = ""
        is_html = False
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        is_html = True
                        break
                elif part['mimeType'] == 'text/plain' and not body:
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            if payload['mimeType'] == 'text/html':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    is_html = True
            elif payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body, is_html
    
    def _get_attachments(self, payload: Dict, message_id: str) -> List[EmailAttachment]:
        """Extrait les pièces jointes."""
        attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    attachment = EmailAttachment(
                        id=part['body'].get('attachmentId', ''),
                        filename=part['filename'],
                        mime_type=part['mimeType'],
                        size=part['body'].get('size', 0),
                        message_id=message_id
                    )
                    attachments.append(attachment)
        
        return attachments
    
    def get_archived_emails(self, max_results: int = 50) -> List[Email]:
        """Récupère les emails archivés."""
        try:
            if not self.authenticated:
                return []
            
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q='-in:inbox -in:trash -in:spam'
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self.get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            return emails
            
        except Exception as e:
            logger.error(f"Erreur récupération archives: {e}")
            return []
    
    def get_trashed_emails(self, max_results: int = 50) -> List[Email]:
        """Récupère les emails supprimés."""
        try:
            if not self.authenticated:
                return []
            
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['TRASH']
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self.get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            return emails
            
        except Exception as e:
            logger.error(f"Erreur récupération corbeille: {e}")
            return []
    
    def send_email(self, to: List[str], subject: str, body: str,
                   cc: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None) -> bool:
        """
        Envoie un email.
        
        Args:
            to: Liste des destinataires
            subject: Sujet
            body: Corps du message
            cc: Liste des destinataires en CC
            attachments: Liste des chemins de fichiers à attacher
            
        Returns:
            True si envoyé avec succès
        """
        try:
            message = MIMEMultipart()
            message['To'] = ', '.join(to)
            message['Subject'] = subject
            
            if cc:
                message['Cc'] = ', '.join(cc)
            
            message.attach(MIMEText(body, 'plain'))
            
            # Ajouter les pièces jointes
            if attachments:
                for filepath in attachments:
                    self._attach_file(message, filepath)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email envoyé à {to}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            return False
    
    def _attach_file(self, message: MIMEMultipart, filepath: str):
        """Attache un fichier au message."""
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(filepath)}'
        )
        message.attach(part)
    
    def mark_as_read(self, email_id: str) -> bool:
        """Marque un email comme lu."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur marquage lu: {e}")
            return False
    
    def archive_email(self, email_id: str) -> bool:
        """Archive un email."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur archivage: {e}")
            return False
    
    def delete_email(self, email_id: str) -> bool:
        """Supprime un email (le met à la corbeille)."""
        try:
            self.service.users().messages().trash(
                userId='me',
                id=email_id
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur suppression: {e}")
            return False