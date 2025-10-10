#!/usr/bin/env python3
"""
Vue Smart Inbox - SANS BARRE DE CATÉGORIES EN HAUT
"""
import logging
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLabel, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from gmail_client import GmailClient
from ai_processor import AIProcessor
from models.email_model import Email
from ui.components.smart_email_card import SmartEmailCard
from ui.views.email_detail_view import EmailDetailView

logger = logging.getLogger(__name__)

class EmailLoaderThread(QThread):
    """Thread pour charger et analyser les emails."""
    
    emails_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor, folder: str):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.folder = folder
        self.should_stop = False
    
    def run(self):
        """Charge et analyse les emails."""
        try:
            logger.info(f"Chargement emails du dossier: {self.folder}")
            
            # Chargement selon le dossier
            if self.folder == "INBOX":
                emails = self.gmail_client.get_inbox_emails(max_results=50)
            elif self.folder == "SENT":
                emails = self.gmail_client.get_sent_emails(max_results=50)
            elif self.folder == "DRAFTS":
                emails = self.gmail_client.get_draft_emails(max_results=50)
            elif self.folder == "ARCHIVED":
                emails = self.gmail_client.get_archived_emails(max_results=50)
            elif self.folder == "TRASH":
                emails = self.gmail_client.get_trash_emails(max_results=50)
            elif self.folder == "SPAM":
                emails = self.gmail_client.get_spam_emails(max_results=50)
            elif self.folder.startswith("CATEGORY:"):
                # Charger inbox et filtrer par catégorie
                emails = self.gmail_client.get_inbox_emails(max_results=100)
                category = self.folder.replace("CATEGORY:", "")
                # Filtrer sera fait après l'analyse
            else:
                emails = self.gmail_client.get_inbox_emails(max_results=50)
            
            if self.should_stop:
                return
            
            # Analyse IA
            analyzed_emails = []
            for email in emails:
                if self.should_stop:
                    break
                
                if not hasattr(email, 'ai_analysis') or not email.ai_analysis:
                    email.ai_analysis = self.ai_processor.analyze_email(email)
                
                analyzed_emails.append(email)
            
            logger.info(f"{len(analyzed_emails)} emails analysés")
            self.emails_loaded.emit(analyzed_emails)
            
        except Exception as e:
            logger.error(f"Erreur chargement emails: {e}")
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """Arrête le thread."""
        self.should_stop = True

