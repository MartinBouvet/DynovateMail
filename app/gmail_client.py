#!/usr/bin/env python3
"""
Client Gmail - VERSION OPTIMISÉE ULTRA-RAPIDE
"""
import logging
import os
import base64
from typing import List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.models.email_model import Email

logger = logging.getLogger(__name__)

class GmailClient:
    """Client Gmail optimisé."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, credentials_file: str = "client_secret.json", mock_mode: bool = False):
        self.credentials_file = credentials_file
        self.mock_mode = mock_mode
        self.service = None
        self.authenticated = False
        
        if not mock_mode:
            self._authenticate()
    
    def _authenticate(self):
        """Authentification."""
        try:
            creds = None
            
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.authenticated = True
            logger.info("✅ Gmail authentifié")
        
        except Exception as e:
            logger.error(f"❌ Erreur auth: {e}")
            self.authenticated = False
    
    def list_emails(self, folder: str = "INBOX", max_results: int = 50) -> List[Email]:
        """Liste emails - RAPIDE."""
        if self.mock_mode or not self.authenticated:
            return []
        
        try:
            label_map = {
                "INBOX": "INBOX",
                "SENT": "SENT",
                "DRAFTS": "DRAFT",
                "TRASH": "TRASH",
                "SPAM": "SPAM",
                "STARRED": "STARRED"
            }
            
            label_id = label_map.get(folder, folder)
            
            results = self.service.users().messages().list(
                userId='me',
                labelIds=[label_id],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                try:
                    email = self._parse_light(msg['id'])
                    if email:
                        emails.append(email)
                except:
                    pass
            
            logger.info(f"📧 {len(emails)} emails de {folder}")
            return emails
        
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return []
    
    def _parse_light(self, message_id: str) -> Optional[Email]:
        """Parse léger - RAPIDE."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            headers = message.get('payload', {}).get('headers', [])
            
            email = Email(
                id=message['id'],
                thread_id=message.get('threadId'),
                sender=self._get_header(headers, 'From'),
                to=self._get_header(headers, 'To'),
                subject=self._get_header(headers, 'Subject'),
                snippet=message.get('snippet', ''),
                received_date=self._parse_date(self._get_header(headers, 'Date')),
                read='UNREAD' not in message.get('labelIds', [])
            )
            
            return email
        
        except:
            return None
    
    def get_email(self, message_id: str) -> Optional[Email]:
        """Récupère email complet."""
        if self.mock_mode or not self.authenticated:
            return None
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message.get('payload', {}).get('headers', [])
            payload = message.get('payload', {})
            
            email = Email(
                id=message['id'],
                thread_id=message.get('threadId'),
                sender=self._get_header(headers, 'From'),
                to=self._get_header(headers, 'To'),
                subject=self._get_header(headers, 'Subject'),
                snippet=message.get('snippet', ''),
                body=self._extract_body(payload),
                received_date=self._parse_date(self._get_header(headers, 'Date')),
                read='UNREAD' not in message.get('labelIds', [])
            )
            
            return email
        
        except:
            return None
    
    def _extract_body(self, payload: dict) -> str:
        """Extrait body."""
        try:
            if 'body' in payload and payload['body'].get('data'):
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
            
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        if part.get('body', {}).get('data'):
                            return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    
                    if 'parts' in part:
                        body = self._extract_body(part)
                        if body:
                            return body
            
            return ""
        except:
            return ""
    
    def _get_header(self, headers: list, name: str) -> str:
        """Header."""
        for h in headers:
            if h.get('name', '').lower() == name.lower():
                return h.get('value', '')
        return ''
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date."""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            return None
    
    def send_email(self, to: str, subject: str, body: str, cc: str = None, attachments: list = None):
        """Envoie email."""
        if self.mock_mode or not self.authenticated:
            logger.info(f"📤 [MOCK] Email à {to}")
            return
        
        try:
            message = MIMEMultipart()
            message['To'] = to
            message['Subject'] = subject
            
            if cc:
                message['Cc'] = cc
            
            message.attach(MIMEText(body, 'plain'))
            
            if attachments:
                for filepath in attachments:
                    self._attach_file(message, filepath)
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"✅ Email envoyé à {to}")
        
        except Exception as e:
            logger.error(f"❌ Erreur envoi: {e}")
            raise
    
    def _attach_file(self, message: MIMEMultipart, filepath: str):
        """Attache fichier."""
        try:
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(filepath)}'
            )
            message.attach(part)
        except:
            pass
    
    def mark_as_read(self, message_id: str):
        """Marquer lu."""
        if self.mock_mode or not self.authenticated:
            return
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"✅ Marqué lu: {message_id}")
        except:
            pass
    
    def search_emails(self, query: str, max_results: int = 50) -> List[Email]:
        """Recherche."""
        if self.mock_mode or not self.authenticated:
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email = self._parse_light(msg['id'])
                if email:
                    emails.append(email)
            
            logger.info(f"🔍 {len(emails)} résultats")
            return emails
        except:
            return []
    
    def archive_email(self, message_id: str):
        """Archive."""
        if self.mock_mode or not self.authenticated:
            return
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            
            logger.info(f"✅ Archivé: {message_id}")
        except Exception as e:
            raise
    
    def delete_email(self, message_id: str):
        """Supprime."""
        if self.mock_mode or not self.authenticated:
            return
        
        try:
            self.service.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()
            
            logger.info(f"✅ Supprimé: {message_id}")
        except Exception as e:
            raise
    def send_email(self, to: str, subject: str, body: str):
        """Envoie un email via Gmail API."""
        import base64
        from email.message import EmailMessage
    
        try:
            message = EmailMessage()
            message.set_content(body, subtype='html')
            message['To'] = to
            message['Subject'] = subject
            message['From'] = 'me'
        
            encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': encoded}
            ).execute()
        
            logger.info(f"✅ Email envoyé à {to}")
            return send_message
        except Exception as e:
            logger.error(f"❌ Erreur envoi: {e}")
            raise