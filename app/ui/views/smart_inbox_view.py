#!/usr/bin/env python3
"""
Vue Smart Inbox avec Layout VERTICAL CORRIGÉ - Tout est parfaitement visible.
"""
import logging
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLabel, QPushButton, QFrame, QButtonGroup, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont

from gmail_client import GmailClient
from ai_processor import AIProcessor
from models.email_model import Email
from ui.components.smart_email_card import SmartEmailCard
from ui.views.email_detail_view import EmailDetailView

logger = logging.getLogger(__name__)

class EmailLoaderThread(QThread):
    """Thread pour charger et analyser les emails avec l'IA."""
    
    emails_loaded = pyqtSignal(list)
    analysis_complete = pyqtSignal()
    progress_updated = pyqtSignal(int, int)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.should_stop = False
        self.emails_with_analysis = []
    
    def run(self):
        """Charge et analyse les emails."""
        try:
            emails = self.gmail_client.get_recent_emails(limit=20)
            self.emails_loaded.emit(emails)
            
            self.emails_with_analysis = []
            total_emails = len(emails)
            
            for i, email in enumerate(emails):
                if self.should_stop:
                    break
                
                analysis = self.ai_processor.process_email(email)
                email.ai_analysis = analysis
                self.emails_with_analysis.append(email)
                
                self.progress_updated.emit(i + 1, total_emails)
                self.msleep(100)
            
            self.analysis_complete.emit()
            logger.info(f"Analyse terminée pour {len(self.emails_with_analysis)} emails")
            
        except Exception as e:
            logger.error(f"Erreur EmailLoaderThread: {e}")
    
    def stop(self):
        """Arrête le thread."""
        self.should_stop = True

class CategoryFilter(QPushButton):
    """Bouton de filtre par catégorie."""
    
    def __init__(self, name: str, category: str, count: int = 0):
        super().__init__(f"{name} ({count})")
        self.category = category
        self.count = count
        self.is_active = False
        self.original_name = name
        
        self.setCheckable(True)
        self.setFixedHeight(35)
        self.setMinimumWidth(80)
        self._apply_style()
    
    def update_count(self, count: int):
        """Met à jour le compteur."""
        self.count = count
        self.setText(f"{self.original_name} ({count})")
    
    def set_active(self, active: bool):
        """Active/désactive le filtre."""
        self.is_active = active
        self.setChecked(active)
        self._apply_style()
    
    def _apply_style(self):
        """Style pour une bonne lisibilité."""
        if self.is_active:
            style = """
                QPushButton {
                    background-color: #1976d2;
                    color: #ffffff;
                    border: 2px solid #1976d2;
                    border-radius: 17px;
                    font-weight: 600;
                    font-size: 12px;
                    padding: 6px 14px;
                    margin: 2px;
                }
            """
        else:
            style = """
                QPushButton {
                    background-color: #ffffff;
                    color: #424242;
                    border: 2px solid #e0e0e0;
                    border-radius: 17px;
                    font-weight: 500;
                    font-size: 12px;
                    padding: 6px 14px;
                    margin: 2px;
                }
                
                QPushButton:hover {
                    background-color: #f5f5f5;
                    border-color: #bdbdbd;
                    color: #1976d2;
                }
            """
        
        self.setStyleSheet(style)

