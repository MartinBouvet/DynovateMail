#!/usr/bin/env python3
"""
Interface principale ultra-moderne corrigée.
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
    
    def _create_main_area(self) -> QWidget:
        """Crée la zone principale avec les vues."""
        container = QWidget()
        container.setObjectName("main-area")
        
        layout = QVBoxLayout(container)
        layout.setSpacing(0)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header avec recherche
        header = self._create_header()
        layout.addWidget(header)
        
        # Stack des vues principales
        self.view_stack = QStackedWidget()
        
        # Vue Inbox intelligente
        self.inbox_view = SmartInboxView(self.gmail_client, self.ai_processor)
        self.inbox_view.email_selected.connect(self._on_email_selected)
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
        """Crée le header moderne avec recherche."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 20)
        
        # Titre de la vue actuelle
        self.view_title = QLabel("Smart Inbox")
        self.view_title.setObjectName("view-title")
        self.view_title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(self.view_title)
        
        layout.addStretch()
        
        # Barre de recherche
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
        
        # Bouton refresh
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setObjectName("refresh-btn")
        self.refresh_btn.setFixedSize(40, 40)
        self.refresh_btn.clicked.connect(self._refresh_data)
        layout.addWidget(self.refresh_btn)
        
        return header
    
    def _setup_theme(self):
        """Configure le thème noir et blanc moderne."""
        style = """
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        
        #main-area {
            background-color: #ffffff;
            border-left: 1px solid #e5e5e5;
        }
        
        #header {
            background-color: #ffffff;
            border-bottom: 1px solid #f0f0f0;
        }
        
        #view-title {
            color: #000000;
            font-weight: 700;
        }
        
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
        """
        
        self.setStyleSheet(style)
    
    def _setup_connections(self):
        """Configure les connexions de signaux."""
        # Timer pour le refresh automatique
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(300000)  # 5 minutes
    
    def _load_initial_data(self):
        """Charge les données initiales."""
        # Le chargement se fait automatiquement via refresh_emails
        QTimer.singleShot(1000, self.inbox_view.refresh_emails)
    
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
            self.view_title.setText(view_titles[view_name])
            self.view_stack.setCurrentIndex(view_indices[view_name])
            self.current_view = view_name
            
            logger.info(f"Vue changée vers: {view_name}")
    
    def _on_search_changed(self, text: str):
        """Gère les changements dans la recherche."""
        if self.current_view == "inbox":
            if len(text) >= 3:
                self.inbox_view.filter_emails(text)
            elif text == "":
                self.inbox_view.clear_filter()
    
    def _on_email_selected(self, email: Email):
        """Gère la sélection d'un email."""
        # Mettre à jour les statistiques
        self.current_emails = self.inbox_view.all_emails
        self._update_sidebar_stats()
        
        logger.info(f"Email sélectionné: {email.subject}")
    
    def _refresh_data(self):
        """Actualise toutes les données."""
        if self.is_loading:
            return
        
        self.is_loading = True
        self._start_refresh_animation()
        
        try:
            # Refresh des emails
            if self.current_view == "inbox":
                self.inbox_view.refresh_emails()
            
            # Refresh du calendrier si visible
            elif self.current_view == "calendar":
                self.calendar_view.refresh_events()
            
            # Mise à jour des statistiques
            self._update_sidebar_stats()
            
        except Exception as e:
            logger.error(f"Erreur lors du refresh: {e}")
            self._show_error_message("Erreur de synchronisation", str(e))
        finally:
            QTimer.singleShot(2000, self._stop_refresh_animation)
    
    def _auto_refresh(self):
        """Refresh automatique en arrière-plan."""
        if not self.is_loading and self.current_view == "inbox":
            self.inbox_view.refresh_emails()
    
    def _start_refresh_animation(self):
        """Démarre l'animation de refresh."""
        self.refresh_btn.setText("⟳")
        self.is_loading = True
    
    def _stop_refresh_animation(self):
        """Arrête l'animation de refresh."""
        self.refresh_btn.setText("🔄")
        self.is_loading = False
    
    def _update_sidebar_stats(self):
        """Met à jour les statistiques dans la sidebar."""
        try:
            if hasattr(self.inbox_view, 'all_emails'):
                emails = self.inbox_view.all_emails
                unread_count = len([e for e in emails if not e.is_read])
                
                # Calculer la précision IA (simplifiée)
                analyzed_emails = [e for e in emails if hasattr(e, 'ai_analysis') and e.ai_analysis]
                ai_accuracy = len(analyzed_emails) / len(emails) if emails else 0
                
                # Compter les réponses automatiques (placeholder)
                auto_responses = 0
                
                stats = {
                    'unread_emails': unread_count,
                    'ai_accuracy': ai_accuracy,
                    'auto_responses': auto_responses
                }
                
                self.sidebar.update_stats(stats)
        except Exception as e:
            logger.error(f"Erreur mise à jour stats: {e}")
    
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
        # Simple notification dans la status bar pour l'instant
        self.statusBar().showMessage(message, duration)
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application."""
        # Arrêter les threads en cours
        if hasattr(self.inbox_view, 'email_loader') and self.inbox_view.email_loader.isRunning():
            self.inbox_view.email_loader.stop()
            self.inbox_view.email_loader.wait(3000)  # Attendre max 3 secondes
        
        logger.info("Fermeture de l'application")
        event.accept()