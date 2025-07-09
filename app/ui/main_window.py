"""
Interface utilisateur principale moderne pour Gmail Assistant IA.
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
                
                # Vérifier si une réponse automatique est nécessaire
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
    """Interface principale moderne avec design noir et blanc."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor,
                 calendar_manager: CalendarManager, auto_responder: AutoResponder,
                 config: Dict[str, Any]):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.calendar_manager = calendar_manager
        self.auto_responder = auto_responder
        self.config = config
        
        self.emails = []
        self.filtered_emails = []
        self.current_filter = "all"
        self.processor_thread = None
        
        self._setup_ui()
        self._setup_style()
        self._setup_system_tray()
        self._setup_timers()
        self._load_initial_data()
    
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
    
    def _create_status_bar(self):
        """Crée la barre de statut moderne."""
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f8f8f8;
                border-top: 1px solid #e0e0e0;
                color: #666666;
                font-size: 12px;
                padding: 5px;
            }
        """)
        status_bar.showMessage("Prêt")
    
    
    def _create_sidebar(self) -> QWidget:
        """Crée la barre latérale moderne."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header avec logo
        header = QFrame()
        header.setObjectName("sidebar-header")
        header.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 20, 20, 20)
        
        # Logo/Titre
        title_label = QLabel("Dynovate Mail")
        title_label.setObjectName("app-title")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        layout.addWidget(header)
        
        # Boutons de navigation
        nav_buttons = [
            ("📧", "Boîte de réception", "inbox"),
            ("📤", "Envoyés", "sent"),
            ("⭐", "Importants", "important"),
            ("🗓️", "Calendrier", "calendar"),
            ("📊", "Statistiques", "stats"),
            ("⚙️", "Paramètres", "settings")
        ]
        
        self.nav_buttons = {}
        for icon, text, key in nav_buttons:
            btn = QPushButton(f"{icon}  {text}")
            btn.setObjectName("nav-button")
            btn.setFixedHeight(50)
            btn.clicked.connect(lambda checked, k=key: self._switch_view(k))
            layout.addWidget(btn)
            self.nav_buttons[key] = btn
        
        # Filtres par catégorie
        layout.addWidget(self._create_category_filters())
        
        # Statistiques rapides
        layout.addWidget(self._create_quick_stats())
        
        layout.addStretch()
        
        return sidebar
    
    def _create_category_filters(self) -> QWidget:
        """Crée les filtres par catégorie."""
        filters_frame = QFrame()
        filters_frame.setObjectName("category-filters")
        
        layout = QVBoxLayout(filters_frame)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel("Catégories")
        title.setObjectName("section-title")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Filtres
        categories = [
            ("📄", "CV/Candidatures", "cv"),
            ("🤝", "Rendez-vous", "rdv"),
            ("🛡️", "Spam", "spam"),
            ("🧾", "Factures", "facture"),
            ("🔧", "Support", "support"),
            ("📰", "Newsletters", "newsletter"),
            ("⚡", "Général", "general")
        ]
        
        self.category_buttons = {}
        for icon, text, key in categories:
            btn = QPushButton(f"{icon} {text}")
            btn.setObjectName("category-filter")
            btn.setFixedHeight(35)
            btn.clicked.connect(lambda checked, k=key: self._filter_by_category(k))
            layout.addWidget(btn)
            self.category_buttons[key] = btn
        
        return filters_frame
    
    def _create_quick_stats(self) -> QWidget:
        """Crée les statistiques rapides."""
        stats_frame = QFrame()
        stats_frame.setObjectName("quick-stats")
        
        layout = QVBoxLayout(stats_frame)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel("Statistiques")
        title.setObjectName("section-title")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Stats
        self.stats_labels = {}
        stats = [
            ("unread", "Non lus", "0"),
            ("today", "Aujourd'hui", "0"),
            ("auto_responses", "Réponses auto", "0"),
            ("meetings", "RDV cette semaine", "0")
        ]
        
        for key, text, value in stats:
            stat_widget = QFrame()
            stat_layout = QHBoxLayout(stat_widget)
            stat_layout.setContentsMargins(10, 5, 10, 5)
            
            label = QLabel(text)
            label.setObjectName("stat-label")
            
            value_label = QLabel(value)
            value_label.setObjectName("stat-value")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            stat_layout.addWidget(label)
            stat_layout.addWidget(value_label)
            
            layout.addWidget(stat_widget)
            self.stats_labels[key] = value_label
        
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
        
        # Vue emails
        self.email_view = self._create_email_view()
        self.content_stack.addWidget(self.email_view)
        
        # Vue calendrier
        self.calendar_view = CalendarView(self.calendar_manager)
        self.content_stack.addWidget(self.calendar_view)
        
        # Vue statistiques
        self.stats_view = self._create_stats_view()
        self.content_stack.addWidget(self.stats_view)
        
        # Vue paramètres
        self.settings_view = SettingsView(self.config)
        self.content_stack.addWidget(self.settings_view)
        
        layout.addWidget(self.content_stack)
        
        return main_widget
    
    def _create_toolbar(self) -> QWidget:
        """Crée la barre d'outils moderne."""
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(60)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Bouton de rafraîchissement
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setObjectName("toolbar-button")
        refresh_btn.clicked.connect(self._refresh_emails)
        layout.addWidget(refresh_btn)
        
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
        """Crée la vue des emails."""
        email_widget = QWidget()
        layout = QHBoxLayout(email_widget)
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Liste des emails
        self.email_list = EmailListView()
        self.email_list.email_selected.connect(self._on_email_selected)
        layout.addWidget(self.email_list)
        
        # Détail de l'email
        self.email_detail = EmailDetailView(self.gmail_client, self.ai_processor)
        self.email_detail.reply_requested.connect(self._reply_to_email)
        self.email_detail.forward_requested.connect(self._forward_email)
        layout.addWidget(self.email_detail)
        
        return email_widget
    
    def _create_stats_view(self) -> QWidget:
        """Crée la vue des statistiques."""
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel("Statistiques détaillées")
        title.setObjectName("page-title")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Conteneur pour les statistiques
        stats_container = QFrame()
        stats_container.setObjectName("stats-container")
        stats_layout = QVBoxLayout(stats_container)
        
        # Graphiques et métriques détaillées
        self.detailed_stats = QLabel("Statistiques en cours de chargement...")
        self.detailed_stats.setObjectName("detailed-stats")
        stats_layout.addWidget(self.detailed_stats)
        
        layout.addWidget(stats_container)
        layout.addStretch()
        
        return stats_widget
    
    def _setup_style(self):
        """Configure le style moderne noir et blanc."""
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
            
            /* Boutons de navigation */
            QPushButton#nav-button {
                background-color: transparent;
                color: #ffffff;
                border: none;
                padding: 15px 20px;
                text-align: left;
                font-size: 14px;
            }
            
            QPushButton#nav-button:hover {
                background-color: #333333;
            }
            
            QPushButton#nav-button:pressed {
                background-color: #555555;
            }
            
            /* Filtres de catégorie */
            QFrame#category-filters {
                background-color: #000000;
                border-top: 1px solid #333333;
            }
            
            QPushButton#category-filter {
                background-color: transparent;
                color: #cccccc;
                border: none;
                padding: 8px 10px;
                text-align: left;
                font-size: 12px;
            }
            
            QPushButton#category-filter:hover {
                background-color: #333333;
                color: #ffffff;
            }
            
            /* Statistiques rapides */
            QFrame#quick-stats {
                background-color: #000000;
                border-top: 1px solid #333333;
            }
            
            QLabel#section-title {
                color: #ffffff;
                margin-bottom: 10px;
            }
            
            QLabel#stat-label {
                color: #cccccc;
                font-size: 11px;
            }
            
            QLabel#stat-value {
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
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
                border-radius: 4px;
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
                border-radius: 4px;
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
                border-radius: 4px;
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
            }
            
            QProgressBar#progress-bar::chunk {
                background-color: #000000;
                border-radius: 3px;
            }
            
            /* Titre de page */
            QLabel#page-title {
                color: #000000;
                margin-bottom: 20px;
            }
            
            /* Conteneur de statistiques */
            QFrame#stats-container {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
            }
            
            QLabel#detailed-stats {
                color: #666666;
                font-size: 14px;
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
            
            quit_action = tray_menu.addAction("Quitter")
            quit_action.triggered.connect(QApplication.instance().quit)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._tray_icon_activated)
            
            # Icône (à remplacer par une vraie icône)
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor('#000000'))
            self.tray_icon.setIcon(QIcon(pixmap))
            
            self.tray_icon.show()
    
    def _setup_timers(self):
        """Configure les timers pour les mises à jour automatiques."""
        # Timer pour rafraîchir les emails
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(300000)  # 5 minutes
        
        # Timer pour mettre à jour les statistiques
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(60000)  # 1 minute
    
    def _load_initial_data(self):
        """Charge les données initiales."""
        self._switch_view("inbox")
        self._refresh_emails()
    
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
        self.current_filter = category
        self._apply_filters()
    
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
        self.stats_labels["auto_responses"].setText(str(auto_stats.get("recent_responses", 0)))
        
        # Rendez-vous cette semaine
        week_events = self.calendar_manager.get_events_for_week()
        self.stats_labels["meetings"].setText(str(len(week_events)))
    
    def _update_detailed_stats(self):
        """Met à jour les statistiques détaillées."""
        if not self.emails:
            self.detailed_stats.setText("Aucun email à analyser")
            return
        
        # Analyser les emails par catégorie
        categories = {}
        for email in self.emails:
            if hasattr(email, 'ai_info'):
                category = email.ai_info.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
        
        # Créer le texte des statistiques
        stats_text = f"""
        📊 STATISTIQUES DÉTAILLÉES
        
        Total d'emails: {len(self.emails)}
        Emails non lus: {len([e for e in self.emails if e.is_unread])}
        Emails importants: {len([e for e in self.emails if e.is_important])}
        
        📁 RÉPARTITION PAR CATÉGORIE:
        """
        
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.emails)) * 100
            stats_text += f"\n{category.upper()}: {count} emails ({percentage:.1f}%)"
        
        # Statistiques temporelles
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        recent_emails = [
            e for e in self.emails
            if e.datetime.date() >= week_ago
        ]
        
        stats_text += f"""
        
        📅 ACTIVITÉ RÉCENTE:
        Cette semaine: {len(recent_emails)} emails
        Aujourd'hui: {len([e for e in self.emails if e.datetime.date() == today])}
        
        🤖 RÉPONSES AUTOMATIQUES:
        Statut: {"Activé" if self.auto_responder.auto_respond_enabled else "Désactivé"}
        Réponses envoyées: {self.auto_responder.get_response_stats().get("total_responses", 0)}
        """
        
        self.detailed_stats.setText(stats_text)
    
    def _tray_icon_activated(self, reason):
        """Callback pour l'icône de la barre système."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def closeEvent(self, event):
        """Événement de fermeture."""
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            if self.processor_thread and self.processor_thread.isRunning():
                self.processor_thread.stop()
                self.processor_thread.wait()
            event.accept()
    
    def show_notification(self, title: str, message: str):
        """Affiche une notification."""
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)