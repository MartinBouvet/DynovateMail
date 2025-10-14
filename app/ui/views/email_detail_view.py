#!/usr/bin/env python3
"""
Vue détail email - AVEC IMAGES FONCTIONNELLES
"""
import logging
import base64
import html
from typing import Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QTextBrowser, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from app.gmail_client import GmailClient
from app.ai_processor import AIProcessor
from app.models.email_model import Email

logger = logging.getLogger(__name__)

class EmailDetailView(QScrollArea):
    """Vue détail avec images."""
    
    reply_requested = pyqtSignal(object)
    forward_requested = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.current_email = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("background-color: #ffffff; border: none;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #ffffff;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(40, 30, 40, 30)
        self.layout.setSpacing(20)
        
        # Message par défaut
        self.empty_label = QLabel("📧 Sélectionnez un email")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setFont(QFont("Arial", 16))
        self.empty_label.setStyleSheet("color: #999999; padding: 100px;")
        self.layout.addWidget(self.empty_label)
        
        self.setWidget(self.container)
    
    def show_email(self, email: Email):
        """Affiche l'email."""
        logger.info(f"📧 Affichage: {email.subject}")
        self.current_email = email
        
        # Effacer
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Barre d'actions
        actions = self._create_actions_bar()
        self.layout.addWidget(actions)
        
        # En-tête
        header = self._create_header(email)
        self.layout.addWidget(header)
        
        # Analyse IA
        if hasattr(email, 'ai_analysis') and email.ai_analysis:
            ai_panel = self._create_ai_panel(email.ai_analysis)
            self.layout.addWidget(ai_panel)
        
        # Corps avec images
        body_viewer = self._create_body_viewer(email)
        self.layout.addWidget(body_viewer)
        
        self.layout.addStretch()
    
    def _create_actions_bar(self) -> QFrame:
        """Barre d'actions."""
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        
        buttons = [
            ("↩️ Répondre", self._on_reply, "#5b21b6"),
            ("➡️ Transférer", self._on_forward, "#059669"),
            ("📦 Archiver", self._on_archive, "#0284c7"),
            ("🗑️ Supprimer", self._on_delete, "#dc2626"),
        ]
        
        for text, handler, color in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 11, QFont.Bold))
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #ffffff;
                    border: 2px solid #e0e0e0;
                    border-radius: 20px;
                    padding: 0 20px;
                    color: #1a1a1a;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    color: white;
                    border-color: {color};
                }}
            """)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        
        layout.addStretch()
        return bar
    
    def _create_header(self, email: Email) -> QFrame:
        """En-tête."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 25px;
            }
        """)
        
        layout = QVBoxLayout(header)
        layout.setSpacing(15)
        
        # Sujet
        subject = QLabel(email.subject or "(Sans sujet)")
        subject.setFont(QFont("Arial", 22, QFont.Bold))
        subject.setStyleSheet("color: #000000; border: none;")
        subject.setWordWrap(True)
        layout.addWidget(subject)
        
        # Ligne
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0; border: none; max-height: 1px;")
        layout.addWidget(line)
        
        # Expéditeur
        sender_layout = QHBoxLayout()
        sender_label = QLabel("De:")
        sender_label.setFont(QFont("Arial", 12, QFont.Bold))
        sender_label.setStyleSheet("color: #666666; border: none;")
        sender_label.setFixedWidth(100)
        sender_layout.addWidget(sender_label)
        
        sender_value = QLabel(email.sender or "Inconnu")
        sender_value.setFont(QFont("Arial", 12))
        sender_value.setStyleSheet("color: #000000; border: none;")
        sender_value.setWordWrap(True)
        sender_layout.addWidget(sender_value, 1)
        layout.addLayout(sender_layout)
        
        # Date
        if email.received_date:
            date_layout = QHBoxLayout()
            date_label = QLabel("Date:")
            date_label.setFont(QFont("Arial", 12, QFont.Bold))
            date_label.setStyleSheet("color: #666666; border: none;")
            date_label.setFixedWidth(100)
            date_layout.addWidget(date_label)
            
            date_value = QLabel(email.received_date.strftime("%d/%m/%Y à %H:%M"))
            date_value.setFont(QFont("Arial", 12))
            date_value.setStyleSheet("color: #000000; border: none;")
            date_layout.addWidget(date_value, 1)
            layout.addLayout(date_layout)
        
        return header
    
    def _create_ai_panel(self, analysis: dict) -> QFrame:
        """Panneau IA."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #faf5ff, stop:1 #f3e8ff);
                border: 2px solid #c084fc;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        
        # Titre
        title = QLabel("🤖 Analyse IA")
        title.setFont(QFont("Arial", 15, QFont.Bold))
        title.setStyleSheet("color: #5b21b6; border: none; background: transparent;")
        layout.addWidget(title)
        
        # Catégorie
        if 'category' in analysis:
            cat = QLabel(f"📁 Catégorie: {analysis['category']}")
            cat.setFont(QFont("Arial", 11))
            cat.setStyleSheet("color: #1a1a1a; border: none; background: transparent;")
            layout.addWidget(cat)
        
        # Sentiment
        if 'sentiment' in analysis:
            sent = QLabel(f"😊 Sentiment: {analysis['sentiment']}")
            sent.setFont(QFont("Arial", 11))
            sent.setStyleSheet("color: #1a1a1a; border: none; background: transparent;")
            layout.addWidget(sent)
        
        # Urgent
        if analysis.get('urgent'):
            urgent = QLabel("⚠️ EMAIL URGENT")
            urgent.setFont(QFont("Arial", 11, QFont.Bold))
            urgent.setStyleSheet("color: #dc2626; border: none; background: transparent;")
            layout.addWidget(urgent)
        
        # Résumé
        if 'summary' in analysis:
            summary = QLabel(f"📋 {analysis['summary']}")
            summary.setFont(QFont("Arial", 11))
            summary.setStyleSheet("color: #374151; border: none; background: transparent;")
            summary.setWordWrap(True)
            layout.addWidget(summary)
        
        return panel
    
    def _create_body_viewer(self, email: Email) -> QTextBrowser:
        """Viewer avec images."""
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setMinimumHeight(500)
        browser.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 25px;
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #000000;
            }
        """)
        
        # HTML
        html_content = self._extract_html(email)
        html_content = self._embed_images(html_content, email)
        
        final_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.7;
                    color: #000000;
                    margin: 0;
                    padding: 0;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 15px 0;
                    border-radius: 8px;
                }}
                a {{
                    color: #5b21b6;
                    text-decoration: none;
                    font-weight: 500;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                p {{
                    margin: 12px 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                }}
                td, th {{
                    border: 1px solid #e0e0e0;
                    padding: 10px;
                }}
                th {{
                    background-color: #f5f5f5;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        browser.setHtml(final_html)
        return browser
    
    def _extract_html(self, email: Email) -> str:
        """Extrait HTML."""
        try:
            if email.body:
                if '<html' in email.body.lower() or '<div' in email.body.lower():
                    return email.body
                else:
                    return self._text_to_html(email.body)
            
            if hasattr(self.gmail_client, 'service') and email.id:
                try:
                    message = self.gmail_client.service.users().messages().get(
                        userId='me',
                        id=email.id,
                        format='full'
                    ).execute()
                    
                    payload = message.get('payload', {})
                    
                    html_content = self._find_html_part(payload)
                    if html_content:
                        return html_content
                    
                    text_content = self._find_text_part(payload)
                    if text_content:
                        return self._text_to_html(text_content)
                except:
                    pass
            
            return "<p>Contenu non disponible</p>"
        except:
            return "<p>Erreur d'affichage</p>"
    
    def _find_html_part(self, payload: dict) -> Optional[str]:
        """Trouve HTML."""
        if payload.get('mimeType') == 'text/html':
            body_data = payload.get('body', {}).get('data', '')
            if body_data:
                return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        
        for part in payload.get('parts', []):
            if part.get('mimeType') == 'text/html':
                body_data = part.get('body', {}).get('data', '')
                if body_data:
                    return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            
            if 'parts' in part:
                html_content = self._find_html_part(part)
                if html_content:
                    return html_content
        
        return None
    
    def _find_text_part(self, payload: dict) -> Optional[str]:
        """Trouve texte."""
        if payload.get('mimeType') == 'text/plain':
            body_data = payload.get('body', {}).get('data', '')
            if body_data:
                return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        
        for part in payload.get('parts', []):
            if part.get('mimeType') == 'text/plain':
                body_data = part.get('body', {}).get('data', '')
                if body_data:
                    return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            
            if 'parts' in part:
                text_content = self._find_text_part(part)
                if text_content:
                    return text_content
        
        return None
    
    def _text_to_html(self, text: str) -> str:
        """Texte vers HTML."""
        text = html.escape(text)
        text = text.replace('\n', '<br>')
        
        # URLs en liens
        import re
        url_pattern = r'(https?://[^\s]+)'
        text = re.sub(url_pattern, r'<a href="\1">\1</a>', text)
        
        return f'<div>{text}</div>'
    
    def _embed_images(self, html_content: str, email: Email) -> str:
        """Intègre les images."""
        try:
            if not hasattr(self.gmail_client, 'service') or not email.id:
                return html_content
            
            message = self.gmail_client.service.users().messages().get(
                userId='me',
                id=email.id,
                format='full'
            ).execute()
            
            images = self._extract_images(message.get('payload', {}))
            
            for cid, image_data in images.items():
                cid_pattern = f'cid:{cid}'
                
                # Détecter MIME
                mime_type = 'image/jpeg'
                if image_data.startswith('/9j/'):
                    mime_type = 'image/jpeg'
                elif image_data.startswith('iVBORw'):
                    mime_type = 'image/png'
                elif image_data.startswith('R0lGOD'):
                    mime_type = 'image/gif'
                
                data_uri = f'data:{mime_type};base64,{image_data}'
                
                html_content = html_content.replace(f'src="{cid_pattern}"', f'src="{data_uri}"')
                html_content = html_content.replace(f"src='{cid_pattern}'", f'src="{data_uri}"')
            
            logger.info(f"✅ {len(images)} images inline intégrées")
        except Exception as e:
            logger.error(f"Erreur images: {e}")
        
        return html_content
    
    def _extract_images(self, payload: dict, images: dict = None) -> dict:
        """Extrait images."""
        if images is None:
            images = {}
        
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
            self._extract_images(part, images)
        
        return images
    
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
        if not self.current_email:
            return
        
        try:
            if hasattr(self.gmail_client, 'archive_email'):
                self.gmail_client.archive_email(self.current_email.id)
                QMessageBox.information(self, "Succès", "✅ Email archivé")
                logger.info("Email archivé")
            else:
                QMessageBox.warning(self, "Non disponible", "Fonction d'archivage non implémentée")
        except Exception as e:
            logger.error(f"Erreur archivage: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'archiver:\n{e}")
    
    def _on_delete(self):
        """Supprimer."""
        if not self.current_email:
            return
        
        reply = QMessageBox.question(
            self, "Confirmation",
            "Supprimer cet email ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if hasattr(self.gmail_client, 'delete_email'):
                    self.gmail_client.delete_email(self.current_email.id)
                    QMessageBox.information(self, "Succès", "✅ Email supprimé")
                    logger.info("Email supprimé")
                else:
                    QMessageBox.warning(self, "Non disponible", "Fonction de suppression non implémentée")
            except Exception as e:
                logger.error(f"Erreur suppression: {e}")
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer:\n{e}")