class AIResponsePanel(QFrame):
    """Panel de réponse IA ULTRA-CORRIGÉ avec hauteur appropriée."""
    
    response_approved = pyqtSignal(str, object)
    response_rejected = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.current_email = None
        self.current_analysis = None
        
        self.setObjectName("ai-response-panel")
        self.setMinimumHeight(400)  # Hauteur minimum confortable
        
        self._setup_ui()
        self._apply_style()
        self.hide()
    
    def _setup_ui(self):
        """Interface PARFAITEMENT LISIBLE avec scroll interne."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Zone de scroll pour le contenu du panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget de contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 25, 30, 25)
        content_layout.setSpacing(20)
        
        # === TITRE ET CONFIANCE ===
        header_frame = QFrame()
        header_frame.setObjectName("header-frame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(20)
        
        title_label = QLabel("🤖 Réponse IA suggérée")
        title_label.setObjectName("main-title")
        title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.confidence_label = QLabel("Confiance: 0%")
        self.confidence_label.setObjectName("confidence-badge")
        self.confidence_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        header_layout.addWidget(self.confidence_label)
        
        content_layout.addWidget(header_frame)
        
        # === INFOS EMAIL ===
        info_frame = QFrame()
        info_frame.setObjectName("info-frame")
        info_frame.setMinimumHeight(80)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 15, 20, 15)
        info_layout.setSpacing(10)
        
        info_title = QLabel("📧 Informations de l'email")
        info_title.setObjectName("section-title")
        info_title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        info_layout.addWidget(info_title)
        
        self.email_info_label = QLabel()
        self.email_info_label.setObjectName("email-info")
        self.email_info_label.setFont(QFont("Inter", 13))
        self.email_info_label.setWordWrap(True)
        self.email_info_label.setMinimumHeight(50)
        info_layout.addWidget(self.email_info_label)
        
        content_layout.addWidget(info_frame)
        
        # === ZONE DE RÉPONSE ===
        response_frame = QFrame()
        response_frame.setObjectName("response-frame")
        response_frame.setMinimumHeight(180)
        response_layout = QVBoxLayout(response_frame)
        response_layout.setContentsMargins(20, 15, 20, 15)
        response_layout.setSpacing(12)
        
        response_title = QLabel("✏️ Réponse suggérée (modifiable)")
        response_title.setObjectName("section-title")
        response_title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        response_layout.addWidget(response_title)
        
        self.response_text = QTextEdit()
        self.response_text.setObjectName("response-text")
        self.response_text.setFont(QFont("Inter", 13))
        self.response_text.setMinimumHeight(120)
        self.response_text.setPlaceholderText("Aucune réponse suggérée...")
        response_layout.addWidget(self.response_text)
        
        content_layout.addWidget(response_frame)
        
        # === BOUTONS ===
        buttons_frame = QFrame()
        buttons_frame.setObjectName("buttons-frame")
        buttons_frame.setFixedHeight(80)
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(15, 15, 15, 15)
        buttons_layout.setSpacing(20)
        
        self.reject_btn = QPushButton("❌ Ignorer cette suggestion")
        self.reject_btn.setObjectName("reject-btn")
        self.reject_btn.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self.reject_btn.setFixedHeight(50)
        self.reject_btn.setMinimumWidth(200)
        self.reject_btn.clicked.connect(self._reject_response)
        buttons_layout.addWidget(self.reject_btn)
        
        buttons_layout.addStretch()
        
        self.approve_btn = QPushButton("✅ Envoyer cette réponse")
        self.approve_btn.setObjectName("approve-btn")
        self.approve_btn.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        self.approve_btn.setFixedHeight(50)
        self.approve_btn.setMinimumWidth(220)
        self.approve_btn.clicked.connect(self._approve_response)
        buttons_layout.addWidget(self.approve_btn)
        
        content_layout.addWidget(buttons_frame)
        
        # Configurer le scroll
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def _apply_style(self):
        """Style ULTRA-SIMPLIFIÉ pour lisibilité maximale."""
        self.setStyleSheet("""
            /* === CONTENEUR PRINCIPAL === */
            QFrame#ai-response-panel {
                background-color: #e8f8e8;
                border: 4px solid #4caf50;
                border-radius: 20px;
                margin: 10px 0;
            }
            
            /* === SCROLLBAR === */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: #f0f8f0;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #4caf50;
                border-radius: 6px;
                min-height: 25px;
                margin: 1px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #45a049;
            }
            
            /* === TITRE PRINCIPAL === */
            QLabel#main-title {
                color: #1b5e20;
                font-weight: 700;
                background-color: transparent;
                border: none;
                padding: 5px 0;
            }
            
            /* === BADGE CONFIANCE === */
            QLabel#confidence-badge {
                background-color: #4caf50;
                color: #ffffff;
                padding: 12px 20px;
                border-radius: 25px;
                font-weight: 700;
                text-align: center;
                min-width: 120px;
                border: none;
            }
            
            /* === FRAMES DE SECTION === */
            QFrame#info-frame, QFrame#response-frame {
                background-color: #ffffff;
                border: 3px solid #81c784;
                border-radius: 15px;
                margin: 5px 0;
            }
            
            QFrame#header-frame, QFrame#buttons-frame {
                background-color: transparent;
                border: none;
            }
            
            /* === TITRES DE SECTION === */
            QLabel#section-title {
                color: #2e7d32;
                font-weight: 700;
                background-color: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }
            
            /* === INFOS EMAIL === */
            QLabel#email-info {
                color: #212121;
                background-color: #f8fdf8;
                border: 2px solid #c8e6c9;
                border-radius: 10px;
                padding: 15px;
                line-height: 1.6;
                font-weight: 500;
            }
            
            /* === ZONE DE TEXTE === */
            QTextEdit#response-text {
                background-color: #ffffff;
                border: 3px solid #81c784;
                border-radius: 12px;
                padding: 15px;
                color: #212121;
                font-size: 13px;
                line-height: 1.6;
                selection-background-color: #c8e6c9;
            }
            
            QTextEdit#response-text:focus {
                border-color: #4caf50;
                background-color: #fefffe;
            }
            
            /* === BOUTONS === */
            QPushButton#approve-btn {
                background-color: #4caf50;
                color: #ffffff;
                border: none;
                border-radius: 25px;
                padding: 15px 30px;
                font-weight: 700;
                font-size: 13px;
            }
            
            QPushButton#approve-btn:hover {
                background-color: #45a049;
                transform: translateY(-2px);
            }
            
            QPushButton#approve-btn:pressed {
                background-color: #3d8b40;
                transform: translateY(0px);
            }
            
            QPushButton#reject-btn {
                background-color: #f44336;
                color: #ffffff;
                border: none;
                border-radius: 25px;
                padding: 15px 30px;
                font-weight: 700;
                font-size: 13px;
            }
            
            QPushButton#reject-btn:hover {
                background-color: #e53935;
                transform: translateY(-2px);
            }
            
            QPushButton#reject-btn:pressed {
                background-color: #d32f2f;
                transform: translateY(0px);
            }
        """)
    
    def show_suggestion(self, email: Email, analysis):
        """Affiche une suggestion PARFAITEMENT CORRIGÉE."""
        self.current_email = email
        self.current_analysis = analysis
        
        # === METTRE À JOUR LA CONFIANCE ===
        confidence_percent = int(analysis.confidence * 100)
        self.confidence_label.setText(f"Confiance: {confidence_percent}%")
        
        # === INFORMATIONS SUR L'EMAIL ===
        sender_name = email.get_sender_name()
        if len(sender_name) > 40:
            sender_name = sender_name[:37] + "..."
        
        category_names = {
            'cv': 'Candidature/CV',
            'rdv': 'Rendez-vous', 
            'support': 'Support technique',
            'facture': 'Facture',
            'general': 'Email général'
        }
        category_display = category_names.get(analysis.category, analysis.category)
        
        subject = email.subject or "(Aucun sujet)"
        if len(subject) > 50:
            subject = subject[:47] + "..."
        
        email_info = f"""👤 Expéditeur: {sender_name}
📂 Catégorie: {category_display}
📋 Sujet: {subject}"""
        
        self.email_info_label.setText(email_info)
        
        # === RÉPONSE SUGGÉRÉE ===
        if analysis.suggested_response and len(analysis.suggested_response.strip()) > 0:
            self.response_text.setPlainText(analysis.suggested_response)
            self.approve_btn.setEnabled(True)
            self.approve_btn.setText("✅ Envoyer cette réponse")
        else:
            self.response_text.setPlainText("Aucune réponse automatique suggérée pour cette catégorie d'email.")
            self.approve_btn.setEnabled(False)
            self.approve_btn.setText("❌ Pas de réponse disponible")
        
        # === AFFICHER LE PANEL ===
        self.show()
        logger.info(f"Panel IA affiché pour {sender_name} - Catégorie: {category_display}")
    
    def _approve_response(self):
        """Approuve et prépare l'envoi de la réponse."""
        if not self.current_email:
            logger.warning("Aucun email sélectionné pour l'approbation")
            return
        
        response_text = self.response_text.toPlainText().strip()
        if not response_text or len(response_text) < 10:
            logger.warning("Réponse trop courte ou vide")
            return
        
        # Émettre le signal avec la réponse
        self.response_approved.emit(response_text, self.current_email)
        self.hide()
        
        logger.info(f"Réponse IA approuvée pour {self.current_email.get_sender_name()}")
    
    def _reject_response(self):
        """Rejette la suggestion de l'IA."""
        if self.current_email:
            self.response_rejected.emit(self.current_email)
            logger.info(f"Suggestion IA rejetée pour {self.current_email.get_sender_name()}")
        
        self.hide()

