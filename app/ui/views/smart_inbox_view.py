#!/usr/bin/env python3
"""
Vue inbox intelligente - VERSION CORRIGÉE
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from app.gmail_client import GmailClient
from app.ai_processor import AIProcessor
from app.models.email_model import Email
from app.ui.views.email_detail_view import EmailDetailView
from app.ui.components.smart_email_card import SmartEmailCard

logger = logging.getLogger(__name__)

class EmailAnalysisWorker(QThread):
    """Worker pour analyse IA en arrière-plan."""
    
    analysis_complete = pyqtSignal(str, dict)
    
    def __init__(self, ai_processor: AIProcessor, emails: list):
        super().__init__()
        self.ai_processor = ai_processor
        self.emails = emails
        self.running = True
    
    def run(self):
        """Lance l'analyse."""
        for email in self.emails:
            if not self.running:
                break
            
            try:
                analysis = self.ai_processor.analyze_email(email)
                self.analysis_complete.emit(email.id, analysis)
            except Exception as e:
                logger.error(f"Erreur analyse {email.id}: {e}")
        
        logger.info("✅ Analyse IA terminée")
    
    def stop(self):
        """Arrête l'analyse."""
        self.running = False


class SmartInboxView(QWidget):
    """Vue inbox optimisée."""
    
    email_selected = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.emails = []
        self.email_cards = {}
        self.current_folder = "INBOX"
        self.analysis_worker = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Liste emails
        list_container = QWidget()
        list_container.setFixedWidth(450)
        list_container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-right: 1px solid #e5e7eb;
            }
        """)
        
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        
        # En-tête liste
        list_header = QFrame()
        list_header.setFixedHeight(65)
        list_header.setStyleSheet("background-color: #fafafa; border-bottom: 1px solid #e5e7eb;")
        
        header_layout = QHBoxLayout(list_header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        
        self.folder_title = QLabel("📥 Réception")
        self.folder_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.folder_title.setStyleSheet("color: #000000;")
        header_layout.addWidget(self.folder_title)
        
        header_layout.addStretch()
        
        self.email_count_label = QLabel("0")
        self.email_count_label.setFont(QFont("Arial", 12))
        self.email_count_label.setStyleSheet("color: #6b7280;")
        header_layout.addWidget(self.email_count_label)
        
        list_layout.addWidget(list_header)
        
        # Scroll emails
        self.emails_scroll = QScrollArea()
        self.emails_scroll.setWidgetResizable(True)
        self.emails_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.emails_scroll.setStyleSheet("border: none; background-color: #ffffff;")
        
        self.emails_container = QWidget()
        self.emails_layout = QVBoxLayout(self.emails_container)
        self.emails_layout.setContentsMargins(0, 0, 0, 0)
        self.emails_layout.setSpacing(0)
        self.emails_layout.addStretch()
        
        self.emails_scroll.setWidget(self.emails_container)
        list_layout.addWidget(self.emails_scroll)
        
        layout.addWidget(list_container)
        
        # Vue détail
        self.email_detail_view = EmailDetailView(self.gmail_client, self.ai_processor)
        layout.addWidget(self.email_detail_view, 1)
    
    def load_folder(self, folder_id: str):
        """Charge un dossier."""
        self.current_folder = folder_id
        
        folder_names = {
            "INBOX": "📥 Réception",
            "STARRED": "⭐ Favoris",
            "SENT": "📤 Envoyés",
            "DRAFTS": "📝 Brouillons",
            "TRASH": "🗑️ Corbeille",
            "SPAM": "🚫 Spam"
        }
        self.folder_title.setText(folder_names.get(folder_id, folder_id))
        
        self.refresh_emails()
    
    def refresh_emails(self):
        """Rafraîchit les emails."""
        logger.info(f"Chargement: {self.current_folder}")
        
        try:
            # Arrêter analyse en cours
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.analysis_worker.stop()
                self.analysis_worker.wait()
            
            # Charger emails
            self.emails = self.gmail_client.list_emails(
                folder=self.current_folder,
                max_results=50
            )
            
            # Compteur
            self.email_count_label.setText(f"{len(self.emails)} emails")
            
            # Afficher IMMÉDIATEMENT
            self._display_emails_instant()
            
            # Analyse IA en arrière-plan
            self._start_background_analysis()
        
        except Exception as e:
            logger.error(f"Erreur: {e}")
            self._show_error(f"Erreur de chargement")
    
    def _display_emails_instant(self):
        """Affichage instantané."""
        # Nettoyer
        while self.emails_layout.count() > 1:
            item = self.emails_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.email_cards = {}
        
        if not self.emails:
            empty = QLabel("📭 Aucun email")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setFont(QFont("Arial", 14))
            empty.setStyleSheet("color: #9ca3af; padding: 50px;")
            self.emails_layout.insertWidget(0, empty)
        else:
            for email in self.emails:
                card = SmartEmailCard(email)
                card.clicked.connect(self._on_email_clicked)
                self.emails_layout.insertWidget(self.emails_layout.count() - 1, card)
                self.email_cards[email.id] = card
        
        logger.info(f"✅ {len(self.emails)} emails affichés")
    
    def _start_background_analysis(self):
        """Analyse IA en arrière-plan."""
        if not self.emails:
            return
        
        logger.info("🤖 Analyse IA...")
        
        self.analysis_worker = EmailAnalysisWorker(self.ai_processor, self.emails)
        self.analysis_worker.analysis_complete.connect(self._on_analysis_complete)
        self.analysis_worker.start()
    
    def _on_analysis_complete(self, email_id: str, analysis: dict):
        """Analyse terminée."""
        # Mettre à jour l'email
        for email in self.emails:
            if email.id == email_id:
                email.ai_analysis = analysis
                break
    
    def _on_email_clicked(self, email: Email):
        """Clic sur email."""
        logger.info(f"📧 Email: {email.subject[:30]}")
        
        # Récupérer contenu complet
        if not email.body:
            try:
                full_email = self.gmail_client.get_email(email.id)
                if full_email:
                    email = full_email
            except:
                pass
        
        # Afficher
        self.email_detail_view.show_email(email)
        self.email_selected.emit(email)
        
        # Marquer lu
        try:
            if not getattr(email, 'read', True):
                self.gmail_client.mark_as_read(email.id)
                email.read = True
                
                # Mettre à jour la carte
                if email.id in self.email_cards:
                    card = self.email_cards[email.id]
                    card.email.read = True
                    card._apply_styles()
        except:
            pass
    
    def _show_error(self, message: str):
        """Erreur."""
        while self.emails_layout.count() > 1:
            item = self.emails_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        error = QLabel(f"❌ {message}")
        error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error.setFont(QFont("Arial", 14))
        error.setStyleSheet("color: #dc2626; padding: 50px;")
        error.setWordWrap(True)
        self.emails_layout.insertWidget(0, error)