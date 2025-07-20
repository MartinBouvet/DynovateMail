#!/usr/bin/env python3
"""
Client Gmail avec authentification réelle et gestion correcte des timezones.
"""
import logging
import os
import base64
import pickle
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Imports Gmail API
try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from email.utils import parsedate_to_datetime
    HAS_GMAIL_API = True
except ImportError:
    HAS_GMAIL_API = False
    logging.error("Gmail API non disponible - installez google-api-python-client")

from models.email_model import Email

logger = logging.getLogger(__name__)

class GmailClient:
    """Client Gmail pour accéder aux vrais emails."""
    
    def __init__(self, credentials_file: str = "client_secret.json", mock_mode: bool = False):
        """
        Initialise le client Gmail.
        
        Args:
            credentials_file: Chemin vers le fichier de credentials
            mock_mode: Mode mock pour tests (par défaut False)
        """
        self.credentials_file = credentials_file
        self.mock_mode = mock_mode
        self.authenticated = False
        self.service = None
        
        # Scopes Gmail nécessaires
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        
        if not HAS_GMAIL_API:
            logger.error("Gmail API non disponible - basculement en mode mock")
            self.mock_mode = True
        
        if self.mock_mode:
            logger.info("Client Gmail en mode mock")
            self.authenticated = True
        else:
            logger.info("Client Gmail en mode production")
            self.authenticate()
    
    def authenticate(self) -> bool:
        """Authentifie l'utilisateur avec Gmail."""
        if self.mock_mode:
            self.authenticated = True
            return True
        
        if not HAS_GMAIL_API:
            logger.error("Gmail API non disponible")
            return False
        
        try:
            creds = None
            token_path = Path('token.pickle')
            
            # Charger les tokens existants
            if token_path.exists():
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            # Si pas de credentials valides, faire l'auth
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        logger.info("Token Gmail rafraîchi")
                    except Exception as e:
                        logger.error(f"Erreur refresh token: {e}")
                        creds = None
                
                if not creds:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Fichier credentials manquant: {self.credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    logger.info("Nouvelle authentification Gmail effectuée")
                
                # Sauvegarder les credentials
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Credentials Gmail sauvegardés")
            
            # Créer le service Gmail
            self.service = build('gmail', 'v1', credentials=creds)
            self.authenticated = True
            logger.info("Service Gmail initialisé avec succès")
            return True
        
        except Exception as e:
            logger.error(f"Erreur authentification Gmail: {e}")
            return False
    
    def get_recent_emails(self, limit: int = 50) -> List[Email]:
        """Récupère les emails récents."""
        if self.mock_mode:
            return self._generate_mock_emails(limit)
        
        if not self.authenticated or not self.service:
            logger.error("Client Gmail non authentifié")
            return []
        
        try:
            # Requête pour récupérer les emails
            results = self.service.users().messages().list(
                userId='me',
                maxResults=limit,
                q='in:inbox'  # Boîte de réception uniquement
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            logger.info(f"Récupération de {len(messages)} emails...")
            
            for i, message in enumerate(messages):
                try:
                    email_data = self._get_email_details(message['id'])
                    if email_data:
                        emails.append(email_data)
                    
                    # Log de progression
                    if (i + 1) % 10 == 0:
                        logger.info(f"Traité {i + 1}/{len(messages)} emails")
                        
                except Exception as e:
                    logger.error(f"Erreur traitement email {message['id']}: {e}")
                    continue
            
            logger.info(f"{len(emails)} emails récupérés depuis Gmail")
            return emails
        
        except Exception as e:
            logger.error(f"Erreur récupération emails: {e}")
            return []
    
    def _get_email_details(self, message_id: str) -> Optional[Email]:
        """Récupère les détails d'un email."""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            payload = message['payload']
            headers = payload.get('headers', [])
            
            # Extraire les headers
            subject = ""
            sender = ""
            recipient = ""
            date_str = ""
            
            for header in headers:
                name = header['name'].lower()
                if name == 'subject':
                    subject = header['value']
                elif name == 'from':
                    sender = header['value']
                elif name == 'to':
                    recipient = header['value']
                elif name == 'date':
                    date_str = header['value']
            
            # Extraire le corps
            body = self._extract_body(payload)
            snippet = message.get('snippet', '')
            
            # Convertir la date en datetime naive
            received_date = self._parse_email_date(date_str)
            
            # Vérifier si lu
            labels = message.get('labelIds', [])
            is_read = 'UNREAD' not in labels
            
            # Extraire les pièces jointes
            attachments = self._extract_attachments(payload)
            
            return Email(
                id=message_id,
                subject=subject or "(Aucun sujet)",
                sender=sender,
                recipient=recipient,
                received_date=received_date,
                body=body or snippet,
                labels=labels,
                thread_id=message.get('threadId', ''),
                snippet=snippet,
                is_read=is_read,
                attachments=attachments
            )
        
        except Exception as e:
            logger.error(f"Erreur détails email {message_id}: {e}")
            return None
    
    def _parse_email_date(self, date_str: str) -> datetime:
        """Parse une date d'email et la convertit en datetime naive local."""
        try:
            if not date_str:
                return datetime.now()
            
            # Parser la date avec timezone
            parsed_date = parsedate_to_datetime(date_str)
            
            # Convertir en timestamp puis en datetime local naive
            if parsed_date.tzinfo is not None:
                timestamp = parsed_date.timestamp()
                local_date = datetime.fromtimestamp(timestamp)
                return local_date
            else:
                return parsed_date
                
        except Exception as e:
            logger.error(f"Erreur parsing date '{date_str}': {e}")
            return datetime.now()
    
    def _extract_body(self, payload) -> str:
        """Extrait le corps de l'email."""
        body = ""
        
        try:
            if 'parts' in payload:
                # Email multipart
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            data = part['body']['data']
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
                    elif part['mimeType'] == 'text/html' and not body:
                        if 'data' in part['body']:
                            data = part['body']['data']
                            html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                            # Nettoyer le HTML basiquement
                            body = self._clean_html(html_body)
            else:
                # Email simple
                if payload['mimeType'] == 'text/plain' and 'data' in payload['body']:
                    data = payload['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                elif payload['mimeType'] == 'text/html' and 'data' in payload['body']:
                    data = payload['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                    body = self._clean_html(html_body)
        
        except Exception as e:
            logger.error(f"Erreur extraction body: {e}")
        
        return body[:2000] if body else ""  # Limiter la taille
    
    def _clean_html(self, html_content: str) -> str:
        """Nettoie le contenu HTML pour extraire le texte."""
        try:
            import re
            # Supprimer les balises HTML
            text = re.sub(r'<[^>]+>', '', html_content)
            # Nettoyer les entités HTML communes
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&amp;', '&')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&quot;', '"')
            # Supprimer les espaces multiples
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except:
            return html_content
    
    def _extract_attachments(self, payload) -> List[dict]:
        """Extrait les informations des pièces jointes."""
        attachments = []
        
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if 'filename' in part and part['filename']:
                        size = part['body'].get('size', 0)
                        # Convertir la taille en format lisible
                        size_str = self._format_file_size(size)
                        
                        attachment = {
                            'filename': part['filename'],
                            'mimeType': part['mimeType'],
                            'size': size_str,
                            'attachment_id': part['body'].get('attachmentId', '')
                        }
                        attachments.append(attachment)
        
        except Exception as e:
            logger.error(f"Erreur extraction pièces jointes: {e}")
        
        return attachments
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formate la taille d'un fichier."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: Optional[List[str]] = None, 
                   bcc: Optional[List[str]] = None) -> bool:
        """Envoie un email."""
        if self.mock_mode:
            logger.info(f"Email simulé envoyé à {to}: {subject}")
            return True
        
        if not self.authenticated or not self.service:
            logger.error("Client Gmail non authentifié")
            return False
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Créer le message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            # Ajouter le corps
            message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Encoder le message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Envoyer
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email envoyé avec succès à {to}, ID: {send_result['id']}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            return False
    
    def mark_as_read(self, email_id: str) -> bool:
        """Marque un email comme lu."""
        if self.mock_mode:
            logger.info(f"Email {email_id} marqué comme lu (simulé)")
            return True
        
        if not self.authenticated or not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"Email {email_id} marqué comme lu")
            return True
        
        except Exception as e:
            logger.error(f"Erreur marquage lu {email_id}: {e}")
            return False
    
    def archive_email(self, email_id: str) -> bool:
        """Archive un email."""
        if self.mock_mode:
            logger.info(f"Email {email_id} archivé (simulé)")
            return True
        
        if not self.authenticated or not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            
            logger.info(f"Email {email_id} archivé")
            return True
        
        except Exception as e:
            logger.error(f"Erreur archivage {email_id}: {e}")
            return False
    
    def delete_email(self, email_id: str) -> bool:
        """Supprime un email."""
        if self.mock_mode:
            logger.info(f"Email {email_id} supprimé (simulé)")
            return True
        
        if not self.authenticated or not self.service:
            return False
        
        try:
            self.service.users().messages().delete(
                userId='me',
                id=email_id
            ).execute()
            
            logger.info(f"Email {email_id} supprimé")
            return True
        
        except Exception as e:
            logger.error(f"Erreur suppression {email_id}: {e}")
            return False
    
    def search_emails(self, query: str, max_results: int = 50) -> List[Email]:
        """Recherche des emails selon une requête."""
        if self.mock_mode:
            return self._generate_mock_emails(max_results)
        
        if not self.authenticated or not self.service:
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            logger.info(f"Recherche '{query}': {len(emails)} résultats")
            return emails
        
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []
    
    def get_connection_status(self) -> dict:
        """Retourne le statut de la connexion."""
        return {
            'authenticated': self.authenticated,
            'mock_mode': self.mock_mode,
            'credentials_file': self.credentials_file,
            'has_service': self.service is not None,
            'last_sync': datetime.now().isoformat() if self.authenticated else None
        }
    
    # Méthodes mock pour les tests
    def _generate_mock_emails(self, limit: int) -> List[Email]:
        """Génère des emails de test."""
        mock_emails = []
        
        email_templates = [
            {
                'subject': 'Candidature pour le poste de développeur IA',
                'body': 'Bonjour, je vous envoie ma candidature pour le poste de développeur IA. Vous trouverez mon CV en pièce jointe.',
                'sender': 'candidat@example.com',
            },
            {
                'subject': 'Demande de rendez-vous - Projet IA',
                'body': 'Bonjour, pourriez-vous me proposer un créneau pour discuter de votre projet IA ? Je suis disponible cette semaine.',
                'sender': 'client@entreprise.com',
            },
            {
                'subject': 'Problème technique urgent - API',
                'body': 'Bonjour, nous rencontrons un problème critique avec notre API. Pourriez-vous nous aider rapidement ?',
                'sender': 'support@client.com',
            }
        ]
        
        for i in range(min(limit, 20)):
            template = email_templates[i % len(email_templates)]
            hours_ago = i * 2
            received_date = datetime.now() - timedelta(hours=hours_ago)
            
            email = Email(
                id=f"mock_{i}",
                subject=template['subject'],
                body=template['body'],
                sender=template['sender'],
                received_date=received_date,
                is_read=(i % 3 != 0)
            )
            mock_emails.append(email)
        
        return mock_emails