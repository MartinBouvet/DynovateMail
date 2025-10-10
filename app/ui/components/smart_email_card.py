#!/usr/bin/env python3
"""
Carte email pour la liste - CORRIGÉE COMPLÈTE
"""
import logging
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

from models.email_model import Email

logger = logging.getLogger(__name__)

class SmartEmailCard(QFrame):
    """Carte email cliquable."""
    
    clicked = pyqtSignal(Email)
    
    def __init__(self, email: Email):
        super().__init__()
        self.email = email
        self._setup_ui()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def _setup_ui(self):
        """Crée la carte."""
        self.setObjectName("email-card")
        self.setFixedHeight(100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6)
        
        # Ligne 1: Expéditeur + Date
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Expéditeur
        sender = self.email.sender or "Inconnu"
        sender_label = QLabel(sender)
        sender_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold if not self.email.is_read else QFont.Weight.Normal))
        sender_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(sender_label)
        
        header_layout.addStretch()
        
        # Date
        date_str = self._format_date(self.email.received_date)
        date_label = QLabel(date_str)
        date_label.setFont(QFont("Segoe UI", 11))
        date_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # Ligne 2: Sujet
        subject = self.email.subject or "(Sans sujet)"
        subject_label = QLabel(subject)
        subject_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold if not self.email.is_read else QFont.Weight.Normal))
        subject_label.setStyleSheet("color: #000000;")
        subject_label.setWordWrap(False)
        layout.addWidget(subject_label)
        
        # Ligne 3: Aperçu + Catégorie IA
        footer_layout = QHBoxLayout()
        
        # Aperçu
        preview = self._get_preview()
        preview_label = QLabel(preview)
        preview_label.setFont(QFont("Segoe UI", 11))
        preview_label.setStyleSheet("color: #666666;")
        preview_label.setWordWrap(False)
        footer_layout.addWidget(preview_label, stretch=1)
        
        # Badge catégorie
        if hasattr(self.email, 'ai_analysis') and self.email.ai_analysis:
            category_badge = self._create_category_badge()
            footer_layout.addWidget(category_badge)
        
        layout.addLayout(footer_layout)
        
        self._apply_styles()
    
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
                days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
                return days[date.weekday()]
            else:
                return date.strftime("%d/%m/%Y")
        except Exception as e:
            logger.error(f"Erreur format date: {e}")
            return ""
    
    def _get_preview(self) -> str:
        """Extrait un aperçu du corps."""
        # Utiliser le snippet si disponible
        if hasattr(self.email, 'snippet') and self.email.snippet:
            preview = self.email.snippet[:80]
            return preview + "..." if len(self.email.snippet) > 80 else preview
        
        # Sinon, extraire du corps
        if not self.email.body:
            return ""
        
        # Nettoyer le HTML
        import re
        text = re.sub('<[^<]+?>', '', self.email.body)
        text = text.strip()[:80]
        return text + "..." if len(text) == 80 else text
    
    def _create_category_badge(self) -> QLabel:
        """Crée le badge de catégorie."""
        category = self.email.ai_analysis.category
        
        # Mapping catégories -> affichage
        category_map = {
            "cv": ("📄 CV", "#5b21b6"),
            "meeting": ("📅 RDV", "#8b5cf6"),
            "invoice": ("💰 Facture", "#10b981"),
            "newsletter": ("📰 News", "#f59e0b"),
            "support": ("🛠️ Support", "#ef4444"),
            "spam": ("⚠️ Spam", "#dc2626"),
            "important": ("⭐ Important", "#eab308")
        }
        
        text, color = category_map.get(category, (category.title(), "#6b7280"))
        
        badge = QLabel(text)
        badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        badge.setStyleSheet(f"""
            background-color: {color};
            color: #ffffff;
            border-radius: 12px;
            padding: 4px 12px;
        """)
        
        return badge
    
    def _apply_styles(self):
        """Applique les styles."""
        bg_color = "#f9f9f9" if self.email.is_read else "#ffffff"
        
        self.setStyleSheet(f"""
            #email-card {{
                background-color: {bg_color};
                border: none;
                border-bottom: 1px solid #e0e0e0;
            }}
            
            #email-card:hover {{
                background-color: #f0f0f0;
                border-left: 4px solid #5b21b6;
            }}
        """)
    
    def mousePressEvent(self, event):
        """Gère le clic."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.email)
        super().mousePressEvent(event)