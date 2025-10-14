#!/usr/bin/env python3
"""
Vue Inbox - VERSION OPTIMISÉE ULTRA-RAPIDE
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont

from app.gmail_client import GmailClient
from app.ai_processor import AIProcessor
from app.models.email_model import Email
from app.ui.views.email_detail_view import EmailDetailView

logger = logging.getLogger(__name__)

class EmailAnalysisWorker(QThread):
    """Worker pour analyse IA en arrière-plan."""
    
    analysis_complete = pyqtSignal(str, dict)
    
    def __init__(self, ai_processor: AIProcessor, emails: List[Email]):
        super().__init__()
        self.ai_processor = ai_processor
        self.emails = emails
        self._is_running = True
    
    def run(self):
        """Analyse en arrière-plan."""
        for email in self.emails:
            if not self._is_running:
                break
            
            try:
                if not hasattr(email, 'ai_analysis') or email.ai_analysis is None:
                    analysis = self.ai_processor.analyze_email_fast(
                        subject=email.subject or "",
                        body=email.snippet or email.body or "",
                        sender=email.sender or ""
                    )
                    
                    if analysis:
                        self.analysis_complete.emit(email.id, analysis)
            except:
                pass
    
    def stop(self):
        """Arrête l'analyse."""
        self._is_running = False

class EmailListItem(QFrame):
    """Item de liste d'email optimisé."""
    
    clicked = pyqtSignal(object)
    
    def __init__(self, email: Email):
        super().__init__()
        self.email = email
        self.setObjectName("email-item")
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Ligne 1: Indicateur + Expéditeur + Date
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # Indicateur non lu
        if not getattr(self.email, 'read', True):
            indicator = QLabel("●")
            indicator.setFont(QFont("Arial", 12, QFont.Bold))
            indicator.setStyleSheet("color: #5b21b6;")
            indicator.setFixedWidth(20)
            header_layout.addWidget(indicator)
        else:
            spacer = QLabel("")
            spacer.setFixedWidth(20)
            header_layout.addWidget(spacer)
        
        # Expéditeur
        sender_label = QLabel(self.email.sender or "Inconnu")
        sender_label.setFont(QFont("Arial", 13, QFont.Bold))
        sender_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(sender_label)
        
        header_layout.addStretch()
        
        # Date
        if self.email.received_date:
            date_str = self._format_date(self.email.received_date)
            date_label = QLabel(date_str)
            date_label.setFont(QFont("Arial", 11))
            date_label.setStyleSheet("color: #666666;")
            header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # Ligne 2: Sujet
        subject_label = QLabel(self.email.subject or "(Sans sujet)")
        subject_label.setFont(QFont("Arial", 12))
        subject_label.setStyleSheet("color: #1a1a1a;")
        subject_label.setWordWrap(False)
        layout.addWidget(subject_label)
        
        # Ligne 3: Aperçu
        if self.email.snippet:
            snippet = self.email.snippet[:150]
            snippet_label = QLabel(snippet + "...")
            snippet_label.setFont(QFont("Arial", 11))
            snippet_label.setStyleSheet("color: #666666;")
            snippet_label.setWordWrap(True)
            snippet_label.setMaximumHeight(45)
            layout.addWidget(snippet_label)
        
        # Ligne 4: Badges IA
        self.badges_layout = QHBoxLayout()
        self.badges_layout.setSpacing(8)
        layout.addLayout(self.badges_layout)
        
        # Style
        self.setStyleSheet("""
            QFrame#email-item {
                background-color: #ffffff;
                border: none;
                border-bottom: 1px solid #f0f0f0;
            }
            QFrame#email-item:hover {
                background-color: #faf5ff;
                border-left: 4px solid #5b21b6;
            }
        """)
    
    def _format_date(self, dt) -> str:
        """Formate la date."""
        try:
            now = datetime.now(timezone.utc)
            
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            elif dt.tzinfo is not None:
                now = now.astimezone(dt.tzinfo)
            
            diff = now - dt
            
            if diff.days == 0:
                return dt.strftime("%H:%M")
            elif diff.days == 1:
                return "Hier"
            elif diff.days < 7:
                days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
                return days[dt.weekday()]
            else:
                return dt.strftime("%d/%m/%Y")
        except:
            return dt.strftime("%d/%m/%Y") if dt else ""
    
    def update_ai_badges(self, analysis: dict):
        """Met à jour les badges IA."""
        # Effacer anciens badges
        while self.badges_layout.count():
            item = self.badges_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Badge catégorie
        if 'category' in analysis and analysis['category'] != 'general':
            icon = self._get_category_icon(analysis['category'])
            badge = self._create_badge(icon, "#5b21b6")
            self.badges_layout.addWidget(badge)
        
        # Badge sentiment
        if analysis.get('sentiment') == 'positive':
            badge = self._create_badge("😊", "#10b981")
            self.badges_layout.addWidget(badge)
        elif analysis.get('sentiment') == 'negative':
            badge = self._create_badge("⚠️", "#ef4444")
            self.badges_layout.addWidget(badge)
        
        # Badge urgent
        if analysis.get('urgent'):
            badge = self._create_badge("🔥 Urgent", "#dc2626")
            self.badges_layout.addWidget(badge)
        
        self.badges_layout.addStretch()
    
    def _create_badge(self, text: str, color: str) -> QLabel:
        """Crée un badge."""
        badge = QLabel(text)
        badge.setFont(QFont("Arial", 9, QFont.Bold))
        badge.setFixedHeight(24)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 12px;
                padding: 4px 12px;
            }}
        """)
        return badge
    
    def _get_category_icon(self, category: str) -> str:
        """Icône de catégorie."""
        icons = {
            'cv': '📄 CV',
            'meeting': '📅 RDV',
            'invoice': '💰',
            'newsletter': '📰',
            'support': '🛠️',
            'important': '⭐',
            'spam': '🚫'
        }
        return icons.get(category, '📧')
    
    def mousePressEvent(self, event):
        """Clic."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.email)
        super().mousePressEvent(event)