class SmartInboxView(QWidget):
    """Vue inbox intelligente."""
    
    email_selected = pyqtSignal(Email)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        
        self.all_emails = []
        self.filtered_emails = []
        self.selected_email = None
        self.current_folder = "INBOX"
        self.current_category = "Tous"
        self.loader_thread = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée l'interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Splitter pour liste et détail
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background-color: #5b21b6; }")
        
        # === PANNEAU LISTE EMAILS ===
        list_panel = self._create_list_panel()
        splitter.addWidget(list_panel)
        
        # === PANNEAU DÉTAIL EMAIL ===
        self.detail_view = EmailDetailView(self.gmail_client, self.ai_processor)
        splitter.addWidget(self.detail_view)
        
        # Proportions
        splitter.setStretchFactor(0, 1)  # Liste
        splitter.setStretchFactor(1, 2)  # Détail
        
        layout.addWidget(splitter)
    
    def _create_list_panel(self) -> QWidget:
        """Crée le panneau liste d'emails."""
        panel = QWidget()
        panel.setMinimumWidth(400)
        panel.setStyleSheet("background-color: #ffffff;")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header avec compteur (SANS LA BARRE DE CATÉGORIES)
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #f5f5f5; border-bottom: 2px solid #5b21b6;")
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.count_label = QLabel("0 emails")
        self.count_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.count_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(self.count_label)
        
        layout.addWidget(header)
        
        # Liste scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #ffffff;
                border: none;
            }
        """)
        
        self.emails_container = QWidget()
        self.emails_container.setStyleSheet("background-color: #ffffff;")
        self.emails_layout = QVBoxLayout(self.emails_container)
        self.emails_layout.setSpacing(0)
        self.emails_layout.setContentsMargins(0, 0, 0, 0)
        self.emails_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Message vide par défaut
        self.empty_label = QLabel("📭 Aucun email")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(QFont("Segoe UI", 16))
        self.empty_label.setStyleSheet("color: #999999; padding: 60px;")
        self.emails_layout.addWidget(self.empty_label)
        
        scroll.setWidget(self.emails_container)
        layout.addWidget(scroll)
        
        return panel
    
    def load_folder(self, folder: str):
        """Charge un dossier."""
        logger.info(f"Chargement dossier: {folder}")
        
        # Extraire la catégorie si c'est un filtre catégorie
        if folder.startswith("CATEGORY:"):
            self.current_folder = folder
            category = folder.replace("CATEGORY:", "")
            self.current_category = category
        else:
            self.current_folder = folder
            self.current_category = "Tous"
        
        self.refresh_emails()
    
    def refresh_emails(self):
        """Rafraîchit les emails."""
        logger.info("Rafraîchissement emails...")
        
        # Arrêter le thread précédent
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.stop()
            self.loader_thread.wait()
        
        # Effacer la liste
        self._clear_email_list()
        
        # Loading
        loading = QLabel("⏳ Chargement en cours...")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading.setFont(QFont("Segoe UI", 15))
        loading.setStyleSheet("color: #5b21b6; padding: 60px;")
        self.emails_layout.addWidget(loading)
        
        # Lancer le chargement
        self.loader_thread = EmailLoaderThread(
            self.gmail_client,
            self.ai_processor,
            self.current_folder
        )
        self.loader_thread.emails_loaded.connect(self._on_emails_loaded)
        self.loader_thread.error_occurred.connect(self._on_error)
        self.loader_thread.start()
    
    def _on_emails_loaded(self, emails: List[Email]):
        """Emails chargés."""
        logger.info(f"{len(emails)} emails chargés")
        self.all_emails = emails
        self._filter_and_display()
    
    def _on_error(self, error: str):
        """Erreur de chargement."""
        logger.error(f"Erreur: {error}")
        self._clear_email_list()
        
        error_label = QLabel(f"❌ Erreur: {error}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setFont(QFont("Segoe UI", 14))
        error_label.setStyleSheet("color: #d13438; padding: 60px;")
        error_label.setWordWrap(True)
        self.emails_layout.addWidget(error_label)
    
    def _filter_and_display(self):
        """Filtre et affiche les emails."""
        # Filtrer par catégorie si nécessaire
        if self.current_folder.startswith("CATEGORY:"):
            category = self.current_folder.replace("CATEGORY:", "")
            self.filtered_emails = [
                email for email in self.all_emails
                if hasattr(email, 'ai_analysis') and 
                   email.ai_analysis and
                   email.ai_analysis.category == category
            ]
        else:
            self.filtered_emails = self.all_emails.copy()
        
        # Trier par date (plus récent d'abord)
        self.filtered_emails.sort(
            key=lambda e: e.received_date if e.received_date else datetime.min,
            reverse=True
        )
        
        # Afficher
        self._display_emails(self.filtered_emails)
        
        # Mettre à jour le compteur
        self.count_label.setText(f"{len(self.filtered_emails)} email(s)")
    
    def _display_emails(self, emails: List[Email]):
        """Affiche la liste d'emails."""
        self._clear_email_list()
        
        if not emails:
            self.empty_label = QLabel("📭 Aucun email dans cette catégorie")
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.empty_label.setFont(QFont("Segoe UI", 16))
            self.empty_label.setStyleSheet("color: #999999; padding: 60px;")
            self.emails_layout.addWidget(self.empty_label)
            return
        
        # Créer les cartes
        for email in emails:
            card = SmartEmailCard(email)
            card.clicked.connect(lambda e=email: self._on_email_clicked(e))
            self.emails_layout.addWidget(card)
        
        logger.info(f"{len(emails)} cartes emails affichées")
    
    def _on_email_clicked(self, email: Email):
        """Email cliqué."""
        logger.info(f"Email cliqué: {email.subject}")
        self.selected_email = email
        
        # Marquer comme lu
        if not email.is_read:
            try:
                self.gmail_client.mark_as_read(email.id)
                email.is_read = True
            except Exception as e:
                logger.error(f"Erreur marquage lu: {e}")
        
        # Afficher dans le détail
        self.detail_view.show_email(email)
        self.email_selected.emit(email)
    
    def _clear_email_list(self):
        """Vide la liste d'emails."""
        while self.emails_layout.count():
            item = self.emails_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()