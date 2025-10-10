#!/usr/bin/env python3
"""
Vue Smart Inbox - OPTIMISÉE: Analyse IA à la demande uniquement
"""
import logging
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QSplitter, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QFont

from gmail_client import GmailClient
from ai_processor import AIProcessor
from models.email_model import Email
from ui.views.email_detail_view import EmailDetailView

logger = logging.getLogger(__name__)


class AIAnalysisThread(QThread):
    """Thread pour analyser un email sans bloquer l'UI."""
    
    analysis_complete = pyqtSignal(object, dict)  # email, analysis
    
    def __init__(self, ai_processor: AIProcessor, email: Email):
        super().__init__()
        self.ai_processor = ai_processor
        self.email = email
    
    def run(self):
        """Analyse l'email dans un thread séparé."""
        try:
            analysis = self.ai_processor.analyze_email(
                subject=self.email.subject or "",
                body=self.email.body or self.email.snippet or "",
                sender=self.email.sender or ""
            )
            self.analysis_complete.emit(self.email, analysis)
        except Exception as e:
            logger.error(f"Erreur analyse IA thread: {e}")
            self.analysis_complete.emit(self.email, None)


class EmailListItem(QFrame):
    """Widget représentant un email dans la liste."""
    
    clicked = pyqtSignal(object)
    
    def __init__(self, email: Email):
        super().__init__()
        self.email = email
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée l'interface de l'item."""
        self.setObjectName("email-item")
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(5)
        
        # En-tête (expéditeur + date)
        header_layout = QHBoxLayout()
        
        sender_label = QLabel(self.email.sender or "Inconnu")
        sender_label.setFont(QFont("SF Pro Display", 12, QFont.Bold))
        sender_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(sender_label)
        
        header_layout.addStretch()
        
        if self.email.received_date:
            date_label = QLabel(self.email.received_date.strftime("%d/%m/%Y"))
            date_label.setFont(QFont("SF Pro Display", 10))
            date_label.setStyleSheet("color: #666666;")
            header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # Sujet
        subject_label = QLabel(self.email.subject or "(Sans sujet)")
        subject_label.setFont(QFont("SF Pro Display", 11))
        subject_label.setStyleSheet("color: #333333;")
        subject_label.setWordWrap(False)
        layout.addWidget(subject_label)
        
        # Aperçu
        if self.email.snippet:
            snippet_label = QLabel(self.email.snippet[:100] + "...")
            snippet_label.setFont(QFont("SF Pro Display", 10))
            snippet_label.setStyleSheet("color: #666666;")
            snippet_label.setWordWrap(True)
            layout.addWidget(snippet_label)
        
        # Badge catégorie IA (si disponible) - sera ajouté après analyse
        self.badges_layout = QHBoxLayout()
        layout.addLayout(self.badges_layout)
        
        # Style
        self.setStyleSheet("""
            QFrame#email-item {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QFrame#email-item:hover {
                background-color: #f9fafb;
                border: 1px solid #5b21b6;
            }
        """)
    
    def update_ai_badges(self, analysis: dict):
        """Met à jour les badges IA après analyse."""
        # Nettoyer les anciens badges
        while self.badges_layout.count():
            item = self.badges_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not analysis:
            return
        
        category = analysis.get('category', 'autre')
        priority = analysis.get('priority', 'moyenne')
        
        # Badge catégorie
        category_badge = QLabel(f"📁 {category.upper()}")
        category_badge.setFont(QFont("SF Pro Display", 9))
        category_badge.setStyleSheet("""
            background-color: #e0e7ff;
            color: #5b21b6;
            padding: 3px 8px;
            border-radius: 10px;
        """)
        self.badges_layout.addWidget(category_badge)
        
        # Badge priorité
        priority_colors = {
            'haute': '#fee2e2',
            'moyenne': '#fef3c7',
            'basse': '#d1fae5'
        }
        priority_text_colors = {
            'haute': '#dc2626',
            'moyenne': '#f59e0b',
            'basse': '#10b981'
        }
        
        priority_badge = QLabel(f"⚡ {priority.upper()}")
        priority_badge.setFont(QFont("SF Pro Display", 9))
        priority_badge.setStyleSheet(f"""
            background-color: {priority_colors.get(priority, '#f3f4f6')};
            color: {priority_text_colors.get(priority, '#666666')};
            padding: 3px 8px;
            border-radius: 10px;
        """)
        self.badges_layout.addWidget(priority_badge)
        
        self.badges_layout.addStretch()
    
    def mousePressEvent(self, event):
        """Gère le clic sur l'email."""
        self.clicked.emit(self.email)
        super().mousePressEvent(event)


