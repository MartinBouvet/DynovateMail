#!/usr/bin/env python3
"""
Carte d'email intelligente - VERSION CORRIGÉE
Corrections: Affichage, style, indicateurs visuels
"""
import logging
from datetime import datetime
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

from models.email_model import Email

logger = logging.getLogger(__name__)


class SmartEmailCard(QFrame):
    """Carte d'email avec analyse IA - CORRIGÉE."""
    
    clicked = pyqtSignal(object)  # Émet l'email cliqué
    
    def __init__(self, email: Email):
        super().__init__()
        self.email = email
        self._setup_ui()
        self._apply_style()
        
        # Curseur pointer
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def _setup_ui(self):
        """Configure l'interface de la carte."""
        self.setObjectName("email-card")
        self.setMinimumHeight(90)
        self.setMaximumHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # === LIGNE 1: Expéditeur + Date + Indicateurs ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Expéditeur
        sender_name = self._get_sender_display_name()
        self.sender_label = QLabel(sender_name)
        self.sender_label.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self.sender_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(self.sender_label)
        
        header_layout.addStretch()
        
        # Indicateur non lu
        if not self.email.is_read:
            unread_badge = QLabel("●")
            unread_badge.setFont(QFont("Arial", 16))
            unread_badge.setStyleSheet("color: #007bff;")
            unread_badge.setToolTip("Non lu")
            header_layout.addWidget(unread_badge)
        
        # Catégorie (si analyse IA disponible)
        if hasattr(self.email, 'ai_analysis') and self.email.ai_analysis:
            category_badge = self._create_category_badge()
            header_layout.addWidget(category_badge)
        
        # Date
        date_str = self._format_date()
        date_label = QLabel(date_str)
        date_label.setFont(QFont("Inter", 11))
        date_label.setStyleSheet("color: #6c757d;")
        header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # === LIGNE 2: Sujet ===
        subject_text = self.email.subject or "(Sans sujet)"
        self.subject_label = QLabel(subject_text)
        self.subject_label.setFont(QFont("Inter", 12, QFont.Weight.Medium))
        self.subject_label.setStyleSheet("color: #495057;")
        self.subject_label.setWordWrap(False)
        
        # Tronquer si trop long
        if len(subject_text) > 60:
            subject_text = subject_text[:60] + "..."
            self.subject_label.setText(subject_text)
        
        layout.addWidget(self.subject_label)
        
        # === LIGNE 3: Aperçu + Indicateurs ===
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(10)
        
        # Aperçu du contenu
        snippet = self.email.snippet or ""
        if len(snippet) > 80:
            snippet = snippet[:80] + "..."
        
        snippet_label = QLabel(snippet)
        snippet_label.setFont(QFont("Inter", 11))
        snippet_label.setStyleSheet("color: #6c757d;")
        snippet_label.setWordWrap(False)
        preview_layout.addWidget(snippet_label)
        
        preview_layout.addStretch()
        
        # Indicateur de pièce jointe
        if self.email.has_attachments:
            attachment_icon = QLabel("📎")
            attachment_icon.setFont(QFont("Arial", 14))
            attachment_icon.setToolTip(f"{len(self.email.attachments or [])} pièce(s) jointe(s)")
            preview_layout.addWidget(attachment_icon)
        
        # Indicateur de priorité
        if hasattr(self.email, 'ai_analysis') and self.email.ai_analysis:
            priority = self.email.ai_analysis.priority
            if priority >= 4:
                priority_icon = QLabel("⚠️")
                priority_icon.setFont(QFont("Arial", 14))
                priority_icon.setToolTip(f"Priorité: {priority}/5")
                preview_layout.addWidget(priority_icon)
        
        layout.addLayout(preview_layout)
    
    def _get_sender_display_name(self) -> str:
        """Retourne le nom d'affichage de l'expéditeur."""
        if hasattr(self.email, 'get_sender_name'):
            return self.email.get_sender_name() or self.email.sender
        return self.email.sender.split('@')[0] if '@' in self.email.sender else self.email.sender
    
    def _format_date(self) -> str:
        """Formate la date d'affichage."""
        if not self.email.received_date:
            return ""
        
        try:
            if isinstance(self.email.received_date, str):
                date_obj = datetime.fromisoformat(self.email.received_date.replace('Z', '+00:00'))
            else:
                date_obj = self.email.received_date
            
            now = datetime.now(date_obj.tzinfo)
            diff = now - date_obj
            
            # Si aujourd'hui
            if diff.days == 0:
                return date_obj.strftime("%H:%M")
            # Si hier
            elif diff.days == 1:
                return "Hier"
            # Si cette semaine
            elif diff.days < 7:
                days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
                return days[date_obj.weekday()]
            # Sinon date complète
            else:
                return date_obj.strftime("%d/%m/%y")
        
        except Exception as e:
            logger.error(f"Erreur formatage date: {e}")
            return str(self.email.received_date)[:10]
    
    def _create_category_badge(self) -> QLabel:
        """Crée un badge de catégorie."""
        category = self.email.ai_analysis.category
        
        # Emojis et couleurs par catégorie
        category_config = {
            'cv': ('💼', '#28a745', 'CV'),
            'rdv': ('📅', '#007bff', 'RDV'),
            'facture': ('💰', '#ffc107', 'Facture'),
            'support': ('🛠️', '#dc3545', 'Support'),
            'partenariat': ('🤝', '#17a2b8', 'Partenariat'),
            'spam': ('🚫', '#6c757d', 'Spam'),
            'general': ('📧', '#6c757d', 'Général')
        }
        
        emoji, color, text = category_config.get(category, ('📧', '#6c757d', category.capitalize()))
        
        badge = QLabel(f"{emoji} {text}")
        badge.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
            }}
        """)
        badge.setToolTip(f"Catégorie: {text}")
        
        return badge
    
    def mousePressEvent(self, event):
        """Gère le clic sur la carte."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.email)
    
    def _apply_style(self):
        """Applique le style à la carte."""
        # Style différent selon lu/non lu
        if self.email.is_read:
            bg_color = "#ffffff"
            border_color = "#dee2e6"
        else:
            bg_color = "#f8f9fa"
            border_color = "#007bff"
        
        self.setStyleSheet(f"""
            QFrame#email-card {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                margin: 2px 0;
            }}
            QFrame#email-card:hover {{
                border-color: #007bff;
                background-color: #e7f3ff;
            }}
        """)