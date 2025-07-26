#!/usr/bin/env python3
"""
Vue détaillée d'un email CORRIGÉE - Alignement parfait des boutons et du texte.
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
    """Vue détaillée CORRIGÉE d'un email avec alignement parfait."""
    
    action_requested = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        self.current_email = None
        
        self.setObjectName("email-detail-view")
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface CORRIGÉE avec alignement parfait."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Zone de scroll pour tout le contenu
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget de contenu scrollable
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        
        # Message par défaut
        self.no_selection_widget = self._create_no_selection_widget()
        self.content_layout.addWidget(self.no_selection_widget)
        
        # Contenu de l'email (caché par défaut)
        self.email_content_widget = self._create_email_content_widget()
        self.email_content_widget.hide()
        self.content_layout.addWidget(self.email_content_widget)
        
        # Spacer pour pousser le contenu vers le haut
        self.content_layout.addStretch()
        
        # Configurer le scroll
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
    
    def _create_no_selection_widget(self) -> QWidget:
        """Widget PARFAITEMENT CENTRÉ quand aucun email n'est sélectionné."""
        widget = QWidget()
        widget.setObjectName("no-selection-widget")
        
        # Layout principal centré
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(40, 0, 40, 0)
        main_layout.setSpacing(0)
        
        # Spacer du haut pour centrer verticalement
        main_layout.addStretch(1)
        
        # Container centré
        center_container = QWidget()
        center_container.setFixedSize(500, 300)  # Taille fixe pour un centrage parfait
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(25)
        
        # Icône
        icon_label = QLabel("📧")
        icon_label.setFont(QFont("Arial", 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #e0e0e0;")
        center_layout.addWidget(icon_label)
        
        # Texte principal
        title_label = QLabel("Sélectionnez un email")
        title_label.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #616161; margin: 0;")
        center_layout.addWidget(title_label)
        
        # Texte descriptif
        desc_label = QLabel("Cliquez sur un email dans la liste de gauche pour voir son contenu détaillé et les suggestions IA.")
        desc_label.setFont(QFont("Inter", 14))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #9e9e9e; line-height: 1.6; margin: 0; padding: 0;")
        center_layout.addWidget(desc_label)
        
        # Centrer le container horizontalement
        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        h_layout.addWidget(center_container)
        h_layout.addStretch(1)
        
        main_layout.addLayout(h_layout)
        
        # Spacer du bas pour centrer verticalement
        main_layout.addStretch(1)
        
        return widget
    
    def _create_email_content_widget(self) -> QWidget:
        """Widget de contenu d'email CORRIGÉ."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(25)
        layout.setContentsMargins(0, 0, 0, 0)
        
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
        """Header de l'email CORRIGÉ avec plus d'espace."""
        header = QFrame()
        header.setObjectName("email-header")
        header.setMinimumHeight(140)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # Ligne 1: Expéditeur et date
        first_row = QHBoxLayout()
        first_row.setSpacing(20)
        
        self.sender_label = QLabel()
        self.sender_label.setObjectName("sender-name")
        self.sender_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.sender_label.setWordWrap(True)
        first_row.addWidget(self.sender_label)
        
        first_row.addStretch()
        
        self.date_label = QLabel()
        self.date_label.setObjectName("email-date")
        self.date_label.setFont(QFont("Inter", 13))
        first_row.addWidget(self.date_label)
        
        layout.addLayout(first_row)
        
        # Ligne 2: Email address
        self.email_address_label = QLabel()
        self.email_address_label.setObjectName("email-address")
        self.email_address_label.setFont(QFont("Inter", 12))
        self.email_address_label.setWordWrap(True)
        layout.addWidget(self.email_address_label)
        
        # Ligne 3: Sujet
        self.subject_label = QLabel()
        self.subject_label.setObjectName("email-subject")
        self.subject_label.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        self.subject_label.setWordWrap(True)
        self.subject_label.setMinimumHeight(50)
        layout.addWidget(self.subject_label)
        
        return header
    
    def _create_email_actions(self) -> QFrame:
        """Barre d'actions PARFAITEMENT CENTRÉE et alignée."""
        actions = QFrame()
        actions.setObjectName("email-actions")
        actions.setFixedHeight(80)
        
        # Layout principal avec centrage parfait
        main_layout = QVBoxLayout(actions)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Spacer vertical pour centrer
        main_layout.addStretch(1)
        
        # Container des boutons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(25, 0, 25, 0)
        buttons_layout.setSpacing(0)  # Pas d'espacement par défaut
        
        # Centrage parfait avec des spacers
        buttons_layout.addStretch(2)  # Spacer gauche large
        
        # Boutons principaux - TAILLES ET ESPACEMENTS IDENTIQUES
        self.reply_btn = QPushButton("↩️ Répondre")
        self.reply_btn.setObjectName("action-btn")
        self.reply_btn.setFixedSize(140, 45)
        self.reply_btn.clicked.connect(lambda: self.action_requested.emit("reply", self.current_email))
        buttons_layout.addWidget(self.reply_btn)
        
        # Spacer identique entre chaque bouton
        buttons_layout.addSpacing(15)
        
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.setObjectName("action-btn")
        self.forward_btn.setFixedSize(140, 45)
        self.forward_btn.clicked.connect(lambda: self.action_requested.emit("forward", self.current_email))
        buttons_layout.addWidget(self.forward_btn)
        
        # Spacer identique
        buttons_layout.addSpacing(15)
        
        self.archive_btn = QPushButton("📁 Archiver")
        self.archive_btn.setObjectName("action-btn")
        self.archive_btn.setFixedSize(140, 45)
        self.archive_btn.clicked.connect(lambda: self.action_requested.emit("archive", self.current_email))
        buttons_layout.addWidget(self.archive_btn)
        
        # Spacer plus large avant le bouton supprimer
        buttons_layout.addSpacing(30)
        
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setObjectName("delete-btn")
        self.delete_btn.setFixedSize(140, 45)
        self.delete_btn.clicked.connect(lambda: self.action_requested.emit("delete", self.current_email))
        buttons_layout.addWidget(self.delete_btn)
        
        # Spacer droit pour équilibrer
        buttons_layout.addStretch(2)
        
        main_layout.addWidget(buttons_container)
        
        # Spacer vertical pour centrer
        main_layout.addStretch(1)
        
        return actions
    
    def _create_email_body(self) -> QFrame:
        """Zone de contenu CORRIGÉE avec hauteur appropriée."""
        body_frame = QFrame()
        body_frame.setObjectName("email-body-frame")
        body_frame.setMinimumHeight(300)
        
        layout = QVBoxLayout(body_frame)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)
        
        # Titre
        title = QLabel("📄 Contenu de l'email")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Zone de texte avec hauteur appropriée
        self.content_display = QTextEdit()
        self.content_display.setObjectName("email-content")
        self.content_display.setReadOnly(True)
        self.content_display.setFont(QFont("Inter", 13))
        self.content_display.setMinimumHeight(250)
        layout.addWidget(self.content_display)
        
        return body_frame
    
    def _create_ai_analysis_section(self) -> QFrame:
        """Section d'analyse IA CORRIGÉE avec plus d'espace."""
        ai_frame = QFrame()
        ai_frame.setObjectName("ai-analysis-frame")
        ai_frame.setMinimumHeight(200)
        
        layout = QVBoxLayout(ai_frame)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)
        
        # Titre
        title = QLabel("🤖 Analyse Intelligence Artificielle")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Contenu de l'analyse avec hauteur appropriée
        self.ai_content = QLabel("Aucune analyse disponible")
        self.ai_content.setObjectName("ai-analysis-content")
        self.ai_content.setWordWrap(True)
        self.ai_content.setFont(QFont("Inter", 13))
        self.ai_content.setMinimumHeight(120)
        self.ai_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.ai_content)
        
        return ai_frame
    
    def _apply_style(self):
        """Style CORRIGÉ pour une excellente lisibilité et alignement parfait."""
        self.setStyleSheet("""
            QWidget#email-detail-view {
                background-color: #ffffff;
            }
            
            /* === MESSAGE DE SÉLECTION === */
            QWidget#no-selection-widget {
                background-color: #ffffff;
            }
            
            /* === SCROLLBAR === */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #cbd3da;
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #9ea7ad;
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* === HEADER EMAIL === */
            QFrame#email-header {
                background-color: #f8fafe;
                border: 3px solid #e3f2fd;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            QLabel#sender-name {
                color: #0d47a1;
                font-weight: 700;
                line-height: 1.3;
            }
            
            QLabel#email-date {
                color: #546e7a;
                font-weight: 500;
                background-color: #eceff1;
                padding: 8px 12px;
                border-radius: 20px;
            }
            
            QLabel#email-address {
                color: #607d8b;
                font-weight: 400;
                font-style: italic;
            }
            
            QLabel#email-subject {
                color: #1a237e;
                font-weight: 700;
                margin-top: 10px;
                line-height: 1.4;
                padding: 10px 0;
            }
            
            /* === ACTIONS - CENTRAGE PARFAIT === */
            QFrame#email-actions {
                background-color: #f8f9fa;
                border: 2px solid #e3f2fd;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            QPushButton#action-btn {
                background-color: #1976d2;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                font-weight: 700;
                font-size: 13px;
                text-align: center;
                margin: 0px;  /* Pas de marge pour un alignement parfait */
            }
            
            QPushButton#action-btn:hover {
                background-color: #1565c0;
                transform: translateY(-1px);
            }
            
            QPushButton#action-btn:pressed {
                background-color: #0d47a1;
                transform: translateY(0px);
            }
            
            QPushButton#delete-btn {
                background-color: #d32f2f;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                font-weight: 700;
                font-size: 13px;
                text-align: center;
                margin: 0px;  /* Pas de marge pour un alignement parfait */
            }
            
            QPushButton#delete-btn:hover {
                background-color: #c62828;
                transform: translateY(-1px);
            }
            
            QPushButton#delete-btn:pressed {
                background-color: #b71c1c;
                transform: translateY(0px);
            }
            
            /* === CONTENU EMAIL === */
            QFrame#email-body-frame {
                background-color: #ffffff;
                border: 3px solid #e8eaf6;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            QLabel#section-title {
                color: #1a237e;
                font-weight: 700;
                margin-bottom: 10px;
                padding: 5px 0;
            }
            
            QTextEdit#email-content {
                background-color: #fafbfc;
                border: 2px solid #e3f2fd;
                border-radius: 12px;
                padding: 20px;
                color: #263238;
                line-height: 1.7;
                font-family: 'Inter', Arial, sans-serif;
                font-size: 13px;
            }
            
            QTextEdit#email-content:focus {
                border-color: #1976d2;
                background-color: #ffffff;
            }
            
            /* === ANALYSE IA === */
            QFrame#ai-analysis-frame {
                background-color: #f3e5f5;
                border: 3px solid #ce93d8;
                border-radius: 15px;
                margin-bottom: 20px;
            }
            
            QLabel#ai-analysis-content {
                background-color: #ffffff;
                border: 2px solid #e1bee7;
                border-radius: 12px;
                padding: 20px;
                color: #4a148c;
                line-height: 1.6;
                font-family: 'Inter', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
        """)
    
    def show_email(self, email: Email):
        """Affiche un email CORRIGÉ avec scroll automatique."""
        self.current_email = email
        
        # Cacher le message par défaut, afficher le contenu
        self.no_selection_widget.hide()
        self.email_content_widget.show()
        
        # Mettre à jour le header
        sender_name = email.get_sender_name()
        self.sender_label.setText(sender_name)
        
        self.email_address_label.setText(f"<{email.sender}>")
        
        subject = email.subject or "(Aucun sujet)"
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
        
        self.content_display.setPlainText(clean_text)
        
        # Mettre à jour l'analyse IA
        self._update_ai_analysis()
        
        # Scroller vers le haut
        self.scroll_area.verticalScrollBar().setValue(0)
        
        logger.info(f"Affichage email: {email.id}")
    
    def _update_ai_analysis(self):
        """Met à jour l'analyse IA CORRIGÉE."""
        if not self.current_email or not hasattr(self.current_email, 'ai_analysis'):
            self.ai_content.setText("🔍 Aucune analyse IA disponible pour cet email.")
            return
        
        analysis = self.current_email.ai_analysis
        if not analysis:
            self.ai_content.setText("🔍 Aucune analyse IA disponible pour cet email.")
            return
        
        # Construire le texte d'analyse de façon très lisible
        category_names = {
            'cv': '📄 Candidature/CV',
            'rdv': '📅 Rendez-vous',
            'support': '🛠️ Support technique',
            'facture': '💰 Facture',
            'spam': '🚫 Spam',
            'general': '📧 Email général'
        }
        
        category_display = category_names.get(getattr(analysis, 'category', 'general'), '📝 Autre')
        confidence = getattr(analysis, 'confidence', 0) * 100
        priority = getattr(analysis, 'priority', 3)
        should_respond = getattr(analysis, 'should_auto_respond', False)
        reasoning = getattr(analysis, 'reasoning', 'Aucun raisonnement disponible')
        
        # Formatage amélioré avec plus d'espacement
        ai_text = f"""📂 CATÉGORIE DÉTECTÉE
{category_display}

📊 NIVEAU DE CONFIANCE
{confidence:.0f}% de certitude

⚡ NIVEAU DE PRIORITÉ
{self._get_priority_text(priority)}

🤖 RÉPONSE AUTOMATIQUE
{'✅ Recommandée par l\'IA' if should_respond else '❌ Non recommandée'}

🧠 ANALYSE DÉTAILLÉE
{reasoning}"""
        
        # Ajouter des informations extraites si disponibles
        extracted_info = getattr(analysis, 'extracted_info', {})
        if extracted_info:
            ai_text += "\n\n📋 INFORMATIONS EXTRAITES"
            for key, value in extracted_info.items():
                if value:
                    ai_text += f"\n• {key.title()}: {value}"
        
        self.ai_content.setText(ai_text)
    
    def _get_priority_text(self, priority: int) -> str:
        """Convertit la priorité en texte CORRIGÉ."""
        priority_map = {
            1: "🔴 Très urgent (priorité maximale)",
            2: "🟠 Urgent (traitement rapide)", 
            3: "🟡 Normal (priorité standard)",
            4: "🟢 Faible (peut attendre)",
            5: "⚪ Très faible (non prioritaire)"
        }
        return priority_map.get(priority, f"❓ Priorité {priority}")
    
    def clear_selection(self):
        """Efface la sélection."""
        self.current_email = None
        self.email_content_widget.hide()
        self.no_selection_widget.show()
        
        # Scroller vers le haut
        self.scroll_area.verticalScrollBar().setValue(0)