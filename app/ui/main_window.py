#!/usr/bin/env python3
"""
Interface principale - VERSION OPTIMISÉE FINALE CORRIGÉE
"""
import logging
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from app.gmail_client import GmailClient
from app.ai_processor import AIProcessor
from app.calendar_manager import CalendarManager
from app.auto_responder import AutoResponder
from app.models.email_model import Email
from app.ui.components.top_toolbar import TopToolbar
from app.ui.components.email_folders_sidebar import EmailFoldersSidebar
from app.ui.views.smart_inbox_view import SmartInboxView
from app.ui.views.calendar_view import CalendarView
from app.ui.views.settings_view import SettingsView
from app.ui.views.ai_assistant_view import AIAssistantView
from app.ui.compose_view import ComposeView

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Interface principale Dynovate Mail - Optimisée."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor,
                 calendar_manager: CalendarManager, auto_responder: AutoResponder):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.calendar_manager = calendar_manager
        self.auto_responder = auto_responder
        
        self.current_view = "inbox"
        self.compose_window = None
        
        self._setup_window()
        self._setup_ui()
        self._setup_connections()
        self._load_initial_data()
        
        # Rafraîchissement auto (10 minutes)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(600000)
        
        logger.info("✅ Interface principale initialisée")
    
    def _setup_window(self):
        """Configure la fenêtre."""
        self.setWindowTitle("Dynovate Mail - Assistant IA")
        self.setGeometry(100, 50, 1600, 1000)
        self.setMinimumSize(1400, 800)
        
        # Centrer
        try:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(
                    (geo.width() - self.width()) // 2,
                    (geo.height() - self.height()) // 2
                )
        except:
            pass
    
    def _setup_ui(self):
        """Crée l'interface."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barre supérieure
        self.top_toolbar = TopToolbar()
        main_layout.addWidget(self.top_toolbar)
        
        # Zone principale
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = EmailFoldersSidebar()
        self.sidebar.setFixedWidth(250)
        content_layout.addWidget(self.sidebar)
        
        # Contenu
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Vues
        self.inbox_view = SmartInboxView(self.gmail_client, self.ai_processor)
        self.calendar_view = CalendarView(self.calendar_manager)
        self.ai_view = AIAssistantView(self.ai_processor, self.gmail_client)
        self.settings_view = SettingsView()
        
        self.content_layout.addWidget(self.inbox_view)
        self.inbox_view.show()
        
        content_layout.addWidget(self.content_container, 1)
        main_layout.addLayout(content_layout)
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
        """)
    
    def _setup_connections(self):
        """Connexions."""
        # Top toolbar
        self.top_toolbar.view_requested.connect(self._switch_view)
        self.top_toolbar.compose_requested.connect(self._open_compose)
        self.top_toolbar.refresh_requested.connect(self._refresh_current_view)
        self.top_toolbar.search_requested.connect(self._perform_search)
        
        # Sidebar
        self.sidebar.folder_changed.connect(self._on_folder_changed)
        
        # Inbox view
        self.inbox_view.email_selected.connect(self._on_email_selected)
        self.inbox_view.email_detail_view.reply_requested.connect(self._open_reply)
        self.inbox_view.email_detail_view.forward_requested.connect(self._open_forward)
        
        # Settings
        self.settings_view.settings_changed.connect(self._on_settings_changed)
        
        # ✨ Assistant IA - Navigation vers emails
        self.ai_view.email_selected.connect(self._on_ai_email_selected)
    
    def _load_initial_data(self):
        """Charge les données."""
        try:
            self.inbox_view.load_folder("INBOX")
            self._update_sidebar_counts()
            logger.info("Données initiales chargées")
        except Exception as e:
            logger.error(f"Erreur chargement: {e}")
    
    def _switch_view(self, view_name: str):
        """Change de vue."""
        logger.info(f"Vue: {view_name}")
        
        # Cacher toutes les vues
        self.inbox_view.hide()
        self.calendar_view.hide()
        self.ai_view.hide()
        self.settings_view.hide()
        
        # Retirer du layout
        while self.content_layout.count():
            self.content_layout.takeAt(0)
        
        # Afficher la vue
        if view_name == "inbox":
            self.content_layout.addWidget(self.inbox_view)
            self.inbox_view.show()
            self.current_view = "inbox"
        
        elif view_name == "calendar":
            self.content_layout.addWidget(self.calendar_view)
            self.calendar_view.show()
            if hasattr(self.calendar_view, 'refresh'):
                self.calendar_view.refresh()
            self.current_view = "calendar"
        
        elif view_name == "ai":
            self.content_layout.addWidget(self.ai_view)
            self.ai_view.show()
            self.current_view = "ai"
        
        elif view_name == "settings":
            self.content_layout.addWidget(self.settings_view)
            self.settings_view.show()
            self.current_view = "settings"
    
    def _on_folder_changed(self, folder_id: str):
        """Changement de dossier."""
        logger.info(f"Dossier: {folder_id}")
        
        if folder_id == "SETTINGS":
            self._switch_view("settings")
        elif folder_id == "SUPPORT":
            QMessageBox.information(
                self, "Support",
                "Support Dynovate Mail\n\n"
                "📧 Email: support@dynovate.com\n"
                "🌐 Site: https://dynovate.com"
            )
        else:
            if self.current_view != "inbox":
                self._switch_view("inbox")
            self.inbox_view.load_folder(folder_id)
    
    def _on_email_selected(self, email: Email):
        """Email sélectionné."""
        logger.info(f"Email: {email.subject[:30]}")
    
    def _on_ai_email_selected(self, email: Email):
        """Email sélectionné depuis l'assistant IA."""
        logger.info(f"📧 Ouverture email depuis IA: {email.subject[:30]}")
        
        # Basculer vers inbox
        self._switch_view("inbox")
        
        # Récupérer l'email complet si nécessaire
        if not email.body:
            try:
                full_email = self.gmail_client.get_email(email.id)
                if full_email:
                    email = full_email
            except Exception as e:
                logger.error(f"Erreur récupération email: {e}")
        
        # Afficher l'email dans la vue détail
        self.inbox_view.email_detail_view.show_email(email)
    
    def _open_compose(self):
        """Ouvre composition."""
        logger.info("Composition")
        
        self.compose_window = ComposeView(
            parent=self,
            gmail_client=self.gmail_client,
            ai_processor=self.ai_processor
        )
        self.compose_window.email_sent.connect(self._on_email_sent)
        self.compose_window.exec()
    
    def _open_reply(self, email: Email):
        """Ouvre réponse."""
        logger.info(f"Réponse: {email.sender}")
        
        self.compose_window = ComposeView(
            parent=self,
            gmail_client=self.gmail_client,
            ai_processor=self.ai_processor,
            reply_to=email
        )
        self.compose_window.email_sent.connect(self._on_email_sent)
        self.compose_window.exec()
    
    def _open_forward(self, email: Email):
        """Ouvre transfert."""
        logger.info(f"Transfert: {email.subject}")
        
        self.compose_window = ComposeView(
            parent=self,
            gmail_client=self.gmail_client,
            ai_processor=self.ai_processor
        )
        
        self.compose_window.subject_input.setText(f"Fwd: {email.subject}")
        body = f"\n\n---\nMessage transféré:\n{email.body or email.snippet or ''}"
        self.compose_window.body_input.setPlainText(body)
        
        self.compose_window.email_sent.connect(self._on_email_sent)
        self.compose_window.exec()
    
    def _on_email_sent(self):
        """Email envoyé."""
        logger.info("Email envoyé")
        self._refresh_current_view()
        if self.compose_window:
            self.compose_window.close()
            self.compose_window = None
    
    def _refresh_current_view(self):
        """Rafraîchit la vue."""
        logger.info(f"Rafraîchissement: {self.current_view}")
        
        try:
            if self.current_view == "inbox":
                self.inbox_view.refresh_emails()
                self._update_sidebar_counts()
            elif self.current_view == "calendar" and hasattr(self.calendar_view, 'refresh'):
                self.calendar_view.refresh()
            elif self.current_view == "ai" and hasattr(self.ai_view, '_load_statistics'):
                self.ai_view._load_statistics()
        except Exception as e:
            logger.error(f"Erreur rafraîchissement: {e}")
    
    def _auto_refresh(self):
        """Rafraîchissement auto."""
        if self.current_view == "inbox":
            try:
                self.inbox_view.refresh_emails()
                self._update_sidebar_counts()
            except:
                pass
    
    def _perform_search(self, query: str):
        """Recherche."""
        logger.info(f"Recherche: {query}")
        
        try:
            if self.current_view != "inbox":
                self._switch_view("inbox")
            
            results = self.gmail_client.search_emails(query)
            self.inbox_view.emails = results
            self.inbox_view._display_emails_instant()
            
            logger.info(f"{len(results)} résultats")
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
    
    def _update_sidebar_counts(self):
        """Met à jour les compteurs."""
        try:
            count = len(self.gmail_client.list_emails(folder="INBOX", max_results=10))
            self.sidebar.update_folder_count("INBOX", count)
        except:
            pass
    
    def _on_settings_changed(self, settings: dict):
        """Paramètres modifiés."""
        logger.info("Paramètres modifiés")
    
    def closeEvent(self, event):
        """Fermeture."""
        reply = QMessageBox.question(
            self, "Confirmation",
            "Fermer Dynovate Mail ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.refresh_timer.stop()
            if hasattr(self.inbox_view, 'analysis_worker') and self.inbox_view.analysis_worker:
                if self.inbox_view.analysis_worker.isRunning():
                    self.inbox_view.analysis_worker.stop()
                    self.inbox_view.analysis_worker.wait()
            event.accept()
        else:
            event.ignore()