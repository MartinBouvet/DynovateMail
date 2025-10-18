#!/usr/bin/env python3
"""
Carte email avec badges catégorie - VERSION AMÉLIORÉE
"""
import logging
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

from app.models.email_model import Email

logger = logging.getLogger(__name__)

class SmartEmailCard(QFrame):
    """Carte email cliquable avec badges."""
    
    clicked = pyqtSignal(Email)
    
    def __init__(self, email: Email):
        super().__init__()
        self.email = email
        self._setup_ui()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def _setup_ui(self):
        """Crée la carte."""
        self.setObjectName("email-card")
        self.setFixedHeight(105)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(6)
        
        # Ligne 1: Expéditeur + Date + Badge non lu
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Badge non lu (à gauche)
        if not self.email.read:
            unread_badge = QLabel("●")
            unread_badge.setFont(QFont("Arial", 16))
            unread_badge.setStyleSheet("color: #5b21b6;")
            unread_badge.setFixedWidth(20)
            header_layout.addWidget(unread_badge)
        
        # Expéditeur
        sender = self.email.sender or "Inconnu"
        if '<' in sender:
            sender = sender.split('<')[0].strip()
        
        sender_label = QLabel(sender)
        sender_label.setFont(QFont("Arial", 13, QFont.Weight.Bold if not self.email.read else QFont.Weight.Normal))
        sender_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(sender_label)
        
        header_layout.addStretch()
        
        # Badge catégorie (si disponible)
        if hasattr(self.email, 'ai_analysis') and self.email.ai_analysis:
            category = self.email.ai_analysis.get('category')
            if category:
                badge = self._create_category_badge(category)
                header_layout.addWidget(badge)
        
        # Date
        date_str = self._format_date(self.email.received_date)
        date_label = QLabel(date_str)
        date_label.setFont(QFont("Arial", 11))
        date_label.setStyleSheet("color: #6b7280;")
        header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # Ligne 2: Sujet
        subject = self.email.subject or "(Sans sujet)"
        subject_label = QLabel(subject)
        subject_label.setFont(QFont("Arial", 12, QFont.Weight.Bold if not self.email.read else QFont.Weight.Normal))
        subject_label.setStyleSheet("color: #1f2937;")
        subject_label.setWordWrap(False)
        layout.addWidget(subject_label)
        
        # Ligne 3: Aperçu + Indicateurs
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        
        # Aperçu
        preview = self._get_preview()
        preview_label = QLabel(preview)
        preview_label.setFont(QFont("Arial", 11))
        preview_label.setStyleSheet("color: #6b7280;")
        preview_label.setWordWrap(False)
        footer_layout.addWidget(preview_label, 1)
        
        # Indicateur pièce jointe
        if self.email.has_attachments:
            attachment_icon = QLabel(f"📎 {self.email.attachment_count}")
            attachment_icon.setFont(QFont("Arial", 10))
            attachment_icon.setStyleSheet("color: #6b7280;")
            footer_layout.addWidget(attachment_icon)
        
        layout.addLayout(footer_layout)
        
        self._apply_styles()
    
    def _create_category_badge(self, category: str) -> QLabel:
        """Crée un badge de catégorie."""
        # Mapping catégories -> affichage
        category_config = {
            "cv": ("📄 CV", "#8b5cf6"),
            "meeting": ("📅 RDV", "#10b981"),
            "invoice": ("💰 Facture", "#f59e0b"),
            "newsletter": ("📰 Newsletter", "#3b82f6"),
            "support": ("🛠️ Support", "#ef4444"),
            "spam": ("🚫 Spam", "#dc2626"),
            "important": ("⭐ Important", "#eab308"),
            "personal": ("👤 Personnel", "#8b5cf6"),
            "work": ("💼 Pro", "#0ea5e9")
        }
        
        text, color = category_config.get(category, (category.title(), "#6b7280"))
        
        badge = QLabel(text)
        badge.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        badge.setStyleSheet(f"""
            background-color: {color};
            color: #ffffff;
            border-radius: 10px;
            padding: 3px 10px;
        """)
        
        return badge
    
    def _format_date(self, date) -> str:
        """Formate la date."""
        if not date:
            return ""
        
        try:
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            
            now = datetime.now(date.tzinfo if date.tzinfo else None)
            diff = now - date
            
            if diff.days == 0:
                return date.strftime("%H:%M")
            elif diff.days == 1:
                return "Hier"
            elif diff.days < 7:
                days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
                return days[date.weekday()]
            else:
                return date.strftime("%d/%m")
        except Exception as e:
            logger.error(f"Erreur format date: {e}")
            return ""
    
    def _get_preview(self) -> str:
        """Extrait un aperçu du corps."""
        if hasattr(self.email, 'snippet') and self.email.snippet:
            preview = self.email.snippet[:70]
            return preview + "..." if len(self.email.snippet) > 70 else preview
        
        if not self.email.body:
            return ""
        
        import re
        text = re.sub('<[^<]+?>', '', self.email.body)
        text = text.strip()[:70]
        return text + "..." if len(text) == 70 else text
    
    def _apply_styles(self):
        """Applique les styles."""
        if not self.email.read:
            # Non lu: fond blanc + bordure violette
            self.setStyleSheet(f"""
                #email-card {{
                    background-color: #ffffff;
                    border: none;
                    border-left: 4px solid #5b21b6;
                    border-bottom: 1px solid #e5e7eb;
                }}
                
                #email-card:hover {{
                    background-color: #f3f4f6;
                    border-left: 4px solid #5b21b6;
                }}
            """)
        else:
            # Lu: fond gris clair
            self.setStyleSheet(f"""
                #email-card {{
                    background-color: #fafafa;
                    border: none;
                    border-left: 4px solid transparent;
                    border-bottom: 1px solid #e5e7eb;
                }}
                
                #email-card:hover {{
                    background-color: #f3f4f6;
                    border-left: 4px solid #9ca3af;
                }}
            """)
    
    def mousePressEvent(self, event):
        """Gère le clic."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.email)
        super().mousePressEvent(event)