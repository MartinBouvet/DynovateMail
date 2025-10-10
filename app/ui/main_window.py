#!/usr/bin/env python3
"""
Interface principale - VERSION COMPLÈTE FINALE
"""
import logging
from typing import Optional
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFrame, QSplitter, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from gmail_client import GmailClient
from ai_processor import AIProcessor
from calendar_manager import CalendarManager
from auto_responder import AutoResponder
from models.email_model import Email
from ui.components.top_toolbar import TopToolbar
from ui.components.email_folders_sidebar import EmailFoldersSidebar
from ui.views.smart_inbox_view import SmartInboxView
from ui.views.calendar_view import CalendarView
from ui.views.settings_view import SettingsView
from ui.views.ai_assistant_view import AIAssistantView
from ui.compose_view import ComposeView

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Interface principale Dynovate Mail - Complète et fonctionnelle."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor,
                 calendar_manager: CalendarManager, auto_responder: AutoResponder):
        super().__init__()
        
        # Services
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.calendar_manager = calendar_manager
        self.auto_responder = auto_responder
        
        # État
        self.current_view = "inbox"
        self.compose_window = None
        
        # Configuration
        self._setup_window()
        self._setup_ui()
        self._apply_theme()
        self._setup_connections()
        self._load_initial_data()
        
        logger.info("Interface principale Dynovate Mail initialisée")
    
    def _setup_window(self):
        """Configure la fenêtre principale."""
        self.setWindowTitle("Dynovate Mail - Assistant IA")
        self.setGeometry(100, 50, 1600, 1000)
        self.setMinimumSize(1200, 700)
        
        # Centrer la fenêtre
        self._center_window()
    
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
            logger.error(f"Erreur centrage fenêtre: {e}")
    
    def _setup_ui(self):
        """Crée l'interface utilisateur complète."""
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout principal
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === BARRE D'OUTILS SUPÉRIEURE ===
        self.top_toolbar = TopToolbar()
        self.top_toolbar.view_requested.connect(self._switch_view)
        self.top_toolbar.compose_requested.connect(self._open_compose)
        self.top_toolbar.refresh_requested.connect(self._refresh_current_view)
        self.top_toolbar.search_requested.connect(self._perform_search)
        main_layout.addWidget(self.top_toolbar)
        
        # === ZONE PRINCIPALE: Sidebar + Contenu ===
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # SIDEBAR GAUCHE (Dossiers + Catégories)
        self.sidebar = EmailFoldersSidebar()
        self.sidebar.folder_changed.connect(self._on_folder_changed)
        self.sidebar.setFixedWidth(220)
        content_layout.addWidget(self.sidebar)
        
        # SÉPARATEUR VERTICAL
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #5b21b6;")
        separator.setFixedWidth(2)
        content_layout.addWidget(separator)
        
        # ZONE CONTENU PRINCIPAL (Stack de vues)
        self.content_stack = QWidget()
        self.content_layout = QVBoxLayout(self.content_stack)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Vue 1: Inbox (emails)
        self.inbox_view = SmartInboxView(
            self.gmail_client,
            self.ai_processor
        )
        self.inbox_view.email_selected.connect(self._on_email_selected)
        self.content_layout.addWidget(self.inbox_view)
        
        # Vue 2: Calendrier
        self.calendar_view = CalendarView(self.calendar_manager)
        self.calendar_view.hide()
        self.content_layout.addWidget(self.calendar_view)
        
        # Vue 3: Assistant IA
        self.ai_view = AIAssistantView(self.ai_processor, self.gmail_client)
        self.ai_view.hide()
        self.content_layout.addWidget(self.ai_view)
        
        # Vue 4: Paramètres
        self.settings_view = SettingsView()
        self.settings_view.settings_changed.connect(self._on_settings_changed)
        self.settings_view.hide()
        self.content_layout.addWidget(self.settings_view)
        
        # Ajouter le contenu au layout
        content_layout.addWidget(self.content_stack, stretch=1)
        
        main_layout.addLayout(content_layout)
        
        logger.info("Interface UI créée avec succès")
    
    def _setup_connections(self):
        """Configure les connexions de signaux."""
        # Timer pour rafraîchissement automatique (5 minutes)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(300000)  # 5 minutes = 300000 ms
        
        logger.info("Connexions configurées")
    
    def _load_initial_data(self):
        """Charge les données initiales au démarrage."""
        try:
            logger.info("Chargement des données initiales...")
            
            # Charger les emails de la boîte de réception
            self.inbox_view.refresh_emails()
            
            logger.info("Données initiales chargées avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement initial: {e}")
            QMessageBox.warning(
                self,
                "Avertissement",
                f"Impossible de charger les données initiales:\n{e}"
            )
    
    def _switch_view(self, view_name: str):
        """Change de vue."""
        logger.info(f"Changement de vue vers: {view_name}")
        
        # Cacher toutes les vues
        self.inbox_view.hide()
        self.calendar_view.hide()
        self.ai_view.hide()
        self.settings_view.hide()
        
        # Afficher la vue demandée
        if view_name == "inbox":
            self.inbox_view.show()
            self.current_view = "inbox"
            
        elif view_name == "calendar":
            self.calendar_view.show()
            self.current_view = "calendar"
            # Rafraîchir le calendrier
            try:
                self.calendar_view.refresh()
            except Exception as e:
                logger.error(f"Erreur rafraîchissement calendrier: {e}")
            
        elif view_name == "ai":
            self.ai_view.show()
            self.current_view = "ai"
            
        elif view_name == "settings":
            self.settings_view.show()
            self.current_view = "settings"
        
        logger.info(f"Vue active: {self.current_view}")
    
    def _on_folder_changed(self, folder: str):
        """Gère le changement de dossier dans la sidebar."""
        logger.info(f"Changement de dossier: {folder}")
        
        # Si on est dans la vue inbox, charger le dossier
        if self.current_view != "inbox":
            # Basculer automatiquement vers la vue inbox
            self._switch_view("inbox")
        
        # Charger le dossier sélectionné
        self.inbox_view.load_folder(folder)
    
    def _on_email_selected(self, email: Email):
        """Gère la sélection d'un email."""
        logger.debug(f"Email sélectionné: {email.subject}")
        
        # Marquer comme lu si nécessaire
        if not email.is_read:
            try:
                self.gmail_client.mark_as_read(email.id)
                email.is_read = True
                logger.info(f"Email {email.id} marqué comme lu")
            except Exception as e:
                logger.error(f"Erreur marquage email comme lu: {e}")
    
    def _open_compose(self):
        """Ouvre la fenêtre de composition d'email."""
        try:
            logger.info("Ouverture de la fenêtre de composition")
            
            # Créer la fenêtre si elle n'existe pas
            if not self.compose_window:
                self.compose_window = ComposeView(
                    parent=self,
                    gmail_client=self.gmail_client,
                    ai_processor=self.ai_processor
                )
                self.compose_window.email_sent.connect(self._on_email_sent)
            
            # Afficher la fenêtre
            self.compose_window.show()
            self.compose_window.raise_()
            self.compose_window.activateWindow()
            
            logger.info("Fenêtre de composition ouverte")
            
        except Exception as e:
            logger.error(f"Erreur ouverture fenêtre composition: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'ouvrir la fenêtre de composition:\n{e}"
            )
    
    def _on_email_sent(self):
        """Gère l'envoi réussi d'un email."""
        logger.info("Email envoyé avec succès")
        
        # Afficher un message de confirmation
        QMessageBox.information(
            self,
            "Succès",
            "Email envoyé avec succès !"
        )
        
        # Rafraîchir la vue actuelle
        self._refresh_current_view()
        
        # Fermer la fenêtre de composition
        if self.compose_window:
            self.compose_window.close()
            self.compose_window = None
    
    def _refresh_current_view(self):
        """Rafraîchit la vue actuelle."""
        logger.info(f"Rafraîchissement de la vue: {self.current_view}")
        
        try:
            if self.current_view == "inbox":
                self.inbox_view.refresh_emails()
                
            elif self.current_view == "calendar":
                self.calendar_view.refresh()
                
            elif self.current_view == "ai":
                # Pas besoin de rafraîchir l'assistant IA
                pass
                
            elif self.current_view == "settings":
                # Pas besoin de rafraîchir les paramètres
                pass
            
            logger.info("Vue rafraîchie avec succès")
            
        except Exception as e:
            logger.error(f"Erreur rafraîchissement vue: {e}")
            QMessageBox.warning(
                self,
                "Erreur",
                f"Impossible de rafraîchir la vue:\n{e}"
            )
    
    def _auto_refresh(self):
        """Rafraîchissement automatique périodique."""
        logger.info("Rafraîchissement automatique déclenché")
        
        # Rafraîchir uniquement si on est dans la vue inbox
        if self.current_view == "inbox":
            try:
                self.inbox_view.refresh_emails()
                logger.info("Rafraîchissement automatique réussi")
            except Exception as e:
                logger.error(f"Erreur rafraîchissement automatique: {e}")
    
    def _perform_search(self, query: str):
        """Effectue une recherche d'emails."""
        logger.info(f"Recherche: {query}")
        
        try:
            # Basculer vers la vue inbox si nécessaire
            if self.current_view != "inbox":
                self._switch_view("inbox")
            
            # Effectuer la recherche via Gmail
            results = self.gmail_client.search_emails(query, max_results=50)
            
            if not results:
                QMessageBox.information(
                    self,
                    "Recherche",
                    f"Aucun résultat trouvé pour: {query}"
                )
                return
            
            # Afficher les résultats dans la vue inbox
            # TODO: Implémenter l'affichage des résultats de recherche
            QMessageBox.information(
                self,
                "Recherche",
                f"{len(results)} email(s) trouvé(s) pour: {query}"
            )
            
            logger.info(f"Recherche terminée: {len(results)} résultats")
            
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la recherche:\n{e}"
            )
    
    def _on_settings_changed(self):
        """Gère les changements de paramètres."""
        logger.info("Paramètres modifiés")
        
        # Appliquer les nouveaux paramètres
        # TODO: Implémenter l'application des paramètres
        
        # Rafraîchir l'interface si nécessaire
        self._apply_theme()
    
    def _apply_theme(self):
        """Applique le thème Dynovate sans bordures visibles."""
        self.setStyleSheet("""
            /* Fenêtre principale */
            QMainWindow {
                background-color: #ffffff;
            }
            
            /* Widgets de base - SANS BORDURES */
            QWidget {
                background-color: #ffffff;
                color: #000000;
                font-family: 'SF Pro Display', 'Inter', Arial, sans-serif;
                border: none;
            }
            
            /* Labels - SANS BORDURES */
            QLabel {
                color: #000000;
                border: none;
                background-color: transparent;
            }
            
            /* Frames - SANS BORDURES VISIBLES */
            QFrame {
                background-color: #ffffff;
                border: none;
            }
            
            /* Boutons */
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #5b21b6;
            }
            
            QPushButton:pressed {
                background-color: #5b21b6;
                color: #ffffff;
            }
            
            /* Champs de texte */
            QLineEdit, QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border-color: #5b21b6;
            }
            
            /* Text Browser - SANS BORDURE */
            QTextBrowser {
                background-color: #ffffff;
                color: #000000;
                border: none;
                padding: 0px;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background: #f5f5f5;
                width: 12px;
                border-radius: 6px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background: #c4c4c4;
                border-radius: 6px;
                min-height: 30px;
                border: none;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            
            QScrollBar:horizontal {
                background: #f5f5f5;
                height: 12px;
                border-radius: 6px;
                border: none;
            }
            
            QScrollBar::handle:horizontal {
                background: #c4c4c4;
                border-radius: 6px;
                min-width: 30px;
                border: none;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #a0a0a0;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #5b21b6;
            }
            
            /* ScrollArea - SANS BORDURE */
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
        """)
        
        logger.info("Thème Dynovate appliqué sans bordures")
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application."""
        try:
            logger.info("Fermeture de l'application")
            
            # Demander confirmation
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Voulez-vous vraiment quitter Dynovate Mail?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Fermer la fenêtre de composition si ouverte
                if self.compose_window:
                    self.compose_window.close()
                
                # Arrêter le timer
                self.refresh_timer.stop()
                
                # Sauvegarder l'état si nécessaire
                # TODO: Sauvegarder l'état de l'application
                
                logger.info("Application fermée proprement")
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture: {e}")
            event.accept()
    
    def showEvent(self, event):
        """Gère l'affichage de la fenêtre."""
        super().showEvent(event)
        logger.debug("Fenêtre affichée")
    
    def hideEvent(self, event):
        """Gère le masquage de la fenêtre."""
        super().hideEvent(event)
        logger.debug("Fenêtre masquée")