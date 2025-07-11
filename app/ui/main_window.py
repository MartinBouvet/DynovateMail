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
    QApplication, QMessageBox, QDialog, QTabWidget
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
                 calendar_manager: CalendarManager, auto_responder: AutoResponder):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.calendar_manager = calendar_manager
        self.auto_responder = auto_responder
        
        # Gestionnaire de configuration réactif
        self.config_manager = get_config_manager()
        
        self.emails = []
        self.filtered_emails = []
        self.current_filter = "all"
        self.processor_thread = None
        self.selected_email = None
        
        # Compteur pour les notifications de réponses en attente
        self._last_pending_count = 0
        
        self._setup_ui()
        self._setup_style()
        self._setup_system_tray()
        self._setup_timers()
        self._connect_config_signals()
        self._load_initial_data()
        
        logger.info("Interface principale initialisée avec validation des réponses")
    
    def _connect_config_signals(self):
        """Connecte les signaux de configuration."""
        # S'abonner aux changements de configuration
        self.config_manager.config_changed.connect(self._on_config_changed)
        
        # Connecter le signal des paramètres
        if hasattr(self, 'settings_view'):
            self.settings_view.settings_applied.connect(self._on_settings_applied)
    
    def _on_config_changed(self, new_config: Dict[str, Any]):
        """Callback appelé quand la configuration change."""
        logger.info("Configuration changée, application des nouveaux paramètres")
        
        # Mettre à jour les timers
        self._update_timers(new_config)
        
        # Mettre à jour l'auto-responder (déjà fait automatiquement via son observer)
        
        # Mettre à jour l'interface si nécessaire
        self._update_ui_from_config(new_config)
    
    def _on_settings_applied(self, config: Dict[str, Any]):
        """Callback appelé quand les paramètres sont appliqués."""
        logger.info("Paramètres appliqués, mise à jour de l'interface")
        # Les changements sont déjà propagés via le config_manager
    
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
            else:
                logger.info("Rafraîchissement automatique désactivé")
    
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
        """Crée la barre latérale moderne et responsive."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        
        layout = QVBoxLayout(sidebar)
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
        
        layout.addStretch()
        
        return sidebar
    
    def _create_category_filters(self) -> QWidget:
        """Crée les filtres par catégorie."""
        filters_frame = QFrame()
        filters_frame.setObjectName("category-filters")
        
        layout = QVBoxLayout(filters_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title = QLabel("Catégories")
        title.setObjectName("section-title")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
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
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, k=key: self._filter_by_category(k))
            layout.addWidget(btn)
            self.category_buttons[key] = btn
        
        return filters_frame
    
    def _create_quick_stats(self) -> QWidget:
        """Crée les statistiques rapides."""
        stats_frame = QFrame()
        stats_frame.setObjectName("quick-stats")
        
        layout = QVBoxLayout(stats_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        
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
        toolbar.setFixedHeight(55)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Bouton de rafraîchissement avec indicateur auto
        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.setObjectName("toolbar-button")
        self.refresh_btn.clicked.connect(self._refresh_emails)
        layout.addWidget(self.refresh_btn)
        
        # Indicateur de rafraîchissement automatique
        self.auto_refresh_indicator = QLabel("⚡ Auto")
        self.auto_refresh_indicator.setObjectName("auto-refresh-indicator")
        self.auto_refresh_indicator.setFont(QFont("Arial", 10))
        self.auto_refresh_indicator.setVisible(False)
        layout.addWidget(self.auto_refresh_indicator)
        
        # Barre de recherche
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search-input")
        self.search_input.setPlaceholderText("Rechercher dans les emails...")
        self.search_input.returnPressed.connect(self._search_emails)
        layout.addWidget(self.search_input)
        
        # Bouton de composition
        compose_btn = QPushButton("✏️ Nouveau")
        compose_btn.setObjectName("compose-button")
        compose_btn.clicked.connect(self._compose_email)
        layout.addWidget(compose_btn)
        
        # Indicateur de traitement
        self.processing_indicator = QProgressBar()
        self.processing_indicator.setObjectName("progress-bar")
        self.processing_indicator.setVisible(False)
        layout.addWidget(self.processing_indicator)
        
        return toolbar
    
    def _create_email_view(self) -> QWidget:
        """Crée la vue des emails avec splitter amélioré."""
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
        """Crée la vue des statistiques améliorée."""
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
        details_layout.addWidget(self.category_stats)
        
        # Section activité récente
        activity_title = QLabel("📈 Activité récente")
        activity_title.setObjectName("stats-section-title")
        activity_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        details_layout.addWidget(activity_title)
        
        self.activity_stats = QLabel("Chargement...")
        self.activity_stats.setObjectName("stats-content")
        self.activity_stats.setFont(QFont("Arial", 12))
        details_layout.addWidget(self.activity_stats)
        
        layout.addWidget(details_frame)
        layout.addStretch()
        
        return stats_widget
    
    def _create_stat_card(self, icon: str, title: str, value: str, subtitle: str) -> QWidget:
        """Crée une carte de statistique."""
        card = QFrame()
        card.setObjectName("stat-card")
        card.setFixedHeight(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Header avec icône et titre
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 20))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("card-title")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
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
        layout.addWidget(subtitle_label)
        
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
        """Configure le style moderne noir et blanc amélioré."""
        self.setStyleSheet("""
            /* Style général */
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
            }
            
            /* Sidebar */
            QFrame#sidebar {
                background-color: #000000;
                border-right: 1px solid #333333;
            }
            
            QFrame#sidebar-header {
                background-color: #000000;
                border-bottom: 1px solid #333333;
            }
            
            QLabel#app-title {
                color: #ffffff;
                font-weight: bold;
            }
            
            /* Séparateurs */
            QFrame#sidebar-separator {
                background-color: #333333;
                border: none;
            }
            
            /* Boutons de navigation */
            QPushButton#nav-button {
                background-color: transparent;
                color: #cccccc;
                border: none;
                padding: 12px 15px;
                text-align: left;
                font-size: 13px;
                border-radius: 6px;
                margin: 2px 10px;
            }
            
            QPushButton#nav-button:hover {
                background-color: #333333;
                color: #ffffff;
            }
            
            QPushButton#nav-button:pressed {
                background-color: #555555;
            }
            
            /* Filtres de catégorie */
            QFrame#category-filters {
                background-color: #000000;
            }
            
            QPushButton#category-filter {
                background-color: transparent;
                color: #999999;
                border: none;
                padding: 8px 10px;
                text-align: left;
                font-size: 11px;
                border-radius: 4px;
                margin: 1px 0px;
            }
            
            QPushButton#category-filter:hover {
                background-color: #333333;
                color: #ffffff;
            }
            
            /* Statistiques rapides */
            QFrame#quick-stats {
                background-color: #000000;
            }
            
            QLabel#section-title {
                color: #ffffff;
                margin-bottom: 8px;
            }
            
            QFrame#stat-item {
                background-color: transparent;
                border-radius: 4px;
                margin: 2px 0px;
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
           }
           
           QLabel#auto-respond-status {
               color: #ffffff;
               font-size: 10px;
           }
           
           /* Barre d'outils */
           QFrame#toolbar {
               background-color: #f8f8f8;
               border-bottom: 1px solid #e0e0e0;
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
           
           QLabel#auto-refresh-indicator {
               color: #4caf50;
               font-weight: bold;
               margin-left: 5px;
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
           
           /* Page des statistiques */
           QWidget#stats-page {
               background-color: #ffffff;
           }
           
           QLabel#stats-title {
               color: #000000;
               margin-bottom: 10px;
           }
           
           QLabel#global-status {
               color: #4caf50;
               padding: 8px 16px;
               background-color: #e8f5e8;
               border-radius: 20px;
           }
           
           QFrame#stat-card {
               background-color: #f8f8f8;
               border: 1px solid #e0e0e0;
               border-radius: 10px;
               margin: 5px;
           }
           
           QFrame#stat-card:hover {
               border-color: #cccccc;
           }
           
           QLabel#card-title {
               color: #666666;
           }
           
           QLabel#card-value {
               color: #000000;
               margin: 5px 0px;
           }
           
           QLabel#card-subtitle {
               color: #999999;
           }
           
           QFrame#config-frame {
               background-color: #f0f8ff;
               border: 1px solid #cce0ff;
               border-radius: 10px;
               margin-top: 10px;
           }
           
           QFrame#stats-details {
               background-color: #f8f8f8;
               border: 1px solid #e0e0e0;
               border-radius: 10px;
               margin-top: 10px;
           }
           
           QLabel#stats-section-title, QLabel#config-section-title {
               color: #000000;
               margin: 10px 0px;
           }
           
           QLabel#stats-content, QLabel#config-content {
               color: #333333;
               line-height: 1.4;
           }
           
           /* Splitter */
           QSplitter::handle {
               background-color: #e0e0e0;
               width: 1px;
           }
           
           QSplitter::handle:hover {
               background-color: #cccccc;
           }
       """)
   
    def _setup_system_tray(self):
       """Configure l'icône de la barre système."""
       if QSystemTrayIcon.isSystemTrayAvailable():
           self.tray_icon = QSystemTrayIcon(self)
           
           # Menu contextuel
           tray_menu = QMenu()
           
           show_action = tray_menu.addAction("Afficher")
           show_action.triggered.connect(self.show)
           
           tray_menu.addSeparator()
           
           # Action pour activer/désactiver les réponses automatiques
           self.auto_respond_action = tray_menu.addAction("Activer réponses auto")
           self.auto_respond_action.setCheckable(True)
           self.auto_respond_action.triggered.connect(self._toggle_auto_respond_from_tray)
           
           # Action pour voir les réponses en attente
           pending_action = tray_menu.addAction("Voir réponses en attente")
           pending_action.triggered.connect(lambda: self._switch_view("pending_responses"))
           
           tray_menu.addSeparator()
           
           quit_action = tray_menu.addAction("Quitter")
           quit_action.triggered.connect(QApplication.instance().quit)
           
           self.tray_icon.setContextMenu(tray_menu)
           self.tray_icon.activated.connect(self._tray_icon_activated)
           
           # Icône (à remplacer par une vraie icône)
           pixmap = QPixmap(16, 16)
           pixmap.fill(QColor('#000000'))
           self.tray_icon.setIcon(QIcon(pixmap))
           
           self.tray_icon.show()
           
           # Mettre à jour l'état initial
           self._update_tray_auto_respond_state()
   
    def _toggle_auto_respond_from_tray(self):
       """Active/désactive les réponses automatiques depuis la barre système."""
       current_state = self.config_manager.get('auto_respond.enabled', False)
       new_state = not current_state
       self.config_manager.set('auto_respond.enabled', new_state)
       
       # Afficher une notification
       if self.tray_icon:
           status = "activées" if new_state else "désactivées"
           self.tray_icon.showMessage(
               "Dynovate Mail",
               f"Réponses automatiques {status}",
               QSystemTrayIcon.MessageIcon.Information,
               3000
           )
   
    def _update_tray_auto_respond_state(self):
       """Met à jour l'état de la réponse automatique dans le menu de la barre système."""
       if hasattr(self, 'auto_respond_action'):
           enabled = self.config_manager.get('auto_respond.enabled', False)
           self.auto_respond_action.setChecked(enabled)
           self.auto_respond_action.setText(
               "Désactiver réponses auto" if enabled else "Activer réponses auto"
           )
   
    def _setup_timers(self):
       """Configure les timers pour les mises à jour automatiques."""
       # Timer pour rafraîchir les emails
       self.refresh_timer = QTimer()
       self.refresh_timer.timeout.connect(self._auto_refresh)
       
       # Timer pour mettre à jour les statistiques
       self.stats_timer = QTimer()
       self.stats_timer.timeout.connect(self._update_stats)
       self.stats_timer.start(60000)  # 1 minute
       
       # Timer pour mettre à jour l'indicateur de status
       self.status_timer = QTimer()
       self.status_timer.timeout.connect(self._update_status_indicators)
       self.status_timer.start(5000)  # 5 secondes
       
       # Timer pour vérifier les réponses en attente
       self.pending_check_timer = QTimer()
       self.pending_check_timer.timeout.connect(self._check_pending_responses)
       self.pending_check_timer.start(15000)  # Vérifier toutes les 15 secondes
       
       # Appliquer la configuration initiale des timers
       config = self.config_manager.get_config()
       self._update_timers(config)
   
    def _check_pending_responses(self):
       """Vérifie s'il y a de nouvelles réponses en attente."""
       try:
           if hasattr(self, 'pending_responses_view'):
               pending_count = self.pending_responses_view.get_pending_count()
               
               # Vérifier si le nombre a augmenté
               if not hasattr(self, '_last_pending_count'):
                   self._last_pending_count = 0
               
               if pending_count > self._last_pending_count:
                   new_count = pending_count - self._last_pending_count
                   self.show_notification(
                       "Nouvelle réponse en attente",
                       f"{new_count} nouvelle(s) réponse(s) automatique(s) en attente de validation"
                   )
               
               self._last_pending_count = pending_count
               
               # Mettre à jour l'indicateur dans la sidebar
               if "pending_responses" in self.nav_buttons:
                   button_text = f"🔔  Réponses en attente"
                   if pending_count > 0:
                       button_text += f" ({pending_count})"
                   self.nav_buttons["pending_responses"].setText(button_text)
                   
       except Exception as e:
           logger.error(f"Erreur lors de la vérification des réponses en attente: {e}")
   
    def _update_status_indicators(self):
       """Met à jour les indicateurs de statut."""
       config = self.config_manager.get_config()
       
       # Indicateur de réponse automatique dans la sidebar
       auto_respond_enabled = config.get('auto_respond', {}).get('enabled', False)
       if auto_respond_enabled:
           self.auto_respond_status.setText("Activé")
           self.auto_respond_status.setStyleSheet("color: #4caf50; font-weight: bold;")
           self.auto_respond_indicator.setStyleSheet("""
               QFrame#auto-respond-indicator {
                   background-color: #e8f5e8;
                   border: 1px solid #4caf50;
                   border-radius: 6px;
               }
           """)
       else:
           self.auto_respond_status.setText("Désactivé")
           self.auto_respond_status.setStyleSheet("color: #f44336; font-weight: bold;")
           self.auto_respond_indicator.setStyleSheet("""
               QFrame#auto-respond-indicator {
                   background-color: #1a1a1a;
                   border: 1px solid #333333;
                   border-radius: 6px;
               }
           """)
       
       # Indicateur de rafraîchissement automatique
       auto_refresh_enabled = config.get('app', {}).get('auto_refresh', True)
       self.auto_refresh_indicator.setVisible(auto_refresh_enabled)
       
       # Mettre à jour la barre de statut
       auto_respond_status = "activée" if auto_respond_enabled else "désactivée"
       refresh_status = "activé" if auto_refresh_enabled else "désactivé"
       self.statusBar().showMessage(
           f"Réponse automatique: {auto_respond_status} | Rafraîchissement: {refresh_status} | Mode validation activé"
       )
       
       # Mettre à jour le menu de la barre système
       self._update_tray_auto_respond_state()
   
    def _load_initial_data(self):
       """Charge les données initiales."""
       self._switch_view("inbox")
       self._refresh_emails()
       self._update_status_indicators()
   
    def _switch_view(self, view_name: str):
       """Change la vue active."""
       # Reset des boutons
       for btn in self.nav_buttons.values():
           btn.setStyleSheet("")
       
       # Highlight du bouton actif
       if view_name in self.nav_buttons:
           self.nav_buttons[view_name].setStyleSheet("""
               QPushButton#nav-button {
                   background-color: #333333;
                   color: #ffffff;
               }
           """)
       
       # Changer la vue
       if view_name == "inbox":
           self.current_filter = "inbox"
           self.content_stack.setCurrentWidget(self.email_view)
           self._refresh_emails()
       elif view_name == "sent":
           self.current_filter = "sent"
           self.content_stack.setCurrentWidget(self.email_view)
           self._refresh_emails()
       elif view_name == "important":
           self.current_filter = "important"
           self.content_stack.setCurrentWidget(self.email_view)
           self._refresh_emails()
       elif view_name == "pending_responses":
           self.content_stack.setCurrentWidget(self.pending_responses_view)
           self.pending_responses_view._refresh_responses()
       elif view_name == "calendar":
           self.content_stack.setCurrentWidget(self.calendar_view)
           self.calendar_view.refresh_events()
       elif view_name == "stats":
           self.content_stack.setCurrentWidget(self.stats_view)
           self._update_detailed_stats()
       elif view_name == "settings":
           self.content_stack.setCurrentWidget(self.settings_view)
   
    def _filter_by_category(self, category: str):
       """Filtre les emails par catégorie."""
       # Reset visual state of all category buttons
       for btn in self.category_buttons.values():
           btn.setStyleSheet("""
               QPushButton#category-filter {
                   background-color: transparent;
                   color: #999999;
                   border: none;
                   padding: 8px 10px;
                   text-align: left;
                   font-size: 11px;
                   border-radius: 4px;
                   margin: 1px 0px;
               }
               QPushButton#category-filter:hover {
                   background-color: #333333;
                   color: #ffffff;
               }
           """)
       
       # Highlight selected category
       if category in self.category_buttons:
           self.category_buttons[category].setStyleSheet("""
               QPushButton#category-filter {
                   background-color: #333333;
                   color: #ffffff;
                   border: none;
                   padding: 8px 10px;
                   text-align: left;
                   font-size: 11px;
                   border-radius: 4px;
                   margin: 1px 0px;
               }
           """)
       
       # Switch to email view if not already there
       self.content_stack.setCurrentWidget(self.email_view)
       
       # Apply the filter
       self.current_filter = category
       self._apply_filters()
       
       logger.info(f"Filtrage par catégorie: {category}")
   
    def _apply_filters(self):
       """Applique les filtres actuels."""
       if self.current_filter == "all":
           self.filtered_emails = self.emails
       elif self.current_filter == "inbox":
           self.filtered_emails = [e for e in self.emails if not e.is_sent]
       elif self.current_filter == "sent":
           self.filtered_emails = [e for e in self.emails if e.is_sent]
       elif self.current_filter == "important":
           self.filtered_emails = [e for e in self.emails if e.is_important]
       else:
           # Filtrer par catégorie IA
           self.filtered_emails = [
               e for e in self.emails
               if hasattr(e, 'ai_info') and e.ai_info.get('category') == self.current_filter
           ]
       
       self.email_list.update_emails(self.filtered_emails)
       self._update_stats()
   
    def _refresh_emails(self):
       """Rafraîchit la liste des emails."""
       if self.processor_thread and self.processor_thread.isRunning():
           return
       
       self.processing_indicator.setVisible(True)
       self.processing_indicator.setRange(0, 0)  # Indéterminé
       
       query = ""
       if self.current_filter == "sent":
           query = "in:sent"
       elif self.current_filter == "important":
           query = "is:important"
       
       self.processor_thread = EmailProcessorThread(
           self.gmail_client,
           self.ai_processor,
           self.auto_responder,
           query
       )
       
       self.processor_thread.emails_processed.connect(self._on_emails_processed)
       self.processor_thread.processing_progress.connect(self._on_processing_progress)
       self.processor_thread.error_occurred.connect(self._on_processing_error)
       self.processor_thread.finished.connect(self._on_processing_finished)
       
       self.processor_thread.start()
   
    def _on_emails_processed(self, emails: List[Email]):
       """Callback quand les emails sont traités."""
       self.emails = emails
       self._apply_filters()
   
    def _on_processing_progress(self, current: int, total: int):
       """Callback pour le progrès du traitement."""
       self.processing_indicator.setRange(0, total)
       self.processing_indicator.setValue(current)
   
    def _on_processing_error(self, error: str):
       """Callback en cas d'erreur."""
       QMessageBox.critical(self, "Erreur", f"Erreur lors du traitement: {error}")
   
    def _on_processing_finished(self):
       """Callback quand le traitement est terminé."""
       self.processing_indicator.setVisible(False)
   
    def _search_emails(self):
       """Recherche des emails."""
       query = self.search_input.text().strip()
       if query:
           self._refresh_emails()
   
    def _compose_email(self):
       """Ouvre la fenêtre de composition."""
       compose_dialog = ComposeView(self.gmail_client, self)
       compose_dialog.email_sent.connect(self._on_email_sent)
       compose_dialog.exec()
   
    def _on_email_selected(self, email: Email):
       """Callback quand un email est sélectionné."""
       self.selected_email = email
       self.email_detail.display_email(email)
   
    def _reply_to_email(self, email: Email):
       """Répond à un email."""
       reply_subject = f"Re: {email.subject}"
       reply_body = f"\n\n--- Message original ---\nDe: {email.sender}\nDate: {email.date}\nSujet: {email.subject}\n\n{email.body}"
       
       compose_dialog = ComposeView(
           self.gmail_client,
           self,
           to=email.get_sender_email(),
           subject=reply_subject,
           body=reply_body,
           is_reply=True
       )
       compose_dialog.email_sent.connect(self._on_email_sent)
       compose_dialog.exec()
   
    def _forward_email(self, email: Email):
       """Transfère un email."""
       forward_subject = f"Fwd: {email.subject}"
       forward_body = f"\n\n--- Message transféré ---\nDe: {email.sender}\nDate: {email.date}\nSujet: {email.subject}\n\n{email.body}"
       
       compose_dialog = ComposeView(
           self.gmail_client,
           self,
           subject=forward_subject,
           body=forward_body,
           is_forward=True
       )
       compose_dialog.email_sent.connect(self._on_email_sent)
       compose_dialog.exec()
   
    def _on_email_sent(self):
       """Callback quand un email est envoyé."""
       self._refresh_emails()
   
    def _auto_refresh(self):
       """Rafraîchissement automatique."""
       if not self.processor_thread or not self.processor_thread.isRunning():
           self._refresh_emails()
   
    def _update_stats(self):
       """Met à jour les statistiques rapides."""
       if not self.emails:
           return
       
       # Compter les emails non lus
       unread_count = len([e for e in self.emails if e.is_unread])
       self.stats_labels["unread"].setText(str(unread_count))
       
       # Compter les emails d'aujourd'hui
       today = datetime.now().date()
       today_count = len([
           e for e in self.emails
           if e.datetime.date() == today
       ])
       self.stats_labels["today"].setText(str(today_count))
       
       # Statistiques des réponses automatiques
       auto_stats = self.auto_responder.get_response_stats()
       self.stats_labels["auto_responses"].setText(str(auto_stats.get("sent_count", 0)))
       
       # Statistiques des réponses en attente
       if hasattr(self, 'pending_responses_view'):
           pending_count = self.pending_responses_view.get_pending_count()
           self.stats_labels["pending_responses"].setText(str(pending_count))
       
       # Rendez-vous cette semaine
       week_events = self.calendar_manager.get_events_for_week()
       self.stats_labels["meetings"].setText(str(len(week_events)))
   
    def _update_detailed_stats(self):
       """Met à jour les statistiques détaillées."""
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
                   font-weight: bold;
               }
           """)
       elif ai_ok:
           self.global_status.setText("🟡 IA active, auto-réponse désactivée")
           self.global_status.setStyleSheet("""
               QLabel#global-status {
                   color: #ff9800;
                   background-color: #fff8e1;
                   padding: 8px 16px;
                   border-radius: 20px;
                   font-weight: bold;
               }
           """)
       else:
           self.global_status.setText("🔴 Fonctionnalités limitées")
           self.global_status.setStyleSheet("""
               QLabel#global-status {
                   color: #f44336;
                   background-color: #ffebee;
                   padding: 8px 16px;
                   border-radius: 20px;
                   font-weight: bold;
               }
           """)
       
       # Mettre à jour la carte des réponses en attente
       pending_stats = self.auto_responder.get_response_stats()
       pending_card_value = self.pending_card.findChild(QLabel, "card-value")
       pending_card_subtitle = self.pending_card.findChild(QLabel, "card-subtitle")
       if pending_card_value and pending_card_subtitle:
           pending_count = pending_stats.get("pending_count", 0)
           pending_card_value.setText(str(pending_count))
           if pending_count > 0:
               pending_card_subtitle.setText("🔔 En attente")
               pending_card_subtitle.setStyleSheet("color: #ff9800; font-weight: bold;")
           else:
               pending_card_subtitle.setText("✅ Aucune")
               pending_card_subtitle.setStyleSheet("color: #4caf50; font-weight: bold;")
       
       # Mettre à jour la carte auto-responder
       auto_card_value = self.auto_card.findChild(QLabel, "card-value")
       auto_card_subtitle = self.auto_card.findChild(QLabel, "card-subtitle")
       if auto_card_value and auto_card_subtitle:
           if auto_respond.get('enabled', False):
               auto_card_value.setText(str(pending_stats.get("sent_count", 0)))
               auto_card_subtitle.setText("🟢 Activé")
               auto_card_subtitle.setStyleSheet("color: #4caf50; font-weight: bold;")
           else:
               auto_card_value.setText("--")
               auto_card_subtitle.setText("🔴 Désactivé")
               auto_card_subtitle.setStyleSheet("color: #f44336; font-weight: bold;")
       
       # Appel des statistiques existantes
       if not self.emails:
           self.category_stats.setText("Aucun email à analyser")
           self.activity_stats.setText("Aucune activité")
           return
       
       # Analyser les emails par catégorie
       categories = {}
       for email in self.emails:
           if hasattr(email, 'ai_info'):
               category = email.ai_info.get('category', 'general')
               categories[category] = categories.get(category, 0) + 1
       
       # Créer le texte des catégories
       category_lines = []
       total_categorized = sum(categories.values())
       
       for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
           percentage = (count / total_categorized) * 100 if total_categorized > 0 else 0
           category_lines.append(f"• {category.upper()}: {count} emails ({percentage:.1f}%)")
       
       category_text = "\n".join(category_lines[:8])  # Top 8 catégories
       if len(categories) > 8:
           category_text += f"\n... et {len(categories) - 8} autres catégories"
       
       self.category_stats.setText(category_text or "Aucune catégorisation disponible")
       
       # Statistiques temporelles
       today = datetime.now().date()
       week_ago = today - timedelta(days=7)
       
       recent_emails = [
           e for e in self.emails
           if e.datetime.date() >= week_ago
       ]
       
       unread_count = len([e for e in self.emails if e.is_unread])
       important_count = len([e for e in self.emails if e.is_important])
       
       # Statistiques des réponses en attente
       pending_text = f"""

