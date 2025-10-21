#!/usr/bin/env python3
"""
Vue détail email - AFFICHAGE PARFAIT FINAL
"""
import logging
import re
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
    """Vue détail email - PARFAIT."""
    
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
        
        # Fond blanc partout
        self.setStyleSheet("QWidget { background-color: #ffffff; }")
        
        # Zone de scroll
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
        
        # Message vide
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
        """Affiche un email - PARFAIT."""
        self.current_email = email
        
        logger.info(f"📧 Affichage: {email.subject[:50]}")
        
        # Nettoyer
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Container principal - FOND BLANC
        main_container = QWidget()
        main_container.setStyleSheet("background-color: #ffffff;")
        
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(24)
        
        # Sujet en gros
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
        
        # Ligne de séparation
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #dadce0; border: none;")
        main_layout.addWidget(separator)
        
        # Header email (expéditeur + date)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        # Avatar coloré
        avatar = QLabel(email.sender[0].upper() if email.sender else "?")
        avatar.setFixedSize(56, 56)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        avatar.setStyleSheet("""
            background-color: #1a73e8;
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
        
        # Contenu email - ZONE DÉDIÉE AVEC FOND
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dadce0;
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
        
        # Formater le contenu
        if email.body:
            if self._is_html(email.body):
                clean_html = self._clean_html_final(email.body, email)
                body_browser.setHtml(clean_html)
            else:
                formatted = self._format_plain_text_final(email.body)
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
                    border: 1px solid #dadce0;
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
    
    def _clean_html_final(self, html_content: str, email: Email) -> str:
        """Nettoie le HTML - VERSION FINALE."""
        
        css = """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 15px;
                line-height: 1.8;
                color: #202124;
                background-color: #ffffff;
                padding: 0;
                margin: 0;
            }
            p {
                margin: 0 0 16px 0;
            }
            img {
                max-width: 100% !important;
                height: auto !important;
                display: block;
                margin: 20px 0;
                border-radius: 4px;
            }
            a {
                color: #1a73e8;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            table {
                border-collapse: collapse;
                max-width: 100%;
                margin: 20px 0;
            }
            td, th {
                padding: 10px;
                border: 1px solid #dadce0;
                text-align: left;
            }
            blockquote {
                border-left: 4px solid #dadce0;
                margin: 20px 0;
                padding-left: 20px;
                color: #5f6368;
                font-style: italic;
            }
            pre, code {
                background-color: #f1f3f4;
                padding: 12px;
                border-radius: 4px;
                font-family: monospace;
                font-size: 14px;
                overflow-x: auto;
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
        </style>
        """
        
        # Injecter le CSS
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head>{css}')
        elif '<html>' in html_content.lower():
            html_content = html_content.replace('<html>', f'<html><head>{css}</head>')
            html_content = html_content.replace('<HTML>', f'<HTML><head>{css}</head>')
        else:
            html_content = f'<html><head>{css}</head><body>{html_content}</body></html>'
        
        # Intégrer images
        html_content = self._embed_images(html_content, email)
        
        return html_content
    
    def _format_plain_text_final(self, text: str) -> str:
        """Formate texte brut - VERSION FINALE."""
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
            r'<a href="\1" style="color: #1a73e8; text-decoration: none;">\1</a>', 
            html_text
        )
        
        # Emails cliquables
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        html_text = re.sub(
            email_pattern, 
            r'<a href="mailto:\1" style="color: #1a73e8; text-decoration: none;">\1</a>', 
            html_text
        )
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 15px;
                line-height: 1.8;
                color: #202124;
                background-color: #ffffff;
                margin: 0;
                padding: 0;
            }}
            p {{
                margin: 0 0 16px 0;
            }}
            a {{
                color: #1a73e8;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
        </head>
        <body>
        {html_text}
        </body>
        </html>
        '''
    
    def _embed_images(self, html_content: str, email: Email) -> str:
        """Intègre images."""
        try:
            if not hasattr(self.gmail_client, 'service') or not email.id:
                return html_content
            
            message = self.gmail_client.service.users().messages().get(
                userId='me',
                id=email.id,
                format='full'
            ).execute()
            
            images = {}
            self._extract_images_recursive(message.get('payload', {}), images)
            
            for cid, image_data in images.items():
                # Type MIME
                if image_data.startswith('/9j/'):
                    mime_type = 'image/jpeg'
                elif image_data.startswith('iVBORw'):
                    mime_type = 'image/png'
                elif image_data.startswith('R0lGOD'):
                    mime_type = 'image/gif'
                else:
                    mime_type = 'image/jpeg'
                
                data_uri = f'data:{mime_type};base64,{image_data}'
                html_content = html_content.replace(f'cid:{cid}', data_uri)
            
            logger.info(f"✅ {len(images)} images")
        
        except Exception as e:
            logger.error(f"Erreur images: {e}")
        
        return html_content
    
    def _extract_images_recursive(self, payload: dict, images: dict):
        """Extrait images."""
        try:
            mime_type = payload.get('mimeType', '')
            
            if mime_type.startswith('image/'):
                headers = payload.get('headers', [])
                content_id = None
                
                for header in headers:
                    if header.get('name', '').lower() == 'content-id':
                        content_id = header.get('value', '').strip('<>')
                        break
                
                body_data = payload.get('body', {}).get('data', '')
                
                if body_data and content_id:
                    images[content_id] = body_data
            
            for part in payload.get('parts', []):
                self._extract_images_recursive(part, images)
        
        except Exception as e:
            logger.error(f"Erreur: {e}")
    
    def _on_reply(self):
        if self.current_email:
            self.reply_requested.emit(self.current_email)
    
    def _on_forward(self):
        if self.current_email:
            self.forward_requested.emit(self.current_email)
    
    def _on_archive(self):
        if self.current_email:
            self.archive_requested.emit(self.current_email)