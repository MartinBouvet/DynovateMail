#!/usr/bin/env python3
"""
Client Gmail CORRIGÉ avec rendu HTML complet et images intégrées.
"""
import logging
import os
import base64
import pickle
import html
import re
from typing import List, Optional, Tuple
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

from models.email_model import Email, EmailAttachment

logger = logging.getLogger(__name__)

class GmailClient:
    """Client Gmail CORRIGÉ pour rendu HTML complet avec images."""
    
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
        
        # Cache pour les images intégrées
        self.image_cache = {}
        
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
        """Récupère les emails récents avec contenu HTML complet."""
        if self.mock_mode:
            logger.warning("Mode mock activé - aucun vrai email ne sera récupéré")
            return []
        
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
                    if (i + 1) % 5 == 0:
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
        """Récupère les détails COMPLETS d'un email avec HTML et images."""
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
            
            # Extraire le corps avec HTML et les pièces jointes
            html_content, plain_content, attachments = self._extract_content_and_attachments(payload, message_id)
            
            # Préférer le HTML si disponible, sinon plain text
            body = html_content if html_content else plain_content
            
            snippet = message.get('snippet', '')
            
            # Convertir la date en datetime naive
            received_date = self._parse_email_date(date_str)
            
            # Vérifier si lu
            labels = message.get('labelIds', [])
            is_read = 'UNREAD' not in labels
            
            email = Email(
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
            
            # Ajouter un attribut pour indiquer si c'est du HTML
            email.is_html = bool(html_content)
            
            return email
        
        except Exception as e:
            logger.error(f"Erreur détails email {message_id}: {e}")
            return None
    
    def _extract_content_and_attachments(self, payload, message_id: str) -> Tuple[str, str, List[EmailAttachment]]:
        """Extrait le contenu HTML/text et les pièces jointes."""
        html_content = ""
        plain_content = ""
        attachments = []
        inline_images = {}
        
        try:
            # Fonction récursive pour traiter toutes les parties
            def process_part(part, part_id=""):
                nonlocal html_content, plain_content, attachments, inline_images
                
                mime_type = part.get('mimeType', '')
                filename = part.get('filename', '')
                headers = part.get('headers', [])
                
                # Récupérer le Content-ID pour les images inline
                content_id = None
                content_disposition = None
                for header in headers:
                    if header['name'].lower() == 'content-id':
                        content_id = header['value'].strip('<>')
                    elif header['name'].lower() == 'content-disposition':
                        content_disposition = header['value']
                
                # Si c'est une pièce jointe ou image inline
                if filename or (mime_type.startswith('image/') and content_id):
                    attachment = self._create_attachment(part, message_id, part_id)
                    if attachment:
                        attachments.append(attachment)
                        
                        # Si c'est une image inline, la télécharger pour l'intégrer
                        if content_id and mime_type.startswith('image/'):
                            image_data = self._download_inline_image(message_id, attachment.attachment_id)
                            if image_data:
                                # Créer une data URL
                                data_url = f"data:{mime_type};base64," + base64.b64encode(image_data).decode()
                                inline_images[content_id] = data_url
                                # Aussi essayer avec cid: prefix
                                inline_images[f"cid:{content_id}"] = data_url
                
                # Si c'est du contenu textuel
                elif mime_type in ['text/plain', 'text/html']:
                    part_content = self._extract_text_from_part(part)
                    if part_content:
                        if mime_type == 'text/html':
                            if html_content:
                                html_content += "\n\n" + part_content
                            else:
                                html_content = part_content
                        else:  # text/plain
                            if plain_content:
                                plain_content += "\n\n" + part_content
                            else:
                                plain_content = part_content
                
                # Traiter les parties imbriquées
                if 'parts' in part:
                    for i, subpart in enumerate(part['parts']):
                        sub_part_id = f"{part_id}.{i}" if part_id else str(i)
                        process_part(subpart, sub_part_id)
            
            # Commencer le traitement
            process_part(payload)
            
            # Intégrer les images inline dans le HTML
            if html_content and inline_images:
                html_content = self._integrate_inline_images(html_content, inline_images)
            
            return html_content.strip(), plain_content.strip(), attachments
            
        except Exception as e:
            logger.error(f"Erreur extraction contenu: {e}")
            return "", "", []
    
    def _download_inline_image(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """Télécharge une image inline pour l'intégrer."""
        try:
            if not attachment_id:
                return None
                
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            data = attachment['data']
            return base64.urlsafe_b64decode(data)
            
        except Exception as e:
            logger.error(f"Erreur téléchargement image inline: {e}")
            return None
    
    def _integrate_inline_images(self, html_content: str, inline_images: dict) -> str:
        """Intègre les images inline dans le HTML."""
        try:
            # Remplacer les références cid: par les data URLs
            for cid, data_url in inline_images.items():
                # Plusieurs patterns possibles
                patterns = [
                    f'src="cid:{cid}"',
                    f"src='cid:{cid}'",
                    f'src="cid:{cid.strip()}"',
                    f"src='cid:{cid.strip()}'",
                    f'src="{cid}"',
                    f"src='{cid}'"
                ]
                
                for pattern in patterns:
                    html_content = html_content.replace(pattern, f'src="{data_url}"')
            
            # Aussi traiter les background-image en CSS
            for cid, data_url in inline_images.items():
                css_patterns = [
                    f'background-image:url(cid:{cid})',
                    f'background-image: url(cid:{cid})',
                    f"background-image:url('cid:{cid}')",
                    f'background-image:url("cid:{cid}")'
                ]
                
                for pattern in css_patterns:
                    html_content = html_content.replace(pattern, f'background-image:url("{data_url}")')
            
            return html_content
            
        except Exception as e:
            logger.error(f"Erreur intégration images: {e}")
            return html_content
    
    def _extract_text_from_part(self, part) -> str:
        """Extrait le texte d'une partie d'email."""
        try:
            body_data = part.get('body', {}).get('data')
            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode('utf-8')
                return decoded
            return ""
        except Exception as e:
            logger.error(f"Erreur extraction texte: {e}")
            return ""
    
    def _create_attachment(self, part, message_id: str, part_id: str) -> Optional[EmailAttachment]:
        """Crée un objet EmailAttachment."""
        try:
            filename = part.get('filename', '')
            mime_type = part.get('mimeType', '')
            
            if not filename and not mime_type.startswith('image/'):
                return None
            
            # Pour les images inline sans filename
            if not filename and mime_type.startswith('image/'):
                extension = mime_type.split('/')[-1]
                filename = f"image_inline.{extension}"
            
            # Informations sur la taille
            body = part.get('body', {})
            size_bytes = body.get('size', 0)
            attachment_id = body.get('attachmentId', '')
            
            # Formater la taille
            size_str = self._format_file_size(size_bytes)
            
            return EmailAttachment(
                filename=filename,
                mime_type=mime_type,
                size=size_str,
                size_bytes=size_bytes,
                attachment_id=attachment_id,
                part_id=part_id,
                downloadable=bool(attachment_id)
            )
            
        except Exception as e:
            logger.error(f"Erreur création pièce jointe: {e}")
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
    
    def download_attachment(self, message_id: str, attachment_id: str, filename: str) -> Optional[bytes]:
        """Télécharge une pièce jointe."""
        if self.mock_mode or not self.authenticated or not self.service:
            return None
        
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            data = attachment['data']
            file_data = base64.urlsafe_b64decode(data)
            
            logger.info(f"Pièce jointe {filename} téléchargée ({len(file_data)} bytes)")
            return file_data
            
        except Exception as e:
            logger.error(f"Erreur téléchargement pièce jointe: {e}")
            return None
    
    def save_attachment(self, message_id: str, attachment_id: str, filename: str, save_path: str = None) -> bool:
        """Sauvegarde une pièce jointe sur le disque."""
        try:
            if not save_path:
                save_path = Path.home() / "Downloads" / filename
            else:
                save_path = Path(save_path)
            
            file_data = self.download_attachment(message_id, attachment_id, filename)
            if not file_data:
                return False
            
            # Créer le dossier si nécessaire
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Éviter l'écrasement
            if save_path.exists():
                base = save_path.stem
                ext = save_path.suffix
                counter = 1
                while save_path.exists():
                    save_path = save_path.parent / f"{base}_{counter}{ext}"
                    counter += 1
            
            # Sauvegarder
            with open(save_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Pièce jointe sauvegardée: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde pièce jointe: {e}")
            return False
    
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
            return []
        
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