"""
Vue liste des emails avec design moderne.
"""
import logging
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime, timedelta

from models.email_model import Email

logger = logging.getLogger(__name__)

class EmailItemWidget(QFrame):
    """Widget pour afficher un email dans la liste."""
    
    clicked = pyqtSignal(object)
    
    def __init__(self, email: Email, parent=None):
        super().__init__(parent)
        self.email = email
        self.selected = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface du widget email."""
        self.setObjectName("email-item")
        self.setFixedHeight(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        # Ligne 1: Expéditeur et date
        header_layout = QHBoxLayout()
        
        # Expéditeur
        sender_label = QLabel(self.email.get_sender_name())
        sender_label.setObjectName("sender-label")
        sender_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        header_layout.addWidget(sender_label)
        
        header_layout.addStretch()
        
        # Date
        date_label = QLabel(self._format_date(self.email.datetime))
        date_label.setObjectName("date-label")
        date_label.setFont(QFont("Arial", 11))
        header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # Ligne 2: Sujet
        subject_label = QLabel(self.email.subject)
        subject_label.setObjectName("subject-label")
        subject_label.setFont(QFont("Arial", 12))
        subject_label.setWordWrap(True)
        layout.addWidget(subject_label)
        
        # Ligne 3: Aperçu et badges
        footer_layout = QHBoxLayout()
        
        # Aperçu
        preview_label = QLabel(self.email.snippet[:80] + "..." if len(self.email.snippet) > 80 else self.email.snippet)
        preview_label.setObjectName("preview-label")
        preview_label.setFont(QFont("Arial", 10))
        footer_layout.addWidget(preview_label)
        
        footer_layout.addStretch()
        
        # Badges
        self._add_badges(footer_layout)
        
        layout.addLayout(footer_layout)
        
        # Appliquer le style
        self._apply_style()
    
    def _add_badges(self, layout: QHBoxLayout):
        """Ajoute les badges (catégorie, priorité, etc.)."""
        # Badge catégorie (si analysé par IA)
        if hasattr(self.email, 'ai_info') and self.email.ai_info:
            category = self.email.ai_info.get('category', 'general')
            category_badge = self._create_badge(category, self._get_category_color(category))
            layout.addWidget(category_badge)
            
            # Badge priorité
            priority = self.email.ai_info.get('priority', 1)
            if priority > 2:
                priority_badge = self._create_badge("⚡", "#ff4444")
                layout.addWidget(priority_badge)
        
        # Badge non lu
        if self.email.is_unread:
            unread_badge = self._create_badge("●", "#0066cc")
            layout.addWidget(unread_badge)
        
        # Badge important
        if self.email.is_important:
            important_badge = self._create_badge("⭐", "#ffaa00")
            layout.addWidget(important_badge)
    
    def _create_badge(self, text: str, color: str) -> QLabel:
        """Crée un badge coloré."""
        badge = QLabel(text)
        badge.setObjectName("badge")
        badge.setStyleSheet(f"""
            QLabel#badge {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: bold;
                margin-left: 5px;
            }}
        """)
        return badge
    
    def _get_category_color(self, category: str) -> str:
        """Retourne la couleur associée à une catégorie."""
        colors = {
            'cv': '#9c27b0',
            'rdv': '#2196f3',
            'spam': '#f44336',
            'facture': '#ff9800',
            'support': '#4caf50',
            'partenariat': '#3f51b5',
            'newsletter': '#795548',
            'important': '#e91e63',
            'general': '#607d8b'
        }
        return colors.get(category, '#607d8b')
    
    def _format_date(self, date: datetime) -> str:
        """Formate la date pour l'affichage."""
        now = datetime.now()
        
        if date.date() == now.date():
            return date.strftime("%H:%M")
        elif date.date() == (now.date() - timedelta(days=1)):
            return "Hier"
        elif date.year == now.year:
            return date.strftime("%d/%m")
        else:
            return date.strftime("%d/%m/%Y")
    
    def _apply_style(self):
        """Applique le style au widget."""
        base_style = """
            QFrame#email-item {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 2px;
            }
            
            QFrame#email-item:hover {
                background-color: #f5f5f5;
                border-color: #cccccc;
            }
            
            QLabel#sender-label {
                color: #000000;
            }
            
            QLabel#date-label {
                color: #666666;
            }
            
            QLabel#subject-label {
                color: #333333;
            }
            
            QLabel#preview-label {
                color: #666666;
            }
        """
        
        # Style différent pour les emails non lus
        if self.email.is_unread:
            base_style += """
                QFrame#email-item {
                    background-color: #f8f9ff;
                    border-left: 4px solid #0066cc;
                }
                
                QLabel#sender-label {
                    font-weight: bold;
                }
                
                QLabel#subject-label {
                    font-weight: bold;
                }
            """
        
        # Style pour la sélection
        if self.selected:
            base_style += """
                QFrame#email-item {
                    background-color: #e3f2fd;
                    border-color: #0066cc;
                }
            """
        
        self.setStyleSheet(base_style)
    
    def set_selected(self, selected: bool):
        """Définit l'état de sélection."""
        self.selected = selected
        self._apply_style()
    
    def mousePressEvent(self, event):
        """Gère le clic sur l'email."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.email)
        super().mousePressEvent(event)

class EmailListView(QWidget):
    """Vue liste des emails avec scrolling."""
    
    email_selected = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.emails = []
        self.email_widgets = []
        self.selected_widget = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setObjectName("list-header")
        header.setFixedHeight(50)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Titre
        self.title_label = QLabel("Boîte de réception")
        self.title_label.setObjectName("list-title")
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Compteur
        self.count_label = QLabel("0 emails")
        self.count_label.setObjectName("count-label")
        self.count_label.setFont(QFont("Arial", 12))
        header_layout.addWidget(self.count_label)
        
        layout.addWidget(header)
        
        # Zone de scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget conteneur pour les emails
        self.emails_container = QWidget()
        self.emails_layout = QVBoxLayout(self.emails_container)
        self.emails_layout.setContentsMargins(5, 5, 5, 5)
        self.emails_layout.setSpacing(5)
        
        scroll_area.setWidget(self.emails_container)
        layout.addWidget(scroll_area)
        
        # Message vide
        self.empty_message = QLabel("Aucun email à afficher")
        self.empty_message.setObjectName("empty-message")
        self.empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_message.setFont(QFont("Arial", 14))
        self.empty_message.setVisible(False)
        layout.addWidget(self.empty_message)
        
        self._apply_style()
    
    def _apply_style(self):
        """Applique le style à la vue."""
        self.setStyleSheet("""
            QFrame#list-header {
                background-color: #f8f8f8;
                border-bottom: 1px solid #e0e0e0;
            }
            
            QLabel#list-title {
                color: #000000;
            }
            
            QLabel#count-label {
                color: #666666;
            }
            
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            
            QLabel#empty-message {
                color: #999999;
                margin: 50px;
            }
        """)
    
    def update_emails(self, emails: List[Email]):
        """Met à jour la liste des emails."""
        self.emails = emails
        self._clear_widgets()
        
        if not emails:
            self.empty_message.setVisible(True)
            self.count_label.setText("0 emails")
            return
        
        self.empty_message.setVisible(False)
        self.count_label.setText(f"{len(emails)} emails")
        
        # Créer les widgets des emails
        for email in emails:
            widget = EmailItemWidget(email)
            widget.clicked.connect(self._on_email_clicked)
            self.emails_layout.addWidget(widget)
            self.email_widgets.append(widget)
        
        # Spacer pour pousser les emails vers le haut
        self.emails_layout.addStretch()
    
    def _clear_widgets(self):
        """Supprime tous les widgets d'emails."""
        for widget in self.email_widgets:
            widget.deleteLater()
        self.email_widgets.clear()
        self.selected_widget = None
    
    def _on_email_clicked(self, email: Email):
        """Gère le clic sur un email."""
        # Désélectionner l'ancien widget
        if self.selected_widget:
            self.selected_widget.set_selected(False)
        
        # Sélectionner le nouveau widget
        sender_widget = self.sender()
        if isinstance(sender_widget, EmailItemWidget):
            sender_widget.set_selected(True)
            self.selected_widget = sender_widget
        
        # Émettre le signal
        self.email_selected.emit(email)
    
    def set_title(self, title: str):
        """Définit le titre de la liste."""
        self.title_label.setText(title)
    
    def get_selected_email(self) -> Optional[Email]:
        """Retourne l'email sélectionné."""
        if self.selected_widget:
            return self.selected_widget.email
        return None
    
    def select_first_email(self):
        """Sélectionne le premier email de la liste."""
        if self.email_widgets:
            self.email_widgets[0].clicked.emit(self.email_widgets[0].email)