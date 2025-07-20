#!/usr/bin/env python3
"""
Vue détaillée d'un email simplifiée et fonctionnelle.
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
    """Vue détaillée simplifiée d'un email."""
    
    action_requested = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        self.current_email = None
        
        self.setObjectName("email-detail-view")
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface de la vue détaillée."""
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
        """Crée le widget affiché quand aucun email n'est sélectionné."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Icône
        icon_label = QLabel("📧")
        icon_label.setFont(QFont("Arial", 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #dee2e6;")
        layout.addWidget(icon_label)
        
        # Texte principal
        title_label = QLabel("Sélectionnez un email")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #6c757d; margin: 16px 0;")
        layout.addWidget(title_label)
        
        # Texte descriptif
        desc_label = QLabel("Cliquez sur un email dans la liste pour voir son contenu détaillé et les suggestions IA.")
        desc_label.setFont(QFont("Arial", 14))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #adb5bd; line-height: 1.5;")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        return widget
    
    def _create_email_content_widget(self) -> QWidget:
        """Crée le widget de contenu d'email."""
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
        """Crée le header de l'email."""
        header = QFrame()
        header.setObjectName("email-header")
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Première ligne : Expéditeur et date
        first_row = QHBoxLayout()
        
        self.sender_label = QLabel()
        self.sender_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        first_row.addWidget(self.sender_label)
        
        first_row.addStretch()
        
        self.date_label = QLabel()
        self.date_label.setFont(QFont("Arial", 12))
        self.date_label.setStyleSheet("color: #6c757d;")
        first_row.addWidget(self.date_label)
        
        layout.addLayout(first_row)
        
        # Deuxième ligne : Email
        self.email_address_label = QLabel()
        self.email_address_label.setFont(QFont("Arial", 11))
        self.email_address_label.setStyleSheet("color: #6c757d;")
        layout.addWidget(self.email_address_label)
        
        # Troisième ligne : Sujet
        self.subject_label = QLabel()
        self.subject_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.subject_label.setWordWrap(True)
        layout.addWidget(self.subject_label)
        
        header.setStyleSheet("""
            #email-header {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
        
        return header
    
    def _create_email_actions(self) -> QFrame:
        """Crée la barre d'actions."""
        actions = QFrame()
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Boutons d'action
        self.reply_btn = QPushButton("↩️ Répondre")
        self.reply_btn.clicked.connect(lambda: self.action_requested.emit("reply", self.current_email))
        layout.addWidget(self.reply_btn)
        
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.clicked.connect(lambda: self.action_requested.emit("forward", self.current_email))
        layout.addWidget(self.forward_btn)
        
        self.archive_btn = QPushButton("📁 Archiver")
        self.archive_btn.clicked.connect(lambda: self.action_requested.emit("archive", self.current_email))
        layout.addWidget(self.archive_btn)
        
        layout.addStretch()
        
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.delete_btn.clicked.connect(lambda: self.action_requested.emit("delete", self.current_email))
        layout.addWidget(self.delete_btn)
        
        # Style des boutons normaux
        for btn in [self.reply_btn, self.forward_btn, self.archive_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
        
        return actions
    
    def _create_email_body(self) -> QFrame:
        """Crée la zone de contenu de l'email."""
        body_frame = QFrame()
        layout = QVBoxLayout(body_frame)
        layout.setSpacing(12)
        
        # Titre
        title = QLabel("📄 Contenu")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Zone de texte
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.setFont(QFont("Arial", 12))
        self.content_display.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
                color: #495057;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.content_display)
        
        return body_frame
    
    def _create_ai_analysis_section(self) -> QFrame:
        """Crée la section d'analyse IA."""
        ai_frame = QFrame()
        layout = QVBoxLayout(ai_frame)
        layout.setSpacing(12)
        
        # Titre
        title = QLabel("🤖 Analyse IA")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Contenu de l'analyse
        self.ai_content = QLabel("Aucune analyse disponible")
        self.ai_content.setWordWrap(True)
        self.ai_content.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 16px;
                color: #495057;
            }
        """)
        layout.addWidget(self.ai_content)
        
        return ai_frame
    
    def _apply_style(self):
        """Applique le style à la vue."""
        self.setStyleSheet("""
            #email-detail-view {
                background-color: #ffffff;
            }
        """)
    
    def show_email(self, email: Email):
        """Affiche un email dans la vue détaillée."""
        self.current_email = email
        
        # Cacher le message par défaut, afficher le contenu
        self.no_selection_widget.hide()
        self.email_content_widget.show()
        
        # Mettre à jour le header
        self.sender_label.setText(email.get_sender_name())
        self.email_address_label.setText(f"<{email.sender}>")
        self.subject_label.setText(email.subject or "(Aucun sujet)")
        
        if email.received_date:
            date_str = email.received_date.strftime("%d/%m/%Y à %H:%M")
            self.date_label.setText(date_str)
        
        # Mettre à jour le contenu
        body_text = email.body or email.snippet or "(Aucun contenu)"
        # Nettoyer le HTML simple
        import re
        clean_text = re.sub(r'<[^>]+>', '', body_text)
        self.content_display.setPlainText(clean_text)
        
        # Mettre à jour l'analyse IA
        self._update_ai_analysis()
        
        logger.info(f"Affichage détaillé de l'email: {email.id}")
    
    def _update_ai_analysis(self):
        """Met à jour l'affichage de l'analyse IA."""
        if not self.current_email or not hasattr(self.current_email, 'ai_analysis'):
            self.ai_content.setText("Aucune analyse IA disponible")
            return
        
        analysis = self.current_email.ai_analysis
        if not analysis:
            self.ai_content.setText("Aucune analyse IA disponible")
            return
        
        # Construire le texte d'analyse
        ai_text = f"""
📂 Catégorie: {getattr(analysis, 'category', 'Inconnue').upper()}
📊 Confiance: {getattr(analysis, 'confidence', 0) * 100:.0f}%
⚡ Priorité: {self._get_priority_text(getattr(analysis, 'priority', 3))}
🤖 Réponse auto: {'Recommandée' if getattr(analysis, 'should_auto_respond', False) else 'Non recommandée'}

🧠 Raisonnement:
{getattr(analysis, 'reasoning', 'Aucun raisonnement disponible')}
        """.strip()
        
        self.ai_content.setText(ai_text)
    
    def _get_priority_text(self, priority: int) -> str:
        """Convertit la priorité numérique en texte."""
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