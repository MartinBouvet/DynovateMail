#!/usr/bin/env python3
"""
Client Gmail CORRIGÉ - VRAIS EMAILS UNIQUEMENT + gestion archives/supprimés.
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
    """Client Gmail CORRIGÉ - VRAIS EMAILS UNIQUEMENT."""
    
    def __init__(self, credentials_file: str = "client_secret.json", mock_mode: bool = False):
        """
        Initialise le client Gmail - FORCE MODE PRODUCTION.
        """
        self.credentials_file = credentials_file
        # FORCER LE MODE PRODUCTION - JAMAIS DE MOCK
        self.mock_mode = False  # TOUJOURS False
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
            logger.error("ERREUR FATALE: Gmail API non disponible - installez google-api-python-client")
            raise ImportError("Gmail API requis pour fonctionner")
        
        logger.info("Client Gmail PRODUCTION UNIQUEMENT initialisé")
        self.authenticate()
    
    def authenticate(self) -> bool:
        """Authentifie l'utilisateur avec Gmail - OBLIGATOIRE."""
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
                        logger.error(f"ERREUR: Fichier credentials manquant: {self.credentials_file}")
                        raise FileNotFoundError(f"Fichier {self.credentials_file} requis")
                    
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
            logger.info("✅ Service Gmail authentifié avec succès")
            return True
        
        except Exception as e:
            logger.error(f"ERREUR FATALE authentification Gmail: {e}")
            raise e
    
    def get_recent_emails(self, limit: int = 50, label_id: str = "INBOX") -> List[Email]:
        """Récupère les emails réels depuis Gmail."""
        if not self.authenticated or not self.service:
            logger.error("Client Gmail non authentifié")
            raise RuntimeError("Gmail non authentifié")
        
        try:
            # Construire la requête selon le label
            query_params = {
                'userId': 'me',
                'maxResults': limit
            }
            
            if label_id == "INBOX":
                query_params['q'] = 'in:inbox'
            elif label_id == "SENT":
                query_params['q'] = 'in:sent'
            elif label_id == "DRAFT":
                query_params['q'] = 'in:draft'
            elif label_id == "TRASH":
                query_params['q'] = 'in:trash'
            elif label_id == "SPAM":
                query_params['q'] = 'in:spam'
            elif label_id == "ARCHIVED":
                query_params['q'] = '-in:inbox -in:trash -in:spam'
            else:
                query_params['labelIds'] = [label_id]
            
            # Requête Gmail API
            results = self.service.users().messages().list(**query_params).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            logger.info(f"Récupération de {len(messages)} emails RÉELS depuis {label_id}...")
            
            for i, message in enumerate(messages):
                try:
                    email_data = self._get_email_details(message['id'])
                    if email_data:
                        emails.append(email_data)
                    
                    # Log de progression
                    if (i + 1) % 5 == 0:
                        logger.info(f"Traité {i + 1}/{len(messages)} emails réels")
                        
                except Exception as e:
                    logger.error(f"Erreur traitement email {message['id']}: {e}")
                    continue
            
            logger.info(f"✅ {len(emails)} emails RÉELS récupérés depuis {label_id}")
            return emails
        
        except Exception as e:
            logger.error(f"Erreur récupération emails: {e}")
            raise e
    
    def get_inbox_emails(self, limit: int = 50) -> List[Email]:
        """Récupère les emails de la boîte de réception."""
        return self.get_recent_emails(limit, "INBOX")
    
    def get_sent_emails(self, limit: int = 50) -> List[Email]:
        """Récupère les emails envoyés."""
        return self.get_recent_emails(limit, "SENT")
    
    def get_archived_emails(self, limit: int = 50) -> List[Email]:
        """Récupère les emails archivés."""
        return self.get_recent_emails(limit, "ARCHIVED")
    
    def get_trash_emails(self, limit: int = 50) -> List[Email]:
        """Récupère les emails supprimés."""
        return self.get_recent_emails(limit, "TRASH")
    
    def get_spam_emails(self, limit: int = 50) -> List[Email]:
        """Récupère les emails spam."""
        return self.get_recent_emails(limit, "SPAM")
    
    def _get_email_details(self, message_id: str) -> Optional[Email]:
        """Récupère les détails COMPLETS d'un email réel."""
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
            is_sent = 'SENT' in labels
            
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
                is_sent=is_sent,
                attachments=attachments
            )
            
            # Ajouter un attribut pour indiquer si c'est du HTML
            email.is_html = bool(html_content)
            email.plain_text_body = plain_content
            
            return email
        
        except Exception as e:
            logger.error(f"Erreur détails email {message_id}: {e}")
            return None
    
    def save_attachment(self, message_id: str, attachment_id: str, filename: str, save_path: str = None) -> bool:
        """Sauvegarde une pièce jointe sur le disque - CORRIGÉE."""
        try:
            if not self.authenticated or not self.service:
                logger.error("Gmail non authentifié")
                return False
            
            # Définir le chemin de sauvegarde
            if not save_path:
                # Utiliser le dossier Downloads par défaut
                downloads_dir = Path.home() / "Downloads"
                downloads_dir.mkdir(exist_ok=True)
                save_path = downloads_dir / filename
            else:
                save_path = Path(save_path)
            
            # Télécharger la pièce jointe
            file_data = self.download_attachment(message_id, attachment_id, filename)
            if not file_data:
                logger.error("Impossible de télécharger la pièce jointe")
                return False
            
            # Créer le dossier parent si nécessaire
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Éviter l'écrasement en ajoutant un numéro
            original_path = save_path
            counter = 1
            while save_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                save_path = original_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Sauvegarder le fichier
            with open(save_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"✅ Pièce jointe sauvegardée: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde pièce jointe: {e}")
            return False
    
    def download_attachment(self, message_id: str, attachment_id: str, filename: str) -> Optional[bytes]:
        """Télécharge une pièce jointe."""
        if not self.authenticated or not self.service:
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
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: Optional[List[str]] = None, 
                   bcc: Optional[List[str]] = None) -> bool:
        """Envoie un email RÉEL."""
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
            
            # Envoyer via Gmail API
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"✅ Email RÉEL envoyé à {to}, ID: {send_result['id']}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            return False
    
    def mark_as_read(self, email_id: str) -> bool:
        """Marque un email comme lu."""
        if not self.authenticated or not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"✅ Email {email_id} marqué comme lu")
            return True
        
        except Exception as e:
            logger.error(f"Erreur marquage lu {email_id}: {e}")
            return False
    
    def archive_email(self, email_id: str) -> bool:
        """Archive un email (retire de INBOX)."""
        if not self.authenticated or not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            
            logger.info(f"✅ Email {email_id} archivé")
            return True
        
        except Exception as e:
            logger.error(f"Erreur archivage {email_id}: {e}")
            return False
    
    def delete_email(self, email_id: str) -> bool:
        """Déplace un email vers la corbeille."""
        if not self.authenticated or not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': ['TRASH'], 'removeLabelIds': ['INBOX']}
            ).execute()
            
            logger.info(f"✅ Email {email_id} déplacé vers la corbeille")
            return True
        
        except Exception as e:
            logger.error(f"Erreur suppression {email_id}: {e}")
            return False
    
    def restore_from_trash(self, email_id: str) -> bool:
        """Restaure un email depuis la corbeille."""
        if not self.authenticated or not self.service:
            return False
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['TRASH'], 'addLabelIds': ['INBOX']}
            ).execute()
            
            logger.info(f"✅ Email {email_id} restauré depuis la corbeille")
            return True
        
        except Exception as e:
            logger.error(f"Erreur restauration {email_id}: {e}")
            return False
    
    def permanently_delete_email(self, email_id: str) -> bool:
        """Supprime définitivement un email."""
        if not self.authenticated or not self.service:
            return False
        
        try:
            self.service.users().messages().delete(
                userId='me',
                id=email_id
            ).execute()
            
            logger.info(f"✅ Email {email_id} supprimé définitivement")
            return True
        
        except Exception as e:
            logger.error(f"Erreur suppression définitive {email_id}: {e}")
            return False
    
    def search_emails(self, query: str, max_results: int = 50) -> List[Email]:
        """Recherche des emails selon une requête."""
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
            'mock_mode': False,  # TOUJOURS False
            'credentials_file': self.credentials_file,
            'has_service': self.service is not None,
            'last_sync': datetime.now().isoformat() if self.authenticated else None,
            'real_gmail_only': True  # NOUVEAU : Confirme que seuls les vrais emails sont utilisés
        }
    
    # === MÉTHODES PRIVÉES CONSERVÉES ===
    
    def _extract_content_and_attachments(self, payload, message_id: str) -> Tuple[str, str, List[EmailAttachment]]:
        """Extrait le contenu HTML/text et les pièces jointes."""
        html_content = ""
        plain_content = ""
        attachments = []
        inline_images = {}
        
        try:
            def process_part(part, part_id=""):
                nonlocal html_content, plain_content, attachments, inline_images
                
                mime_type = part.get('mimeType', '')
                filename = part.get('filename', '')
                headers = part.get('headers', [])
                
                content_id = None
                content_disposition = None
                for header in headers:
                    if header['name'].lower() == 'content-id':
                        content_id = header['value'].strip('<>')
                    elif header['name'].lower() == 'content-disposition':
                        content_disposition = header['value']
                
                if filename or (mime_type.startswith('image/') and content_id):
                    attachment = self._create_attachment(part, message_id, part_id)
                    if attachment:
                        attachments.append(attachment)
                        
                        if content_id and mime_type.startswith('image/'):
                            image_data = self._download_inline_image(message_id, attachment.attachment_id)
                            if image_data:
                                data_url = f"data:{mime_type};base64," + base64.b64encode(image_data).decode()
                                inline_images[content_id] = data_url
                                inline_images[f"cid:{content_id}"] = data_url
                
                elif mime_type in ['text/plain', 'text/html']:
                    part_content = self._extract_text_from_part(part)
                    if part_content:
                        if mime_type == 'text/html':
                            if html_content:
                                html_content += "\n\n" + part_content
                            else:
                                html_content = part_content
                        else:
                            if plain_content:
                                plain_content += "\n\n" + part_content
                            else:
                                plain_content = part_content
                
                if 'parts' in part:
                    for i, subpart in enumerate(part['parts']):
                        sub_part_id = f"{part_id}.{i}" if part_id else str(i)
                        process_part(subpart, sub_part_id)
            
            process_part(payload)
            
            if html_content and inline_images:
                html_content = self._integrate_inline_images(html_content, inline_images)
            
            return html_content.strip(), plain_content.strip(), attachments
            
        except Exception as e:
            logger.error(f"Erreur extraction contenu: {e}")
            return "", "", []
    
    def _download_inline_image(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """Télécharge une image inline."""
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
            for cid, data_url in inline_images.items():
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
            
            if not filename and mime_type.startswith('image/'):
                extension = mime_type.split('/')[-1]
                filename = f"image_inline.{extension}"
            
            body = part.get('body', {})
            size_bytes = body.get('size', 0)
            attachment_id = body.get('attachmentId', '')
            
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
        """Parse une date d'email."""
        try:
            if not date_str:
                return datetime.now()
            
            parsed_date = parsedate_to_datetime(date_str)
            
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