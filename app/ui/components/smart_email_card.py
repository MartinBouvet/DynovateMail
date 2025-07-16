#!/usr/bin/env python3
"""
Carte d'email intelligente avec informations IA et actions rapides.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette

from models.email_model import Email
from ai.smart_classifier import EmailAnalysis

logger = logging.getLogger(__name__)

class CategoryBadge(QLabel):
    """Badge de catégorie avec couleur."""
    
    def __init__(self, category: str, confidence: float):
        super().__init__()
        self.category = category
        self.confidence = confidence
        
        # Texte et couleurs selon la catégorie
        category_config = {
            'cv': ('CV', '#28a745'),
            'rdv': ('RDV', '#007bff'),
            'facture': ('Facture', '#ffc107'),
            'support': ('Support', '#dc3545'),
            'spam': ('Spam', '#6c757d'),
            'general': ('Général', '#17a2b8')
        }
        
        text, color = category_config.get(category, ('Autre', '#6c757d'))
        self.setText(text)
        
        self.setStyleSheet(f"""
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
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setToolTip(f"Confiance: {confidence:.0%}")

class PriorityIndicator(QWidget):
    """Indicateur de priorité visuel."""
    
    def __init__(self, priority: int):
        super().__init__()
        self.priority = priority
        self.setFixedSize(20, 20)
        
    def paintEvent(self, event):
        """Dessine l'indicateur de priorité."""
        from PyQt6.QtGui import QPainter, QBrush
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Couleurs selon la priorité
        colors = {
            1: QColor("#dc3545"),  # Rouge - Urgent
            2: QColor("#fd7e14"),  # Orange - Haute
            3: QColor("#ffc107"),  # Jaune - Normale
            4: QColor("#28a745"),  # Vert - Basse
            5: QColor("#6c757d")   # Gris - Très basse
        }
        
        color = colors.get(self.priority, QColor("#6c757d"))
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Cercle plein pour priorité haute, cercle vide pour basse
        if self.priority <= 2:
            painter.drawEllipse(2, 2, 16, 16)
        else:
            painter.setPen(color)
            painter.setBrush(QBrush())
            painter.drawEllipse(2, 2, 16, 16)

class QuickActionButton(QPushButton):
    """Bouton d'action rapide."""
    
    def __init__(self, text: str, icon: str = "", action_type: str = ""):
        super().__init__(f"{icon} {text}" if icon else text)
        self.action_type = action_type
        self.setFixedHeight(28)
        
        self.setStyleSheet("""
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
               border-color: #adb5bd;
           }
           
           QPushButton:pressed {
               background-color: #dee2e6;
           }
       """)

