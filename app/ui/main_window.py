#!/usr/bin/env python3
"""
Interface principale ultra-moderne style Discord/Notion avec design noir et blanc.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from gmail_client import GmailClient
from ai_processor import AIProcessor
from calendar_manager import CalendarManager
from auto_responder import AutoResponder
from models.email_model import Email
from ui.components.modern_sidebar import ModernSidebar
from ui.components.smart_email_card import SmartEmailCard
from ui.components.ai_suggestion_panel import AISuggestionPanel
from ui.views.smart_inbox_view import SmartInboxView
from ui.views.calendar_view import CalendarView
from ui.views.settings_view import SettingsView

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Interface principale avec design ultra-moderne."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor,
                 calendar_manager: CalendarManager, auto_responder: AutoResponder):
        super().__init__()
        
        # Services
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.calendar_manager = calendar_manager
        self.auto_responder = auto_responder
        
        # État
        self.current_emails = []
        self.current_view = "inbox"
        self.is_loading = False
        
        # Configuration de base
        self._setup_window()
        self._setup_ui()
        self._setup_theme()
        self._setup_connections()
        
        # Chargement initial
        self._load_initial_data()
        
        logger.info("Interface principale initialisée")
    
    def _setup_window(self):
        """Configure la fenêtre principale."""
        self.setWindowTitle("Dynovate Mail Assistant IA")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1200, 800)
        
        # Icône de l'application
        self.setWindowIcon(QIcon("assets/logo.png"))
    
    def _setup_ui(self):
        """Configure l'interface utilisateur moderne."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar moderne et collapsible
        self.sidebar = ModernSidebar()
        self.sidebar.view_changed.connect(self._on_view_changed)
        main_layout.addWidget(self.sidebar)
       
       # Zone principale avec animation
        self.main_area = self._create_main_area()
        main_layout.addWidget(self.main_area)
       
       # Panel IA flottant
        self.ai_panel = AISuggestionPanel()
        self.ai_panel.hide()  # Caché par défaut
   
    def _create_main_area(self) -> QWidget:
       """Crée la zone principale avec les vues."""
       container = QWidget()
       container.setObjectName("main-area")
       
       layout = QVBoxLayout(container)
       layout.setSpacing(0)
       layout.setContentsMargins(20, 20, 20, 20)
       
       # Header avec recherche et actions
       header = self._create_header()
       layout.addWidget(header)
       
       # Stack des vues principales
       self.view_stack = QStackedWidget()
       
       # Vue Inbox intelligente
       self.inbox_view = SmartInboxView(self.gmail_client, self.ai_processor)
       self.inbox_view.email_selected.connect(self._on_email_selected)
       self.inbox_view.ai_suggestion_requested.connect(self._show_ai_suggestion)
       self.view_stack.addWidget(self.inbox_view)
       
       # Vue Calendrier
       self.calendar_view = CalendarView(self.calendar_manager)
       self.view_stack.addWidget(self.calendar_view)
       
       # Vue Paramètres
       self.settings_view = SettingsView()
       self.view_stack.addWidget(self.settings_view)
       
       layout.addWidget(self.view_stack)
       
       return container
   
    def _create_header(self) -> QWidget:
       """Crée le header moderne avec recherche et actions."""
       header = QFrame()
       header.setObjectName("header")
       header.setFixedHeight(80)
       
       layout = QHBoxLayout(header)
       layout.setContentsMargins(0, 0, 0, 20)
       
       # Titre de la vue actuelle
       self.view_title = QLabel("Smart Inbox")
       self.view_title.setObjectName("view-title")
       self.view_title.setFont(QFont("Inter", 24, QFont.Weight.Bold))
       layout.addWidget(self.view_title)
       
       layout.addStretch()
       
       # Barre de recherche moderne
       search_container = QFrame()
       search_container.setObjectName("search-container")
       search_container.setFixedSize(400, 40)
       
       search_layout = QHBoxLayout(search_container)
       search_layout.setContentsMargins(15, 0, 15, 0)
       
       self.search_input = QLineEdit()
       self.search_input.setObjectName("search-input")
       self.search_input.setPlaceholderText("Rechercher dans vos emails...")
       self.search_input.textChanged.connect(self._on_search_changed)
       search_layout.addWidget(self.search_input)
       
       layout.addWidget(search_container)
       
       # Bouton refresh avec animation
       self.refresh_btn = QPushButton("🔄")
       self.refresh_btn.setObjectName("refresh-btn")
       self.refresh_btn.setFixedSize(40, 40)
       self.refresh_btn.clicked.connect(self._refresh_data)
       layout.addWidget(self.refresh_btn)
       
       # Indicateur de notifications
       self.notification_indicator = QLabel("●")
       self.notification_indicator.setObjectName("notification-indicator")
       self.notification_indicator.hide()
       layout.addWidget(self.notification_indicator)
       
       return header
   
    def _setup_theme(self):
       """Configure le thème noir et blanc moderne."""
       style = """
       /* Variables globales */
       * {
           font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
       }
       
       /* Fenêtre principale */
       QMainWindow {
           background-color: #ffffff;
           color: #000000;
       }
       
       /* Zone principale */
       #main-area {
           background-color: #ffffff;
           border-left: 1px solid #e5e5e5;
       }
       
       /* Header */
       #header {
           background-color: #ffffff;
           border-bottom: 1px solid #f0f0f0;
       }
       
       #view-title {
           color: #000000;
           font-weight: 700;
       }
       
       /* Recherche */
       #search-container {
           background-color: #f8f9fa;
           border: 1px solid #e9ecef;
           border-radius: 20px;
       }
       
       #search-input {
           background: transparent;
           border: none;
           color: #000000;
           font-size: 14px;
           font-weight: 400;
       }
       
       #search-input:focus {
           outline: none;
       }
       
       /* Boutons */
       #refresh-btn {
           background-color: #f8f9fa;
           border: 1px solid #e9ecef;
           border-radius: 20px;
           color: #6c757d;
           font-size: 16px;
       }
       
       #refresh-btn:hover {
           background-color: #e9ecef;
           color: #000000;
       }
       
       #refresh-btn:pressed {
           background-color: #dee2e6;
       }
       
       /* Indicateur de notification */
       #notification-indicator {
           color: #dc3545;
           font-size: 20px;
           font-weight: bold;
       }
       
       /* Scrollbars modernes */
       QScrollArea {
           border: none;
       }
       
       QScrollBar:vertical {
           background-color: #f8f9fa;
           width: 8px;
           border-radius: 4px;
       }
       
       QScrollBar::handle:vertical {
           background-color: #dee2e6;
           border-radius: 4px;
           min-height: 20px;
       }
       
       QScrollBar::handle:vertical:hover {
           background-color: #adb5bd;
       }
       
       /* Animations */
       * {
           transition: all 0.2s ease-in-out;
       }
       """
       
       self.setStyleSheet(style)
   
    def _setup_connections(self):
       """Configure les connexions de signaux."""
       # Timer pour le refresh automatique
       self.refresh_timer = QTimer()
       self.refresh_timer.timeout.connect(self._auto_refresh)
       self.refresh_timer.start(300000)  # 5 minutes
       
       # Timer pour les animations
       self.animation_timer = QTimer()
       self.animation_timer.timeout.connect(self._update_animations)
       self.animation_timer.start(50)  # 20 FPS
   
    def _load_initial_data(self):
       """Charge les données initiales."""
       self._refresh_data()
   
   # Slots et méthodes d'interaction
   
    def _on_view_changed(self, view_name: str):
       """Gère le changement de vue."""
       view_titles = {
           "inbox": "Smart Inbox",
           "calendar": "Calendrier",
           "settings": "Paramètres"
       }
       
       view_indices = {
           "inbox": 0,
           "calendar": 1,
           "settings": 2
       }
       
       if view_name in view_indices:
           self.view_title.setText(view_titles[view_name])
           self.view_stack.setCurrentIndex(view_indices[view_name])
           self.current_view = view_name
           
           # Animation de transition
           self._animate_view_transition()
           
           logger.info(f"Vue changée vers: {view_name}")
   
    def _on_search_changed(self, text: str):
       """Gère les changements dans la recherche."""
       if len(text) >= 3:  # Minimum 3 caractères
           self.inbox_view.filter_emails(text)
       elif text == "":
           self.inbox_view.clear_filter()
   
    def _on_email_selected(self, email: Email):
       """Gère la sélection d'un email."""
       # Traitement IA de l'email si pas déjà fait
       if not hasattr(email, 'ai_analysis'):
           email.ai_analysis = self.ai_processor.process_email(email)
       
       # Afficher le panel IA si pertinent
       if email.ai_analysis.should_auto_respond:
           self._show_ai_suggestion(email)
   
    def _show_ai_suggestion(self, email: Email):
       """Affiche le panel de suggestions IA."""
       if hasattr(email, 'ai_analysis'):
           self.ai_panel.show_suggestion(email, email.ai_analysis)
           self.ai_panel.show()
           self._animate_ai_panel_in()
   
    def _refresh_data(self):
       """Actualise toutes les données."""
       if self.is_loading:
           return
       
       self.is_loading = True
       self._start_refresh_animation()
       
       try:
           # Refresh des emails
           self.inbox_view.refresh_emails()
           
           # Refresh du calendrier si visible
           if self.current_view == "calendar":
               self.calendar_view.refresh_events()
           
           # Mise à jour des statistiques dans la sidebar
           self.sidebar.update_stats(self._get_current_stats())
           
       except Exception as e:
           logger.error(f"Erreur lors du refresh: {e}")
           self._show_error_message("Erreur de synchronisation", str(e))
       finally:
           self.is_loading = False
           self._stop_refresh_animation()
   
    def _auto_refresh(self):
       """Refresh automatique en arrière-plan."""
       if not self.is_loading:
           self._refresh_data()
   
   # Méthodes d'animation
   
    def _animate_view_transition(self):
       """Anime la transition entre les vues."""
       self.animation = QPropertyAnimation(self.view_stack, b"pos")
       self.animation.setDuration(300)
       self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
       self.animation.start()
   
    def _animate_ai_panel_in(self):
       """Anime l'entrée du panel IA."""
       self.ai_panel_animation = QPropertyAnimation(self.ai_panel, b"geometry")
       self.ai_panel_animation.setDuration(250)
       self.ai_panel_animation.setEasingCurve(QEasingCurve.Type.OutBack)
       self.ai_panel_animation.start()
   
    def _start_refresh_animation(self):
       """Démarre l'animation de refresh."""
       self.refresh_btn.setText("⟳")
       # Animation de rotation
       self.rotation_animation = QPropertyAnimation(self.refresh_btn, b"rotation")
       self.rotation_animation.setDuration(1000)
       self.rotation_animation.setLoopCount(-1)  # Infini
       self.rotation_animation.start()
   
    def _stop_refresh_animation(self):
       """Arrête l'animation de refresh."""
       if hasattr(self, 'rotation_animation'):
           self.rotation_animation.stop()
       self.refresh_btn.setText("🔄")
   
    def _update_animations(self):
       """Met à jour les animations en cours."""
       # Pulse de l'indicateur de notification
       if self.notification_indicator.isVisible():
           current_time = datetime.now().timestamp()
           opacity = 0.5 + 0.5 * abs(current_time % 2 - 1)
           self.notification_indicator.setStyleSheet(f"color: rgba(220, 53, 69, {opacity});")
   
   # Méthodes utilitaires
   
    def _get_current_stats(self) -> Dict:
       """Retourne les statistiques actuelles."""
       unread_count = len([e for e in self.current_emails if not e.is_read])
       total_count = len(self.current_emails)
       
       ai_stats = self.ai_processor.get_statistics()
       
       return {
           'unread_emails': unread_count,
           'total_emails': total_count,
           'ai_accuracy': ai_stats.get('accuracy', 0.0),
           'auto_responses': ai_stats.get('auto_responses_sent', 0)
       }
   
    def _show_error_message(self, title: str, message: str):
       """Affiche un message d'erreur moderne."""
       msg_box = QMessageBox(self)
       msg_box.setWindowTitle(title)
       msg_box.setText(message)
       msg_box.setIcon(QMessageBox.Icon.Warning)
       msg_box.setStyleSheet("""
           QMessageBox {
               background-color: #ffffff;
               color: #000000;
           }
           QMessageBox QPushButton {
               background-color: #000000;
               color: #ffffff;
               border: none;
               padding: 8px 16px;
               border-radius: 4px;
               min-width: 80px;
           }
           QMessageBox QPushButton:hover {
               background-color: #333333;
           }
       """)
       msg_box.exec()
   
    def show_notification(self, message: str, duration: int = 3000):
       """Affiche une notification temporaire."""
       self.notification_indicator.show()
       QTimer.singleShot(duration, self.notification_indicator.hide)
   
    def closeEvent(self, event):
       """Gère la fermeture de l'application."""
       # Sauvegarder l'état
       # Nettoyer les ressources
       logger.info("Fermeture de l'application")
       event.accept()