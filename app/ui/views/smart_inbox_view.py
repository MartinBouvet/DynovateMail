#!/usr/bin/env python3
"""
Vue Smart Inbox - VERSION CORRIGÉE COMPLÈTE
Corrections: Navigation dossiers, filtres, affichage
"""
import logging
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLabel, QPushButton, QFrame, QButtonGroup, QSplitter, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
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
    analysis_complete = pyqtSignal()
    progress_updated = pyqtSignal(int, int)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.should_stop = False
        self.emails_with_analysis = []
        self.current_folder = "INBOX"
    
    def set_folder(self, folder: str):
        """Définit le dossier à charger."""
        self.current_folder = folder
    
    def run(self):
        """Charge et analyse les emails."""
        try:
            logger.info(f"Chargement emails depuis {self.current_folder}...")
            
            # Charger selon le dossier
            if self.current_folder == "INBOX":
                emails = self.gmail_client.get_recent_emails(max_results=50)
            elif self.current_folder == "ARCHIVES":
                emails = self.gmail_client.get_archived_emails(max_results=50)
            elif self.current_folder == "TRASH":
                emails = self.gmail_client.get_trashed_emails(max_results=50)
            else:
                emails = []
            
            if not emails:
                logger.warning(f"Aucun email trouvé dans {self.current_folder}")
                self.emails_loaded.emit([])
                self.analysis_complete.emit()
                return
            
            logger.info(f"{len(emails)} emails chargés, analyse IA en cours...")
            
            # Analyser avec l'IA
            for i, email in enumerate(emails):
                if self.should_stop:
                    break
                
                try:
                    email.ai_analysis = self.ai_processor.process_email(email)
                    self.emails_with_analysis.append(email)
                    self.progress_updated.emit(i + 1, len(emails))
                except Exception as e:
                    logger.error(f"Erreur analyse email {email.id}: {e}")
            
            self.emails_loaded.emit(self.emails_with_analysis)
            self.analysis_complete.emit()
            
        except Exception as e:
            logger.error(f"Erreur chargement emails: {e}")
            self.emails_loaded.emit([])
            self.analysis_complete.emit()
    
    def stop(self):
        """Arrête le thread."""
        self.should_stop = True


