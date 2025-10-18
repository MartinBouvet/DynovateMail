#!/usr/bin/env python3
"""
Vue détail email - VERSION CORRIGÉE COMPLÈTE
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
    """Vue détail d'un email."""
    
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
        
        # En-tête avec actions
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #fafafa; border-bottom: 1px solid #e5e7eb;")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 12, 25, 12)
        header_layout.setSpacing(10)
        
        self.subject_label = QLabel("Sélectionnez un email")
        self.subject_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.subject_label.setStyleSheet("color: #000000;")
        self.subject_label.setWordWrap(True)
        header_layout.addWidget(self.subject_label, 1)
        
        # Boutons d'action
        btn_style = """
            QPushButton {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 16px;
                color: #374151;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5b21b6;
                color: white;
                border-color: #5b21b6;
            }
        """
        
        self.reply_btn = QPushButton("↩️ Répondre")
        self.reply_btn.setFont(QFont("Arial", 12))
        self.reply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reply_btn.clicked.connect(self._on_reply)
        self.reply_btn.setStyleSheet(btn_style)
        header_layout.addWidget(self.reply_btn)
        
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.setFont(QFont("Arial", 12))
        self.forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forward_btn.clicked.connect(self._on_forward)
        self.forward_btn.setStyleSheet(btn_style)
        header_layout.addWidget(self.forward_btn)
        
        self.archive_btn = QPushButton("📥 Archiver")
        self.archive_btn.setFont(QFont("Arial", 12))
        self.archive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.archive_btn.clicked.connect(self._on_archive)
        self.archive_btn.setStyleSheet(btn_style)
        header_layout.addWidget(self.archive_btn)
        
        layout.addWidget(header)
        
        # Zone de scroll pour le contenu
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: #ffffff;")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(30, 25, 30, 25)
        self.content_layout.setSpacing(20)
        
        # Message vide
        self.empty_label = QLabel("📭 Sélectionnez un email pour le lire")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(QFont("Arial", 14))
        self.empty_label.setStyleSheet("color: #9ca3af; padding: 100px;")
        self.content_layout.addWidget(self.empty_label)
        
        self.scroll.setWidget(self.content_widget)
        layout.addWidget(self.scroll)
    
    def show_email(self, email: Email):
        """Affiche un email."""
        self.current_email = email
        
        logger.info(f"📧 Affichage: {email.subject[:50]}")
        
        # Mettre à jour le sujet
        self.subject_label.setText(email.subject or "(Sans sujet)")
        
        # Nettoyer le contenu
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Informations expéditeur
        sender_frame = QFrame()
        sender_frame.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        sender_layout = QVBoxLayout(sender_frame)
        sender_layout.setSpacing(8)
        
        # De
        from_label = QLabel(f"<b>De:</b> {email.sender}")
        from_label.setFont(QFont("Arial", 12))
        from_label.setStyleSheet("color: #1f2937;")
        from_label.setWordWrap(True)
        sender_layout.addWidget(from_label)
        
        # À
        to_label = QLabel(f"<b>À:</b> {email.to}")
        to_label.setFont(QFont("Arial", 12))
        to_label.setStyleSheet("color: #1f2937;")
        to_label.setWordWrap(True)
        sender_layout.addWidget(to_label)
        
        # Date
        if email.received_date:
            date_str = email.received_date.strftime("%d/%m/%Y à %H:%M")
            date_label = QLabel(f"<b>Date:</b> {date_str}")
            date_label.setFont(QFont("Arial", 12))
            date_label.setStyleSheet("color: #6b7280;")
            sender_layout.addWidget(date_label)
        
        self.content_layout.addWidget(sender_frame)
        
        # Contenu de l'email
        body_browser = QTextBrowser()
        body_browser.setOpenExternalLinks(True)
        body_browser.setMinimumHeight(400)
        body_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 20px;
                background-color: #ffffff;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        
        # Formater le contenu
        if email.body:
            # Détecter si c'est du HTML
            if '<html' in email.body.lower() or '<div' in email.body.lower():
                # C'est du HTML
                clean_html = self._clean_html(email.body)
                body_browser.setHtml(clean_html)
            else:
                # C'est du texte brut
                formatted_text = self._format_plain_text(email.body)
                body_browser.setHtml(formatted_text)
        elif email.snippet:
            body_browser.setHtml(f'<div style="color: #6b7280;">{email.snippet}</div>')
        else:
            body_browser.setHtml('<div style="color: #9ca3af;">Aucun contenu disponible</div>')
        
        self.content_layout.addWidget(body_browser)
        
        # Pièces jointes
        if email.has_attachments:
            attachments_label = QLabel(f"📎 {email.attachment_count} pièce(s) jointe(s)")
            attachments_label.setFont(QFont("Arial", 12))
            attachments_label.setStyleSheet("""
                color: #5b21b6;
                padding: 10px;
                background-color: #ede9fe;
                border-radius: 6px;
            """)
            self.content_layout.addWidget(attachments_label)
        
        # Analyse IA
        if hasattr(email, 'ai_analysis') and email.ai_analysis:
            self._show_ai_analysis(email.ai_analysis)
        
        self.content_layout.addStretch()
    
    def _clean_html(self, html_content: str) -> str:
        """Nettoie et sécurise le HTML."""
        # Wrapper CSS pour un rendu propre
        css = """
        <style>
            body {
                font-family: Arial, sans-serif;
                font-size: 13px;
                line-height: 1.6;
                color: #1f2937;
                max-width: 100%;
                overflow-wrap: break-word;
            }
            img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 10px 0;
            }
            table {
                border-collapse: collapse;
                max-width: 100%;
            }
            a {
                color: #5b21b6;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            blockquote {
                border-left: 3px solid #e5e7eb;
                margin: 10px 0;
                padding-left: 15px;
                color: #6b7280;
            }
        </style>
        """
        
        # Ajouter le CSS
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head>{css}')
        elif '<html>' in html_content:
            html_content = html_content.replace('<html>', f'<html><head>{css}</head>')
        else:
            html_content = f'<html><head>{css}</head><body>{html_content}</body></html>'
        
        # Intégrer les images inline
        html_content = self._embed_images(html_content, self.current_email)
        
        return html_content
    
    def _format_plain_text(self, text: str) -> str:
        """Formate du texte brut en HTML."""
        import html
        
        # Échapper le HTML
        text = html.escape(text)
        
        # Remplacer les retours à la ligne
        text = text.replace('\n', '<br>')
        
        # Détecter les URLs et les transformer en liens
        url_pattern = r'(https?://[^\s<>"]+)'
        text = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)
        
        # Wrapper avec style
        return f'''
        <html>
        <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 13px;
                line-height: 1.6;
                color: #1f2937;
            }}
            a {{
                color: #5b21b6;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
        </head>
        <body>{text}</body>
        </html>
        '''
    
    def _embed_images(self, html_content: str, email: Email) -> str:
        """Intègre les images inline."""
        try:
            if not hasattr(self.gmail_client, 'service') or not email.id:
                return html_content
            
            # Récupérer le message complet
            message = self.gmail_client.service.users().messages().get(
                userId='me',
                id=email.id,
                format='full'
            ).execute()
            
            # Extraire les images
            images = self._extract_images(message.get('payload', {}))
            
            # Remplacer les CID par des data URIs
            for cid, image_data in images.items():
                cid_pattern = f'cid:{cid}'
                
                # Détecter le type MIME
                if image_data.startswith('/9j/'):
                    mime_type = 'image/jpeg'
                elif image_data.startswith('iVBORw'):
                    mime_type = 'image/png'
                elif image_data.startswith('R0lGOD'):
                    mime_type = 'image/gif'
                else:
                    mime_type = 'image/jpeg'
                
                data_uri = f'data:{mime_type};base64,{image_data}'
                
                # Remplacer dans le HTML
                html_content = html_content.replace(f'src="{cid_pattern}"', f'src="{data_uri}"')
                html_content = html_content.replace(f"src='{cid_pattern}'", f'src="{data_uri}"')
            
            logger.info(f"✅ {len(images)} images inline intégrées")
        
        except Exception as e:
            logger.error(f"Erreur images: {e}")
        
        return html_content
    
    def _extract_images(self, payload: dict, images: dict = None) -> dict:
        """Extrait les images du payload."""
        if images is None:
            images = {}
        
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
                images[content_id] = body_data
        
        # Récursion sur les parts
        for part in payload.get('parts', []):
            self._extract_images(part, images)
        
        return images
    
    def _show_ai_analysis(self, analysis: dict):
        """Affiche l'analyse IA."""
        ai_frame = QFrame()
        ai_frame.setStyleSheet("""
            QFrame {
                background-color: #ede9fe;
                border: 1px solid #c4b5fd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        ai_layout = QVBoxLayout(ai_frame)
        ai_layout.setSpacing(8)
        
        title = QLabel("🤖 Analyse IA")
        title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #5b21b6;")
        ai_layout.addWidget(title)
        
        # Catégorie
        if 'category' in analysis:
            cat_label = QLabel(f"<b>Catégorie:</b> {analysis['category'].title()}")
            cat_label.setFont(QFont("Arial", 12))
            cat_label.setStyleSheet("color: #1f2937;")
            ai_layout.addWidget(cat_label)
        
        # Sentiment
        if 'sentiment' in analysis:
            sent_label = QLabel(f"<b>Sentiment:</b> {analysis['sentiment'].title()}")
            sent_label.setFont(QFont("Arial", 12))
            sent_label.setStyleSheet("color: #1f2937;")
            ai_layout.addWidget(sent_label)
        
        # Résumé
        if 'summary' in analysis:
            summary_label = QLabel(f"<b>Résumé:</b> {analysis['summary']}")
            summary_label.setFont(QFont("Arial", 12))
            summary_label.setStyleSheet("color: #374151;")
            summary_label.setWordWrap(True)
            ai_layout.addWidget(summary_label)
        
        self.content_layout.addWidget(ai_frame)
    
    def _on_reply(self):
        """Répondre."""
        if self.current_email:
            self.reply_requested.emit(self.current_email)
    
    def _on_forward(self):
        """Transférer."""
        if self.current_email:
            self.forward_requested.emit(self.current_email)
    
    def _on_archive(self):
        """Archiver."""
        if self.current_email:
            self.archive_requested.emit(self.current_email)