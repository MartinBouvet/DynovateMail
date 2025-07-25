#!/usr/bin/env python3
"""
Carte d'email intelligente CORRIGÉE - Affichage propre et lisible.
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
    """Carte d'email intelligente avec affichage CORRIGÉ."""
    
    clicked = pyqtSignal(object)
    action_requested = pyqtSignal(str, object)
    
    def __init__(self, email: Email, ai_analysis: Optional[object] = None):
        super().__init__()
        self.email = email
        self.ai_analysis = ai_analysis
        self.is_selected = False
        self.is_hovered = False
        
        self.setObjectName("email-card")
        self.setFixedHeight(120)  # Hauteur réduite et fixe
        self.setMinimumWidth(350)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Configuration initiale
        self._setup_ui()
        self._apply_style()
        
        # Effet d'ombre léger
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(6)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 1)
        self.setGraphicsEffect(shadow)
    
    def _setup_ui(self):
        """Configure l'interface de la carte."""
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)
        
        # Ligne 1: Expéditeur, Date, Indicateur non lu
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Nom de l'expéditeur
        sender_name = self.email.get_sender_name()
        if len(sender_name) > 25:
            sender_name = sender_name[:22] + "..."
        
        self.sender_label = QLabel(sender_name)
        self.sender_label.setObjectName("sender-name")
        self.sender_label.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        header_layout.addWidget(self.sender_label)
        
        header_layout.addStretch()
        
        # Date
        date_str = self._format_date(self.email.received_date)
        self.date_label = QLabel(date_str)
        self.date_label.setObjectName("email-date")
        self.date_label.setFont(QFont("Inter", 11))
        header_layout.addWidget(self.date_label)
        
        # Indicateur non lu
        if not self.email.is_read:
            unread_dot = QLabel("●")
            unread_dot.setObjectName("unread-dot")
            unread_dot.setFont(QFont("Arial", 12))
            header_layout.addWidget(unread_dot)
        
        main_layout.addLayout(header_layout)
        
        # Ligne 2: Sujet
        subject_text = self.email.subject or "(Aucun sujet)"
        if len(subject_text) > 50:
            subject_text = subject_text[:47] + "..."
        
        self.subject_label = QLabel(subject_text)
        self.subject_label.setObjectName("email-subject")
        font = QFont("Inter", 14)
        if not self.email.is_read:
            font.setWeight(QFont.Weight.Bold)
        else:
            font.setWeight(QFont.Weight.Medium)
        self.subject_label.setFont(font)
        main_layout.addWidget(self.subject_label)
        
        # Ligne 3: Prévisualisation
        preview_text = self._get_preview_text()
        if len(preview_text) > 60:
            preview_text = preview_text[:57] + "..."
        
        self.preview_label = QLabel(preview_text)
        self.preview_label.setObjectName("email-preview")
        self.preview_label.setFont(QFont("Inter", 12))
        main_layout.addWidget(self.preview_label)
        
        # Ligne 4: Badge et actions
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        
        # Badge catégorie IA
        if self.ai_analysis and hasattr(self.ai_analysis, 'category'):
            category_badge = self._create_category_badge()
            footer_layout.addWidget(category_badge)
        
        footer_layout.addStretch()
        
        # Actions rapides (seulement si pertinentes)
        if self.ai_analysis and hasattr(self.ai_analysis, 'should_auto_respond'):
            if getattr(self.ai_analysis, 'should_auto_respond', False):
                ai_btn = QPushButton("🤖 IA")
                ai_btn.setObjectName("ai-action-btn")
                ai_btn.setFixedSize(45, 24)
                ai_btn.clicked.connect(lambda: self.action_requested.emit("ai_response", self.email))
                footer_layout.addWidget(ai_btn)
        
        main_layout.addLayout(footer_layout)
        
        # Appliquer le layout
        self.setLayout(main_layout)
    
    def _create_category_badge(self) -> QLabel:
        """Crée le badge de catégorie."""
        category = getattr(self.ai_analysis, 'category', 'general')
        
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
        badge.setFixedHeight(20)
        badge.setMinimumWidth(50)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 10px;
                font-weight: 600;
                text-align: center;
            }}
        """)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        return badge
    
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
            return date.strftime("%d/%m %H:%M")
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                if minutes < 1:
                    return "maintenant"
                else:
                    return f"{minutes}min"
            else:
                return date.strftime("%H:%M")
        elif diff.days == 1:
            return "hier"
        elif diff.days < 7:
            days = ['lun', 'mar', 'mer', 'jeu', 'ven', 'sam', 'dim']
            return days[date.weekday()]
        else:
            return date.strftime("%d/%m")
    
    def _apply_style(self):
        """Applique le style à la carte."""
        # Style de base
        base_style = """
            QFrame#email-card {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 2px;
            }
            
            QLabel#sender-name {
                color: #1a1a1a;
                font-weight: 700;
            }
            
            QLabel#email-date {
                color: #666666;
                font-weight: 500;
            }
            
            QLabel#unread-dot {
                color: #007bff;
            }
            
            QLabel#email-subject {
                color: #2c2c2c;
                font-weight: 600;
            }
            
            QLabel#email-preview {
                color: #666666;
                font-weight: 400;
            }
            
            QPushButton#ai-action-btn {
                background-color: #e3f2fd;
                color: #1976d2;
                border: 1px solid #90caf9;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 600;
            }
            
            QPushButton#ai-action-btn:hover {
                background-color: #bbdefb;
            }
        """
        
        # Modifications selon l'état
        if not self.email.is_read:
            base_style += """
                QFrame#email-card {
                    border-left: 3px solid #007bff;
                    background-color: #f8fbff;
                }
            """
        
        if self.is_selected:
            base_style += """
                QFrame#email-card {
                    border: 2px solid #007bff;
                    background-color: #e3f2fd;
                }
            """
        
        if self.is_hovered and not self.is_selected:
            base_style += """
                QFrame#email-card {
                    border-color: #90caf9;
                    background-color: #fafafa;
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
        """Met à jour l'analyse IA."""
        self.ai_analysis = analysis
        self._apply_style()