class SmartInboxView(QWidget):
    """Vue de la boîte de réception intelligente."""
    
    email_selected = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.current_folder = "INBOX"
        self.emails: List[Email] = []
        self.email_items: dict = {}  # Pour retrouver les items visuels
        self.analysis_thread: Optional[AIAnalysisThread] = None
        
        self._setup_ui()
        
        # Charger les emails après un court délai
        QTimer.singleShot(100, self.refresh_emails)
    
    def _setup_ui(self):
        """Crée l'interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Splitter pour diviser liste/détail
        splitter = QSplitter(Qt.Horizontal)
        
        # === PARTIE GAUCHE: LISTE DES EMAILS ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)
        
        # Barre de recherche
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher dans les emails...")
        self.search_input.setFont(QFont("SF Pro Display", 12))
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 20px;
                padding: 8px 15px;
            }
            QLineEdit:focus {
                border: 2px solid #5b21b6;
            }
        """)
        search_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFont(QFont("SF Pro Display", 14))
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #e0e0e0;
                border-radius: 20px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #5b21b6;
                border-color: #5b21b6;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_emails)
        search_layout.addWidget(refresh_btn)
        
        left_layout.addLayout(search_layout)
        
        # Zone de liste scrollable
        self.emails_scroll = QScrollArea()
        self.emails_scroll.setWidgetResizable(True)
        self.emails_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.emails_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f9fafb;
            }
        """)
        
        self.emails_container = QWidget()
        self.emails_layout = QVBoxLayout(self.emails_container)
        self.emails_layout.setContentsMargins(0, 0, 0, 0)
        self.emails_layout.setSpacing(10)
        self.emails_layout.addStretch()
        
        self.emails_scroll.setWidget(self.emails_container)
        left_layout.addWidget(self.emails_scroll)
        
        # === PARTIE DROITE: DÉTAIL EMAIL ===
        self.email_detail_view = EmailDetailView(self.gmail_client, self.ai_processor)
        
        # Ajouter au splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.email_detail_view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
    
    def load_folder(self, folder: str):
        """Charge les emails d'un dossier."""
        logger.info(f"Chargement dossier: {folder}")
        self.current_folder = folder
        self.refresh_emails()
    
    def refresh_emails(self):
        """Rafraîchit la liste des emails."""
        logger.info("Rafraîchissement emails...")
        
        # Nettoyer la liste actuelle
        while self.emails_layout.count() > 1:
            item = self.emails_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.email_items.clear()
        
        # Afficher un message de chargement
        loading_label = QLabel("⏳ Chargement des emails...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setFont(QFont("SF Pro Display", 14))
        loading_label.setStyleSheet("color: #666666; padding: 50px;")
        self.emails_layout.insertWidget(0, loading_label)
        
        # Charger les emails
        QTimer.singleShot(100, self._load_emails_async)
    
    def _load_emails_async(self):
        """Charge les emails de manière asynchrone - SANS ANALYSE IA."""
        try:
            logger.info(f"Chargement emails du dossier: {self.current_folder}")
            
            # Récupérer les emails selon le dossier
            if self.current_folder == "INBOX":
                self.emails = self.gmail_client.search_emails(query='in:inbox', max_results=50)
            elif self.current_folder == "SPAM":
                self.emails = self.gmail_client.search_emails(query='in:spam', max_results=50)
            elif self.current_folder == "SENT":
                self.emails = self.gmail_client.search_emails(query='in:sent', max_results=50)
            elif self.current_folder == "DRAFTS":
                self.emails = self.gmail_client.search_emails(query='in:draft', max_results=50)
            elif self.current_folder == "STARRED":
                self.emails = self.gmail_client.search_emails(query='is:starred', max_results=50)
            elif self.current_folder == "TRASH":
                self.emails = self.gmail_client.search_emails(query='in:trash', max_results=50)
            else:
                self.emails = []
            
            logger.info(f"{len(self.emails)} emails chargés (analyse IA à la demande)")
            
            # Afficher les emails IMMÉDIATEMENT sans analyse IA
            self._display_emails()
            
        except Exception as e:
            logger.error(f"Erreur chargement emails: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(f"Erreur: {e}")
    
    def _display_emails(self):
        """Affiche les emails dans la liste - INSTANTANÉ."""
        # Nettoyer la liste
        while self.emails_layout.count() > 1:
            item = self.emails_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.emails:
            # Aucun email
            empty_label = QLabel("📭 Aucun email dans ce dossier")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setFont(QFont("SF Pro Display", 14))
            empty_label.setStyleSheet("color: #999999; padding: 50px;")
            self.emails_layout.insertWidget(0, empty_label)
        else:
            # Afficher les emails IMMÉDIATEMENT
            for email in self.emails:
                item = EmailListItem(email)
                item.clicked.connect(self._on_email_clicked)
                self.emails_layout.insertWidget(self.emails_layout.count() - 1, item)
                
                # Sauvegarder la référence
                self.email_items[email.id] = item
        
        logger.info(f"{len(self.emails)} emails affichés instantanément")
    
    def _show_error(self, message: str):
        """Affiche un message d'erreur."""
        while self.emails_layout.count() > 1:
            item = self.emails_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        error_label = QLabel(f"❌ {message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setFont(QFont("SF Pro Display", 14))
        error_label.setStyleSheet("color: #dc2626; padding: 50px;")
        error_label.setWordWrap(True)
        self.emails_layout.insertWidget(0, error_label)
    
    def _on_email_clicked(self, email: Email):
        """Gère le clic sur un email - ANALYSE IA ICI."""
        logger.info(f"Email sélectionné: {email.subject}")
        
        # Récupérer le contenu complet si nécessaire
        if not email.body:
            try:
                if hasattr(self.gmail_client, 'get_email'):
                    full_email = self.gmail_client.get_email(email.id)
                    if full_email:
                        email = full_email
            except Exception as e:
                logger.error(f"Erreur chargement email complet: {e}")
        
        # Afficher dans la vue détail IMMÉDIATEMENT
        self.email_detail_view.show_email(email)
        self.email_selected.emit(email)
        
        # Lancer l'analyse IA EN ARRIÈRE-PLAN (si pas déjà fait)
        if not hasattr(email, 'ai_analysis') or email.ai_analysis is None:
            self._analyze_email_async(email)
    
    def _analyze_email_async(self, email: Email):
        """Analyse un email en arrière-plan sans bloquer l'UI."""
        logger.info(f"🔍 Analyse IA en arrière-plan: {email.subject}")
        
        # Annuler l'analyse précédente si en cours
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.quit()
            self.analysis_thread.wait()
        
        # Lancer une nouvelle analyse
        self.analysis_thread = AIAnalysisThread(self.ai_processor, email)
        self.analysis_thread.analysis_complete.connect(self._on_analysis_complete)
        self.analysis_thread.start()
    
    def _on_analysis_complete(self, email: Email, analysis: dict):
        """Callback quand l'analyse IA est terminée."""
        if analysis:
            logger.info(f"✅ Analyse terminée: {analysis.get('category', 'autre')}")
            
            # Sauvegarder l'analyse
            email.ai_analysis = analysis
            email.category = analysis.get('category', 'autre')
            
            # Mettre à jour les badges visuels si l'email est dans la liste
            if email.id in self.email_items:
                item = self.email_items[email.id]
                item.email.ai_analysis = analysis
                item.update_ai_badges(analysis)
            
            # Mettre à jour la vue détail si cet email est affiché
            if hasattr(self.email_detail_view, 'current_email') and \
               self.email_detail_view.current_email and \
               self.email_detail_view.current_email.id == email.id:
                self.email_detail_view.show_email(email)
        else:
            logger.warning(f"⚠️ Échec analyse IA pour: {email.subject}")