class SmartInboxView(QWidget):
    """Vue inbox optimisée."""
    
    email_selected = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.emails = []
        self.email_items = {}
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
        list_container.setFixedWidth(480)
        list_container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-right: 2px solid #e0e0e0;
            }
        """)
        
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        
        # En-tête liste
        list_header = QFrame()
        list_header.setFixedHeight(70)
        list_header.setStyleSheet("background-color: #fafafa; border-bottom: 2px solid #e0e0e0;")
        
        header_layout = QHBoxLayout(list_header)
        header_layout.setContentsMargins(25, 15, 25, 15)
        
        self.folder_title = QLabel("📥 Réception")
        self.folder_title.setFont(QFont("Arial", 18, QFont.Bold))
        self.folder_title.setStyleSheet("color: #000000;")
        header_layout.addWidget(self.folder_title)
        
        header_layout.addStretch()
        
        self.email_count_label = QLabel("0")
        self.email_count_label.setFont(QFont("Arial", 13))
        self.email_count_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(self.email_count_label)
        
        list_layout.addWidget(list_header)
        
        # Scroll emails
        self.emails_scroll = QScrollArea()
        self.emails_scroll.setWidgetResizable(True)
        self.emails_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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
            self.email_count_label.setText(f"{len(self.emails)}")
            
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
        
        self.email_items = {}
        
        if not self.emails:
            empty = QLabel("📭 Aucun email")
            empty.setAlignment(Qt.AlignCenter)
            empty.setFont(QFont("Arial", 14))
            empty.setStyleSheet("color: #999999; padding: 50px;")
            self.emails_layout.insertWidget(0, empty)
        else:
            for email in self.emails:
                item = EmailListItem(email)
                item.clicked.connect(self._on_email_clicked)
                self.emails_layout.insertWidget(self.emails_layout.count() - 1, item)
                self.email_items[email.id] = item
        
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
        if email_id in self.email_items:
            self.email_items[email_id].update_ai_badges(analysis)
            
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
        except:
            pass
    
    def _show_error(self, message: str):
        """Erreur."""
        while self.emails_layout.count() > 1:
            item = self.emails_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        error = QLabel(f"❌ {message}")
        error.setAlignment(Qt.AlignCenter)
        error.setFont(QFont("Arial", 14))
        error.setStyleSheet("color: #dc2626; padding: 50px;")
        error.setWordWrap(True)
        self.emails_layout.insertWidget(0, error)