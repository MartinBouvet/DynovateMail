#!/usr/bin/env python3
"""
Client Gmail - MÉTHODES COMPLÈTES
"""
import logging
import base64
import os
from typing import List, Optional, Dict
from datetime import datetime, timezone
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

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose'
]

class GmailClient:
    """Client pour l'API Gmail."""
    
    def __init__(self, credentials_file: str = "client_secret.json", mock_mode: bool = False):
        self.credentials_file = credentials_file
        self.mock_mode = mock_mode
        self.service = None
        self.authenticated = False
        
        if not mock_mode:
            self._authenticate()
    
    def _authenticate(self):
        """Authentifie avec Gmail API."""
        try:
            creds = None
            
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.authenticated = True
            logger.info("Authentification Gmail réussie")
            
        except Exception as e:
            logger.error(f"Erreur authentification Gmail: {e}")
            self.authenticated = False
    
    def get_inbox_emails(self, max_results: int = 50) -> List[Email]:
        """Récupère les emails de la boîte de réception."""
        try:
            logger.info(f"Récupération de {max_results} emails de la boîte de réception")
            
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self._get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            logger.info(f"{len(emails)} emails récupérés de INBOX")
            return emails
            
        except Exception as e:
            logger.error(f"Erreur récupération inbox: {e}")
            return []
    
    def get_sent_emails(self, max_results: int = 50) -> List[Email]:
        """Récupère les emails envoyés."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['SENT'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self._get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            logger.info(f"{len(emails)} emails envoyés récupérés")
            return emails
            
        except Exception as e:
            logger.error(f"Erreur récupération emails envoyés: {e}")
            return []
    
    def get_archived_emails(self, max_results: int = 50) -> List[Email]:
        """Récupère les emails archivés."""
        try:
            # Les emails archivés n'ont pas le label INBOX mais ne sont pas dans TRASH
            results = self.service.users().messages().list(
                userId='me',
                q='-in:inbox -in:trash -in:spam',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self._get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            logger.info(f"{len(emails)} emails archivés récupérés")
            return emails
            
        except Exception as e:
            logger.error(f"Erreur récupération archives: {e}")
            return []
    
    def get_draft_emails(self, max_results: int = 50) -> List[Email]:
        """Récupère les brouillons."""
        try:
            results = self.service.users().drafts().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            drafts = results.get('drafts', [])
            emails = []
            
            for draft in drafts:
                msg = draft.get('message', {})
                email = self._get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            logger.info(f"{len(emails)} brouillons récupérés")
            return emails
            
        except Exception as e:
            logger.error(f"Erreur récupération brouillons: {e}")
            return []
    
    def get_trash_emails(self, max_results: int = 50) -> List[Email]:
        """Récupère les emails de la corbeille."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['TRASH'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self._get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            logger.info(f"{len(emails)} emails de la corbeille récupérés")
            return emails
            
        except Exception as e:
            logger.error(f"Erreur récupération corbeille: {e}")
            return []
    
    def get_spam_emails(self, max_results: int = 50) -> List[Email]:
        """Récupère les spams."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['SPAM'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self._get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            logger.info(f"{len(emails)} spams récupérés")
            return emails
            
        except Exception as e:
            logger.error(f"Erreur récupération spam: {e}")
            return []
    
    def _get_email_by_id(self, email_id: str) -> Optional[Email]:
        """Récupère un email par son ID."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            
            # Extraction des informations
            subject = self._get_header(headers, 'Subject')
            sender = self._get_header(headers, 'From')
            to = self._get_header(headers, 'To')
            cc = self._get_header(headers, 'Cc')
            date_str = self._get_header(headers, 'Date')
            
            # Snippet (aperçu court)
            snippet = message.get('snippet', '')
            
            # Parser la date
            received_date = None
            if date_str:
                try:
                    from email.utils import parsedate_to_datetime
                    received_date = parsedate_to_datetime(date_str)
                except:
                    received_date = datetime.now(timezone.utc)
            
            # Corps du message
            body, is_html = self._get_body(message['payload'])
            
            # Pièces jointes
            attachments = self._get_attachments(message['payload'], email_id)
            
            # Labels
            labels = message.get('labelIds', [])
            is_read = 'UNREAD' not in labels
            
            email = Email(
                id=email_id,
                subject=subject,
                sender=sender,
                to=[to] if to else [],
                cc=[cc] if cc else [],
                body=body,
                snippet=snippet,  # AJOUT DU SNIPPET
                received_date=received_date,
                is_read=is_read,
                is_html=is_html,
                attachments=attachments,
                labels=labels
            )
            
            return email
            
        except Exception as e:
            logger.error(f"Erreur récupération email {email_id}: {e}")
            return None
    
    def _get_header(self, headers: List[Dict], name: str) -> Optional[str]:
        """Extrait une en-tête."""
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
    
    def send_email(self, to: List[str], subject: str, body: str, 
                   cc: Optional[List[str]] = None, 
                   attachments: Optional[List[str]] = None) -> bool:
        """Envoie un email."""
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
            f'attachment; filename={os.path.basename(filepath)}'
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
    
    def mark_as_unread(self, email_id: str) -> bool:
        """Marque un email comme non lu."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur marquage non lu: {e}")
            return False
    
    def archive_email(self, email_id: str) -> bool:
        """Archive un email."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            logger.info(f"Email {email_id} archivé")
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
            logger.info(f"Email {email_id} supprimé")
            return True
        except Exception as e:
            logger.error(f"Erreur suppression: {e}")
            return False
    
    def search_emails(self, query: str, max_results: int = 50) -> List[Email]:
        """Recherche des emails."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self._get_email_by_id(msg['id'])
                if email:
                    emails.append(email)
            
            logger.info(f"{len(emails)} emails trouvés pour: {query}")
            return emails
            
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []