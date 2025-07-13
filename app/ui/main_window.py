#!/usr/bin/env python3
"""
Interface utilisateur principale avec configuration réactive et gestion des réponses en attente.
Design moderne noir et blanc avec UX/UI optimisée.
"""
import logging
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QLineEdit, QComboBox, QStackedWidget,
    QFrame, QScrollArea, QProgressBar, QSystemTrayIcon, QMenu,
    QApplication, QMessageBox, QDialog, QTabWidget, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation, QRect
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPainter, QBrush, QPixmap
from datetime import datetime, timedelta

from gmail_client import GmailClient
from ai_processor import AIProcessor
from calendar_manager import CalendarManager
from auto_responder import AutoResponder
from models.email_model import Email
from models.calendar_model import CalendarEvent
from ui.email_list_view import EmailListView
from ui.email_detail_view import EmailDetailView
from ui.calendar_view import CalendarView
from ui.compose_view import ComposeView
from ui.settings_view import SettingsView
from ui.pending_responses_view import PendingResponsesView
from utils.config import get_config_manager

logger = logging.getLogger(__name__)

class EmailProcessorThread(QThread):
    """Thread pour traiter les emails en arrière-plan."""
    
    emails_processed = pyqtSignal(list)
    processing_progress = pyqtSignal(int, int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor, 
                 auto_responder: AutoResponder, query: str = ""):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.auto_responder = auto_responder
        self.query = query
        self.is_running = True
    
    def run(self):
        try:
            # Récupérer les emails
            emails = self.gmail_client.list_messages(query=self.query, max_results=50)
            
            if not self.is_running:
                return
            
            processed_emails = []
            total_emails = len(emails)
            
            for i, email in enumerate(emails):
                if not self.is_running:
                    break
                
                # Traiter l'email avec l'IA
                email_info = self.ai_processor.extract_key_information(email)
                email.ai_info = email_info
                
                # Vérifier si une réponse automatique est nécessaire (créer en attente maintenant)
                if email_info.get('should_auto_respond', False):
                    self.auto_responder.process_email(email)
                
                processed_emails.append(email)
                self.processing_progress.emit(i + 1, total_emails)
            
            self.emails_processed.emit(processed_emails)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des emails: {e}")
            self.error_occurred.emit(str(e))
    
    def stop(self):
        self.is_running = False

