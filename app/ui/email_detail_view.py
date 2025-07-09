"""
Vue détaillée d'un email avec fonctionnalités IA.
"""
import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QTextEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime

from models.email_model import Email
from gmail_client import GmailClient
from ai_processor import AIProcessor

logger = logging.getLogger(__name__)

class EmailDetailView(QWidget):
    """Vue détaillée d'un email avec analyse IA."""
    
    reply_requested = pyqtSignal(object)
    forward_requested = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor, parent=None):
        super().__init__(parent)
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.current_email = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Zone de scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget principal
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Message par défaut
        self.empty_state = QLabel("Sélectionnez un email pour le visualiser")
        self.empty_state.setObjectName("empty-state")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setFont(QFont("Arial", 16))
        main_layout.addWidget(self.empty_state)
        
        # Contenu de l'email (masqué par défaut)
        self.email_content = QWidget()
        self.email_content.setVisible(False)
        self._setup_email_content()
        main_layout.addWidget(self.email_content)
        
        main_layout.addStretch()
        
        scroll_area.setWidget(main_widget)
        layout.addWidget(scroll_area)
        
        self._apply_style()
    
    def _setup_email_content(self):
        """Configure le contenu de l'email."""
        layout = QVBoxLayout(self.email_content)
        layout.setSpacing(20)
        
        # En-tête de l'email
        self.header = self._create_header()
        layout.addWidget(self.header)
        
        # Analyse IA
        self.ai_analysis = self._create_ai_analysis()
        layout.addWidget(self.ai_analysis)
        
        # Barre d'actions
        self.actions_bar = self._create_actions_bar()
        layout.addWidget(self.actions_bar)
        
        # Corps de l'email
        self.body_text = QTextEdit()
        self.body_text.setObjectName("email-body")
        self.body_text.setReadOnly(True)
        self.body_text.setFont(QFont("Arial", 12))
        self.body_text.setMinimumHeight(400)
        layout.addWidget(self.body_text)
    
    def _create_header(self) -> QWidget:
        """Crée l'en-tête de l'email."""
        header = QFrame()
        header.setObjectName("email-header")
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Sujet
        self.subject_label = QLabel()
        self.subject_label.setObjectName("email-subject")
        self.subject_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.subject_label.setWordWrap(True)
        layout.addWidget(self.subject_label)
        
        # Informations expéditeur
        sender_layout = QHBoxLayout()
        
        # Avatar/Initiales
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("sender-avatar")
        self.avatar_label.setFixedSize(40, 40)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        sender_layout.addWidget(self.avatar_label)
        
        # Infos expéditeur
        sender_info_layout = QVBoxLayout()
        
        self.sender_name_label = QLabel()
        self.sender_name_label.setObjectName("sender-name")
        self.sender_name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        sender_info_layout.addWidget(self.sender_name_label)
        
        self.sender_email_label = QLabel()
        self.sender_email_label.setObjectName("sender-email")
        self.sender_email_label.setFont(QFont("Arial", 11))
        sender_info_layout.addWidget(self.sender_email_label)
        
        sender_layout.addLayout(sender_info_layout)
        sender_layout.addStretch()
        
        # Date
        self.date_label = QLabel()
        self.date_label.setObjectName("email-date")
        self.date_label.setFont(QFont("Arial", 11))
        sender_layout.addWidget(self.date_label)
        
        layout.addLayout(sender_layout)
        
        return header
    
    def _create_ai_analysis(self) -> QWidget:
        """Crée la section d'analyse IA."""
        analysis = QFrame()
        analysis.setObjectName("ai-analysis")
        
        layout = QVBoxLayout(analysis)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Titre
        title = QLabel("🤖 Analyse IA")
        title.setObjectName("ai-title")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Badges d'analyse
        self.analysis_badges = QHBoxLayout()
        layout.addLayout(self.analysis_badges)
        
        # Résumé d'analyse
        self.analysis_summary = QLabel()
        self.analysis_summary.setObjectName("ai-summary")
        self.analysis_summary.setFont(QFont("Arial", 11))
        self.analysis_summary.setWordWrap(True)
        layout.addWidget(self.analysis_summary)
        
        # Actions suggérées
        self.suggested_actions = QHBoxLayout()
        layout.addLayout(self.suggested_actions)
        
        return analysis
    
    def _create_actions_bar(self) -> QWidget:
        """Crée la barre d'actions."""
        actions_bar = QFrame()
        actions_bar.setObjectName("actions-bar")
        
        layout = QHBoxLayout(actions_bar)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Bouton répondre
        reply_btn = QPushButton("↩️ Répondre")
        reply_btn.setObjectName("action-button")
        reply_btn.clicked.connect(self._on_reply_clicked)
        layout.addWidget(reply_btn)
        
        # Bouton transférer
        forward_btn = QPushButton("➡️ Transférer")
        forward_btn.setObjectName("action-button")
        forward_btn.clicked.connect(self._on_forward_clicked)
        layout.addWidget(forward_btn)
        
        # Bouton réponse automatique
        auto_reply_btn = QPushButton("🤖 Réponse IA")
        auto_reply_btn.setObjectName("ai-button")
        auto_reply_btn.clicked.connect(self._on_auto_reply_clicked)
        layout.addWidget(auto_reply_btn)
        
        layout.addStretch()
        
        # Bouton marquer comme lu/non lu
        self.read_btn = QPushButton("👁️ Marquer comme lu")
        self.read_btn.setObjectName("action-button")
        self.read_btn.clicked.connect(self._on_toggle_read)
        layout.addWidget(self.read_btn)
        
        # Bouton important
        self.important_btn = QPushButton("⭐ Important")
        self.important_btn.setObjectName("action-button")
        self.important_btn.clicked.connect(self._on_toggle_important)
        layout.addWidget(self.important_btn)
        
        return actions_bar
    
    def _apply_style(self):
        """Applique le style à la vue."""
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
            
            QLabel#empty-state {
                color: #999999;
                margin: 100px;
            }
            
            QFrame#email-header {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            
            QLabel#email-subject {
                color: #000000;
            }
            
            QLabel#sender-avatar {
                background-color: #000000;
                color: #ffffff;
                border-radius: 20px;
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
            
            QFrame#ai-analysis {
                background-color: #f0f8ff;
                border: 1px solid #cce0ff;
                border-radius: 8px;
            }
            
            QLabel#ai-title {
                color: #0066cc;
            }
            
            QLabel#ai-summary {
                color: #333333;
            }
            
            QFrame#actions-bar {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            
            QPushButton#action-button {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            
            QPushButton#action-button:hover {
                background-color: #f0f0f0;
            }
            
            QPushButton#ai-button {
                background-color: #0066cc;
                color: #ffffff;
                border: 1px solid #0066cc;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            
            QPushButton#ai-button:hover {
                background-color: #0052a3;
            }
            
            QTextEdit#email-body {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                color: #333333;
            }
            
            QScrollArea {
                border: none;
            }
        """)
    
    def display_email(self, email: Email):
        """Affiche un email dans la vue."""
        if not email:
            self._show_empty_state()
            return
        
        self.current_email = email
        self.empty_state.setVisible(False)
        self.email_content.setVisible(True)
        
        # Mettre à jour l'en-tête
        self.subject_label.setText(email.subject)
        self.sender_name_label.setText(email.get_sender_name())
        self.sender_email_label.setText(email.get_sender_email())
        self.date_label.setText(self._format_date(email.datetime))
        
        # Avatar avec initiales
        initials = self._get_initials(email.get_sender_name())
        self.avatar_label.setText(initials)
        
        # Corps de l'email
        self.body_text.setPlainText(email.body)
        
        # Analyse IA
        self._update_ai_analysis(email)
        
        # Mettre à jour les boutons
        self._update_action_buttons(email)
    
    def _show_empty_state(self):
        """Affiche l'état vide."""
        self.current_email = None
        self.empty_state.setVisible(True)
        self.email_content.setVisible(False)
    
    def _format_date(self, date: datetime) -> str:
        """Formate la date pour l'affichage."""
        return date.strftime("%d/%m/%Y à %H:%M")
    
    def _get_initials(self, name: str) -> str:
        """Extrait les initiales d'un nom."""
        words = name.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        elif len(words) == 1:
            return words[0][0].upper()
        return "?"
    
    def _update_ai_analysis(self, email: Email):
        """Met à jour l'analyse IA."""
        # Effacer les anciens badges
        self._clear_layout(self.analysis_badges)
        self._clear_layout(self.suggested_actions)
        
        if not hasattr(email, 'ai_info') or not email.ai_info:
            self.analysis_summary.setText("Analyse IA non disponible")
            return
        
        ai_info = email.ai_info
        
        # Badges d'analyse
        category = ai_info.get('category', 'general')
        category_badge = self._create_analysis_badge(f"📁 {category.upper()}", self._get_category_color(category))
        self.analysis_badges.addWidget(category_badge)
        
        priority = ai_info.get('priority', 1)
        if priority > 1:
            priority_colors = {2: "#ffaa00", 3: "#ff4444"}
            priority_badge = self._create_analysis_badge(f"⚡ PRIORITÉ {priority}", priority_colors.get(priority, "#ffaa00"))
            self.analysis_badges.addWidget(priority_badge)
        
        # Badge sentiment
        sentiment = ai_info.get('sentiment')
        if sentiment:
            sentiment_text = sentiment.get('label', 'neutral')
            sentiment_color = "#4caf50" if sentiment_text == "POSITIVE" else "#f44336" if sentiment_text == "NEGATIVE" else "#9e9e9e"
            sentiment_badge = self._create_analysis_badge(f"💭 {sentiment_text}", sentiment_color)
            self.analysis_badges.addWidget(sentiment_badge)
        
        self.analysis_badges.addStretch()
        
        # Résumé d'analyse
        summary_parts = []
        
        if category != 'general':
            summary_parts.append(f"Catégorisé comme: {category}")
        
        if priority > 1:
            summary_parts.append(f"Priorité: {'élevée' if priority == 3 else 'moyenne'}")
        
        if ai_info.get('should_auto_respond'):
            summary_parts.append("Réponse automatique recommandée")
        
        if ai_info.get('meeting_info'):
            summary_parts.append("Demande de rendez-vous détectée")
        
        summary_text = " • ".join(summary_parts) if summary_parts else "Email analysé automatiquement"
        self.analysis_summary.setText(summary_text)
        
        # Actions suggérées
        if ai_info.get('should_auto_respond'):
            auto_respond_btn = QPushButton("🤖 Répondre automatiquement")
            auto_respond_btn.setObjectName("suggested-action")
            auto_respond_btn.clicked.connect(self._on_auto_reply_clicked)
            self.suggested_actions.addWidget(auto_respond_btn)
        
        if ai_info.get('meeting_info'):
            calendar_btn = QPushButton("📅 Ajouter au calendrier")
            calendar_btn.setObjectName("suggested-action")
            calendar_btn.clicked.connect(self._on_add_to_calendar)
            self.suggested_actions.addWidget(calendar_btn)
        
        self.suggested_actions.addStretch()
    
    def _create_analysis_badge(self, text: str, color: str) -> QLabel:
        """Crée un badge d'analyse."""
        badge = QLabel(text)
        badge.setObjectName("analysis-badge")
        badge.setStyleSheet(f"""
            QLabel#analysis-badge {{
                background-color: {color};
                color: white;
                border-radius: 12px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: bold;
                margin-right: 5px;
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
    
    def _update_action_buttons(self, email: Email):
        """Met à jour les boutons d'action."""
        # Bouton lu/non lu
        if email.is_unread:
            self.read_btn.setText("👁️ Marquer comme lu")
        else:
            self.read_btn.setText("👁️‍🗨️ Marquer comme non lu")
        
        # Bouton important
        if email.is_important:
            self.important_btn.setText("⭐ Retirer important")
            self.important_btn.setStyleSheet("QPushButton { background-color: #fff3cd; }")
        else:
            self.important_btn.setText("⭐ Marquer important")
            self.important_btn.setStyleSheet("")
    
    def _on_reply_clicked(self):
        """Gère le clic sur répondre."""
        if self.current_email:
            self.reply_requested.emit(self.current_email)
    
    def _on_forward_clicked(self):
        """Gère le clic sur transférer."""
        if self.current_email:
            self.forward_requested.emit(self.current_email)
    
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
                QMessageBox.information(self, "Succès", "Événement ajouté au calendrier!")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Erreur", "Impossible d'ajouter l'événement au calendrier")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout au calendrier: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'ajout au calendrier: {e}")
    
    def _on_toggle_read(self):
        """Toggle l'état lu/non lu."""
        if not self.current_email:
            return
        
        try:
            # Mettre à jour via Gmail API
            if self.current_email.is_unread:
                # Marquer comme lu
                self.gmail_client.mark_as_read(self.current_email.id)
                self.current_email.labels.remove('UNREAD')
            else:
                # Marquer comme non lu
                self.gmail_client.mark_as_unread(self.current_email.id)
                self.current_email.labels.append('UNREAD')
            
            # Mettre à jour l'affichage
            self._update_action_buttons(self.current_email)
            
        except Exception as e:
            logger.error(f"Erreur lors du changement d'état lu/non lu: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la mise à jour: {e}")
    
    def _on_toggle_important(self):
        """Toggle l'état important."""
        if not self.current_email:
            return
        
        try:
            # Mettre à jour via Gmail API
            if self.current_email.is_important:
                # Retirer important
                self.gmail_client.remove_important(self.current_email.id)
                if 'IMPORTANT' in self.current_email.labels:
                    self.current_email.labels.remove('IMPORTANT')
            else:
                # Marquer important
                self.gmail_client.mark_as_important(self.current_email.id)
                self.current_email.labels.append('IMPORTANT')
            
            # Mettre à jour l'affichage
            self._update_action_buttons(self.current_email)
            
        except Exception as e:
            logger.error(f"Erreur lors du changement d'état important: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la mise à jour: {e}")