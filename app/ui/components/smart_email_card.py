#!/usr/bin/env python3
"""
Carte d'email intelligente corrigée.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from models.email_model import Email

logger = logging.getLogger(__name__)

class SmartEmailCard(QFrame):
    """Carte d'email intelligente sans problème de layout."""
    
    clicked = pyqtSignal(object)
    action_requested = pyqtSignal(str, object)
    
    def __init__(self, email: Email, ai_analysis: Optional[object] = None):
        super().__init__()
        self.email = email
        self.ai_analysis = ai_analysis
        self.is_selected = False
        self.is_hovered = False
        
        self.setObjectName("email-card")
        self.setFixedHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Configuration initiale
        self._setup_ui()
        self._apply_style()
        
        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def _setup_ui(self):
        """Configure l'interface de la carte - VERSION CORRIGÉE."""
        # Créer le layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)
        
        # Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # Nom de l'expéditeur
        sender_name = self.email.get_sender_name()
        self.sender_label = QLabel(sender_name)
        self.sender_label.setObjectName("sender-name")
        self.sender_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        header_layout.addWidget(self.sender_label)
        
        header_layout.addStretch()
        
        # Date
        date_str = self._format_date(self.email.received_date)
        self.date_label = QLabel(date_str)
        self.date_label.setObjectName("email-date")
        self.date_label.setFont(QFont("Arial", 11))
        header_layout.addWidget(self.date_label)
        
        # Indicateur non lu
        if not self.email.is_read:
            unread_indicator = QLabel("●")
            unread_indicator.setObjectName("unread-indicator")
            unread_indicator.setFont(QFont("Arial", 16))
            header_layout.addWidget(unread_indicator)
        
        main_layout.addWidget(header_widget)
        
        # Sujet
        subject_text = self.email.subject or "(Aucun sujet)"
        self.subject_label = QLabel(subject_text)
        self.subject_label.setObjectName("email-subject")
        font = QFont("Arial", 14)
        if not self.email.is_read:
            font.setWeight(QFont.Weight.Bold)
        self.subject_label.setFont(font)
        self.subject_label.setWordWrap(True)
        main_layout.addWidget(self.subject_label)
        
        # Prévisualisation
        preview_text = self._get_preview_text()
        self.preview_label = QLabel(preview_text)
        self.preview_label.setObjectName("email-preview")
        self.preview_label.setFont(QFont("Arial", 12))
        self.preview_label.setWordWrap(True)
        self.preview_label.setMaximumHeight(40)
        main_layout.addWidget(self.preview_label)
        
        # Footer avec badges IA
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)
        
        # Badge catégorie IA
        if self.ai_analysis and hasattr(self.ai_analysis, 'category'):
            category_badge = self._create_category_badge()
            footer_layout.addWidget(category_badge)
        
        footer_layout.addStretch()
        
        # Actions rapides
        if self.ai_analysis:
            actions = self._get_quick_actions()
            for action_text, action_type in actions[:2]:  # Limiter à 2 actions
                btn = QPushButton(action_text)
                btn.setFixedHeight(28)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f8f9fa;
                        border: 1px solid #dee2e6;
                        border-radius: 14px;
                        color: #495057;
                        font-size: 12px;
                        font-weight: 500;
                        padding: 4px 12px;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                    }
                """)
                btn.clicked.connect(lambda checked, at=action_type: self.action_requested.emit(at, self.email))
                footer_layout.addWidget(btn)
        
        main_layout.addWidget(footer_widget)
        
        # Appliquer le layout à la carte
        self.setLayout(main_layout)
    
    def _create_category_badge(self) -> QLabel:
        """Crée le badge de catégorie."""
        category = getattr(self.ai_analysis, 'category', 'general')
        confidence = getattr(self.ai_analysis, 'confidence', 0.0)
        
        category_config = {
            'cv': ('CV', '#28a745'),
            'rdv': ('RDV', '#007bff'),
            'facture': ('Facture', '#ffc107'),
            'support': ('Support', '#dc3545'),
            'spam': ('Spam', '#6c757d'),
            'general': ('Général', '#17a2b8')
        }
        
        text, color = category_config.get(category, ('Autre', '#6c757d'))
        
        badge = QLabel(text)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                min-width: 50px;
            }}
        """)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setToolTip(f"Confiance: {confidence:.0%}")
        
        return badge
    
    def _get_quick_actions(self) -> list:
        """Retourne les actions rapides selon la catégorie."""
        if not self.ai_analysis or not hasattr(self.ai_analysis, 'category'):
            return [("Répondre", "reply")]
        
        actions_by_category = {
            'cv': [("Répondre", "reply"), ("Archiver", "archive")],
            'rdv': [("Calendrier", "add_to_calendar"), ("Répondre", "reply")],
            'support': [("Répondre", "reply"), ("Urgent", "mark_urgent")],
            'facture': [("Archiver", "archive"), ("Répondre", "reply")],
            'spam': [("Supprimer", "delete"), ("Signaler", "report_spam")]
        }
        
        return actions_by_category.get(self.ai_analysis.category, [("Répondre", "reply")])
    
    def _get_preview_text(self) -> str:
        """Génère le texte de prévisualisation."""
        if not self.email.body and not self.email.snippet:
            return "(Pas de contenu)"
        
        text = self.email.snippet or self.email.body or ""
        
        # Nettoyer le texte
        import re
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = clean_text.strip()
        
        if len(clean_text) > 100:
            return clean_text[:97] + "..."
        
        return clean_text or "(Contenu vide)"
    
    def _format_date(self, date: datetime) -> str:
        """Formate la date de manière intelligente."""
        if not date:
            return ""
        
        # Convertir en datetime naive si nécessaire
        if hasattr(date, 'tzinfo') and date.tzinfo is not None:
            try:
                timestamp = date.timestamp()
                date = datetime.fromtimestamp(timestamp)
            except:
                date = date.replace(tzinfo=None)
        
        now = datetime.now()
        
        try:
            diff = now - date
        except TypeError:
            return date.strftime("%d/%m/%y %H:%M")
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                if minutes < 1:
                    return "À l'instant"
                else:
                    return f"Il y a {minutes} min"
            else:
                return date.strftime("%H:%M")
        elif diff.days == 1:
            return "Hier"
        elif diff.days < 7:
            days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
            return days[date.weekday()]
        elif date.year == now.year:
            return date.strftime("%d/%m")
        else:
            return date.strftime("%d/%m/%y")
    
    def _apply_style(self):
        """Applique le style à la carte."""
        base_style = """
            #email-card {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                margin: 4px 0;
            }
            
            #sender-name {
                color: #000000;
            }
            
            #email-date {
                color: #6c757d;
            }
            
            #unread-indicator {
                color: #007bff;
            }
            
            #email-subject {
                color: #000000;
            }
            
            #email-preview {
                color: #6c757d;
                line-height: 1.4;
            }
        """
        
        if not self.email.is_read:
            base_style += """
               #email-card {
                   border-left: 4px solid #007bff;
                   background-color: #f8f9ff;
               }
           """
       
        if self.is_selected:
           base_style += """
               #email-card {
                   border-color: #007bff;
                   background-color: #e3f2fd;
               }
           """
       
        if self.is_hovered:
           base_style += """
               #email-card {
                   border-color: #adb5bd;
               }
           """
       
        self.setStyleSheet(base_style)
   
    def set_selected(self, selected: bool):
       """Définit l'état de sélection."""
       self.is_selected = selected
       self._apply_style()
   
    def enterEvent(self, event):
       """Gère l'entrée de la souris."""
       self.is_hovered = True
       self._apply_style()
       super().enterEvent(event)
   
    def leaveEvent(self, event):
       """Gère la sortie de la souris."""
       self.is_hovered = False
       self._apply_style()
       super().leaveEvent(event)
   
    def mousePressEvent(self, event):
       """Gère le clic sur la carte."""
       if event.button() == Qt.MouseButton.LeftButton:
           self.clicked.emit(self.email)
       super().mousePressEvent(event)
   
    def update_ai_analysis(self, analysis):
       """Met à jour l'analyse IA sans recréer le layout."""
       self.ai_analysis = analysis
       # Juste mettre à jour le style
       self._apply_style()