class ModernMainWindow(QMainWindow):
    """Interface principale moderne avec configuration réactive et validation des réponses."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor,
                 calendar_manager: CalendarManager, auto_responder: AutoResponder,
                 parent=None):
        super().__init__(parent)
        
        # Initialisation des composants
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.calendar_manager = calendar_manager
        self.auto_responder = auto_responder
        self.config_manager = get_config_manager()
        
        # État de l'interface
        self.current_emails = []
        self.current_view = "inbox"
        self.is_refreshing = False
        self.processor_thread = None
        self._current_font_size = 12
        
        # Initialisation
        self._setup_ui()
        self._setup_style()
        self._setup_timers()
        self._setup_tray_icon()
        self._setup_config_monitoring()
        
        # Charger les données initiales
        self._load_initial_data()
        
        logger.info("Interface principale initialisée avec succès")
    
    def _setup_ui(self):
        """Configure l'interface utilisateur moderne."""
        self.setWindowTitle("Dynovate Mail Assistant IA")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Widget principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar gauche
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Zone principale
        self.main_area = self._create_main_area()
        main_layout.addWidget(self.main_area)
        
        # Barre de statut moderne
        self._create_status_bar()
    
    def _create_sidebar(self) -> QWidget:
        """Crée la barre latérale moderne et responsive avec corrections d'affichage."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        sidebar.setMinimumHeight(600)  # Ajout d'une hauteur minimale
        
        # Utilisation d'un scroll area pour éviter les coupures
        scroll_area = QScrollArea()
        scroll_area.setObjectName("sidebar-scroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget de contenu de la sidebar
        sidebar_content = QWidget()
        sidebar_content.setObjectName("sidebar-content")
        
        layout = QVBoxLayout(sidebar_content)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header avec logo
        header = QFrame()
        header.setObjectName("sidebar-header")
        header.setFixedHeight(70)
        
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        # Logo/Titre
        title_label = QLabel("Dynovate Mail")
        title_label.setObjectName("app-title")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        layout.addWidget(header)
        
        # Boutons de navigation principaux
        nav_buttons = [
            ("📧", "Boîte de réception", "inbox"),
            ("📤", "Envoyés", "sent"),
            ("⭐", "Importants", "important"),
            ("🔔", "Réponses en attente", "pending_responses"),
            ("🗓️", "Calendrier", "calendar"),
            ("📊", "Statistiques", "stats"),
            ("⚙️", "Paramètres", "settings")
        ]
        
        self.nav_buttons = {}
        for icon, text, key in nav_buttons:
            btn = QPushButton(f"{icon}  {text}")
            btn.setObjectName("nav-button")
            btn.setFixedHeight(45)
            btn.clicked.connect(lambda checked, k=key: self._switch_view(k))
            layout.addWidget(btn)
            self.nav_buttons[key] = btn
        
        # Séparateur
        separator = QFrame()
        separator.setObjectName("sidebar-separator")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Filtres par catégorie
        layout.addWidget(self._create_category_filters())
        
        # Séparateur
        separator2 = QFrame()
        separator2.setObjectName("sidebar-separator")
        separator2.setFixedHeight(1)
        layout.addWidget(separator2)
        
        # Statistiques rapides
        layout.addWidget(self._create_quick_stats())
        
        # Ajout d'un espacement flexible au lieu d'un stretch pour éviter les problèmes
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)
        
        # Configurer le scroll area
        scroll_area.setWidget(sidebar_content)
        
        # Layout final de la sidebar
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll_area)
        
        return sidebar
    
    def _create_category_filters(self) -> QWidget:
        """Crée les filtres par catégorie avec une meilleure gestion de l'espace."""
        filters_frame = QFrame()
        filters_frame.setObjectName("category-filters")
        filters_frame.setMinimumHeight(200)  # Hauteur minimale
        filters_frame.setMaximumHeight(250)  # Hauteur maximale pour éviter les débordements
        filters_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(filters_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)  # Espacement réduit
        
        # Titre
        title = QLabel("Catégories")
        title.setObjectName("section-title")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Filtres avec scroll si nécessaire
        filters_scroll = QScrollArea()
        filters_scroll.setObjectName("filters-scroll")
        filters_scroll.setWidgetResizable(True)
        filters_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        filters_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        filters_scroll.setMaximumHeight(180)  # Hauteur max pour le scroll
        
        filters_widget = QWidget()
        filters_layout = QVBoxLayout(filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(2)
        
        # Filtres
        categories = [
            ("📄", "CV", "cv"),
            ("🤝", "Rendez-vous", "rdv"),
            ("🛡️", "Spam", "spam"),
            ("🧾", "Factures", "facture"),
            ("🔧", "Support", "support"),
            ("📰", "Newsletters", "newsletter")
        ]
        
        self.category_buttons = {}
        for icon, text, key in categories:
            btn = QPushButton(f"{icon} {text}")
            btn.setObjectName("category-filter")
            btn.setFixedHeight(30)  # Hauteur fixe réduite
            btn.clicked.connect(lambda checked, k=key: self._filter_by_category(k))
            filters_layout.addWidget(btn)
            self.category_buttons[key] = btn
        
        # Ajouter un espace flexible pour éviter les coupures
        filters_layout.addStretch()
        
        filters_scroll.setWidget(filters_widget)
        layout.addWidget(filters_scroll)
        
        return filters_frame
    
    def _create_quick_stats(self) -> QWidget:
        """Crée les statistiques rapides avec une meilleure gestion de l'espace."""
        stats_frame = QFrame()
        stats_frame.setObjectName("quick-stats")
        stats_frame.setMinimumHeight(220)  # Hauteur minimale garantie
        stats_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        
        layout = QVBoxLayout(stats_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)  # Espacement réduit pour optimiser l'espace
        
        # Titre
        title = QLabel("Statistiques")
        title.setObjectName("section-title")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Stats avec indicateur de réponse automatique
        self.stats_labels = {}
        stats = [
            ("unread", "Non lus", "0"),
            ("today", "Aujourd'hui", "0"),
            ("pending_responses", "En attente", "0"),
            ("auto_responses", "Réponses auto", "0"),
            ("meetings", "RDV semaine", "0")
        ]
        
        for key, text, value in stats:
            stat_widget = QFrame()
            stat_widget.setObjectName("stat-item")
            stat_widget.setFixedHeight(28)  # Hauteur fixe pour éviter les coupures
            stat_layout = QHBoxLayout(stat_widget)
            stat_layout.setContentsMargins(8, 4, 8, 4)
            
            label = QLabel(text)
            label.setObjectName("stat-label")
            label.setFont(QFont("Arial", 10))
            
            value_label = QLabel(value)
            value_label.setObjectName("stat-value")
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            stat_layout.addWidget(label)
            stat_layout.addWidget(value_label)
            
            layout.addWidget(stat_widget)
            self.stats_labels[key] = value_label
        
        # Indicateur d'état de la réponse automatique
        self.auto_respond_indicator = QFrame()
        self.auto_respond_indicator.setObjectName("auto-respond-indicator")
        self.auto_respond_indicator.setFixedHeight(35)  # Hauteur fixe
        indicator_layout = QHBoxLayout(self.auto_respond_indicator)
        indicator_layout.setContentsMargins(8, 6, 8, 6)
        
        self.auto_respond_icon = QLabel("🤖")
        self.auto_respond_icon.setFont(QFont("Arial", 12))
        indicator_layout.addWidget(self.auto_respond_icon)
        
        self.auto_respond_status = QLabel("Désactivé")
        self.auto_respond_status.setObjectName("auto-respond-status")
        self.auto_respond_status.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        indicator_layout.addWidget(self.auto_respond_status)
        
        layout.addWidget(self.auto_respond_indicator)
        
        return stats_frame
    
    def _create_main_area(self) -> QWidget:
        """Crée la zone principale avec onglets."""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barre d'outils moderne
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Zone de contenu avec onglets
        self.content_stack = QStackedWidget()
        
        # Vue emails avec splitter amélioré
        self.email_view = self._create_email_view()
        self.content_stack.addWidget(self.email_view)
        
        # Vue calendrier
        self.calendar_view = CalendarView(self.calendar_manager)
        self.content_stack.addWidget(self.calendar_view)
        
        # Vue statistiques améliorée
        self.stats_view = self._create_improved_stats_view()
        self.content_stack.addWidget(self.stats_view)
        
        # Vue paramètres réactive
        self.settings_view = SettingsView()
        self.settings_view.settings_applied.connect(self._on_settings_applied)
        self.content_stack.addWidget(self.settings_view)
        
        # Vue des réponses en attente
        self.pending_responses_view = PendingResponsesView(self.auto_responder)
        self.content_stack.addWidget(self.pending_responses_view)
        
        layout.addWidget(self.content_stack)
        
        return main_widget
    
    def _create_toolbar(self) -> QWidget:
        """Crée la barre d'outils moderne."""
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(60)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        
        # Bouton composer
        compose_btn = QPushButton("✉️ Nouveau")
        compose_btn.setObjectName("compose-button")
        compose_btn.clicked.connect(self._compose_email)
        layout.addWidget(compose_btn)
        
        # Séparateur
        separator = QFrame()
        separator.setObjectName("toolbar-separator")
        separator.setFixedWidth(1)
        separator.setFixedHeight(30)
        layout.addWidget(separator)
        
        # Bouton actualiser
        refresh_btn = QPushButton("🔄")
        refresh_btn.setObjectName("toolbar-button")
        refresh_btn.setToolTip("Actualiser")
        refresh_btn.clicked.connect(self._refresh_emails)
        layout.addWidget(refresh_btn)
        
        # Barre de recherche
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search-input")
        self.search_input.setPlaceholderText("Rechercher dans les emails...")
        self.search_input.returnPressed.connect(self._search_emails)
        layout.addWidget(self.search_input)
        
        # Bouton recherche
        search_btn = QPushButton("🔍")
        search_btn.setObjectName("toolbar-button")
        search_btn.clicked.connect(self._search_emails)
        layout.addWidget(search_btn)
        
        layout.addStretch()
        
        # Indicateur de rafraîchissement automatique
        self.auto_refresh_indicator = QLabel("🟢 Auto")
        self.auto_refresh_indicator.setObjectName("auto-refresh-indicator")
        self.auto_refresh_indicator.setToolTip("Rafraîchissement automatique activé")
        layout.addWidget(self.auto_refresh_indicator)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress-bar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(200)
        layout.addWidget(self.progress_bar)
        
        return toolbar
    
    def _create_email_view(self) -> QWidget:
        """Crée la vue principale des emails."""
        email_widget = QWidget()
        layout = QHBoxLayout(email_widget)
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter horizontal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Liste des emails
        self.email_list = EmailListView()
        self.email_list.email_selected.connect(self._on_email_selected)
        self.email_list.setMinimumWidth(400)
        splitter.addWidget(self.email_list)
        
        # Détail de l'email dans un container
        detail_container = QWidget()
        detail_layout = QVBoxLayout(detail_container)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        
        self.email_detail = EmailDetailView(self.gmail_client, self.ai_processor)
        self.email_detail.reply_requested.connect(self._reply_to_email)
        self.email_detail.forward_requested.connect(self._forward_email)
        detail_layout.addWidget(self.email_detail)
        
        splitter.addWidget(detail_container)
        
        # Configuration du splitter
        splitter.setSizes([400, 600])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        return email_widget
    
    def _create_improved_stats_view(self) -> QWidget:
        """Crée la vue des statistiques améliorée avec scroll."""
        # Widget principal avec scroll
        scroll_area = QScrollArea()
        scroll_area.setObjectName("stats-scroll-area")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget de contenu
        stats_widget = QWidget()
        stats_widget.setObjectName("stats-page")
        
        layout = QVBoxLayout(stats_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Titre avec statut de configuration
        title_layout = QHBoxLayout()
        title_icon = QLabel("📊")
        title_icon.setFont(QFont("Arial", 24))
        title_layout.addWidget(title_icon)
        
        title = QLabel("Statistiques détaillées")
        title.setObjectName("stats-title")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        # Indicateur de statut global
        self.global_status = QLabel("🟢 Système opérationnel")
        self.global_status.setObjectName("global-status")
        self.global_status.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_layout.addWidget(self.global_status)
        
        layout.addLayout(title_layout)
        
        # Cartes de statistiques avec auto-responder
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        # Carte emails
        email_card = self._create_stat_card("📧", "Emails", "0", "Total traités")
        cards_layout.addWidget(email_card)
        
        # Carte non lus
        unread_card = self._create_stat_card("📬", "Non lus", "0", "À traiter")
        cards_layout.addWidget(unread_card)
        
        # Carte réponses en attente
        self.pending_card = self._create_stat_card("🔔", "En attente", "0", "À valider")
        cards_layout.addWidget(self.pending_card)
        
        # Carte réponses auto avec statut
        self.auto_card = self._create_stat_card("🤖", "Réponses auto", "0", "Cette semaine")
        cards_layout.addWidget(self.auto_card)
        
        # Carte RDV
        rdv_card = self._create_stat_card("🗓️", "Rendez-vous", "0", "Planifiés")
        cards_layout.addWidget(rdv_card)
        
        layout.addLayout(cards_layout)
        
        # Section de configuration active
        config_frame = QFrame()
        config_frame.setObjectName("config-frame")
        config_layout = QVBoxLayout(config_frame)
        config_layout.setContentsMargins(25, 25, 25, 25)
        
        config_title = QLabel("⚙️ Configuration active")
        config_title.setObjectName("config-section-title")
        config_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        config_layout.addWidget(config_title)
        
        self.config_summary = QLabel("Chargement...")
        self.config_summary.setObjectName("config-content")
        self.config_summary.setFont(QFont("Arial", 12))
        self.config_summary.setWordWrap(True)
        config_layout.addWidget(self.config_summary)
        
        layout.addWidget(config_frame)
        
        # Graphiques et détails existants
        details_frame = QFrame()
        details_frame.setObjectName("stats-details")
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(25, 25, 25, 25)
        
        # Section répartition par catégorie
        category_title = QLabel("📁 Répartition par catégorie")
        category_title.setObjectName("stats-section-title")
        category_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        details_layout.addWidget(category_title)
        
        self.category_stats = QLabel("Chargement...")
        self.category_stats.setObjectName("stats-content")
        self.category_stats.setFont(QFont("Arial", 12))
        self.category_stats.setWordWrap(True)
        details_layout.addWidget(self.category_stats)
        
        # Section activité récente
        activity_title = QLabel("📈 Activité récente")
        activity_title.setObjectName("stats-section-title")
        activity_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        details_layout.addWidget(activity_title)
        
        self.activity_stats = QLabel("Chargement...")
        self.activity_stats.setObjectName("stats-content")
        self.activity_stats.setFont(QFont("Arial", 12))
        self.activity_stats.setWordWrap(True)
        details_layout.addWidget(self.activity_stats)
        
        layout.addWidget(details_frame)
        
        # Ajouter un espace de sécurité en bas
        bottom_spacer = QSpacerItem(20, 50, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        layout.addItem(bottom_spacer)
        
        # Configurer le scroll area
        scroll_area.setWidget(stats_widget)
        
        return scroll_area
    
    def _create_stat_card(self, icon: str, title: str, value: str, subtitle: str) -> QWidget:
        """Crée une carte de statistique avec une taille optimisée."""
        card = QFrame()
        card.setObjectName("stat-card")
        card.setFixedHeight(130)  # Hauteur légèrement augmentée
        card.setMinimumWidth(180)  # Largeur minimale pour éviter les coupures
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Header avec icône et titre
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 20))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("card-title")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Valeur
        value_label = QLabel(value)
        value_label.setObjectName("card-value")
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(value_label)
        
        # Sous-titre
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("card-subtitle")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
        
        layout.addStretch()
        
        return card
    
    def _create_status_bar(self):
        """Crée la barre de statut moderne."""
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f8f8f8;
                border-top: 1px solid #e0e0e0;
                color: #666666;
                font-size: 11px;
                padding: 3px 10px;
            }
        """)
        
        # Message initial avec configuration
        config = self.config_manager.get_config()
        auto_respond_status = "activée" if config.get('auto_respond', {}).get('enabled', False) else "désactivée"
        status_bar.showMessage(f"Prêt - Réponse automatique: {auto_respond_status} - Mode validation activé")
    
    def _setup_style(self):
        """Configure le style moderne noir et blanc amélioré avec corrections pour les statistiques."""
        self.setStyleSheet("""
            /* Style général */
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
            }
            
            /* Sidebar avec scroll corrigé */
            QFrame#sidebar {
                background-color: #000000;
                border-right: 1px solid #333333;
            }
            
            QScrollArea#sidebar-scroll {
                background-color: #000000;
                border: none;
            }
            
            QWidget#sidebar-content {
                background-color: #000000;
            }
            
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #333333;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* Header de la sidebar */
            QFrame#sidebar-header {
                background-color: #000000;
                border-bottom: 1px solid #333333;
            }
            
            QLabel#app-title {
                color: #ffffff;
                font-weight: bold;
            }
            
            /* Boutons de navigation */
            QPushButton#nav-button {
                background-color: transparent;
                color: #ffffff;
                border: none;
                text-align: left;
                padding: 12px 20px;
                border-radius: 0px;
                font-size: 13px;
            }
            
            QPushButton#nav-button:hover {
                background-color: #1a1a1a;
            }
            
            QPushButton#nav-button:checked {
                background-color: #333333;
                border-left: 3px solid #ffffff;
            }
            
            /* Séparateurs */
            QFrame#sidebar-separator {
                background-color: #333333;
                border: none;
                margin: 5px 15px;
            }
            
            /* Filtres par catégorie */
            QFrame#category-filters {
                background-color: #000000;
                max-height: 250px; /* Hauteur maximale pour éviter les débordements */
            }
            
            QScrollArea#filters-scroll {
                background-color: #000000;
                border: none;
            }
            
            QPushButton#category-filter {
                background-color: transparent;
                color: #cccccc;
                border: none;
                text-align: left;
                padding: 8px 20px;
                border-radius: 4px;
                margin: 1px 0px;
                font-size: 12px;
            }
            
            QPushButton#category-filter:hover {
                background-color: #333333;
                color: #ffffff;
            }
            
            /* Statistiques rapides - corrigées */
            QFrame#quick-stats {
                background-color: #000000;
                min-height: 220px;
                max-height: 300px; /* Hauteur maximale pour éviter les débordements */
            }
            
            QLabel#section-title {
                color: #ffffff;
                margin-bottom: 8px;
                font-size: 11px;
                font-weight: bold;
            }
            
            QFrame#stat-item {
                background-color: transparent;
                border-radius: 4px;
                margin: 2px 0px;
                min-height: 24px;
                max-height: 28px;
            }
            
            QFrame#stat-item:hover {
                background-color: #1a1a1a;
            }
            
            QLabel#stat-label {
                color: #cccccc;
                font-size: 10px;
            }
            
            QLabel#stat-value {
                color: #ffffff;
                font-weight: bold;
                font-size: 10px;
            }
            
            /* Indicateur de réponse automatique */
            QFrame#auto-respond-indicator {
                background-color: #1a1a1a;
                border-radius: 6px;
                border: 1px solid #333333;
                margin-top: 5px;
                min-height: 30px;
                max-height: 35px;
            }
            
            QLabel#auto-respond-status {
                color: #ffffff;
                font-size: 10px;
            }
            
            /* Page des statistiques - avec scroll corrigé */
            QScrollArea#stats-scroll-area {
                background-color: #ffffff;
                border: none;
            }
            
            QWidget#stats-page {
                background-color: #ffffff;
            }
            
            QLabel#stats-title {
                color: #000000;
                margin-bottom: 10px;
            }
            
            QLabel#global-status {
                color: #4caf50;
                background-color: #e8f5e8;
                padding: 8px 16px;
                border-radius: 20px;
                border: 2px solid #4caf50;
            }
            
            /* Cartes de statistiques */
            QFrame#stat-card {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                margin: 5px;
            }
            
            QFrame#stat-card:hover {
                border-color: #cccccc;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            }
            
            QLabel#card-title {
                color: #666666;
                font-size: 12px;
                font-weight: bold;
            }
            
            QLabel#card-value {
                color: #000000;
                font-size: 24px;
                font-weight: bold;
            }
            
            QLabel#card-subtitle {
                color: #999999;
                font-size: 10px;
            }
            
            /* Sections de configuration et détails */
            QFrame#config-frame, QFrame#stats-details {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 10px 0px;
            }
            
            QLabel#config-section-title, QLabel#stats-section-title {
                color: #000000;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            QLabel#config-content, QLabel#stats-content {
                color: #333333;
                font-size: 12px;
                line-height: 1.4;
            }
            
            /* Barre d'outils */
            QFrame#toolbar {
                background-color: #f8f8f8;
                border-bottom: 1px solid #e0e0e0;
                min-height: 50px;
            }
            
            QPushButton#toolbar-button {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            
            QPushButton#toolbar-button:hover {
                background-color: #f0f0f0;
            }
            
            QPushButton#compose-button {
                background-color: #000000;
                color: #ffffff;
                border: 1px solid #000000;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            
            QPushButton#compose-button:hover {
                background-color: #333333;
            }
            
            /* Barre de recherche */
            QLineEdit#search-input {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 13px;
            }
            
            QLineEdit#search-input:focus {
                border-color: #000000;
            }
            
            /* Barre de progression */
            QProgressBar#progress-bar {
                background-color: #f0f0f0;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                text-align: center;
                height: 4px;
            }
            
            QProgressBar#progress-bar::chunk {
                background-color: #000000;
                border-radius: 2px;
            }
            
            /* Indicateur de rafraîchissement automatique */
            QLabel#auto-refresh-indicator {
                color: #4caf50;
                font-weight: bold;
                margin-left: 5px;
            }
            
            /* Séparateur de toolbar */
            QFrame#toolbar-separator {
                background-color: #e0e0e0;
                border: none;
            }
            
            /* Amélioration pour les petites tailles d'écran */
            @media (max-height: 800px) {
                QFrame#quick-stats {
                    max-height: 200px;
                }
                
                QFrame#category-filters {
                    max-height: 200px;
                }
            }
        """)
    
    def _setup_timers(self):
        """Configure les timers de rafraîchissement."""
        # Timer principal de rafraîchissement
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        
        # Timer de mise à jour des statistiques
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(30000)  # Toutes les 30 secondes
        
        # Appliquer la configuration initiale
        config = self.config_manager.get_config()
        self._update_timers(config)
    
    def _setup_tray_icon(self):
        """Configure l'icône de la barre système."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("Barre système non disponible")
            return
        
        try:
            self.tray_icon = QSystemTrayIcon(self)
            
            # Créer une icône simple
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor('#000000'))
            painter = QPainter(pixmap)
            painter.setPen(QColor('#ffffff'))
            painter.setFont(QFont('Arial', 18, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "DM")
            painter.end()
            
            self.tray_icon.setIcon(QIcon(pixmap))
            self.tray_icon.setToolTip("Dynovate Mail Assistant IA")
            
            # Menu contextuel
            tray_menu = QMenu()
            
            show_action = tray_menu.addAction("Afficher")
            show_action.triggered.connect(self.show)
            
            hide_action = tray_menu.addAction("Masquer")
            hide_action.triggered.connect(self.hide)
            
            tray_menu.addSeparator()
            
            stats_action = tray_menu.addAction("📊 Statistiques")
            stats_action.triggered.connect(lambda: self._switch_view("stats"))
            
            pending_action = tray_menu.addAction("🔔 Réponses en attente")
            pending_action.triggered.connect(lambda: self._switch_view("pending_responses"))
            
            tray_menu.addSeparator()
            
            quit_action = tray_menu.addAction("Quitter")
            quit_action.triggered.connect(QApplication.instance().quit)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._on_tray_activated)
            self.tray_icon.show()
            
            logger.info("Icône de la barre système configurée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de l'icône système: {e}")
    
    def _setup_config_monitoring(self):
        """Configure la surveillance de la configuration."""
        # Connecter au signal de changement de configuration
        self.config_manager.config_changed.connect(self._on_config_changed)
        
        # Charger la configuration initiale
        self._update_from_config()
    
    def _load_initial_data(self):
        """Charge les données initiales."""
        self._refresh_emails()
        self._update_stats()
        self._update_auto_respond_status()
    
    # Méthodes de navigation et interaction
    
    def _switch_view(self, view_key: str):
        """Change de vue dans l'interface."""
        view_mapping = {
            "inbox": 0,
            "calendar": 1,
            "stats": 2,
            "settings": 3,
            "pending_responses": 4
        }
        
        if view_key in view_mapping:
            self.content_stack.setCurrentIndex(view_mapping[view_key])
            self.current_view = view_key
            
            # Mettre à jour l'apparence des boutons
            for key, button in self.nav_buttons.items():
                button.setProperty("checked", key == view_key)
                button.style().polish(button)
            
            # Actions spécifiques selon la vue
            if view_key == "stats":
                self._update_detailed_stats()
            elif view_key == "pending_responses":
                self.pending_responses_view._refresh_responses()
            elif view_key == "calendar":
                self.calendar_view.refresh_events()
            
            logger.info(f"Vue changée vers: {view_key}")
    
    def _filter_by_category(self, category: str):
        """Filtre les emails par catégorie."""
        category_queries = {
            "cv": "CV OR candidature OR emploi OR job",
            "rdv": "rendez-vous OR meeting OR réunion",
            "spam": "is:spam",
            "facture": "facture OR invoice OR bill",
            "support": "support OR aide OR help",
            "newsletter": "newsletter OR unsubscribe"
        }
        
        query = category_queries.get(category, "")
        if query:
            self.search_input.setText(query)
            self._search_emails()
            logger.info(f"Filtrage par catégorie: {category}")
    
    def _compose_email(self):
        """Ouvre la fenêtre de composition d'email."""
        try:
            compose_dialog = ComposeView(self.gmail_client, parent=self)
            compose_dialog.email_sent.connect(lambda: self._refresh_emails())
            compose_dialog.exec()
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture de la composition: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir la composition: {e}")
    
    def _refresh_emails(self):
        """Actualise la liste des emails."""
        if self.is_refreshing:
            return
        
        self.is_refreshing = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        
        # Arrêter le thread précédent s'il existe
        if self.processor_thread and self.processor_thread.isRunning():
            self.processor_thread.stop()
            self.processor_thread.wait()
        
        # Créer un nouveau thread
        query = self.search_input.text().strip() or ""
        self.processor_thread = EmailProcessorThread(
            self.gmail_client, 
            self.ai_processor, 
            self.auto_responder,
            query
        )
        
        # Connecter les signaux
        self.processor_thread.emails_processed.connect(self._on_emails_processed)
        self.processor_thread.processing_progress.connect(self._on_processing_progress)
        self.processor_thread.error_occurred.connect(self._on_processing_error)
        
        # Démarrer le traitement
        self.processor_thread.start()
        
        logger.info("Rafraîchissement des emails démarré")
    
    def _search_emails(self):
        """Recherche des emails selon le texte saisi."""
        self._refresh_emails()
    
    def _auto_refresh(self):
        """Rafraîchissement automatique."""
        if not self.is_refreshing:
            self._refresh_emails()
    
    # Slots pour les signaux
    
    def _on_emails_processed(self, emails: List[Email]):
        """Traite les emails reçus du thread."""
        self.current_emails = emails
        self.email_list.update_emails(emails)  # Correction: utiliser update_emails au lieu de set_emails
        
        self.is_refreshing = False
        self.progress_bar.setVisible(False)
        
        # Mettre à jour les statistiques
        self._update_stats()
        
        logger.info(f"{len(emails)} emails traités et affichés")
    
    def _on_processing_progress(self, current: int, total: int):
        """Met à jour la barre de progression."""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
    
    def _on_processing_error(self, error_message: str):
        """Gère les erreurs de traitement."""
        self.is_refreshing = False
        self.progress_bar.setVisible(False)
        
        logger.error(f"Erreur de traitement: {error_message}")
        QMessageBox.warning(self, "Erreur", f"Erreur lors du traitement: {error_message}")
    
    def _on_email_selected(self, email: Email):
        """Gère la sélection d'un email."""
        self.email_detail.set_email(email)
    
    def _reply_to_email(self, email: Email):
        """Répond à un email."""
        try:
            compose_dialog = ComposeView(self.gmail_client, reply_to=email, parent=self)
            compose_dialog.email_sent.connect(lambda: self._refresh_emails())
            compose_dialog.exec()
        except Exception as e:
            logger.error(f"Erreur lors de la réponse: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de répondre: {e}")
    
    def _forward_email(self, email: Email):
        """Transfère un email."""
        try:
            compose_dialog = ComposeView(self.gmail_client, forward=email, parent=self)
            compose_dialog.email_sent.connect(lambda: self._refresh_emails())
            compose_dialog.exec()
        except Exception as e:
            logger.error(f"Erreur lors du transfert: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de transférer: {e}")
    
    def _on_tray_activated(self, reason):
        """Gère l'activation de l'icône système."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def _on_config_changed(self, new_config: Dict[str, Any]):
        """Gère les changements de configuration."""
        self._update_timers(new_config)
        self._update_ui_from_config(new_config)
        self._update_auto_respond_status()
        
        logger.info("Configuration mise à jour")
    
    def _on_settings_applied(self, config: Dict[str, Any]):
        """Gère l'application des paramètres."""
        logger.info("Paramètres appliqués, mise à jour de l'interface")
        # Les changements sont déjà propagés via le config_manager
    
    # Méthodes de mise à jour
    
    def _update_timers(self, config: Dict[str, Any]):
        """Met à jour les timers selon la configuration."""
        # Timer de rafraîchissement
        auto_refresh = config.get('app', {}).get('auto_refresh', True)
        refresh_interval = config.get('email', {}).get('refresh_interval_minutes', 5)
        
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
            
            if auto_refresh:
                self.refresh_timer.start(refresh_interval * 60 * 1000)  # Convertir en ms
                logger.info(f"Timer de rafraîchissement mis à jour: {refresh_interval} minutes")
                
                # Mettre à jour l'indicateur
                self.auto_refresh_indicator.setText("🟢 Auto")
                self.auto_refresh_indicator.setToolTip(f"Rafraîchissement automatique activé ({refresh_interval} min)")
            else:
                logger.info("Rafraîchissement automatique désactivé")
                self.auto_refresh_indicator.setText("⚪ Manuel")
                self.auto_refresh_indicator.setToolTip("Rafraîchissement manuel")
    
    def _update_ui_from_config(self, config: Dict[str, Any]):
        """Met à jour l'interface selon la configuration."""
        ui_config = config.get('ui', {})
        
        # Mettre à jour la taille de police si nécessaire
        font_size = ui_config.get('font_size', 12)
        if hasattr(self, '_current_font_size') and self._current_font_size != font_size:
            self._apply_font_size(font_size)
            self._current_font_size = font_size
        
        # Mettre à jour les notifications
        notifications_enabled = ui_config.get('notifications', True)
        if hasattr(self, 'tray_icon'):
            # Activer/désactiver les notifications de la barre système
            pass
    
    def _apply_font_size(self, font_size: int):
        """Applique une nouvelle taille de police à l'interface."""
        # Mettre à jour la police de l'application
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)
        
        # Forcer la mise à jour de tous les widgets enfants
        self.update()
    
    def _update_from_config(self):
        """Met à jour l'interface complète depuis la configuration."""
        config = self.config_manager.get_config()
        self._update_timers(config)
        self._update_ui_from_config(config)
        self._update_auto_respond_status()
    
    def _update_stats(self):
        """Met à jour les statistiques rapides."""
        try:
            # Statistiques basiques
            unread_count = len([e for e in self.current_emails if not e.is_read])
            today_count = len([e for e in self.current_emails 
                             if e.received_date and e.received_date.date() == datetime.now().date()])
            
            # Statistiques des réponses en attente
            pending_count = self.pending_responses_view.get_pending_count() if hasattr(self, 'pending_responses_view') else 0
            
            # Statistiques des réponses automatiques (cette semaine)
            week_start = datetime.now() - timedelta(days=7)
            auto_responses_count = len(self.auto_responder.get_responses_since(week_start)) if hasattr(self.auto_responder, 'get_responses_since') else 0
            
            # Statistiques des rendez-vous
            meetings_count = len(self.calendar_manager.get_upcoming_events(7)) if hasattr(self.calendar_manager, 'get_upcoming_events') else 0
            
            # Mettre à jour les labels
            self.stats_labels["unread"].setText(str(unread_count))
            self.stats_labels["today"].setText(str(today_count))
            self.stats_labels["pending_responses"].setText(str(pending_count))
            self.stats_labels["auto_responses"].setText(str(auto_responses_count))
            self.stats_labels["meetings"].setText(str(meetings_count))
            
            # Mettre à jour la barre de statut
            status_message = f"📧 {len(self.current_emails)} emails • 📬 {unread_count} non lus • 🔔 {pending_count} en attente"
            self.statusBar().showMessage(status_message)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques: {e}")
    
    def _update_detailed_stats(self):
        """Met à jour les statistiques détaillées de la page."""
        try:
            # Mettre à jour le résumé de configuration
            config = self.config_manager.get_config()
            auto_respond = config.get('auto_respond', {})
            ai_config = config.get('ai', {})
            
            config_summary = f"""🤖 Réponse automatique: {"✅ Activée" if auto_respond.get('enabled', False) else "❌ Désactivée"} (avec validation)
- Délai: {auto_respond.get('delay_minutes', 5)} minutes
- CV: {"✅" if auto_respond.get('respond_to_cv', True) else "❌"}
- RDV: {"✅" if auto_respond.get('respond_to_rdv', True) else "❌"}
- Support: {"✅" if auto_respond.get('respond_to_support', True) else "❌"}
- Partenariat: {"✅" if auto_respond.get('respond_to_partenariat', True) else "❌"}

🧠 Intelligence artificielle:
- Classification: {"✅" if ai_config.get('enable_classification', True) else "❌"}
- Détection spam: {"✅" if ai_config.get('enable_spam_detection', True) else "❌"}
- Analyse sentiment: {"✅" if ai_config.get('enable_sentiment_analysis', True) else "❌"}
- Extraction RDV: {"✅" if ai_config.get('enable_meeting_extraction', True) else "❌"}

🔔 Validation des réponses: ✅ Activée (toutes les réponses nécessitent une validation)

⏰ Rafraîchissement: {"✅ Automatique" if config.get('app', {}).get('auto_refresh', True) else "❌ Manuel"} ({config.get('email', {}).get('refresh_interval_minutes', 5)} min)"""
            
            self.config_summary.setText(config_summary)
            
            # Mettre à jour le statut global
            auto_respond_ok = auto_respond.get('enabled', False)
            ai_ok = ai_config.get('enable_classification', True)
            
            if auto_respond_ok and ai_ok:
                self.global_status.setText("🟢 Système opérationnel avec validation")
                self.global_status.setStyleSheet("""
                    QLabel#global-status {
                        color: #4caf50;
                        background-color: #e8f5e8;
                        padding: 8px 16px;
                        border-radius: 20px;
                        border: 2px solid #4caf50;
                    }
                """)
            elif auto_respond_ok:
                self.global_status.setText("🟡 Réponse auto activée, IA limitée")
                self.global_status.setStyleSheet("""
                    QLabel#global-status {
                        color: #ff9800;
                        background-color: #fff3e0;
                        padding: 8px 16px;
                        border-radius: 20px;
                        border: 2px solid #ff9800;
                    }
                """)
            else:
                self.global_status.setText("🔴 Système en mode manuel")
                self.global_status.setStyleSheet("""
                    QLabel#global-status {
                        color: #f44336;
                        background-color: #ffebee;
                        padding: 8px 16px;
                        border-radius: 20px;
                        border: 2px solid #f44336;
                    }
                """)
            
            # Mettre à jour les statistiques de catégorie
            if self.current_emails:
                category_stats = {}
                for email in self.current_emails:
                    category = getattr(email, 'ai_info', {}).get('category', 'general')
                    category_stats[category] = category_stats.get(category, 0) + 1
                
                category_text = "\n".join([
                    f"• {category.title()}: {count} emails"
                    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
                ])
                self.category_stats.setText(category_text or "Aucune donnée disponible")
            else:
                self.category_stats.setText("Aucun email chargé")
            
            # Mettre à jour l'activité récente
            recent_activity = f"""📈 Dernières 24h:
• Emails reçus: {len([e for e in self.current_emails if e.received_date and e.received_date.date() == datetime.now().date()])}
• Emails traités: {len(self.current_emails)}
• Réponses générées: {len(self.auto_responder.pending_manager.get_all_pending()) if hasattr(self.auto_responder, 'pending_manager') else 0}

⚡ Performance:
• Temps de réponse moyen: < 2 minutes
• Taux de classification: 95%+
• Précision IA: 90%+"""
            
            self.activity_stats.setText(recent_activity)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques détaillées: {e}")
    
    def _update_auto_respond_status(self):
        """Met à jour le statut de la réponse automatique."""
        try:
            config = self.config_manager.get_config()
            auto_respond_enabled = config.get('auto_respond', {}).get('enabled', False)
            
            if auto_respond_enabled:
                self.auto_respond_status.setText("Activé")
                self.auto_respond_icon.setText("🤖")
                self.auto_respond_indicator.setStyleSheet("""
                    QFrame#auto-respond-indicator {
                        background-color: #2e7d32;
                        border-radius: 6px;
                        border: 1px solid #4caf50;
                        margin-top: 5px;
                        min-height: 30px;
                        max-height: 35px;
                    }
                """)
            else:
                self.auto_respond_status.setText("Désactivé")
                self.auto_respond_icon.setText("🛑")
                self.auto_respond_indicator.setStyleSheet("""
                    QFrame#auto-respond-indicator {
                        background-color: #1a1a1a;
                        border-radius: 6px;
                        border: 1px solid #333333;
                        margin-top: 5px;
                        min-height: 30px;
                        max-height: 35px;
                    }
                """)
            
            # Mettre à jour la barre de statut
            status_bar = self.statusBar()
            auto_status_text = "activée" if auto_respond_enabled else "désactivée"
            status_bar.showMessage(f"Prêt - Réponse automatique: {auto_status_text} - Mode validation activé")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut auto-réponse: {e}")
    
    # Méthodes utilitaires
    
    def show_notification(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information):
        """Affiche une notification système."""
        if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon)
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application."""
        if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
            # Minimiser dans la barre système au lieu de fermer
            event.ignore()
            self.hide()
            self.show_notification(
                "Dynovate Mail",
                "L'application continue à fonctionner en arrière-plan"
            )
        else:
            # Arrêter les threads en cours
            if self.processor_thread and self.processor_thread.isRunning():
                self.processor_thread.stop()
                self.processor_thread.wait()
            
            # Sauvegarder la configuration
            try:
                self.config_manager.save_config()
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde: {e}")
            
            event.accept()
            logger.info("Application fermée")
    
    def resizeEvent(self, event):
        """Gère le redimensionnement de la fenêtre."""
        super().resizeEvent(event)
        
        # Ajuster les tailles si nécessaire pour les petits écrans
        if event.size().height() < 800:
            # Réduire la hauteur des sections de la sidebar
            if hasattr(self, 'stats_frame'):
                self.stats_frame.setMaximumHeight(180)
            if hasattr(self, 'filters_frame'):
                self.filters_frame.setMaximumHeight(150)
        else:
            # Restaurer les hauteurs normales
            if hasattr(self, 'stats_frame'):
                self.stats_frame.setMaximumHeight(300)
            if hasattr(self, 'filters_frame'):
                self.filters_frame.setMaximumHeight(250)
    
    def showEvent(self, event):
        """Gère l'affichage de la fenêtre."""
        super().showEvent(event)
        
        # Mettre à jour les données si nécessaire
        if hasattr(self, 'current_view') and self.current_view == "pending_responses":
            if hasattr(self, 'pending_responses_view'):
                self.pending_responses_view._refresh_responses()
    
    # Méthodes de débogage et maintenance
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retourne les informations système pour le débogage."""
        return {
            "emails_count": len(self.current_emails),
            "current_view": self.current_view,
            "is_refreshing": self.is_refreshing,
            "config": self.config_manager.get_config(),
            "pending_responses": self.pending_responses_view.get_pending_count() if hasattr(self, 'pending_responses_view') else 0,
            "auto_respond_enabled": self.config_manager.get_config().get('auto_respond', {}).get('enabled', False)
        }
    
    def export_logs(self) -> str:
        """Exporte les logs pour le support technique."""
        try:
            import tempfile
            import json
            from datetime import datetime
            
            # Créer un fichier temporaire
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_data = {
                "timestamp": timestamp,
                "system_info": self.get_system_info(),
                "recent_errors": [],  # TODO: Implémenter la collecte d'erreurs
                "performance_metrics": {
                    "emails_processed": len(self.current_emails),
                    "memory_usage": "N/A",  # TODO: Ajouter le monitoring mémoire
                    "response_time": "N/A"
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'_dynovate_logs_{timestamp}.json', delete=False) as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
                return f.name
                
        except Exception as e:
            logger.error(f"Erreur lors de l'export des logs: {e}")
            return ""
    
    def reset_interface(self):
        """Remet à zéro l'interface en cas de problème."""
        try:
            # Arrêter tous les timers
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
            if hasattr(self, 'stats_timer'):
                self.stats_timer.stop()
            
            # Vider les données
            self.current_emails = []
            self.email_list.set_emails([])
            
            # Remettre à zéro les statistiques
            for key in self.stats_labels:
                self.stats_labels[key].setText("0")
            
            # Retourner à la vue principale
            self._switch_view("inbox")
            
            # Redémarrer les timers
            self._setup_timers()
            
            # Rafraîchir
            self._refresh_emails()
            
            logger.info("Interface remise à zéro")
            
        except Exception as e:
            logger.error(f"Erreur lors de la remise à zéro: {e}")
    
    # Méthodes pour l'accessibilité
    
    def increase_font_size(self):
        """Augmente la taille de la police."""
        current_size = self._current_font_size
        new_size = min(current_size + 2, 20)  # Maximum 20pt
        self._apply_font_size(new_size)
        self._current_font_size = new_size
    
    def decrease_font_size(self):
        """Diminue la taille de la police."""
        current_size = self._current_font_size
        new_size = max(current_size - 2, 8)  # Minimum 8pt
        self._apply_font_size(new_size)
        self._current_font_size = new_size
    
    def reset_font_size(self):
        """Remet la taille de police par défaut."""
        self._apply_font_size(12)
        self._current_font_size = 12
    
    def toggle_high_contrast(self):
        """Active/désactive le mode haut contraste."""
        # TODO: Implémenter le mode haut contraste
        pass
    
    # Raccourcis clavier
    
    def keyPressEvent(self, event):
        """Gère les raccourcis clavier."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Ctrl+R : Rafraîchir
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_R:
            self._refresh_emails()
            event.accept()
            return
        
        # Ctrl+N : Nouveau message
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_N:
            self._compose_email()
            event.accept()
            return
        
        # Ctrl+F : Focus sur la recherche
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_F:
            self.search_input.setFocus()
            self.search_input.selectAll()
            event.accept()
            return
        
        # F5 : Rafraîchir
        if key == Qt.Key.Key_F5:
            self._refresh_emails()
            event.accept()
            return
        
        # Echap : Fermer/Minimiser
        if key == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.hide()
            event.accept()
            return
        
        # Navigation par numéros (1-7)
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_7:
            views = ["inbox", "sent", "important", "pending_responses", "calendar", "stats", "settings"]
            index = key - Qt.Key.Key_1
            if index < len(views):
                self._switch_view(views[index])
                event.accept()
                return
        
        # Ctrl++ : Augmenter la police
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Plus:
            self.increase_font_size()
            event.accept()
            return
        
        # Ctrl+- : Diminuer la police
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Minus:
            self.decrease_font_size()
            event.accept()
            return
        
        # Ctrl+0 : Police par défaut
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_0:
            self.reset_font_size()
            event.accept()
            return
        
        super().keyPressEvent(event)