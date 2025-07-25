#!/usr/bin/env python3
"""
Interface principale ultra-moderne corrigée - VERSION COMPLÈTE.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from PyQt6.QtWidgets import (
   QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
   QStackedWidget, QLabel, QPushButton, QLineEdit,
   QScrollArea, QFrame, QSplitter, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from gmail_client import GmailClient
from ai_processor import AIProcessor
from calendar_manager import CalendarManager
from auto_responder import AutoResponder
from models.email_model import Email
from ui.components.modern_sidebar import ModernSidebar
from ui.views.smart_inbox_view import SmartInboxView
from ui.views.calendar_view import CalendarView
from ui.views.settings_view import SettingsView

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
   """Interface principale avec design ultra-moderne corrigé."""
   
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
       self.setMinimumSize(1400, 900)
       
       # Icône de l'application
       self.setWindowIcon(QIcon())  # Vous pouvez ajouter une icône ici
       
       # Configuration de la fenêtre
       self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
   
   def _setup_ui(self):
       """Configure l'interface utilisateur moderne."""
       # Widget central
       central_widget = QWidget()
       self.setCentralWidget(central_widget)
       
       # Layout principal horizontal
       main_layout = QHBoxLayout(central_widget)
       main_layout.setSpacing(0)
       main_layout.setContentsMargins(0, 0, 0, 0)
       
       # Sidebar moderne
       self.sidebar = ModernSidebar()
       self.sidebar.view_changed.connect(self._on_view_changed)
       main_layout.addWidget(self.sidebar)
       
       # Zone principale
       self.main_area = self._create_main_area()
       main_layout.addWidget(self.main_area)
       
       # Proportions : sidebar fixe, main area flexible
       main_layout.setStretchFactor(self.sidebar, 0)
       main_layout.setStretchFactor(self.main_area, 1)
   
   def _create_main_area(self) -> QWidget:
       """Crée la zone principale avec les vues."""
       container = QWidget()
       container.setObjectName("main-area")
       
       layout = QVBoxLayout(container)
       layout.setSpacing(0)
       layout.setContentsMargins(0, 0, 0, 0)
       
       # Header avec recherche
       header = self._create_header()
       layout.addWidget(header)
       
       # Stack des vues principales
       self.view_stack = QStackedWidget()
       self.view_stack.setObjectName("view-stack")
       
       # Vue Inbox intelligente
       try:
           self.inbox_view = SmartInboxView(self.gmail_client, self.ai_processor)
           self.inbox_view.email_selected.connect(self._on_email_selected)
           self.view_stack.addWidget(self.inbox_view)
       except Exception as e:
           logger.error(f"Erreur création inbox view: {e}")
           # Vue de fallback
           fallback_inbox = QLabel("Erreur de chargement de la boîte mail")
           fallback_inbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
           self.view_stack.addWidget(fallback_inbox)
       
       # Vue Calendrier
       try:
           self.calendar_view = CalendarView(self.calendar_manager)
           self.view_stack.addWidget(self.calendar_view)
       except Exception as e:
           logger.error(f"Erreur création calendar view: {e}")
           # Vue de fallback
           fallback_calendar = QLabel("Erreur de chargement du calendrier")
           fallback_calendar.setAlignment(Qt.AlignmentFlag.AlignCenter)
           self.view_stack.addWidget(fallback_calendar)
       
       # Vue Paramètres
       try:
           self.settings_view = SettingsView()
           self.view_stack.addWidget(self.settings_view)
       except Exception as e:
           logger.error(f"Erreur création settings view: {e}")
           # Vue de fallback
           fallback_settings = QLabel("Erreur de chargement des paramètres")
           fallback_settings.setAlignment(Qt.AlignmentFlag.AlignCenter)
           self.view_stack.addWidget(fallback_settings)
       
       layout.addWidget(self.view_stack)
       
       return container
   
   def _create_header(self) -> QWidget:
       """Crée le header moderne avec recherche."""
       header = QFrame()
       header.setObjectName("header")
       header.setFixedHeight(100)
       
       layout = QHBoxLayout(header)
       layout.setContentsMargins(30, 20, 30, 20)
       layout.setSpacing(25)
       
       # Titre de la vue actuelle
       self.view_title = QLabel("Smart Inbox")
       self.view_title.setObjectName("view-title")
       self.view_title.setFont(QFont("Inter", 32, QFont.Weight.Bold))
       layout.addWidget(self.view_title)
       
       # Spacer flexible
       layout.addStretch()
       
       # Barre de recherche
       search_container = self._create_search_container()
       layout.addWidget(search_container)
       
       # Bouton refresh
       self.refresh_btn = self._create_refresh_button()
       layout.addWidget(self.refresh_btn)
       
       return header
   
   def _create_search_container(self) -> QWidget:
       """Crée le conteneur de recherche."""
       search_container = QFrame()
       search_container.setObjectName("search-container")
       search_container.setFixedSize(500, 50)
       
       search_layout = QHBoxLayout(search_container)
       search_layout.setContentsMargins(20, 0, 20, 0)
       search_layout.setSpacing(10)
       
       # Icône de recherche
       search_icon = QLabel("🔍")
       search_icon.setFont(QFont("Arial", 16))
       search_icon.setStyleSheet("color: #6c757d;")
       search_layout.addWidget(search_icon)
       
       # Champ de recherche
       self.search_input = QLineEdit()
       self.search_input.setObjectName("search-input")
       self.search_input.setPlaceholderText("Rechercher dans vos emails...")
       self.search_input.setFont(QFont("Inter", 15))
       self.search_input.textChanged.connect(self._on_search_changed)
       search_layout.addWidget(self.search_input)
       
       # Bouton effacer (optionnel)
       clear_btn = QPushButton("✕")
       clear_btn.setObjectName("clear-search-btn")
       clear_btn.setFixedSize(25, 25)
       clear_btn.setFont(QFont("Arial", 12))
       clear_btn.clicked.connect(lambda: self.search_input.clear())
       clear_btn.hide()  # Caché par défaut
       
       # Afficher/cacher le bouton selon le contenu
       self.search_input.textChanged.connect(
           lambda text: clear_btn.show() if text else clear_btn.hide()
       )
       
       search_layout.addWidget(clear_btn)
       
       return search_container
   
   def _create_refresh_button(self) -> QPushButton:
       """Crée le bouton de refresh."""
       refresh_btn = QPushButton("🔄")
       refresh_btn.setObjectName("refresh-btn")
       refresh_btn.setFixedSize(50, 50)
       refresh_btn.setFont(QFont("Arial", 20))
       refresh_btn.setToolTip("Actualiser les données")
       refresh_btn.clicked.connect(self._refresh_data)
       
       return refresh_btn
   
   def _setup_theme(self):
       """Configure le thème noir et blanc moderne."""
       style = """
       /* === STYLES PRINCIPAUX === */
       QMainWindow {
           background-color: #ffffff;
           color: #000000;
       }
       
       #main-area {
           background-color: #ffffff;
           border-left: 2px solid #e9ecef;
       }
       
       /* === HEADER === */
       #header {
           background-color: #ffffff;
           border-bottom: 2px solid #f0f0f0;
       }
       
       #view-title {
           color: #000000;
           font-weight: 700;
           margin: 0;
           padding: 0;
           letter-spacing: -0.5px;
       }
       
       /* === RECHERCHE === */
       #search-container {
           background-color: #f8f9fa;
           border: 2px solid #e9ecef;
           border-radius: 25px;
       }
       
       #search-container:focus-within {
           border-color: #007bff;
           background-color: #ffffff;
       }
       
       #search-input {
           background: transparent;
           border: none;
           color: #000000;
           font-size: 15px;
           font-weight: 400;
           padding: 10px 0;
           outline: none;
       }
       
       #search-input::placeholder {
           color: #6c757d;
           font-style: italic;
       }
       
       #clear-search-btn {
           background-color: #e9ecef;
           border: none;
           border-radius: 12px;
           color: #6c757d;
           font-size: 12px;
           font-weight: bold;
       }
       
       #clear-search-btn:hover {
           background-color: #dc3545;
           color: #ffffff;
       }
       
       /* === BOUTON REFRESH === */
       #refresh-btn {
           background-color: #f8f9fa;
           border: 2px solid #e9ecef;
           border-radius: 25px;
           color: #6c757d;
           font-size: 20px;
       }
       
       #refresh-btn:hover {
           background-color: #e9ecef;
           color: #000000;
           border-color: #adb5bd;
           transform: scale(1.05);
       }
       
       #refresh-btn:pressed {
           background-color: #dee2e6;
           transform: scale(0.95);
       }
       
       /* === STACK DE VUES === */
       #view-stack {
           background-color: #ffffff;
       }
       
       /* === SCROLLBARS GLOBALES === */
       QScrollArea {
           border: none;
           background-color: transparent;
       }
       
       QScrollBar:vertical {
           background-color: #f8f9fa;
           width: 12px;
           border-radius: 6px;
           margin: 2px;
       }
       
       QScrollBar::handle:vertical {
           background-color: #dee2e6;
           border-radius: 6px;
           min-height: 30px;
           margin: 2px;
       }
       
       QScrollBar::handle:vertical:hover {
           background-color: #adb5bd;
       }
       
       QScrollBar::handle:vertical:pressed {
           background-color: #6c757d;
       }
       
       QScrollBar::add-line:vertical,
       QScrollBar::sub-line:vertical {
           height: 0px;
       }
       
       QScrollBar:horizontal {
           background-color: #f8f9fa;
           height: 12px;
           border-radius: 6px;
           margin: 2px;
       }
       
       QScrollBar::handle:horizontal {
           background-color: #dee2e6;
           border-radius: 6px;
           min-width: 30px;
           margin: 2px;
       }
       
       QScrollBar::handle:horizontal:hover {
           background-color: #adb5bd;
       }
       
       /* === MESSAGEBOX === */
       QMessageBox {
           background-color: #ffffff;
           color: #000000;
           border: 1px solid #dee2e6;
           border-radius: 8px;
       }
       
       QMessageBox QPushButton {
           background-color: #007bff;
           color: #ffffff;
           border: none;
           padding: 8px 16px;
           border-radius: 6px;
           font-weight: 500;
           min-width: 80px;
       }
       
       QMessageBox QPushButton:hover {
           background-color: #0056b3;
       }
       
       QMessageBox QPushButton:pressed {
           background-color: #004085;
       }
       
       /* === SPLITTER === */
       QSplitter::handle {
           background-color: #e9ecef;
           width: 2px;
           height: 2px;
       }
       
       QSplitter::handle:hover {
           background-color: #adb5bd;
       }
       
       /* === LABELS GÉNÉRAUX === */
       QLabel {
           color: #000000;
       }
       
       /* === TRANSITIONS ET ANIMATIONS === */
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
       
       # Raccourcis clavier
       self._setup_shortcuts()
   
   def _setup_shortcuts(self):
       """Configure les raccourcis clavier."""
       from PyQt6.QtGui import QShortcut, QKeySequence
       
       # Ctrl+R pour refresh
       refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
       refresh_shortcut.activated.connect(self._refresh_data)
       
       # Ctrl+F pour focus sur la recherche
       search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
       search_shortcut.activated.connect(lambda: self.search_input.setFocus())
       
       # Échap pour vider la recherche
       escape_shortcut = QShortcut(QKeySequence("Escape"), self)
       escape_shortcut.activated.connect(lambda: self.search_input.clear())
       
       # Ctrl+1, Ctrl+2, Ctrl+3 pour changer de vue
       inbox_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
       inbox_shortcut.activated.connect(lambda: self._on_view_changed("inbox"))
       
       calendar_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
       calendar_shortcut.activated.connect(lambda: self._on_view_changed("calendar"))
       
       settings_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
       settings_shortcut.activated.connect(lambda: self._on_view_changed("settings"))
   
   def _load_initial_data(self):
       """Charge les données initiales."""
       # Déclencher le chargement des emails après un court délai
       QTimer.singleShot(1500, self._initial_load)
   
   def _initial_load(self):
       """Charge les données initiales de manière asynchrone."""
       try:
           if hasattr(self, 'inbox_view') and hasattr(self.inbox_view, 'refresh_emails'):
               self.inbox_view.refresh_emails()
           else:
               logger.warning("Inbox view non disponible pour le chargement initial")
       except Exception as e:
           logger.error(f"Erreur lors du chargement initial: {e}")
   
   def _on_view_changed(self, view_name: str):
       """Gère le changement de vue."""
       view_titles = {
           "inbox": "Smart Inbox",
           "calendar": "Calendrier Intelligent",
           "settings": "Paramètres"
       }
       
       view_indices = {
           "inbox": 0,
           "calendar": 1,
           "settings": 2
       }
       
       if view_name in view_indices:
           # Mettre à jour le titre avec animation
           new_title = view_titles[view_name]
           self._animate_title_change(new_title)
           
           # Changer la vue
           self.view_stack.setCurrentIndex(view_indices[view_name])
           self.current_view = view_name
           
           # Actions spécifiques selon la vue
           if view_name == "inbox" and hasattr(self, 'inbox_view'):
               # Activer la recherche pour la boîte mail
               self.search_input.setEnabled(True)
               self.search_input.setPlaceholderText("Rechercher dans vos emails...")
           elif view_name == "calendar":
               # Désactiver la recherche pour le calendrier
               self.search_input.setEnabled(False)
               self.search_input.setPlaceholderText("Recherche non disponible")
               self.search_input.clear()
           elif view_name == "settings":
               # Désactiver la recherche pour les paramètres
               self.search_input.setEnabled(False)
               self.search_input.setPlaceholderText("Recherche non disponible")
               self.search_input.clear()
           
           logger.info(f"Vue changée vers: {view_name}")
   
   def _animate_title_change(self, new_title: str):
       """Anime le changement de titre."""
       # Simple changement pour l'instant, on peut ajouter une vraie animation plus tard
       self.view_title.setText(new_title)
   
   def _on_search_changed(self, text: str):
       """Gère les changements dans la recherche."""
       if self.current_view == "inbox" and hasattr(self, 'inbox_view'):
           try:
               if len(text) >= 3:
                   self.inbox_view.filter_emails(text)
               elif text == "":
                   self.inbox_view.clear_filter()
           except Exception as e:
               logger.error(f"Erreur lors de la recherche: {e}")
   
   def _on_email_selected(self, email: Email):
       """Gère la sélection d'un email."""
       try:
           # Mettre à jour les statistiques
           if hasattr(self, 'inbox_view'):
               self.current_emails = self.inbox_view.all_emails
               self._update_sidebar_stats()
           
           logger.info(f"Email sélectionné: {email.subject}")
       except Exception as e:
           logger.error(f"Erreur lors de la sélection d'email: {e}")
   
   def _refresh_data(self):
       """Actualise toutes les données."""
       if self.is_loading:
           logger.info("Refresh déjà en cours, ignoré")
           return
       
       self.is_loading = True
       self._start_refresh_animation()
       
       try:
           # Refresh selon la vue actuelle
           if self.current_view == "inbox" and hasattr(self, 'inbox_view'):
               if hasattr(self.inbox_view, 'refresh_emails'):
                   self.inbox_view.refresh_emails()
               else:
                   logger.warning("Méthode refresh_emails non disponible")
           
           elif self.current_view == "calendar" and hasattr(self, 'calendar_view'):
               if hasattr(self.calendar_view, 'refresh_events'):
                   self.calendar_view.refresh_events()
               else:
                   logger.warning("Méthode refresh_events non disponible")
           
           # Mise à jour des statistiques
           self._update_sidebar_stats()
           
           logger.info(f"Refresh déclenché pour la vue: {self.current_view}")
           
       except Exception as e:
           logger.error(f"Erreur lors du refresh: {e}")
           self._show_error_message("Erreur de synchronisation", str(e))
       finally:
           # Arrêter l'animation après un délai
           QTimer.singleShot(2000, self._stop_refresh_animation)
   
   def _auto_refresh(self):
       """Refresh automatique en arrière-plan."""
       if not self.is_loading and self.current_view == "inbox":
           try:
               if hasattr(self, 'inbox_view') and hasattr(self.inbox_view, 'refresh_emails'):
                   self.inbox_view.refresh_emails()
                   logger.info("Auto-refresh effectué")
           except Exception as e:
               logger.error(f"Erreur lors de l'auto-refresh: {e}")
   
   def _start_refresh_animation(self):
       """Démarre l'animation de refresh."""
       self.refresh_btn.setText("⟳")
       self.refresh_btn.setStyleSheet("""
           #refresh-btn {
               background-color: #007bff;
               border: 2px solid #007bff;
               border-radius: 25px;
               color: #ffffff;
               font-size: 20px;
           }
       """)
       
       # Animation de rotation (simplifiée)
       self.refresh_btn.setEnabled(False)
   
   def _stop_refresh_animation(self):
       """Arrête l'animation de refresh."""
       self.refresh_btn.setText("🔄")
       self.refresh_btn.setStyleSheet("")  # Retour au style par défaut
       self.refresh_btn.setEnabled(True)
       self.is_loading = False
   
   def _update_sidebar_stats(self):
       """Met à jour les statistiques dans la sidebar."""
       try:
           if hasattr(self, 'inbox_view') and hasattr(self.inbox_view, 'all_emails'):
               emails = self.inbox_view.all_emails
               unread_count = len([e for e in emails if not e.is_read])
               
               # Calculer la précision IA
               analyzed_emails = [e for e in emails if hasattr(e, 'ai_analysis') and e.ai_analysis]
               ai_accuracy = len(analyzed_emails) / len(emails) if emails else 0
               
               # Compter les réponses automatiques (placeholder)
               auto_responses = 0
               
               stats = {
                   'unread_emails': unread_count,
                   'ai_accuracy': ai_accuracy,
                   'auto_responses': auto_responses
               }
               
               if hasattr(self.sidebar, 'update_stats'):
                   self.sidebar.update_stats(stats)
               
               logger.debug(f"Stats mises à jour: {stats}")
       except Exception as e:
           logger.error(f"Erreur mise à jour stats: {e}")
   
   def _show_error_message(self, title: str, message: str):
       """Affiche un message d'erreur moderne."""
       try:
           msg_box = QMessageBox(self)
           msg_box.setWindowTitle(title)
           msg_box.setText(message)
           msg_box.setIcon(QMessageBox.Icon.Warning)
           msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
           
           # Style déjà défini dans le CSS global
           msg_box.exec()
       except Exception as e:
           logger.error(f"Erreur lors de l'affichage du message d'erreur: {e}")
   
   def show_notification(self, message: str, duration: int = 3000):
       """Affiche une notification temporaire."""
       try:
           # Utiliser la status bar pour les notifications
           if not hasattr(self, '_status_bar'):
               self._status_bar = self.statusBar()
               self._status_bar.setStyleSheet("""
                   QStatusBar {
                       background-color: #e3f2fd;
                       color: #1976d2;
                       font-weight: 500;
                       border-top: 1px solid #bbdefb;
                       padding: 4px 8px;
                   }
               """)
           
           self._status_bar.showMessage(message, duration)
       except Exception as e:
           logger.error(f"Erreur lors de l'affichage de la notification: {e}")
   
   def resizeEvent(self, event):
       """Gère le redimensionnement de la fenêtre."""
       super().resizeEvent(event)
       
       # Ajuster les éléments selon la taille
       window_width = event.size().width()
       
       if window_width < 1200:
           # Mode compact
           if hasattr(self, 'search_input'):
               self.search_input.parent().setFixedSize(350, 50)
       else:
           # Mode normal
           if hasattr(self, 'search_input'):
               self.search_input.parent().setFixedSize(500, 50)
   
   def closeEvent(self, event):
       """Gère la fermeture de l'application."""
       try:
           logger.info("Fermeture de l'application en cours...")
           
           # Arrêter les threads en cours
           if hasattr(self, 'inbox_view') and hasattr(self.inbox_view, 'email_loader'):
               if self.inbox_view.email_loader.isRunning():
                   self.inbox_view.email_loader.stop()
                   self.inbox_view.email_loader.wait(3000)  # Attendre max 3 secondes
           
           # Arrêter les timers
           if hasattr(self, 'refresh_timer'):
               self.refresh_timer.stop()
           
           # Sauvegarder l'état si nécessaire
           self._save_window_state()
           
           logger.info("Fermeture de l'application terminée")
           event.accept()
           
       except Exception as e:
           logger.error(f"Erreur lors de la fermeture: {e}")
           event.accept()  # Forcer la fermeture même en cas d'erreur
   
   def _save_window_state(self):
       """Sauvegarde l'état de la fenêtre."""
       try:
           # Ici on pourrait sauvegarder la géométrie, la vue actuelle, etc.
           # Pour l'instant, juste un log
           logger.info(f"État sauvegardé - Vue actuelle: {self.current_view}")
       except Exception as e:
           logger.error(f"Erreur lors de la sauvegarde de l'état: {e}")
   
   def showEvent(self, event):
       """Gère l'affichage de la fenêtre."""
       super().showEvent(event)
       
       # Centrer la fenêtre au premier affichage
       if not hasattr(self, '_window_centered'):
           self._center_window()
           self._window_centered = True
   
   def _center_window(self):
       """Centre la fenêtre sur l'écran."""
       try:
           screen = QApplication.primaryScreen()
           if screen:
               screen_geometry = screen.availableGeometry()
               window_geometry = self.frameGeometry()
               center_point = screen_geometry.center()
               window_geometry.moveCenter(center_point)
               self.move(window_geometry.topLeft())
       except Exception as e:
           logger.error(f"Erreur lors du centrage: {e}")