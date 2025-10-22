#!/usr/bin/env python3
"""
Vue détail email - VERSION CORRIGÉE
Affichage parfait des emails avec images, HTML responsive, et formatage optimal
"""
import logging
import re
import base64
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.gmail_client import GmailClient
from app.ai_processor import AIProcessor
from app.models.email_model import Email

logger = logging.getLogger(__name__)

class EmailDetailView(QWidget):
    """Vue détail email avec affichage correct des images et du HTML."""
    
    reply_requested = pyqtSignal(Email)
    forward_requested = pyqtSignal(Email)
    archive_requested = pyqtSignal(Email)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.current_email = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.setStyleSheet("QWidget { background-color: #ffffff; }")
        
        # Zone scrollable
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: #ffffff;
            }
        """)
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #ffffff;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Message vide initial
        empty_container = QWidget()
        empty_container.setStyleSheet("background-color: #ffffff;")
        empty_layout = QVBoxLayout(empty_container)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        
        self.empty_label = QLabel("📭 Sélectionnez un email pour le lire")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(QFont("Arial", 16))
        self.empty_label.setStyleSheet("""
            color: #5f6368; 
            padding: 100px; 
            background-color: #ffffff;
        """)
        empty_layout.addWidget(self.empty_label)
        
        self.content_layout.addWidget(empty_container)
        
        self.scroll.setWidget(self.content_widget)
        layout.addWidget(self.scroll)
    
    def show_email(self, email: Email):
        """Affiche un email avec images correctement intégrées."""
        self.current_email = email
        
        logger.info(f"📧 Affichage email: {email.subject[:50] if email.subject else 'Sans sujet'}")
        
        # Nettoyer le layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Container principal
        main_container = QWidget()
        main_container.setStyleSheet("background-color: #ffffff;")
        
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(24)
        
        # Sujet
        subject_label = QLabel(email.subject or "(Sans sujet)")
        subject_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        subject_label.setStyleSheet("color: #202124; background-color: transparent;")
        subject_label.setWordWrap(True)
        main_layout.addWidget(subject_label)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        btn_style = """
            QPushButton {
                background-color: #f1f3f4;
                border: none;
                border-radius: 20px;
                padding: 12px 28px;
                color: #3c4043;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e8eaed;
            }
        """
        
        reply_btn = QPushButton("↩️ Répondre")
        reply_btn.setFont(QFont("Arial", 13))
        reply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reply_btn.clicked.connect(self._on_reply)
        reply_btn.setStyleSheet(btn_style)
        actions_layout.addWidget(reply_btn)
        
        forward_btn = QPushButton("➡️ Transférer")
        forward_btn.setFont(QFont("Arial", 13))
        forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        forward_btn.clicked.connect(self._on_forward)
        forward_btn.setStyleSheet(btn_style)
        actions_layout.addWidget(forward_btn)
        
        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #dadce0; border: none;")
        main_layout.addWidget(separator)
        
        # Header (expéditeur + date)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        # Avatar
        avatar = QLabel(email.sender[0].upper() if email.sender else "?")
        avatar.setFixedSize(56, 56)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        avatar.setStyleSheet("""
            background-color: #000000;
            color: white;
            border-radius: 28px;
        """)
        header_layout.addWidget(avatar)
        
        # Info expéditeur
        sender_info = QVBoxLayout()
        sender_info.setSpacing(4)
        
        from_label = QLabel(email.sender)
        from_label.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        from_label.setStyleSheet("color: #202124; background-color: transparent;")
        sender_info.addWidget(from_label)
        
        to_me = QLabel("À moi")
        to_me.setFont(QFont("Arial", 13))
        to_me.setStyleSheet("color: #5f6368; background-color: transparent;")
        sender_info.addWidget(to_me)
        
        header_layout.addLayout(sender_info)
        header_layout.addStretch()
        
        # Date
        if email.received_date:
            date_str = self._format_date(email.received_date)
            date_label = QLabel(date_str)
            date_label.setFont(QFont("Arial", 13))
            date_label.setStyleSheet("color: #5f6368; background-color: transparent;")
            header_layout.addWidget(date_label)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)
        
        # Contenu email avec images
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 24px;
            }
        """)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(0)
        
        body_browser = QTextBrowser()
        body_browser.setOpenExternalLinks(True)
        body_browser.setFrameShape(QFrame.Shape.NoFrame)
        body_browser.setMinimumHeight(300)
        body_browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background-color: #ffffff;
                color: #202124;
                font-family: Arial, sans-serif;
                font-size: 15px;
                line-height: 1.8;
                padding: 0;
            }
        """)
        
        # Formater le contenu AVEC IMAGES
        if email.body:
            if self._is_html(email.body):
                clean_html = self._clean_html_with_images(email.body, email)
                body_browser.setHtml(clean_html)
            else:
                formatted = self._format_plain_text(email.body)
                body_browser.setHtml(formatted)
        elif email.snippet:
            body_browser.setHtml(f'<div style="color: #5f6368; font-style: italic; padding: 20px;">{email.snippet}</div>')
        else:
            body_browser.setHtml('<div style="color: #80868b; padding: 20px;">Aucun contenu disponible</div>')
        
        content_layout.addWidget(body_browser)
        main_layout.addWidget(content_frame)
        
        # Pièces jointes
        if email.has_attachments:
            att_frame = QFrame()
            att_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 16px 20px;
                }
            """)
            
            att_layout = QHBoxLayout(att_frame)
            att_layout.setSpacing(12)
            
            att_icon = QLabel("📎")
            att_icon.setFont(QFont("Arial", 18))
            att_layout.addWidget(att_icon)
            
            att_text = QLabel(f"{email.attachment_count} pièce(s) jointe(s)")
            att_text.setFont(QFont("Arial", 14))
            att_text.setStyleSheet("color: #3c4043; background-color: transparent;")
            att_layout.addWidget(att_text)
            
            att_layout.addStretch()
            main_layout.addWidget(att_frame)
        
        main_layout.addStretch()
        self.content_layout.addWidget(main_container)
    
    def _format_date(self, date):
        """Formate la date."""
        from datetime import datetime
        now = datetime.now()
        
        if date.date() == now.date():
            return date.strftime("%H:%M")
        elif date.year == now.year:
            return date.strftime("%d %b à %H:%M")
        else:
            return date.strftime("%d %b %Y")
    
    def _is_html(self, text: str) -> bool:
        """Détecte HTML."""
        return '<html' in text.lower() or '<div' in text.lower() or '<p>' in text.lower() or '<br' in text.lower()
    
    def _clean_html_with_images(self, html_content: str, email: Email) -> str:
        """
        Nettoie le HTML ET intègre les images en base64.
        C'EST LA FONCTION CLÉE qui résout tous les problèmes d'affichage.
        """
        
        # CSS moderne et responsive
        css = """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 15px;
                line-height: 1.6;
                color: #202124;
                background-color: #ffffff;
                padding: 0;
                margin: 0;
                max-width: 100%;
                overflow-x: hidden;
            }
            p {
                margin: 0 0 16px 0;
            }
            img {
                max-width: 100% !important;
                height: auto !important;
                display: block;
                margin: 16px 0;
                border-radius: 8px;
            }
            a {
                color: #000000;
                text-decoration: none;
                border-bottom: 1px solid #000000;
            }
            a:hover {
                opacity: 0.7;
            }
            table {
                border-collapse: collapse;
                max-width: 100% !important;
                width: 100% !important;
                margin: 20px 0;
                table-layout: fixed !important;
            }
            td, th {
                padding: 12px;
                border: 1px solid #e0e0e0;
                text-align: left;
                word-wrap: break-word !important;
                overflow-wrap: break-word !important;
            }
            /* FIX Instagram et emails avec layouts complexes */
            table table {
                width: 100% !important;
            }
            td[style*="vertical-align"] {
                vertical-align: top !important;
            }
            /* Fix pour les tables imbriquées */
            .gmail_quote {
                margin: 20px 0;
                padding-left: 20px;
                border-left: 4px solid #e0e0e0;
            }
            blockquote {
                border-left: 4px solid #e0e0e0;
                margin: 20px 0;
                padding-left: 20px;
                color: #5f6368;
                font-style: italic;
            }
            pre, code {
                background-color: #f1f3f4;
                padding: 12px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            h1, h2, h3, h4 {
                color: #202124;
                margin: 24px 0 12px 0;
                font-weight: 600;
            }
            h1 { font-size: 24px; }
            h2 { font-size: 20px; }
            h3 { font-size: 18px; }
            h4 { font-size: 16px; }
            ul, ol {
                margin: 16px 0;
                padding-left: 28px;
            }
            li {
                margin: 8px 0;
            }
            /* Forcer le responsive */
            div, span, p, td {
                max-width: 100% !important;
            }
            /* Fix pour les emails avec width fixes */
            [width] {
                width: auto !important;
                max-width: 100% !important;
            }
            /* Support mode sombre potentiel */
            @media (prefers-color-scheme: dark) {
                body {
                    background-color: #ffffff;
                    color: #202124;
                }
            }
        </style>
        """
        
        # Injecter le CSS
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head>{css}')
        elif '<html>' in html_content.lower():
            html_content = html_content.replace('<html>', f'<html><head>{css}</head>', 1)
            html_content = html_content.replace('<HTML>', f'<HTML><head>{css}</head>', 1)
        else:
            html_content = f'<!DOCTYPE html><html><head>{css}</head><body>{html_content}</body></html>'
        
        # CORRECTION CRITIQUE : Intégrer les images
        html_content = self._embed_images_correctly(html_content, email)
        
        return html_content
    
    def _embed_images_correctly(self, html_content: str, email: Email) -> str:
        """
        Intègre correctement les images en base64.
        Remplace les cid: par des data URIs.
        """
        try:
            if not hasattr(self.gmail_client, 'service') or not email.id:
                logger.warning("Service Gmail non disponible ou email sans ID")
                return html_content
            
            # Récupérer le message complet avec toutes les parties
            message = self.gmail_client.service.users().messages().get(
                userId='me',
                id=email.id,
                format='full'
            ).execute()
            
            # Extraire toutes les images
            images_map = {}
            self._extract_all_images(message.get('payload', {}), images_map)
            
            logger.info(f"📷 {len(images_map)} images trouvées dans l'email")
            
            # Remplacer chaque référence cid: par une data URI
            for cid, image_data in images_map.items():
                # Déterminer le type MIME de l'image
                mime_type = self._detect_image_type(image_data)
                
                # Créer la data URI
                data_uri = f'data:{mime_type};base64,{image_data}'
                
                # Remplacer dans le HTML - TOUS les formats possibles
                html_content = html_content.replace(f'cid:{cid}', data_uri)
                html_content = html_content.replace(f'"cid:{cid}"', f'"{data_uri}"')
                html_content = html_content.replace(f"'cid:{cid}'", f"'{data_uri}'")
                html_content = html_content.replace(f'src="cid:{cid}"', f'src="{data_uri}"')
                
                logger.info(f"✅ Image remplacée: cid:{cid[:20]}... -> data URI ({mime_type})")
            
            return html_content
        
        except Exception as e:
            logger.error(f"❌ Erreur intégration images: {e}")
            import traceback
            traceback.print_exc()
            return html_content
    
    def _extract_all_images(self, payload: dict, images_map: dict):
        """Extrait récursivement toutes les images du payload."""
        try:
            mime_type = payload.get('mimeType', '')
            
            # Si c'est une image
            if mime_type.startswith('image/'):
                headers = payload.get('headers', [])
                content_id = None
                
                # Chercher le Content-ID
                for header in headers:
                    if header.get('name', '').lower() == 'content-id':
                        content_id = header.get('value', '').strip('<>')
                        break
                
                # Récupérer les données
                body_data = payload.get('body', {}).get('data', '')
                
                if body_data and content_id:
                    images_map[content_id] = body_data
                    logger.info(f"📷 Image extraite: {content_id}")
                elif body_data:
                    # Image sans Content-ID, utiliser un ID généré
                    import hashlib
                    generated_id = hashlib.md5(body_data.encode()).hexdigest()[:12]
                    images_map[generated_id] = body_data
                    logger.info(f"📷 Image extraite (sans CID): {generated_id}")
            
            # Parcourir récursivement toutes les parties
            for part in payload.get('parts', []):
                self._extract_all_images(part, images_map)
        
        except Exception as e:
            logger.error(f"❌ Erreur extraction image: {e}")
    
    def _detect_image_type(self, base64_data: str) -> str:
        """Détecte le type MIME d'une image depuis ses données base64."""
        try:
            # Les premiers caractères en base64 indiquent le type de fichier
            if base64_data.startswith('/9j/'):
                return 'image/jpeg'
            elif base64_data.startswith('iVBORw'):
                return 'image/png'
            elif base64_data.startswith('R0lGOD'):
                return 'image/gif'
            elif base64_data.startswith('Qk'):
                return 'image/bmp'
            elif base64_data.startswith('SUkq') or base64_data.startswith('TU0A'):
                return 'image/tiff'
            elif base64_data.startswith('PD9xml') or base64_data.startswith('PHN2Zy'):
                return 'image/svg+xml'
            elif base64_data.startswith('UklGR'):
                return 'image/webp'
            else:
                # Par défaut, JPEG
                return 'image/jpeg'
        except:
            return 'image/jpeg'
    
    def _format_plain_text(self, text: str) -> str:
        """Formate le texte brut en HTML."""
        import html
        
        # Échapper HTML
        text = html.escape(text)
        
        # Paragraphes
        paragraphs = text.split('\n\n')
        formatted = []
        for p in paragraphs:
            if p.strip():
                p = p.replace('\n', '<br>')
                formatted.append(f'<p style="margin: 0 0 16px 0;">{p}</p>')
        
        html_text = '\n'.join(formatted)
        
        # URLs cliquables
        url_pattern = r'(https?://[^\s<>"]+)'
        html_text = re.sub(
            url_pattern, 
            r'<a href="\1" style="color: #000000; text-decoration: none; border-bottom: 1px solid #000000;">\1</a>', 
            html_text
        )
        
        # Emails cliquables
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        html_text = re.sub(
            email_pattern, 
            r'<a href="mailto:\1" style="color: #000000; text-decoration: none; border-bottom: 1px solid #000000;">\1</a>', 
            html_text
        )
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                font-size: 15px;
                line-height: 1.6;
                color: #202124;
                background-color: #ffffff;
                margin: 0;
                padding: 0;
            }}
            p {{
                margin: 0 0 16px 0;
            }}
            a {{
                color: #000000;
                text-decoration: none;
                border-bottom: 1px solid #000000;
            }}
            a:hover {{
                opacity: 0.7;
            }}
        </style>
        </head>
        <body>
        {html_text}
        </body>
        </html>
        '''
    
    def _on_reply(self):
        if self.current_email:
            self.reply_requested.emit(self.current_email)
    
    def _on_forward(self):
        if self.current_email:
            self.forward_requested.emit(self.current_email)
    
    def _on_archive(self):
        if self.current_email:
            self.archive_requested.emit(self.current_email)