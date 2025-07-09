"""
Vue détaillée d'un email améliorée avec gestion intelligente de l'espace.
"""
import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QTextEdit, QScrollArea, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime

from models.email_model import Email
from gmail_client import GmailClient
from ai_processor import AIProcessor

logger = logging.getLogger(__name__)

class EmptyStateWidget(QWidget):
    """Widget d'état vide avec design moderne."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface de l'état vide."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Icône
        icon_label = QLabel("📧")
        icon_label.setObjectName("empty-icon")
        icon_label.setFont(QFont("Arial", 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Titre
        title_label = QLabel("Sélectionnez un email")
        title_label.setObjectName("empty-title")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Choisissez un email dans la liste pour voir son contenu et ses détails")
        desc_label.setObjectName("empty-description")
        desc_label.setFont(QFont("Arial", 12))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Conseils
        tips_frame = QFrame()
        tips_frame.setObjectName("tips-frame")
        tips_layout = QVBoxLayout(tips_frame)
        tips_layout.setContentsMargins(20, 15, 20, 15)
        
        tips_title = QLabel("💡 Conseils")
        tips_title.setObjectName("tips-title")
        tips_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        tips_layout.addWidget(tips_title)
        
        tips = [
            "• Utilisez les filtres pour organiser vos emails",
            "• L'IA classe automatiquement vos messages",
            "• Les réponses automatiques peuvent être activées",
            "• Ctrl+N pour composer un nouvel email"
        ]
        
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setObjectName("tip-item")
            tip_label.setFont(QFont("Arial", 11))
            tips_layout.addWidget(tip_label)
        
        layout.addWidget(tips_frame)
        layout.addStretch()

class CompactEmailHeader(QFrame):
    """En-tête compact pour l'email."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("compact-header")
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'en-tête compact."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        # Ligne 1: Sujet
        self.subject_label = QLabel()
        self.subject_label.setObjectName("email-subject")
        self.subject_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.subject_label.setWordWrap(True)
        layout.addWidget(self.subject_label)
        
        # Ligne 2: Expéditeur et date
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)
        
        # Avatar compact
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("compact-avatar")
        self.avatar_label.setFixedSize(28, 28)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        info_layout.addWidget(self.avatar_label)
        
        # Infos expéditeur
        sender_layout = QVBoxLayout()
        sender_layout.setSpacing(2)
        
        self.sender_name_label = QLabel()
        self.sender_name_label.setObjectName("sender-name")
        self.sender_name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        sender_layout.addWidget(self.sender_name_label)
        
        self.sender_email_label = QLabel()
        self.sender_email_label.setObjectName("sender-email")
        self.sender_email_label.setFont(QFont("Arial", 10))
        sender_layout.addWidget(self.sender_email_label)
        
        info_layout.addLayout(sender_layout)
        info_layout.addStretch()
        
        # Date et badges
        right_layout = QVBoxLayout()
        right_layout.setSpacing(4)
        
        self.date_label = QLabel()
        self.date_label.setObjectName("email-date")
        self.date_label.setFont(QFont("Arial", 10))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(self.date_label)
        
        # Container pour les badges
        self.badges_layout = QHBoxLayout()
        self.badges_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addLayout(self.badges_layout)
        
        info_layout.addLayout(right_layout)
        layout.addLayout(info_layout)
    
    def update_email(self, email: Email):
        """Met à jour l'en-tête avec les infos de l'email."""
        self.subject_label.setText(email.subject)
        self.sender_name_label.setText(email.get_sender_name())
        self.sender_email_label.setText(email.get_sender_email())
        self.date_label.setText(self._format_date(email.datetime))
        
        # Avatar avec initiales
        initials = self._get_initials(email.get_sender_name())
        self.avatar_label.setText(initials)
        
        # Badges
        self._update_badges(email)
    
    def _format_date(self, date: datetime) -> str:
        """Formate la date pour l'affichage."""
        return date.strftime("%d/%m à %H:%M")
    
    def _get_initials(self, name: str) -> str:
        """Extrait les initiales d'un nom."""
        words = name.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        elif len(words) == 1:
            return words[0][0].upper()
        return "?"
    
    def _update_badges(self, email: Email):
        """Met à jour les badges."""
        # Nettoyer les anciens badges
        while self.badges_layout.count():
            child = self.badges_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Ajouter nouveaux badges
        if email.is_unread:
            unread_badge = self._create_badge("●", "#0066cc")
            self.badges_layout.addWidget(unread_badge)
        
        if email.is_important:
            important_badge = self._create_badge("⭐", "#ffaa00")
            self.badges_layout.addWidget(important_badge)
        
        if hasattr(email, 'ai_info') and email.ai_info:
            priority = email.ai_info.get('priority', 1)
            if priority > 2:
                priority_badge = self._create_badge("⚡", "#ff4444")
                self.badges_layout.addWidget(priority_badge)
    
    def _create_badge(self, text: str, color: str) -> QLabel:
        """Crée un petit badge."""
        badge = QLabel(text)
        badge.setObjectName("header-badge")
        badge.setStyleSheet(f"""
            QLabel#header-badge {{
                background-color: {color};
                color: white;
                border-radius: 8px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: bold;
                margin-left: 3px;
            }}
        """)
        return badge

