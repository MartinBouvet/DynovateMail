#!/usr/bin/env python3
"""
Vue détail email - AFFICHAGE CORRIGÉ avec images et formatage
"""
import logging
import base64
import re
from typing import Dict  # ← AJOUTER CETTE LIGNE
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QTextBrowser
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices

from gmail_client import GmailClient
from ai_processor import AIProcessor
from models.email_model import Email

logger = logging.getLogger(__name__)

class EmailDetailView(QScrollArea):
    """Vue détail d'un email avec affichage optimisé."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.current_email = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée l'interface."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("background-color: #ffffff; border: none;")
        
        # Container principal
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #ffffff;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(30, 20, 30, 20)
        self.layout.setSpacing(15)
        
        # Message par défaut
        self.empty_label = QLabel("📧 Sélectionnez un email pour le lire")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setFont(QFont("SF Pro Display", 16))
        self.empty_label.setStyleSheet("color: #999999; padding: 100px;")
        self.layout.addWidget(self.empty_label)
        
        self.setWidget(self.container)
    
    def show_email(self, email: Email):
        """Affiche un email avec formatage correct."""
        logger.info(f"📧 Affichage email: {email.subject}")
        self.current_email = email
        
        # Effacer le contenu précédent
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # === BARRE D'ACTIONS ===
        actions_bar = self._create_actions_bar()
        self.layout.addWidget(actions_bar)
        
        # === EN-TÊTE EMAIL ===
        header = self._create_email_header(email)
        self.layout.addWidget(header)
        
        # === ANALYSE IA ===
        if hasattr(email, 'ai_analysis') and email.ai_analysis:
            ai_panel = self._create_ai_panel(email.ai_analysis)
            self.layout.addWidget(ai_panel)
        
        # === CORPS EMAIL (CORRIGÉ) ===
        body_viewer = self._create_improved_body_viewer(email)
        self.layout.addWidget(body_viewer)
        
        self.layout.addStretch()
    
    def _create_actions_bar(self) -> QFrame:
        """Crée la barre d'actions."""
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Boutons
        reply_btn = QPushButton("↩️ Répondre")
        reply_btn.setFont(QFont("SF Pro Display", 11))
        reply_btn.clicked.connect(self._on_reply)
        
        forward_btn = QPushButton("➡️ Transférer")
        forward_btn.setFont(QFont("SF Pro Display", 11))
        forward_btn.clicked.connect(self._on_forward)
        
        archive_btn = QPushButton("📦 Archiver")
        archive_btn.setFont(QFont("SF Pro Display", 11))
        archive_btn.clicked.connect(self._on_archive)
        
        delete_btn = QPushButton("🗑️ Supprimer")
        delete_btn.setFont(QFont("SF Pro Display", 11))
        delete_btn.clicked.connect(self._on_delete)
        
        for btn in [reply_btn, forward_btn, archive_btn, delete_btn]:
            btn.setFixedHeight(35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 6px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #5b21b6;
                    color: white;
                }
            """)
            layout.addWidget(btn)
        
        layout.addStretch()
        return bar
    
    def _create_email_header(self, email: Email) -> QFrame:
        """Crée l'en-tête de l'email."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 2px solid #5b21b6;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(header)
        
        # Sujet
        subject_label = QLabel(email.subject or "(Sans sujet)")
        subject_label.setFont(QFont("SF Pro Display", 18, QFont.Bold))
        subject_label.setStyleSheet("color: #000000; border: none;")
        subject_label.setWordWrap(True)
        layout.addWidget(subject_label)
        
        # Infos expéditeur
        info_layout = QHBoxLayout()
        
        sender_label = QLabel(f"👤 De: {email.sender}")
        sender_label.setFont(QFont("SF Pro Display", 12))
        sender_label.setStyleSheet("color: #333333; border: none;")
        info_layout.addWidget(sender_label)
        
        info_layout.addStretch()
        
        if email.received_date:
            date_label = QLabel(f"🕒 {email.received_date.strftime('%d/%m/%Y à %H:%M')}")
            date_label.setFont(QFont("SF Pro Display", 11))
            date_label.setStyleSheet("color: #666666; border: none;")
            info_layout.addWidget(date_label)
        
        layout.addLayout(info_layout)
        
        # Destinataires (si plusieurs)
        if hasattr(email, 'to') and email.to:
            to_label = QLabel(f"📨 À: {', '.join(email.to)}")
            to_label.setFont(QFont("SF Pro Display", 10))
            to_label.setStyleSheet("color: #666666; border: none;")
            to_label.setWordWrap(True)
            layout.addWidget(to_label)
        
        return header
    
    def _create_ai_panel(self, analysis: Dict) -> QFrame:
        """Crée le panneau d'analyse IA."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f0e6ff, stop:1 #e6d9ff);
                border-radius: 10px;
                padding: 15px;
                border: 2px solid #5b21b6;
            }
        """)
        
        layout = QVBoxLayout(panel)
        
        # Titre
        title = QLabel("🤖 Analyse IA")
        title.setFont(QFont("SF Pro Display", 14, QFont.Bold))
        title.setStyleSheet("color: #5b21b6; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Catégorie + Priorité
        meta_layout = QHBoxLayout()
        
        category_label = QLabel(f"📁 {analysis.get('category', 'autre').upper()}")
        category_label.setFont(QFont("SF Pro Display", 11, QFont.Bold))
        category_label.setStyleSheet("color: #000000; background: transparent; border: none;")
        meta_layout.addWidget(category_label)
        
        priority = analysis.get('priority', 'moyenne')
        priority_colors = {'haute': '#dc2626', 'moyenne': '#f59e0b', 'basse': '#10b981'}
        priority_label = QLabel(f"⚡ {priority.upper()}")
        priority_label.setFont(QFont("SF Pro Display", 11, QFont.Bold))
        priority_label.setStyleSheet(f"color: {priority_colors.get(priority, '#666666')}; background: transparent; border: none;")
        meta_layout.addWidget(priority_label)
        
        sentiment_label = QLabel(f"😊 {analysis.get('sentiment', 'neutre').capitalize()}")
        sentiment_label.setFont(QFont("SF Pro Display", 11))
        sentiment_label.setStyleSheet("color: #333333; background: transparent; border: none;")
        meta_layout.addWidget(sentiment_label)
        
        meta_layout.addStretch()
        layout.addLayout(meta_layout)
        
        # Résumé
        if analysis.get('summary'):
            summary_label = QLabel(f"📝 {analysis['summary']}")
            summary_label.setFont(QFont("SF Pro Display", 11))
            summary_label.setStyleSheet("color: #000000; background: transparent; border: none; margin-top: 10px;")
            summary_label.setWordWrap(True)
            layout.addWidget(summary_label)
        
        # Actions suggérées
        if analysis.get('suggested_actions'):
            actions_label = QLabel("✅ Actions suggérées:")
            actions_label.setFont(QFont("SF Pro Display", 10, QFont.Bold))
            actions_label.setStyleSheet("color: #333333; background: transparent; border: none; margin-top: 10px;")
            layout.addWidget(actions_label)
            
            for action in analysis['suggested_actions'][:3]:
                action_label = QLabel(f"  • {action}")
                action_label.setFont(QFont("SF Pro Display", 10))
                action_label.setStyleSheet("color: #000000; background: transparent; border: none;")
                layout.addWidget(action_label)
        
        return panel
    
    def _create_improved_body_viewer(self, email: Email) -> QTextBrowser:
        """
        Crée le visualiseur de corps d'email AMÉLIORÉ.
        Corrige l'affichage des images et du contenu.
        """
        viewer = QTextBrowser()
        viewer.setOpenExternalLinks(True)
        viewer.setMinimumHeight(500)
        
        if email.body:
            if email.is_html:
                # HTML avec images intégrées
                html_content = self._process_html_with_images(email)
                viewer.setHtml(html_content)
            else:
                # Texte brut avec formatage
                formatted_text = self._format_plain_text(email.body)
                viewer.setHtml(formatted_text)
        else:
            viewer.setPlainText("(Email vide)")
        
        viewer.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                font-family: 'SF Pro Display', Arial, sans-serif;
                font-size: 13px;
                color: #000000;
                line-height: 1.6;
            }
        """)
        
        return viewer
    
    def _process_html_with_images(self, email: Email) -> str:
        """
        Traite le HTML et intègre les images en base64.
        CORRIGE l'affichage des images dans les emails.
        """
        html = email.body
        
        # Si l'email a des pièces jointes, chercher les images
        if hasattr(email, 'attachments') and email.attachments:
            for attachment in email.attachments:
                if attachment.get('is_inline') and attachment.get('content_id'):
                    # Image inline avec CID
                    cid = attachment['content_id'].strip('<>')
                    
                    # Récupérer les données de l'image
                    if attachment.get('data'):
                        mime_type = attachment.get('mime_type', 'image/jpeg')
                        image_data = attachment['data']
                        
                        # Convertir en base64 si nécessaire
                        if isinstance(image_data, bytes):
                            image_b64 = base64.b64encode(image_data).decode('utf-8')
                        else:
                            image_b64 = image_data
                        
                        # Remplacer dans le HTML
                        data_url = f"data:{mime_type};base64,{image_b64}"
                        html = html.replace(f"cid:{cid}", data_url)
        
        # Améliorer le HTML avec styles
        improved_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'SF Pro Display', Arial, sans-serif;
                    font-size: 13px;
                    color: #000000;
                    line-height: 1.6;
                    word-wrap: break-word;
                    max-width: 100%;
                    margin: 0;
                    padding: 0;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 10px 0;
                }}
                a {{
                    color: #5b21b6;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                p {{
                    margin: 10px 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    max-width: 100%;
                }}
                td, th {{
                    padding: 8px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                blockquote {{
                    margin: 15px 0;
                    padding-left: 15px;
                    border-left: 3px solid #5b21b6;
                    color: #666;
                }}
                pre, code {{
                    background-color: #f5f5f5;
                    padding: 5px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
                /* Corriger les layouts email */
                table[role="presentation"] {{
                    width: 100% !important;
                }}
                .gmail_quote {{
                    margin: 20px 0;
                    padding: 10px;
                    border-left: 3px solid #ccc;
                    background-color: #f9f9f9;
                }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        return improved_html
    
    def _format_plain_text(self, text: str) -> str:
        """
        Formate le texte brut en HTML lisible.
        """
        # Échapper le HTML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Détecter et formater les URLs
        url_pattern = r'(https?://[^\s]+)'
        text = re.sub(url_pattern, r'<a href="\1" style="color: #5b21b6;">\1</a>', text)
        
        # Détecter et formater les emails
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        text = re.sub(email_pattern, r'<a href="mailto:\1" style="color: #5b21b6;">\1</a>', text)
        
        # Convertir les retours à la ligne
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            if para.strip():
                # Remplacer les simples retours à la ligne par <br>
                para = para.replace('\n', '<br>')
                formatted_paragraphs.append(f'<p>{para}</p>')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'SF Pro Display', Arial, sans-serif;
                    font-size: 13px;
                    color: #000000;
                    line-height: 1.6;
                    padding: 0;
                    margin: 0;
                }}
                p {{
                    margin: 10px 0;
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
        <body>
            {''.join(formatted_paragraphs)}
        </body>
        </html>
        """
        
        return html
    
    def _on_reply(self):
        """Répondre à l'email."""
        if not self.current_email:
            return
        
        logger.info("↩️ Répondre à l'email")
        # TODO: Ouvrir fenêtre de composition avec pré-remplissage
    
    def _on_forward(self):
        """Transférer l'email."""
        if not self.current_email:
            return
        
        logger.info("➡️ Transférer l'email")
        # TODO: Ouvrir fenêtre de composition pour transfert
    
    def _on_archive(self):
        """Archiver l'email."""
        if not self.current_email:
            return
        
        logger.info("📦 Archiver l'email")
        # TODO: Implémenter l'archivage
    
    def _on_delete(self):
        """Supprimer l'email."""
        if not self.current_email:
            return
        
        logger.info("🗑️ Supprimer l'email")
        # TODO: Implémenter la suppression