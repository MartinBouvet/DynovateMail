#!/usr/bin/env python3
"""
Vue détail d'un email - SANS WebEngine (compatible)
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QTextBrowser
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gmail_client import GmailClient
from ai_processor import AIProcessor
from models.email_model import Email

logger = logging.getLogger(__name__)

class EmailDetailView(QScrollArea):
    """Vue détail d'un email."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.current_email = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée l'interface."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("background-color: #ffffff; border: none;")
        
        # Container principal
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #ffffff;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(30, 20, 30, 20)
        self.layout.setSpacing(15)
        
        # Message par défaut
        self.empty_label = QLabel("Sélectionnez un email pour le lire")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(QFont("Segoe UI", 16))
        self.empty_label.setStyleSheet("color: #999999; padding: 100px;")
        self.layout.addWidget(self.empty_label)
        
        self.setWidget(self.container)
    
    def show_email(self, email: Email):
        """Affiche un email."""
        logger.info(f"Affichage email: {email.subject}")
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
        
        # === CORPS EMAIL ===
        body_viewer = self._create_body_viewer(email)
        self.layout.addWidget(body_viewer)
        
        self.layout.addStretch()
    
    def _create_actions_bar(self) -> QFrame:
        """Crée la barre d'actions."""
        bar = QFrame()
        bar.setFixedHeight(60)
        bar.setStyleSheet("background-color: #f5f5f5; border-bottom: 2px solid #5b21b6;")
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        
        # Boutons d'action
        reply_btn = QPushButton("↩️ Répondre")
        reply_btn.setFont(QFont("Segoe UI", 12))
        reply_btn.setFixedHeight(40)
        reply_btn.clicked.connect(self._on_reply)
        layout.addWidget(reply_btn)
        
        forward_btn = QPushButton("➡️ Transférer")
        forward_btn.setFont(QFont("Segoe UI", 12))
        forward_btn.setFixedHeight(40)
        forward_btn.clicked.connect(self._on_forward)
        layout.addWidget(forward_btn)
        
        layout.addStretch()
        
        archive_btn = QPushButton("📦 Archiver")
        archive_btn.setFont(QFont("Segoe UI", 12))
        archive_btn.setFixedHeight(40)
        archive_btn.clicked.connect(self._on_archive)
        layout.addWidget(archive_btn)
        
        delete_btn = QPushButton("🗑️ Supprimer")
        delete_btn.setFont(QFont("Segoe UI", 12))
        delete_btn.setFixedHeight(40)
        delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(delete_btn)
        
        return bar
    
    def _create_email_header(self, email: Email) -> QFrame:
        """Crée l'en-tête de l'email."""
        header = QFrame()
        header.setStyleSheet("background-color: #ffffff; border: none;")
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 15, 0, 15)
        layout.setSpacing(10)
        
        # Sujet
        subject = QLabel(email.subject or "(Sans sujet)")
        subject.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        subject.setWordWrap(True)
        subject.setStyleSheet("color: #000000;")
        layout.addWidget(subject)
        
        # Expéditeur
        sender_layout = QHBoxLayout()
        
        sender_label = QLabel("De:")
        sender_label.setFont(QFont("Segoe UI", 12))
        sender_label.setStyleSheet("color: #666666;")
        sender_layout.addWidget(sender_label)
        
        sender = QLabel(email.sender or "Inconnu")
        sender.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sender.setStyleSheet("color: #000000;")
        sender_layout.addWidget(sender)
        
        sender_layout.addStretch()
        
        # Date
        if email.received_date:
            date_str = email.received_date.strftime("%d/%m/%Y %H:%M")
            date = QLabel(date_str)
            date.setFont(QFont("Segoe UI", 12))
            date.setStyleSheet("color: #666666;")
            sender_layout.addWidget(date)
        
        layout.addLayout(sender_layout)
        
        # Destinataire
        if email.to:
            to_layout = QHBoxLayout()
            
            to_label = QLabel("À:")
            to_label.setFont(QFont("Segoe UI", 12))
            to_label.setStyleSheet("color: #666666;")
            to_layout.addWidget(to_label)
            
            to_text = ", ".join(email.to) if isinstance(email.to, list) else email.to
            to_value = QLabel(to_text)
            to_value.setFont(QFont("Segoe UI", 12))
            to_value.setStyleSheet("color: #000000;")
            to_layout.addWidget(to_value)
            
            to_layout.addStretch()
            layout.addLayout(to_layout)
        
        return header
    
    def _create_ai_panel(self, ai_analysis) -> QFrame:
        """Crée le panneau d'analyse IA."""
        panel = QFrame()
        panel.setObjectName("ai-panel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Titre
        title = QLabel("🤖 Analyse IA")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #5b21b6;")
        layout.addWidget(title)
        
        # Catégorie
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Catégorie:"))
        
        category_value = QLabel(ai_analysis.category.title())
        category_value.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        category_value.setStyleSheet("color: #000000;")
        category_layout.addWidget(category_value)
        category_layout.addStretch()
        
        layout.addLayout(category_layout)
        
        # Priorité
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Priorité:")
        priority_label.setStyleSheet("color: #000000;")
        priority_layout.addWidget(priority_label)
        
        priority_stars = "⭐" * ai_analysis.priority
        priority_value = QLabel(f"{priority_stars} ({ai_analysis.priority}/5)")
        priority_value.setStyleSheet("color: #000000;")
        priority_layout.addWidget(priority_value)
        priority_layout.addStretch()
        
        layout.addLayout(priority_layout)
        
        # Sentiment
        if hasattr(ai_analysis, 'sentiment'):
            sentiment_layout = QHBoxLayout()
            sentiment_label = QLabel("Sentiment:")
            sentiment_label.setStyleSheet("color: #000000;")
            sentiment_layout.addWidget(sentiment_label)
            
            sentiment_value = QLabel(ai_analysis.sentiment)
            sentiment_value.setStyleSheet("color: #000000;")
            sentiment_layout.addWidget(sentiment_value)
            sentiment_layout.addStretch()
            
            layout.addLayout(sentiment_layout)
        
        # Résumé
        if hasattr(ai_analysis, 'summary') and ai_analysis.summary:
            summary_label = QLabel("Résumé:")
            summary_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            summary_label.setStyleSheet("color: #000000;")
            layout.addWidget(summary_label)
            
            summary_text = QLabel(ai_analysis.summary)
            summary_text.setWordWrap(True)
            summary_text.setStyleSheet("color: #000000; padding: 10px; background-color: #f5f5f5; border-radius: 6px;")
            layout.addWidget(summary_text)
        
        panel.setStyleSheet("""
            #ai-panel {
                background-color: #f0e7ff;
                border: 2px solid #5b21b6;
                border-radius: 8px;
            }
        """)
        
        return panel
    
    def _create_body_viewer(self, email: Email) -> QTextBrowser:
        """Crée le visualiseur du corps."""
        viewer = QTextBrowser()
        viewer.setOpenExternalLinks(True)
        viewer.setMinimumHeight(400)
        
        if email.body:
            if email.is_html:
                # Améliorer l'affichage HTML
                html_content = self._improve_html(email.body)
                viewer.setHtml(html_content)
            else:
                viewer.setPlainText(email.body)
        else:
            viewer.setPlainText("(Email vide)")
        
        viewer.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: none;
                padding: 20px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #000000;
                line-height: 1.6;
            }
        """)
        
        return viewer
    
    def _improve_html(self, html: str) -> str:
        """Améliore l'affichage HTML."""
        # Ajouter des styles pour améliorer l'affichage
        improved_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 13px;
                    color: #000000;
                    line-height: 1.6;
                    word-wrap: break-word;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
                a {{
                    color: #5b21b6;
                }}
                p {{
                    margin: 10px 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                td, th {{
                    padding: 8px;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        return improved_html
    
    def _on_reply(self):
        """Répondre à l'email."""
        if not self.current_email:
            return
        
        try:
            from ui.compose_view import ComposeView
            
            sender_email = self.current_email.sender
            if '<' in sender_email:
                sender_email = sender_email.split('<')[1].split('>')[0]
            
            main_window = self
            while main_window.parent():
                main_window = main_window.parent()
            
            compose = ComposeView(
                parent=main_window,
                gmail_client=self.gmail_client,
                ai_processor=self.ai_processor
            )
            
            compose.to_input.setText(sender_email)
            compose.subject_input.setText(f"Re: {self.current_email.subject or ''}")
            
            original_text = self.current_email.body or self.current_email.snippet or ''
            if self.current_email.is_html:
                import re
                original_text = re.sub('<[^<]+?>', '', original_text)
            
            original_body = f"\n\n--- Message original ---\nDe: {self.current_email.sender}\nDate: {self.current_email.received_date}\n\n{original_text[:500]}"
            compose.body_input.setPlainText(original_body)
            
            cursor = compose.body_input.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            compose.body_input.setTextCursor(cursor)
            
            compose.show()
            logger.info("Fenêtre de réponse ouverte")
            
        except Exception as e:
            logger.error(f"Erreur ouverture réponse: {e}")
    
    def _on_forward(self):
        """Transférer l'email."""
        if not self.current_email:
            return
        
        try:
            from ui.compose_view import ComposeView
            
            main_window = self
            while main_window.parent():
                main_window = main_window.parent()
            
            compose = ComposeView(
                parent=main_window,
                gmail_client=self.gmail_client,
                ai_processor=self.ai_processor
            )
            
            compose.subject_input.setText(f"Fwd: {self.current_email.subject or ''}")
            
            original_text = self.current_email.body or self.current_email.snippet or ''
            if self.current_email.is_html:
                import re
                original_text = re.sub('<[^<]+?>', '', original_text)
            
            forwarded_body = f"\n\n--- Message transféré ---\nDe: {self.current_email.sender}\nDate: {self.current_email.received_date}\nSujet: {self.current_email.subject}\n\n{original_text[:500]}"
            compose.body_input.setPlainText(forwarded_body)
            
            cursor = compose.body_input.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            compose.body_input.setTextCursor(cursor)
            
            compose.show()
            logger.info("Fenêtre de transfert ouverte")
            
        except Exception as e:
            logger.error(f"Erreur ouverture transfert: {e}")
    
    def _on_archive(self):
        """Archiver l'email."""
        if self.current_email:
            try:
                self.gmail_client.archive_email(self.current_email.id)
                logger.info("Email archivé")
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(None, "Succès", "Email archivé!")
            except Exception as e:
                logger.error(f"Erreur archivage: {e}")
    
    def _on_delete(self):
        """Supprimer l'email."""
        if self.current_email:
            try:
                self.gmail_client.delete_email(self.current_email.id)
                logger.info("Email supprimé")
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(None, "Succès", "Email supprimé!")
            except Exception as e:
                logger.error(f"Erreur suppression: {e}")