class SmartInboxView(QWidget):
    """Vue Inbox intelligente avec navigation et filtres - CORRIGÉE."""
    
    email_selected = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        
        # État
        self.all_emails = []
        self.filtered_emails = []
        self.current_folder = "INBOX"
        self.current_category = "Tous"
        self.selected_email = None
        
        # Thread de chargement
        self.loader_thread = None
        
        self._setup_ui()
        self._apply_styles()
        
        # Chargement initial automatique
        QTimer.singleShot(500, self.refresh_emails)
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Navigation dossiers + Filtres
        navigation_section = self._create_navigation()
        layout.addWidget(navigation_section)
        
        # Splitter horizontal: Liste | Détail
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(2)
        
        # === COLONNE GAUCHE: Liste emails ===
        email_list = self._create_email_list()
        main_splitter.addWidget(email_list)
        
        # === COLONNE DROITE: Détail email ===
        self.detail_view = EmailDetailView()
        self.detail_view.set_gmail_client(self.gmail_client)
        main_splitter.addWidget(self.detail_view)
        
        # Proportions: Liste (35%) - Détail (65%)
        main_splitter.setSizes([400, 700])
        layout.addWidget(main_splitter)
    
    def _create_navigation(self) -> QWidget:
        """Crée la navigation COMPLÈTE avec dossiers - CORRIGÉE."""
        nav_frame = QFrame()
        nav_frame.setObjectName("navigation-bar")
        nav_frame.setFixedHeight(70)
        
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(20, 10, 20, 10)
        nav_layout.setSpacing(15)
        
        # === NAVIGATION DOSSIERS ===
        folders_label = QLabel("📁 Dossiers:")
        folders_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        folders_label.setStyleSheet("color: #000000;")
        nav_layout.addWidget(folders_label)
        
        # Groupe de boutons pour les dossiers
        self.folder_group = QButtonGroup()
        
        folders = [
            ("📥 Boîte de réception", "INBOX"),
            ("📦 Archives", "ARCHIVES"),
            ("🗑️ Corbeille", "TRASH")
        ]
        
        for label, folder_id in folders:
            btn = QPushButton(label)
            btn.setObjectName("folder-btn")
            btn.setCheckable(True)
            btn.setProperty("folder_id", folder_id)
            btn.clicked.connect(lambda checked, fid=folder_id: self._on_folder_changed(fid))
            self.folder_group.addButton(btn)
            nav_layout.addWidget(btn)
            
            if folder_id == "INBOX":
                btn.setChecked(True)
        
        nav_layout.addSpacing(20)
        
        # === FILTRES PAR CATÉGORIE ===
        filter_label = QLabel("🏷️ Catégorie:")
        filter_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        filter_label.setStyleSheet("color: #000000;")
        nav_layout.addWidget(filter_label)
        
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "Tous", "CV", "RDV", "Facture", "Support", 
            "Partenariat", "Spam", "Général"
        ])
        self.category_filter.setMinimumWidth(150)
        self.category_filter.setFixedHeight(35)
        self.category_filter.currentTextChanged.connect(self._on_category_changed)
        nav_layout.addWidget(self.category_filter)
        
        nav_layout.addStretch()
        
        # Bouton refresh
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setObjectName("refresh-btn")
        refresh_btn.setFixedHeight(35)
        refresh_btn.clicked.connect(self.refresh_emails)
        nav_layout.addWidget(refresh_btn)
        
        return nav_frame
    
    def _create_email_list(self) -> QWidget:
        """Crée la liste d'emails avec scroll."""
        list_container = QFrame()
        list_container.setObjectName("email-list-container")
        
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        
        # Header de la liste
        header = QFrame()
        header.setObjectName("list-header")
        header.setFixedHeight(50)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.list_title = QLabel("📥 Boîte de réception")
        self.list_title.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        self.list_title.setStyleSheet("color: #000000;")
        header_layout.addWidget(self.list_title)
        
        header_layout.addStretch()
        
        self.email_count_label = QLabel("0 emails")
        self.email_count_label.setFont(QFont("Inter", 11))
        self.email_count_label.setStyleSheet("color: #6c757d;")
        header_layout.addWidget(self.email_count_label)
        
        list_layout.addWidget(header)
        
        # Scroll area pour les emails
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setObjectName("emails-scroll")
        
        # Container des emails
        self.emails_container = QWidget()
        self.emails_layout = QVBoxLayout(self.emails_container)
        self.emails_layout.setSpacing(0)
        self.emails_layout.setContentsMargins(0, 0, 0, 0)
        self.emails_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Message par défaut
        self.empty_label = QLabel("📭 Aucun email à afficher")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(QFont("Inter", 14))
        self.empty_label.setStyleSheet("color: #6c757d; padding: 50px;")
        self.emails_layout.addWidget(self.empty_label)
        
        scroll_area.setWidget(self.emails_container)
        list_layout.addWidget(scroll_area)
        
        return list_container
    
    def _on_folder_changed(self, folder_id: str):
        """Gère le changement de dossier - CORRIGÉ."""
        if folder_id == self.current_folder:
            return
        
        logger.info(f"Changement de dossier: {self.current_folder} -> {folder_id}")
        self.current_folder = folder_id
        
        # Mettre à jour le titre
        folder_names = {
            "INBOX": "📥 Boîte de réception",
            "ARCHIVES": "📦 Archives",
            "TRASH": "🗑️ Corbeille"
        }
        self.list_title.setText(folder_names.get(folder_id, "Emails"))
        
        # Recharger les emails
        self.refresh_emails()
    
    def _on_category_changed(self, category: str):
        """Gère le changement de catégorie - CORRIGÉ."""
        self.current_category = category
        logger.info(f"Filtre catégorie: {category}")
        self._filter_and_display_emails()
    
    def refresh_emails(self):
        """Recharge les emails - CORRIGÉ."""
        logger.info(f"Actualisation emails du dossier {self.current_folder}...")
        
        # Arrêter le thread précédent
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.stop()
            self.loader_thread.wait()
        
        # Vider la liste
        self._clear_email_list()
        
        # Message de chargement
        loading_label = QLabel("⏳ Chargement en cours...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setFont(QFont("Inter", 14))
        loading_label.setStyleSheet("color: #007bff; padding: 50px;")
        self.emails_layout.addWidget(loading_label)
        
        # Lancer le nouveau thread
        self.loader_thread = EmailLoaderThread(self.gmail_client, self.ai_processor)
        self.loader_thread.set_folder(self.current_folder)
        self.loader_thread.emails_loaded.connect(self._on_emails_loaded)
        self.loader_thread.progress_updated.connect(self._on_progress_updated)
        self.loader_thread.start()
    
    def _on_emails_loaded(self, emails: List[Email]):
        """Gère les emails chargés - CORRIGÉ."""
        logger.info(f"{len(emails)} emails chargés avec analyse IA")
        self.all_emails = emails
        self._filter_and_display_emails()
    
    def _on_progress_updated(self, current: int, total: int):
        """Met à jour la progression."""
        logger.debug(f"Analyse IA: {current}/{total}")
    
    def _filter_and_display_emails(self):
        """Filtre et affiche les emails - CORRIGÉ."""
        # Appliquer le filtre de catégorie
        if self.current_category == "Tous":
            self.filtered_emails = self.all_emails
        else:
            self.filtered_emails = [
                email for email in self.all_emails
                if hasattr(email, 'ai_analysis') and 
                   hasattr(email.ai_analysis, 'category') and
                   email.ai_analysis.category.lower() == self.current_category.lower()
            ]
        
        # Mettre à jour le compteur
        self.email_count_label.setText(f"{len(self.filtered_emails)} email(s)")
        
        # Afficher les emails
        self._display_email_list()
    
    def _display_email_list(self):
        """Affiche la liste d'emails - CORRIGÉ PyQt5."""
        self._clear_email_list()
    
        if not self.filtered_emails:
        # Recréer le label vide
            try:
                from PyQt5.QtWidgets import QLabel
                from PyQt5.QtCore import Qt
                from PyQt5.QtGui import QFont
            
                self.empty_label = QLabel(f"📭 Aucun email dans {self.list_title.text()}")
                self.empty_label.setAlignment(Qt.AlignCenter)  # CORRIGÉ pour PyQt5
                self.empty_label.setFont(QFont("Arial", 14))
                self.empty_label.setStyleSheet("color: #6c757d; padding: 50px;")
                self.emails_layout.addWidget(self.empty_label)
            except Exception as e:
                logger.error(f"Erreur création label vide: {e}")
            return
    
    # Créer les cartes d'emails
        for email in self.filtered_emails:
            try:
                card = SmartEmailCard(email)
                card.clicked.connect(lambda e=email: self._on_email_card_clicked(e))
                self.emails_layout.addWidget(card)
            except Exception as e:
                logger.error(f"Erreur création carte email: {e}")
    
    def _on_email_card_clicked(self, email: Email):
        """Gère le clic sur une carte d'email - CORRIGÉ."""
        logger.info(f"Email sélectionné: {email.id}")
        self.selected_email = email
        
        # Marquer comme lu si nécessaire
        if not email.is_read and self.gmail_client:
            try:
                self.gmail_client.mark_as_read(email.id)
                email.is_read = True
            except Exception as e:
                logger.error(f"Erreur marquage lu: {e}")
        
        # Afficher dans la vue détail
        self.detail_view.show_email(email)
        
        # Émettre le signal
        self.email_selected.emit(email)
    
    def _clear_email_list(self):
        """Vide la liste d'emails."""
        while self.emails_layout.count():
            child = self.emails_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _apply_styles(self):
        """Applique les styles."""
        self.setStyleSheet("""
            /* Navigation Bar */
            QFrame#navigation-bar {
                background-color: #f8f9fa;
                border-bottom: 2px solid #dee2e6;
            }
            
            QPushButton#folder-btn {
                background-color: transparent;
                border: 2px solid transparent;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                color: #495057;
            }
            
            QPushButton#folder-btn:hover {
                background-color: #e9ecef;
            }
            
            QPushButton#folder-btn:checked {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
            }
            
            QPushButton#refresh-btn {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton#refresh-btn:hover { background-color: #218838; }
            
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QComboBox:focus { border-color: #007bff; }
            
            /* List Container */
            QFrame#email-list-container {
                background-color: #ffffff;
                border-right: 1px solid #dee2e6;
            }
            
            QFrame#list-header {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
            
            QScrollArea#emails-scroll {
                border: none;
                background-color: #ffffff;
            }
        """)