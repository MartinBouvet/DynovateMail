#!/usr/bin/env python3
"""
Vue détaillée d'un email CORRIGÉE - Affichage propre et lisible.
"""
import logging
from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from models.email_model import Email

logger = logging.getLogger(__name__)

class EmailDetailView(QWidget):
    """Vue détaillée CORRIGÉE d'un email."""
    
    action_requested = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        self.current_email = None
        
        self.setObjectName("email-detail-view")
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface CORRIGÉE."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Message par défaut
        self.no_selection_widget = self._create_no_selection_widget()
        layout.addWidget(self.no_selection_widget)
        
        # Contenu de l'email (caché par défaut)
        self.email_content_widget = self._create_email_content_widget()
        self.email_content_widget.hide()
        layout.addWidget(self.email_content_widget)
    
    def _create_no_selection_widget(self) -> QWidget:
        """Widget affiché quand aucun email n'est sélectionné."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 60, 40, 60)
        
        # Icône
        icon_label = QLabel("📧")
        icon_label.setFont(QFont("Arial", 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #bdbdbd;")
        layout.addWidget(icon_label)
        
        # Texte principal
        title_label = QLabel("Sélectionnez un email")
        title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #424242; margin: 16px 0;")
        layout.addWidget(title_label)
        
        # Texte descriptif
        desc_label = QLabel("Cliquez sur un email dans la liste pour voir son contenu détaillé et les suggestions IA.")
        desc_label.setFont(QFont("Inter", 13))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #757575; line-height: 1.5;")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        return widget
    
    def _create_email_content_widget(self) -> QWidget:
        """Widget de contenu d'email CORRIGÉ."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # Header de l'email
        self.email_header = self._create_email_header()
        layout.addWidget(self.email_header)
        
        # Actions
        self.email_actions = self._create_email_actions()
        layout.addWidget(self.email_actions)
        
        # Contenu
        self.email_body = self._create_email_body()
        layout.addWidget(self.email_body)
        
        # Analyse IA
        self.ai_analysis_section = self._create_ai_analysis_section()
        layout.addWidget(self.ai_analysis_section)
        
        return widget
    
    def _create_email_header(self) -> QFrame:
        """Header de l'email CORRIGÉ."""
        header = QFrame()
        header.setObjectName("email-header")
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        
        # Ligne 1: Expéditeur et date
        first_row = QHBoxLayout()
        first_row.setSpacing(15)
        
        self.sender_label = QLabel()
        self.sender_label.setObjectName("sender-name")
        self.sender_label.setFont(QFont("Inter", 15, QFont.Weight.Bold))
        first_row.addWidget(self.sender_label)
        
        first_row.addStretch()
        
        self.date_label = QLabel()
        self.date_label.setObjectName("email-date")
        self.date_label.setFont(QFont("Inter", 11))
        first_row.addWidget(self.date_label)
        
        layout.addLayout(first_row)
        
        # Ligne 2: Email address
        self.email_address_label = QLabel()
        self.email_address_label.setObjectName("email-address")
        self.email_address_label.setFont(QFont("Inter", 11))
        layout.addWidget(self.email_address_label)
        
        # Ligne 3: Sujet
        self.subject_label = QLabel()
        self.subject_label.setObjectName("email-subject")
        self.subject_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.subject_label.setWordWrap(True)
        layout.addWidget(self.subject_label)
        
        return header
    
    def _create_email_actions(self) -> QFrame:
        """Barre d'actions CORRIGÉE."""
        actions = QFrame()
        actions.setObjectName("email-actions")
        
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        
        # Boutons d'action
        self.reply_btn = QPushButton("↩️ Répondre")
        self.reply_btn.setObjectName("action-btn")
        self.reply_btn.clicked.connect(lambda: self.action_requested.emit("reply", self.current_email))
        layout.addWidget(self.reply_btn)
        
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.setObjectName("action-btn")
        self.forward_btn.clicked.connect(lambda: self.action_requested.emit("forward", self.current_email))
        layout.addWidget(self.forward_btn)
        
        self.archive_btn = QPushButton("📁 Archiver")
        self.archive_btn.setObjectName("action-btn")
        self.archive_btn.clicked.connect(lambda: self.action_requested.emit("archive", self.current_email))
        layout.addWidget(self.archive_btn)
        
        layout.addStretch()
        
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setObjectName("delete-btn")
        self.delete_btn.clicked.connect(lambda: self.action_requested.emit("delete", self.current_email))
        layout.addWidget(self.delete_btn)
        
        return actions
    
    def _create_email_body(self) -> QFrame:
        """Zone de contenu CORRIGÉE."""
        body_frame = QFrame()
        body_frame.setObjectName("email-body-frame")
        
        layout = QVBoxLayout(body_frame)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Titre
        title = QLabel("📄 Contenu")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Zone de texte
        self.content_display = QTextEdit()
        self.content_display.setObjectName("email-content")
        self.content_display.setReadOnly(True)
        self.content_display.setFont(QFont("Inter", 12))
        self.content_display.setMinimumHeight(200)
        layout.addWidget(self.content_display)
        
        return body_frame
    
    def _create_ai_analysis_section(self) -> QFrame:
        """Section d'analyse IA CORRIGÉE."""
        ai_frame = QFrame()
        ai_frame.setObjectName("ai-analysis-frame")
        
        layout = QVBoxLayout(ai_frame)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Titre
        title = QLabel("🤖 Analyse IA")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Contenu de l'analyse
        self.ai_content = QLabel("Aucune analyse disponible")
        self.ai_content.setObjectName("ai-analysis-content")
        self.ai_content.setWordWrap(True)
        self.ai_content.setFont(QFont("Inter", 11))
        self.ai_content.setMinimumHeight(80)
        layout.addWidget(self.ai_content)
        
        return ai_frame
    
    def _apply_style(self):
        """Style CORRIGÉ pour une bonne lisibilité."""
        self.setStyleSheet("""
            QWidget#email-detail-view {
                background-color: #ffffff;
            }
            
            /* === HEADER EMAIL === */
            QFrame#email-header {
                background-color: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                margin-bottom: 8px;
            }
            
            QLabel#sender-name {
                color: #1a1a1a;
                font-weight: 700;
            }
            
            QLabel#email-date {
                color: #757575;
                font-weight: 500;
            }
            
            QLabel#email-address {
                color: #757575;
                font-weight: 400;
            }
            
            QLabel#email-subject {
                color: #1a1a1a;
                font-weight: 700;
                margin-top: 8px;
            }
            
            /* === ACTIONS === */
            QFrame#email-actions {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-bottom: 8px;
            }
            
            QPushButton#action-btn {
                background-color: #1976d2;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12px;
                min-width: 100px;
                min-height: 32px;
            }
            
            QPushButton#action-btn:hover {
                background-color: #1565c0;
            }
            
            QPushButton#action-btn:pressed {
                background-color: #0d47a1;
            }
            
            QPushButton#delete-btn {
                background-color: #d32f2f;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12px;
                min-width: 100px;
                min-height: 32px;
            }
            
            QPushButton#delete-btn:hover {
                background-color: #c62828;
            }
            
            /* === CONTENU EMAIL === */
            QFrame#email-body-frame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                margin-bottom: 8px;
            }
            
            QLabel#section-title {
                color: #1a1a1a;
                font-weight: 700;
                margin-bottom: 8px;
            }
            
            QTextEdit#email-content {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                color: #424242;
                line-height: 1.6;
                font-family: 'Inter', Arial, sans-serif;
            }
            
            QTextEdit#email-content:focus {
                border-color: #1976d2;
            }
            
            /* === ANALYSE IA === */
            QFrame#ai-analysis-frame {
                background-color: #f3e5f5;
                border: 2px solid #9c27b0;
                border-radius: 12px;
            }
            
            QLabel#ai-analysis-content {
                background-color: #ffffff;
                border: 1px solid #ce93d8;
                border-radius: 8px;
                padding: 15px;
                color: #424242;
                line-height: 1.5;
                font-family: 'Inter', Arial, sans-serif;
            }
            
            /* === SCROLLBARS === */
            QTextEdit QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            
            QTextEdit QScrollBar::handle:vertical {
                background-color: #bdbdbd;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            
            QTextEdit QScrollBar::handle:vertical:hover {
                background-color: #9e9e9e;
            }
            
            QTextEdit QScrollBar::add-line:vertical,
            QTextEdit QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
    
    def show_email(self, email: Email):
        """Affiche un email CORRIGÉ."""
        self.current_email = email
        
        # Cacher le message par défaut, afficher le contenu
        self.no_selection_widget.hide()
        self.email_content_widget.show()
        
        # Mettre à jour le header
        sender_name = email.get_sender_name()
        if len(sender_name) > 50:
            sender_name = sender_name[:47] + "..."
        self.sender_label.setText(sender_name)
        
        self.email_address_label.setText(f"<{email.sender}>")
        
        subject = email.subject or "(Aucun sujet)"
        if len(subject) > 100:
            subject = subject[:97] + "..."
        self.subject_label.setText(subject)
        
        if email.received_date:
            date_str = email.received_date.strftime("%d/%m/%Y à %H:%M")
            self.date_label.setText(date_str)
        else:
            self.date_label.setText("Date inconnue")
        
        # Mettre à jour le contenu
        body_text = email.body or email.snippet or "(Aucun contenu)"
        
        # Nettoyer le HTML
        import re
        clean_text = re.sub(r'<[^>]+>', '', body_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = clean_text.strip()
        
        if len(clean_text) > 5000:
            clean_text = clean_text[:5000] + "\n\n[Contenu tronqué...]"
        
        self.content_display.setPlainText(clean_text)
        
        # Mettre à jour l'analyse IA
        self._update_ai_analysis()
        
        logger.info(f"Affichage email: {email.id}")
    
    def _update_ai_analysis(self):
        """Met à jour l'analyse IA CORRIGÉE."""
        if not self.current_email or not hasattr(self.current_email, 'ai_analysis'):
            self.ai_content.setText("Aucune analyse IA disponible pour cet email.")
            return
        
        analysis = self.current_email.ai_analysis
        if not analysis:
            self.ai_content.setText("Aucune analyse IA disponible pour cet email.")
            return
        
        # Construire le texte d'analyse de façon lisible
        category_names = {
            'cv': 'Candidature/CV',
            'rdv': 'Rendez-vous',
            'support': 'Support technique',
            'facture': 'Facture',
            'spam': 'Spam',
            'general': 'Email général'
        }
        
        category_display = category_names.get(getattr(analysis, 'category', 'general'), 'Autre')
        confidence = getattr(analysis, 'confidence', 0) * 100
        priority = getattr(analysis, 'priority', 3)
        should_respond = getattr(analysis, 'should_auto_respond', False)
        reasoning = getattr(analysis, 'reasoning', 'Aucun raisonnement disponible')
        
        ai_text = f"""📂 Catégorie détectée: {category_display}
📊 Niveau de confiance: {confidence:.0f}%
⚡ Priorité: {self._get_priority_text(priority)}
🤖 Réponse automatique: {'✅ Recommandée' if should_respond else '❌ Non recommandée'}

🧠 Analyse de l'IA:
{reasoning}"""
        
        # Ajouter des informations extraites si disponibles
        extracted_info = getattr(analysis, 'extracted_info', {})
        if extracted_info:
            ai_text += "\n\n📋 Informations extraites:"
            for key, value in extracted_info.items():
                if value:
                    ai_text += f"\n• {key}: {value}"
        
        self.ai_content.setText(ai_text)
    
    def _get_priority_text(self, priority: int) -> str:
        """Convertit la priorité en texte CORRIGÉ."""
        priority_map = {
            1: "🔴 Très urgent",
            2: "🟠 Urgent", 
            3: "🟡 Normal",
            4: "🟢 Faible",
            5: "⚪ Très faible"
        }
        return priority_map.get(priority, f"Priorité {priority}")
    
    def clear_selection(self):
        """Efface la sélection."""
        self.current_email = None
        self.email_content_widget.hide()
        self.no_selection_widget.show()