class QuickActionsBar(QFrame):
    """Barre d'actions rapides compacte."""
    
    reply_clicked = pyqtSignal()
    forward_clicked = pyqtSignal()
    auto_reply_clicked = pyqtSignal()
    toggle_read_clicked = pyqtSignal()
    toggle_important_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quick-actions")
        self.current_email = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure la barre d'actions."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(8)
        
        # Actions principales
        self.reply_btn = QPushButton("↩️")
        self.reply_btn.setObjectName("quick-action")
        self.reply_btn.setToolTip("Répondre")
        self.reply_btn.clicked.connect(self.reply_clicked.emit)
        layout.addWidget(self.reply_btn)
        
        self.forward_btn = QPushButton("➡️")
        self.forward_btn.setObjectName("quick-action")
        self.forward_btn.setToolTip("Transférer")
        self.forward_btn.clicked.connect(self.forward_clicked.emit)
        layout.addWidget(self.forward_btn)
        
        self.auto_reply_btn = QPushButton("🤖")
        self.auto_reply_btn.setObjectName("quick-action-ai")
        self.auto_reply_btn.setToolTip("Réponse IA")
        self.auto_reply_btn.clicked.connect(self.auto_reply_clicked.emit)
        layout.addWidget(self.auto_reply_btn)
        
        # Séparateur
        separator = QFrame()
        separator.setObjectName("action-separator")
        separator.setFixedWidth(1)
        separator.setFixedHeight(20)
        layout.addWidget(separator)
        
        # Actions de statut
        self.read_btn = QPushButton("👁️")
        self.read_btn.setObjectName("quick-action")
        self.read_btn.setToolTip("Marquer comme lu")
        self.read_btn.clicked.connect(self.toggle_read_clicked.emit)
        layout.addWidget(self.read_btn)
        
        self.important_btn = QPushButton("⭐")
        self.important_btn.setObjectName("quick-action")
        self.important_btn.setToolTip("Marquer comme important")
        self.important_btn.clicked.connect(self.toggle_important_clicked.emit)
        layout.addWidget(self.important_btn)
        
        layout.addStretch()
    
    def update_email(self, email: Email):
        """Met à jour les boutons selon l'email."""
        self.current_email = email
        
        # Bouton lu/non lu
        if email.is_unread:
            self.read_btn.setText("👁️")
            self.read_btn.setToolTip("Marquer comme lu")
        else:
            self.read_btn.setText("👁️‍🗨️")
            self.read_btn.setToolTip("Marquer comme non lu")
        
        # Bouton important
        if email.is_important:
            self.important_btn.setText("⭐")
            self.important_btn.setStyleSheet("QPushButton { background-color: #fff3cd; }")
            self.important_btn.setToolTip("Retirer important")
        else:
            self.important_btn.setText("☆")
            self.important_btn.setStyleSheet("")
            self.important_btn.setToolTip("Marquer important")