🔔 Réponses en attente:
- En attente de validation: {pending_stats.get('pending_count', 0)}
- Approuvées aujourd'hui: {pending_stats.get('approved_count', 0)}
- Rejetées: {pending_stats.get('rejected_count', 0)}
- Envoyées au total: {pending_stats.get('sent_count', 0)}"""
       
       activity_text = f"""📊 Résumé général:
- Total d'emails: {len(self.emails)}
- Emails non lus: {unread_count}
- Emails importants: {important_count}
- Cette semaine: {len(recent_emails)} emails
- Aujourd'hui: {len([e for e in self.emails if e.datetime.date() == today])}

🤖 Réponses automatiques:
- Statut: {"✅ Activé avec validation" if auto_respond.get('enabled', False) else "❌ Désactivé"}
- Réponses envoyées: {pending_stats.get("sent_count", 0)}
- Cette semaine: {pending_stats.get("approved_count", 0)}{pending_text}"""
       
       self.activity_stats.setText(activity_text)
   
    def _tray_icon_activated(self, reason):
       """Callback pour l'icône de la barre système."""
       if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
           self.show()
           self.raise_()
           self.activateWindow()
   
    def closeEvent(self, event):
       """Événement de fermeture."""
       config = self.config_manager.get_config()
       minimize_to_tray = config.get('ui', {}).get('minimize_to_tray', True)
       
       if self.tray_icon and self.tray_icon.isVisible() and minimize_to_tray:
           self.hide()
           event.ignore()
       else:
           if self.processor_thread and self.processor_thread.isRunning():
               self.processor_thread.stop()
               self.processor_thread.wait()
           event.accept()
   
    def show_notification(self, title: str, message: str):
       """Affiche une notification."""
       config = self.config_manager.get_config()
       notifications_enabled = config.get('ui', {}).get('notifications', True)
       
       if self.tray_icon and self.tray_icon.isVisible() and notifications_enabled:
           self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