class SmartInboxView(QWidget):
    """Vue Smart Inbox avec Layout VERTICAL CORRIGÉ - Parfaitement visible."""
    
    email_selected = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        
        self.all_emails = []
        self.filtered_emails = []
        self.email_cards = []
        self.current_filter = "all"
        self.selected_email = None
        self.is_loading = False
        
        self._setup_ui()
        self._setup_loader()
        
        # Auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_emails)
        self.refresh_timer.start(300000)
    
    def _setup_ui(self):
        """Configuration LAYOUT VERTICAL - Tout est visible."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Filtres en haut
        filters_section = self._create_filters()
        layout.addWidget(filters_section)
        
        # Layout HORIZONTAL pour le contenu principal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(2)
        
        # === COLONNE GAUCHE: Liste emails ===
        email_list = self._create_email_list()
        main_splitter.addWidget(email_list)
        
        # === COLONNE DROITE: Layout VERTICAL ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Vue détail email (HAUT)
        self.detail_view = EmailDetailView()
        self.detail_view.action_requested.connect(self._handle_email_action)
        right_layout.addWidget(self.detail_view)
        
        # Panel IA de réponse (BAS) - HAUTEUR FIXE
        self.ai_response_panel = AIResponsePanel()
        self.ai_response_panel.response_approved.connect(self._on_ai_response_approved)
        self.ai_response_panel.response_rejected.connect(self._on_ai_response_rejected)
        right_layout.addWidget(self.ai_response_panel)
        
        main_splitter.addWidget(right_panel)
        
        # Proportions: Liste (35%) - Détail+IA (65%)
        main_splitter.setSizes([400, 700])
        layout.addWidget(main_splitter)
    
    def _create_filters(self) -> QWidget:
        """Crée les filtres."""
        filters_frame = QFrame()
        filters_frame.setObjectName("filters-section")
        filters_frame.setFixedHeight(70)
        
        layout = QHBoxLayout(filters_frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Groupe de boutons
        self.filter_group = QButtonGroup()
        
        # Filtres
        filters_data = [
            ("Tous", "all", 0),
            ("⚡ Réponses IA", "ai_suggestions", 0),
            ("🔴 Urgent", "urgent", 0),
            ("📄 CV", "cv", 0),
            ("📅 RDV", "rdv", 0),
            ("🛠️ Support", "support", 0)
        ]
        
        self.category_filters = {}
        
        for name, category, count in filters_data:
            filter_btn = CategoryFilter(name, category, count)
            filter_btn.clicked.connect(lambda checked, cat=category: self._apply_filter(cat))
            
            self.filter_group.addButton(filter_btn)
            self.category_filters[category] = filter_btn
            layout.addWidget(filter_btn)
            
            if category == "all":
                filter_btn.set_active(True)
        
        layout.addStretch()
        
        # Bouton refresh
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setFixedHeight(35)
        refresh_btn.setMinimumWidth(100)
        refresh_btn.clicked.connect(self.refresh_emails)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 17px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        layout.addWidget(refresh_btn)
        
        # Style du container
        filters_frame.setStyleSheet("""
            QFrame#filters-section {
                background-color: #fafafa;
                border-bottom: 2px solid #e0e0e0;
            }
        """)
        
        return filters_frame
    
    def _create_email_list(self) -> QWidget:
        """Crée la liste d'emails."""
        container = QFrame()
        container.setObjectName("email-list-container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)
        
        # Zone de scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container des emails
        self.email_container = QWidget()
        self.email_layout = QVBoxLayout(self.email_container)
        self.email_layout.setSpacing(8)
        self.email_layout.setContentsMargins(0, 0, 0, 0)
        
        # Message de chargement
        self.loading_label = QLabel("🔄 Chargement des emails...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setFont(QFont("Inter", 14, QFont.Weight.Medium))
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #424242; 
                padding: 40px;
                background-color: #f5f5f5;
                border-radius: 12px;
                border: 2px dashed #bdbdbd;
                margin: 20px 0;
            }
        """)
        self.email_layout.addWidget(self.loading_label)
        
        # Barre de progression
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Inter", 12))
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #1976d2; 
                padding: 12px;
                background-color: #e3f2fd;
                border-radius: 8px;
                margin: 8px 0;
                font-weight: 500;
            }
        """)
        self.progress_label.hide()
        self.email_layout.addWidget(self.progress_label)
        
        self.email_layout.addStretch()
        
        self.scroll_area.setWidget(self.email_container)
        layout.addWidget(self.scroll_area)
        
        # Style du container
        container.setStyleSheet("""
            QFrame#email-list-container {
                background-color: #ffffff;
                border-right: 2px solid #e0e0e0;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #bdbdbd;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #9e9e9e;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        return container
    
    def _setup_loader(self):
        """Configure le loader."""
        self.email_loader = EmailLoaderThread(self.gmail_client, self.ai_processor)
        self.email_loader.emails_loaded.connect(self._on_emails_loaded)
        self.email_loader.analysis_complete.connect(self._on_analysis_complete)
        self.email_loader.progress_updated.connect(self._on_progress_updated)
    
    def refresh_emails(self):
        """Actualise les emails."""
        if self.is_loading or self.email_loader.isRunning():
            return
        
        self.is_loading = True
        
        # Cacher le panel IA
        self.ai_response_panel.hide()
        
        # Afficher le chargement
        self._clear_email_list()
        self.loading_label.setText("🔄 Connexion à Gmail...")
        self.loading_label.show()
        self.progress_label.hide()
        
        # Réinitialiser le filtre
        self.current_filter = "all"
        for cat, btn in self.category_filters.items():
            btn.set_active(cat == "all")
        
        # Démarrer le chargement
        self.email_loader.start()
    
    def _on_emails_loaded(self, emails: List[Email]):
        """Gère la réception des emails."""
        self.all_emails = emails
        self.loading_label.setText("🤖 Analyse IA en cours...")
        self.progress_label.setText("Analyse IA: 0 / 0")
        self.progress_label.show()
        
        logger.info(f"{len(emails)} emails chargés, analyse en cours...")
    
    def _on_progress_updated(self, current: int, total: int):
        """Met à jour la progression."""
        self.progress_label.setText(f"🤖 Analyse IA: {current} / {total}")
    
    def _on_analysis_complete(self):
        """Fin de l'analyse IA."""
        self.all_emails = self.email_loader.emails_with_analysis
        
        # Cacher les messages
        self.loading_label.hide()
        self.progress_label.hide()
        
        # Créer les cartes
        self._create_email_cards()
        self._update_filter_counts()
        
        self.is_loading = False
        
        # Log des suggestions IA
        ai_suggestions_count = len([e for e in self.all_emails 
                                   if hasattr(e, 'ai_analysis') and e.ai_analysis and 
                                   getattr(e.ai_analysis, 'should_auto_respond', False)])
        
        if ai_suggestions_count > 0:
            logger.info(f"🤖 {ai_suggestions_count} réponses IA disponibles")
        
        logger.info(f"Interface mise à jour avec {len(self.all_emails)} emails")
    
    def _create_email_cards(self):
        """Crée les cartes d'emails."""
        self._clear_email_list()
        
        emails_to_show = self.filtered_emails if self.filtered_emails else self.all_emails
        
        if not emails_to_show:
            # Message si aucun email
            no_email_label = QLabel("📭 Aucun email à afficher")
            no_email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_email_label.setFont(QFont("Inter", 14, QFont.Weight.Medium))
            no_email_label.setStyleSheet("""
                QLabel {
                    color: #757575; 
                    padding: 40px;
                    background-color: #f5f5f5;
                    border-radius: 12px;
                    border: 2px dashed #bdbdbd;
                    margin: 20px 0;
                }
            """)
            self.email_layout.insertWidget(self.email_layout.count() - 1, no_email_label)
            return
        
        for email in emails_to_show:
            # Créer la carte
            card = SmartEmailCard(email, getattr(email, 'ai_analysis', None))
            card.clicked.connect(self._on_email_card_clicked)
            card.action_requested.connect(self._handle_email_action)
            
            self.email_cards.append(card)
            self.email_layout.insertWidget(self.email_layout.count() - 1, card)
        
        logger.info(f"Créé {len(self.email_cards)} cartes")
    
    def _clear_email_list(self):
        """Vide la liste des emails."""
        for card in self.email_cards:
            card.setParent(None)
            card.deleteLater()
        self.email_cards.clear()
        
        # Nettoyer les autres widgets
        for i in reversed(range(self.email_layout.count() - 1)):
            item = self.email_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget not in [self.loading_label, self.progress_label]:
                    widget.setParent(None)
                    widget.deleteLater()
    
    def _apply_filter(self, category: str):
        """Applique un filtre."""
        self.current_filter = category
        
        # Mettre à jour les filtres
        for cat, filter_btn in self.category_filters.items():
            filter_btn.set_active(cat == category)
        
        # Filtrer les emails
        if category == "all":
            self.filtered_emails = self.all_emails.copy()
        elif category == "ai_suggestions":
            self.filtered_emails = [
                email for email in self.all_emails 
                if hasattr(email, 'ai_analysis') and email.ai_analysis and 
                getattr(email.ai_analysis, 'should_auto_respond', False)
            ]
        elif category == "urgent":
            self.filtered_emails = [
                email for email in self.all_emails 
                if hasattr(email, 'ai_analysis') and email.ai_analysis and 
                getattr(email.ai_analysis, 'priority', 5) <= 2
            ]
        else:
            self.filtered_emails = [
                email for email in self.all_emails 
                if hasattr(email, 'ai_analysis') and email.ai_analysis and 
                getattr(email.ai_analysis, 'category', 'general') == category
            ]
        
        # Recréer les cartes
        self._create_email_cards()
        
        logger.info(f"Filtre '{category}': {len(self.filtered_emails)} emails")
    
    def _update_filter_counts(self):
        """Met à jour les compteurs."""
        counts = {
            "all": len(self.all_emails),
            "ai_suggestions": 0,
            "urgent": 0,
            "cv": 0,
            "rdv": 0,
            "support": 0
        }
        
        # Compter par catégorie
        for email in self.all_emails:
            if hasattr(email, 'ai_analysis') and email.ai_analysis:
                analysis = email.ai_analysis
                
                # Suggestions IA
                if getattr(analysis, 'should_auto_respond', False):
                    counts["ai_suggestions"] += 1
                
                # Urgent
                if getattr(analysis, 'priority', 5) <= 2:
                    counts["urgent"] += 1
                
                # Par catégorie
                category = getattr(analysis, 'category', 'general')
                if category in counts:
                    counts[category] += 1
        
        # Mettre à jour les boutons
        for category, count in counts.items():
            if category in self.category_filters:
                self.category_filters[category].update_count(count)
    
    def _on_email_card_clicked(self, email: Email):
        """Gère le clic sur une carte d'email."""
        # Désélectionner toutes les cartes
        for card in self.email_cards:
            card.set_selected(False)
        
        # Sélectionner la carte cliquée
        for card in self.email_cards:
            if card.email.id == email.id:
                card.set_selected(True)
                break
        
        # Afficher les détails
        self.detail_view.show_email(email)
        self.selected_email = email
        
        # Marquer comme lu
        if not email.is_read:
            email.is_read = True
            self.gmail_client.mark_as_read(email.id)
            
            # Mettre à jour la carte
            for card in self.email_cards:
                if card.email.id == email.id:
                    card._apply_style()
                    break
        
        # PANEL IA : Afficher SEULEMENT s'il y a une suggestion de réponse
        if (hasattr(email, 'ai_analysis') and email.ai_analysis and 
            getattr(email.ai_analysis, 'should_auto_respond', False) and
            getattr(email.ai_analysis, 'suggested_response', '') and
            len(getattr(email.ai_analysis, 'suggested_response', '').strip()) > 0):
            
            logger.info("🤖 Affichage du panel de réponse IA")
            self.ai_response_panel.show_suggestion(email, email.ai_analysis)
        else:
            logger.info("❌ Pas de suggestion IA - Panel caché")
            self.ai_response_panel.hide()
        
        # Émettre le signal
        self.email_selected.emit(email)
        
        logger.info(f"Email sélectionné: {email.id}")
    
    def _on_ai_response_approved(self, response_text: str, email: Email):
        """Gère l'approbation d'une réponse IA."""
        try:
            from ui.compose_view import ComposeView
            
            # Préparer le sujet
            subject = email.subject or ""
            if not subject.lower().startswith('re:'):
                subject = f"Re: {subject}"
            
            # Créer le dialogue de composition
            compose_dialog = ComposeView(
                self.gmail_client,
                parent=self.window(),
                to=email.sender,
                subject=subject,
                body=response_text,
                is_reply=True
            )
            
            # Indiquer que c'est une réponse IA
            compose_dialog.show_ai_indicator()
            
            # Connecter le signal d'envoi
            compose_dialog.email_sent.connect(self._on_email_sent)
            
            compose_dialog.exec()
            
            logger.info(f"Réponse IA approuvée pour {email.id}")
            
        except Exception as e:
            logger.error(f"Erreur ouverture composition: {e}")
    
    def _on_ai_response_rejected(self, email: Email):
        """Gère le rejet d'une réponse IA."""
        logger.info(f"Réponse IA rejetée pour {email.id}")
    
    def _on_email_sent(self):
        """Gère la confirmation d'envoi."""
        main_window = self.window()
        if hasattr(main_window, 'show_notification'):
            main_window.show_notification("✅ Réponse envoyée avec succès", 3000)
    
    def _handle_email_action(self, action_type: str, email: Email):
        """Gère les actions sur les emails."""
        logger.info(f"Action '{action_type}' pour email {email.id}")
        
        if action_type == "reply":
            self._reply_to_email(email)
        elif action_type == "archive":
            self._archive_email(email)
        elif action_type == "delete":
            self._delete_email(email)
        elif action_type == "ai_response":
            # Déclencher l'affichage du panel IA
            if hasattr(email, 'ai_analysis') and email.ai_analysis:
                self.ai_response_panel.show_suggestion(email, email.ai_analysis)
    
    def _reply_to_email(self, email: Email):
        """Ouvre la fenêtre de réponse."""
        try:
            from ui.compose_view import ComposeView
            
            subject = email.subject or ""
            if not subject.lower().startswith('re:'):
                subject = f"Re: {subject}"
            
            original_body = email.body or email.snippet or ""
            if len(original_body) > 300:
                original_body = original_body[:300] + "..."
            
            body = f"\n\n--- Message original ---\nDe: {email.sender}\nObjet: {email.subject}\n\n{original_body}"
            
            compose_dialog = ComposeView(
                self.gmail_client,
                parent=self.window(),
                to=email.sender,
                subject=subject,
                body=body,
                is_reply=True
            )
            
            compose_dialog.email_sent.connect(self._on_email_sent)
            compose_dialog.exec()
            
        except Exception as e:
            logger.error(f"Erreur ouverture compose: {e}")
    
    def _archive_email(self, email: Email):
        """Archive un email."""
        success = self.gmail_client.archive_email(email.id)
        if success:
            # Supprimer de la liste
            self.all_emails = [e for e in self.all_emails if e.id != email.id]
            if self.filtered_emails:
                self.filtered_emails = [e for e in self.filtered_emails if e.id != email.id]
            
            # Recréer l'affichage
            self._create_email_cards()
            self._update_filter_counts()
            
            # Effacer la vue détail si nécessaire
            if self.selected_email and self.selected_email.id == email.id:
                self.detail_view.clear_selection()
                self.ai_response_panel.hide()
                self.selected_email = None
            
            logger.info(f"Email {email.id} archivé")
    
    def _delete_email(self, email: Email):
        """Supprime un email."""
        success = self.gmail_client.delete_email(email.id)
        if success:
            # Même logique que archive
            self.all_emails = [e for e in self.all_emails if e.id != email.id]
            if self.filtered_emails:
                self.filtered_emails = [e for e in self.filtered_emails if e.id != email.id]
            
            self._create_email_cards()
            self._update_filter_counts()
            
            if self.selected_email and self.selected_email.id == email.id:
                self.detail_view.clear_selection()
                self.ai_response_panel.hide()
                self.selected_email = None
            
            logger.info(f"Email {email.id} supprimé")
    
    def filter_emails(self, search_text: str):
        """Filtre par texte de recherche."""
        if not search_text:
            self.filtered_emails = self.all_emails.copy()
        else:
            search_lower = search_text.lower()
            self.filtered_emails = [
                email for email in self.all_emails
                if (search_lower in (email.subject or '').lower() or
                    search_lower in (email.body or '').lower() or
                    search_lower in (email.sender or '').lower() or
                    search_lower in (email.snippet or '').lower())
            ]
        
        self._create_email_cards()
        logger.info(f"Recherche '{search_text}': {len(self.filtered_emails)} résultats")
    
    def clear_filter(self):
        """Supprime le filtre de recherche."""
        self.filtered_emails = self.all_emails.copy()
        self._create_email_cards()
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques."""
        unread_count = len([e for e in self.all_emails if not e.is_read])
        analyzed_count = len([e for e in self.all_emails if hasattr(e, 'ai_analysis') and e.ai_analysis])
        ai_suggestions_count = len([e for e in self.all_emails 
                                   if hasattr(e, 'ai_analysis') and e.ai_analysis and 
                                   getattr(e.ai_analysis, 'should_auto_respond', False)])
        
        return {
            'total_emails': len(self.all_emails),
            'unread_emails': unread_count,
            'analyzed_emails': analyzed_count,
            'ai_suggestions': ai_suggestions_count,
            'ai_accuracy': analyzed_count / len(self.all_emails) if self.all_emails else 0
        }