class SmartEmailCard(QFrame):
   """Carte d'email intelligente avec IA et actions rapides."""
   
   clicked = pyqtSignal(object)
   action_requested = pyqtSignal(str, object)  # action_type, email
   
   def __init__(self, email: Email, ai_analysis: Optional[EmailAnalysis] = None):
       super().__init__()
       self.email = email
       self.ai_analysis = ai_analysis
       self.is_selected = False
       self.is_hovered = False
       
       self.setObjectName("email-card")
       self.setFixedHeight(120)
       self.setCursor(Qt.CursorShape.PointingHandCursor)
       
       self._setup_ui()
       self._apply_style()
       self._setup_animations()
       
       # Effet d'ombre
       shadow = QGraphicsDropShadowEffect()
       shadow.setBlurRadius(8)
       shadow.setColor(QColor(0, 0, 0, 30))
       shadow.setOffset(0, 2)
       self.setGraphicsEffect(shadow)
   
   def _setup_ui(self):
       """Configure l'interface de la carte."""
       layout = QVBoxLayout(self)
       layout.setContentsMargins(16, 12, 16, 12)
       layout.setSpacing(8)
       
       # Header avec expéditeur et métadonnées
       header = self._create_header()
       layout.addWidget(header)
       
       # Sujet de l'email
       subject = self._create_subject()
       layout.addWidget(subject)
       
       # Aperçu du contenu
       preview = self._create_preview()
       layout.addWidget(preview)
       
       # Footer avec badges et actions
       footer = self._create_footer()
       layout.addWidget(footer)
   
   def _create_header(self) -> QWidget:
       """Crée le header avec expéditeur et informations."""
       header = QWidget()
       layout = QHBoxLayout(header)
       layout.setContentsMargins(0, 0, 0, 0)
       layout.setSpacing(8)
       
       # Indicateur de priorité
       if self.ai_analysis:
           priority_indicator = PriorityIndicator(self.ai_analysis.priority)
           layout.addWidget(priority_indicator)
       
       # Nom de l'expéditeur
       sender_name = self.email.get_sender_name()
       sender_label = QLabel(sender_name)
       sender_label.setObjectName("sender-name")
       sender_label.setFont(QFont("Inter", 13, QFont.Weight.Bold))
       layout.addWidget(sender_label)
       
       layout.addStretch()
       
       # Date
       date_str = self._format_date(self.email.received_date)
       date_label = QLabel(date_str)
       date_label.setObjectName("email-date")
       date_label.setFont(QFont("Inter", 11))
       layout.addWidget(date_label)
       
       # Indicateur non lu
       if not self.email.is_read:
           unread_indicator = QLabel("●")
           unread_indicator.setObjectName("unread-indicator")
           unread_indicator.setFont(QFont("Arial", 16))
           layout.addWidget(unread_indicator)
       
       return header
   
   def _create_subject(self) -> QWidget:
       """Crée la ligne du sujet."""
       subject_label = QLabel(self.email.subject or "(Aucun sujet)")
       subject_label.setObjectName("email-subject")
       font = QFont("Inter", 14)
       if not self.email.is_read:
           font.setWeight(QFont.Weight.Bold)
       subject_label.setFont(font)
       subject_label.setWordWrap(True)
       
       return subject_label
   
   def _create_preview(self) -> QWidget:
       """Crée l'aperçu du contenu."""
       # Texte de prévisualisation
       preview_text = self._get_preview_text()
       preview_label = QLabel(preview_text)
       preview_label.setObjectName("email-preview")
       preview_label.setFont(QFont("Inter", 12))
       preview_label.setWordWrap(True)
       preview_label.setMaximumHeight(40)
       
       return preview_label
   
   def _create_footer(self) -> QWidget:
       """Crée le footer avec badges et actions."""
       footer = QWidget()
       layout = QHBoxLayout(footer)
       layout.setContentsMargins(0, 0, 0, 0)
       layout.setSpacing(8)
       
       # Badge de catégorie IA
       if self.ai_analysis:
           category_badge = CategoryBadge(
               self.ai_analysis.category, 
               self.ai_analysis.confidence
           )
           layout.addWidget(category_badge)
       
       layout.addStretch()
       
       # Actions rapides selon la catégorie
       if self.ai_analysis:
           actions = self._get_quick_actions()
           for action_text, action_icon, action_type in actions:
               btn = QuickActionButton(action_text, action_icon, action_type)
               btn.clicked.connect(lambda checked, at=action_type: self.action_requested.emit(at, self.email))
               layout.addWidget(btn)
       
       return footer
   
   def _get_preview_text(self) -> str:
       """Génère le texte de prévisualisation."""
       if not self.email.body:
           return "(Pas de contenu)"
       
       # Nettoyer le texte
       import re
       clean_text = re.sub(r'<[^>]+>', '', self.email.body)  # Supprimer HTML
       clean_text = re.sub(r'\s+', ' ', clean_text)  # Normaliser espaces
       
       # Tronquer à 100 caractères
       if len(clean_text) > 100:
           return clean_text[:97] + "..."
       
       return clean_text
   
   def _get_quick_actions(self) -> list:
       """Retourne les actions rapides selon la catégorie."""
       if not self.ai_analysis:
           return []
       
       actions_by_category = {
           'cv': [
               ("Répondre", "↩️", "reply_cv"),
               ("Archiver", "📁", "archive")
           ],
           'rdv': [
               ("Calendrier", "📅", "add_to_calendar"),
               ("Répondre", "↩️", "reply_meeting")
           ],
           'support': [
               ("Répondre", "↩️", "reply_support"),
               ("Urgent", "🚨", "mark_urgent")
           ],
           'facture': [
               ("Payer", "💳", "process_payment"),
               ("Archiver", "📁", "archive")
           ]
       }
       
       return actions_by_category.get(self.ai_analysis.category, [("Répondre", "↩️", "reply")])
   
   def _format_date(self, date: datetime) -> str:
       """Formate la date de manière intelligente."""
       if not date:
           return ""
       
       now = datetime.now()
       diff = now - date
       
       if diff.days == 0:
           return date.strftime("%H:%M")
       elif diff.days == 1:
           return "Hier"
       elif diff.days < 7:
           return date.strftime("%a")  # Lun, Mar, etc.
       elif date.year == now.year:
           return date.strftime("%d/%m")
       else:
           return date.strftime("%d/%m/%y")
   
   def _setup_animations(self):
       """Configure les animations."""
       self.hover_animation = QPropertyAnimation(self, b"geometry")
       self.hover_animation.setDuration(200)
       self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
   
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
       
       # Style pour email non lu
       if not self.email.is_read:
           base_style += """
               #email-card {
                   border-left: 4px solid #007bff;
                   background-color: #f8f9ff;
               }
           """
       
       # Style pour sélection
       if self.is_selected:
           base_style += """
               #email-card {
                   border-color: #007bff;
                   background-color: #e3f2fd;
               }
           """
       
       # Style pour hover
       if self.is_hovered:
           base_style += """
               #email-card {
                   border-color: #adb5bd;
                   transform: translateY(-2px);
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
   
   def update_ai_analysis(self, analysis: EmailAnalysis):
       """Met à jour l'analyse IA."""
       self.ai_analysis = analysis
       # Reconstruire l'interface si nécessaire
       # Pour simplifier, on recrée juste le footer
       self._create_footer()