class EmailDetailView(QWidget):
    """Vue détaillée d'un email avec gestion intelligente de l'espace."""
    
    reply_requested = pyqtSignal(object)
    forward_requested = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor, parent=None):
        super().__init__(parent)
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.current_email = None
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface avec gestion d'état."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stack pour gérer les états
        self.content_stack = QStackedWidget()
        
        # État vide
        self.empty_state = EmptyStateWidget()
        self.content_stack.addWidget(self.empty_state)
        
        # État avec email
        self.email_content = self._create_email_content()
        self.content_stack.addWidget(self.email_content)
        
        # Commencer par l'état vide
        self.content_stack.setCurrentWidget(self.empty_state)
        
        layout.addWidget(self.content_stack)
    
    def _create_email_content(self) -> QWidget:
        """Crée le contenu de l'email."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # En-tête compact
        self.header = CompactEmailHeader()
        layout.addWidget(self.header)
        
        # Barre d'actions rapides
        self.actions_bar = QuickActionsBar()
        self.actions_bar.reply_clicked.connect(lambda: self.reply_requested.emit(self.current_email))
        self.actions_bar.forward_clicked.connect(lambda: self.forward_requested.emit(self.current_email))
        self.actions_bar.auto_reply_clicked.connect(self._on_auto_reply_clicked)
        self.actions_bar.toggle_read_clicked.connect(self._on_toggle_read)
        self.actions_bar.toggle_important_clicked.connect(self._on_toggle_important)
        layout.addWidget(self.actions_bar)
        
        # Analyse IA compacte (pliable)
        self.ai_section = self._create_ai_section()
        layout.addWidget(self.ai_section)
        
        # Corps de l'email
        self.body_scroll = QScrollArea()
        self.body_scroll.setWidgetResizable(True)
        self.body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.body_text = QTextEdit()
        self.body_text.setObjectName("email-body")
        self.body_text.setReadOnly(True)
        self.body_text.setFont(QFont("Arial", 11))
        
        self.body_scroll.setWidget(self.body_text)
        layout.addWidget(self.body_scroll)
        
        return widget
    
    def _create_ai_section(self) -> QWidget:
        """Crée la section d'analyse IA compacte."""
        section = QFrame()
        section.setObjectName("ai-section")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)
        
        # Header pliable
        header_layout = QHBoxLayout()
        
        self.ai_toggle_btn = QPushButton("🤖 Analyse IA")
        self.ai_toggle_btn.setObjectName("ai-toggle")
        self.ai_toggle_btn.setCheckable(True)
        self.ai_toggle_btn.setChecked(True)
        self.ai_toggle_btn.clicked.connect(self._toggle_ai_section)
        header_layout.addWidget(self.ai_toggle_btn)
        
        header_layout.addStretch()
        
        # Badges d'analyse rapide
        self.quick_badges = QHBoxLayout()
        header_layout.addLayout(self.quick_badges)
        
        layout.addLayout(header_layout)
        
        # Contenu détaillé (pliable)
        self.ai_details = QFrame()
        self.ai_details.setObjectName("ai-details")
        details_layout = QVBoxLayout(self.ai_details)
        details_layout.setContentsMargins(0, 5, 0, 0)
        
        self.ai_summary = QLabel()
        self.ai_summary.setObjectName("ai-summary")
        self.ai_summary.setFont(QFont("Arial", 10))
        self.ai_summary.setWordWrap(True)
        details_layout.addWidget(self.ai_summary)
        
        self.suggested_actions = QHBoxLayout()
        details_layout.addLayout(self.suggested_actions)
        
        layout.addWidget(self.ai_details)
        
        return section
    
    def _toggle_ai_section(self):
        """Plie/déplie la section IA."""
        is_expanded = self.ai_toggle_btn.isChecked()
        self.ai_details.setVisible(is_expanded)
        
        # Animation
        self.animation = QPropertyAnimation(self.ai_section, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if is_expanded:
            self.animation.setStartValue(50)
            self.animation.setEndValue(150)
        else:
            self.animation.setStartValue(150)
            self.animation.setEndValue(50)
        
        self.animation.start()
    
    def display_email(self, email: Email):
        """Affiche un email dans la vue."""
        if not email:
            self.content_stack.setCurrentWidget(self.empty_state)
            return
        
        self.current_email = email
        self.content_stack.setCurrentWidget(self.email_content)
        
        # Mettre à jour l'en-tête
        self.header.update_email(email)
        
        # Mettre à jour les actions
        self.actions_bar.update_email(email)
        
        # Corps de l'email
        self.body_text.setPlainText(email.body)
        
        # Analyse IA
        self._update_ai_analysis(email)
    
    def _update_ai_analysis(self, email: Email):
        """Met à jour l'analyse IA."""
        # Nettoyer les anciens badges
        self._clear_layout(self.quick_badges)
        self._clear_layout(self.suggested_actions)
        
        if not hasattr(email, 'ai_info') or not email.ai_info:
            self.ai_summary.setText("Analyse IA non disponible")
            return
        
        ai_info = email.ai_info
        
        # Badges rapides
        category = ai_info.get('category', 'general')
        if category != 'general':
            category_badge = self._create_badge(f"📁 {category.upper()}", self._get_category_color(category))
            self.quick_badges.addWidget(category_badge)
        
        priority = ai_info.get('priority', 1)
        if priority > 1:
            priority_colors = {2: "#ffaa00", 3: "#ff4444"}
            priority_badge = self._create_badge(f"⚡ P{priority}", priority_colors.get(priority, "#ffaa00"))
            self.quick_badges.addWidget(priority_badge)
        
        self.quick_badges.addStretch()
        
        # Résumé
        summary_parts = []
        if category != 'general':
            summary_parts.append(f"Catégorie: {category}")
        if priority > 1:
            summary_parts.append(f"Priorité: {'élevée' if priority == 3 else 'moyenne'}")
        if ai_info.get('should_auto_respond'):
            summary_parts.append("Réponse automatique recommandée")
        
        summary_text = " • ".join(summary_parts) if summary_parts else "Email analysé par l'IA"
        self.ai_summary.setText(summary_text)
        
        # Actions suggérées compactes
        if ai_info.get('should_auto_respond'):
            auto_btn = QPushButton("🤖 Auto")
            auto_btn.setObjectName("suggested-action-compact")
            auto_btn.setToolTip("Réponse automatique")
            auto_btn.clicked.connect(self._on_auto_reply_clicked)
            self.suggested_actions.addWidget(auto_btn)
        
        if ai_info.get('meeting_info'):
            calendar_btn = QPushButton("📅 RDV")
            calendar_btn.setObjectName("suggested-action-compact")
            calendar_btn.setToolTip("Ajouter au calendrier")
            calendar_btn.clicked.connect(self._on_add_to_calendar)
            self.suggested_actions.addWidget(calendar_btn)
        
        self.suggested_actions.addStretch()
    
    def _create_badge(self, text: str, color: str) -> QLabel:
        """Crée un badge compact."""
        badge = QLabel(text)
        badge.setObjectName("ai-badge")
        badge.setStyleSheet(f"""
            QLabel#ai-badge {{
                background-color: {color};
                color: white;
                border-radius: 8px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: bold;
                margin-right: 4px;
            }}
        """)
        return badge
    
    def _get_category_color(self, category: str) -> str:
        """Retourne la couleur d'une catégorie."""
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
    
    def _clear_layout(self, layout):
        """Efface tous les widgets d'un layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _apply_style(self):
        """Applique le style moderne."""
        self.setStyleSheet("""
            /* État vide */
            QLabel#empty-icon {
                color: #cccccc;
            }
            
            QLabel#empty-title {
                color: #333333;
                margin-bottom: 10px;
            }
            
            QLabel#empty-description {
                color: #666666;
                margin-bottom: 20px;
            }
            
            QFrame#tips-frame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                max-width: 300px;
            }
            
            QLabel#tips-title {
                color: #000000;
                margin-bottom: 8px;
            }
            
            QLabel#tip-item {
                color: #555555;
                margin: 2px 0px;
            }
            
            /* En-tête compact */
            QFrame#compact-header {
                background-color: #f8f8f8;
                border-bottom: 1px solid #e0e0e0;
            }
            
            QLabel#email-subject {
                color: #000000;
            }
            
            QLabel#compact-avatar {
                background-color: #000000;
                color: #ffffff;
                border-radius: 14px;
            }
            
            QLabel#sender-name {
                color: #000000;
            }
            
            QLabel#sender-email {
                color: #666666;
            }
            
            QLabel#email-date {
                color: #666666;
            }
            
            /* Actions rapides */
            QFrame#quick-actions {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
            }
            
            QPushButton#quick-action {
                background-color: #f8f8f8;
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 14px;
                min-width: 32px;
                max-width: 32px;
            }
            
            QPushButton#quick-action:hover {
                background-color: #e9ecef;
            }
            
            QPushButton#quick-action-ai {
                background-color: #0066cc;
                color: #ffffff;
                border: 1px solid #0066cc;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 14px;
                min-width: 32px;
                max-width: 32px;
            }
            
            QPushButton#quick-action-ai:hover {
                background-color: #0052a3;
            }
            
            QFrame#action-separator {
                background-color: #e0e0e0;
                border: none;
            }
            
            /* Section IA */
            QFrame#ai-section {
                background-color: #f0f8ff;
                border-bottom: 1px solid #cce0ff;
            }
            
            QPushButton#ai-toggle {
                background-color: transparent;
                color: #0066cc;
                border: none;
                text-align: left;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 0px;
            }
            
            QPushButton#ai-toggle:hover {
                color: #0052a3;
            }
            
            QFrame#ai-details {
                background-color: transparent;
            }
            
            QLabel#ai-summary {
                color: #333333;
            }
            
            QPushButton#suggested-action-compact {
                background-color: #ffffff;
                color: #0066cc;
                border: 1px solid #0066cc;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
                margin-right: 5px;
            }
            
            QPushButton#suggested-action-compact:hover {
                background-color: #f0f8ff;
            }
            
            /* Corps de l'email */
            QTextEdit#email-body {
                background-color: #ffffff;
                border: none;
                padding: 15px;
                color: #333333;
                line-height: 1.4;
            }
            
            /* Scroll Area */
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            
            QScrollBar:vertical {
                background-color: #f8f8f8;
                width: 8px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #cccccc;
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #999999;
            }
        """)
    
    def _on_auto_reply_clicked(self):
        """Gère le clic sur réponse automatique."""
        if not self.current_email:
            return
        
        try:
            # Générer une réponse automatique
            response = self.ai_processor.generate_auto_response(self.current_email)
            
            # Ouvrir la fenêtre de composition avec la réponse pré-remplie
            from ui.compose_view import ComposeView
            compose_dialog = ComposeView(
                self.gmail_client,
                self.parent(),
                to=self.current_email.get_sender_email(),
                subject=f"Re: {self.current_email.subject}",
                body=response,
                is_reply=True
            )
            compose_dialog.exec()
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de réponse automatique: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la génération de la réponse: {e}")
    
    def _on_add_to_calendar(self):
        """Ajoute l'événement au calendrier."""
        if not self.current_email or not hasattr(self.current_email, 'ai_info'):
            return
        
        meeting_info = self.current_email.ai_info.get('meeting_info')
        if not meeting_info:
            return
        
        try:
            # Ajouter au calendrier via le gestionnaire
            calendar_manager = self.parent().calendar_manager
            success = calendar_manager.add_event(meeting_info)
            
            if success:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Succès", "✅ Événement ajouté au calendrier!")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Erreur", "❌ Impossible d'ajouter l'événement au calendrier")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout au calendrier: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"❌ Erreur lors de l'ajout au calendrier: {e}")
    
    def _on_toggle_read(self):
        """Toggle l'état lu/non lu."""
        if not self.current_email:
            return
        
        try:
            # Simuler le changement d'état
            if self.current_email.is_unread:
                self.current_email.labels.remove('UNREAD')
            else:
                self.current_email.labels.append('UNREAD')
            
            # Mettre à jour l'affichage
            self.actions_bar.update_email(self.current_email)
            self.header.update_email(self.current_email)
            
        except Exception as e:
            logger.error(f"Erreur lors du changement d'état lu/non lu: {e}")
    
    def _on_toggle_important(self):
        """Toggle l'état important."""
        if not self.current_email:
            return
        
        try:
            # Simuler le changement d'état
            if self.current_email.is_important:
                if 'IMPORTANT' in self.current_email.labels:
                    self.current_email.labels.remove('IMPORTANT')
            else:
                self.current_email.labels.append('IMPORTANT')
            
            # Mettre à jour l'affichage
            self.actions_bar.update_email(self.current_email)
            self.header.update_email(self.current_email)
            
        except Exception as e:
            logger.error(f"Erreur lors du changement d'état important: {e}")
    
    def show_empty_state(self):
        """Affiche l'état vide."""
        self.current_email = None
        self.content_stack.setCurrentWidget(self.empty_state)