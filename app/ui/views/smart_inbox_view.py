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
            elif self.current_folder == "SENT":
                emails = self.gmail_client.get_sent_emails(max_results=50)
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
        """Configure l'interface complète - CORRIGÉE."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
    
    # Sidebar (navigation)
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
    
    # Splitter pour liste emails + détails
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
    
    # === PANNEAU GAUCHE: Liste emails ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
    
    # Header avec titre et filtre
        header = self._create_header()
        left_layout.addWidget(header)
    
    # Zone de défilement pour les emails
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setObjectName("emails-scroll-area")
    
    # Container des emails
        self.emails_container = QWidget()
        self.emails_layout = QVBoxLayout(self.emails_container)
        self.emails_layout.setContentsMargins(10, 10, 10, 10)
        self.emails_layout.setSpacing(8)
        self.emails_layout.addStretch()
    
        scroll_area.setWidget(self.emails_container)
        left_layout.addWidget(scroll_area)
    
    # === PANNEAU DROIT: Détail email ===
        self.detail_view = EmailDetailView()
    
    # Ajouter au splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.detail_view)
        splitter.setSizes([400, 600])
    
        main_layout.addWidget(splitter)

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
        """Filtre et affiche les emails selon catégorie et tri."""
        try:
        # Filtrer par catégorie
            if self.current_category == "Tous":
                self.filtered_emails = self.all_emails.copy()
            else:
                self.filtered_emails = [
                    email for email in self.all_emails
                    if hasattr(email, 'ai_analysis') and 
                    email.ai_analysis and
                    email.ai_analysis.category == self.current_category
                ]
        
        # Trier
            sort_index = self.sort_combo.currentIndex() if hasattr(self, 'sort_combo') else 0
            if sort_index == 0:  # Plus récent
                self.filtered_emails.sort(key=lambda e: e.received_date or datetime.min, reverse=True)
            elif sort_index == 1:  # Plus ancien
                self.filtered_emails.sort(key=lambda e: e.received_date or datetime.min)
            elif sort_index == 2:  # Priorité
                self.filtered_emails.sort(
                    key=lambda e: (
                        e.ai_analysis.priority if hasattr(e, 'ai_analysis') and e.ai_analysis else 5
                    )
                )
            elif sort_index == 3:  # Expéditeur
                self.filtered_emails.sort(key=lambda e: e.sender or "")
        
        # Afficher
            self._display_emails(self.filtered_emails)
        
        # Mettre à jour le compteur
            if hasattr(self, 'count_label'):
                self.count_label.setText(f"{len(self.filtered_emails)} email(s)")
        
            logger.info(f"{len(self.filtered_emails)} emails affichés (catégorie: {self.current_category})")
        
        except Exception as e:
            logger.error(f"Erreur filtrage emails: {e}")
            self._display_emails([])
    
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
        """Applique les styles - ULTRA CORRIGÉS pour contraste."""
        self.setStyleSheet("""
            /* SIDEBAR */
            QFrame#sidebar {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
        
            /* BOUTONS SIDEBAR - CORRECTION CONTRASTE */
            QPushButton#sidebar-btn {
                text-align: left;
                padding: 12px 15px;
                border: none;
                border-radius: 6px;
                background-color: transparent;
                color: #000000;  /* CORRECTION: Texte noir */
                font-size: 13px;
                font-weight: 500;
            }
        
            QPushButton#sidebar-btn:hover {
                background-color: #e9ecef;
                color: #000000;  /* CORRECTION: Reste noir au survol */
            }
        
            QPushButton#sidebar-btn:checked {
                background-color: #007bff;
                color: #ffffff;  /* CORRECTION: Blanc sur bleu */
                font-weight: 600;
            }
        
            /* BOUTON RAFRAÎCHIR */
            QPushButton#refresh-btn {
                background-color: #28a745;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: 600;
                font-size: 13px;
            }
        
            QPushButton#refresh-btn:hover {
                background-color: #218838;
            }
        
            /* HEADER */
            QFrame#inbox-header {
                background-color: #ffffff;
                border-bottom: 1px solid #dee2e6;
                padding: 15px 20px;
            }
        
            QLabel#inbox-title {
                color: #000000;  /* CORRECTION: Noir */
                font-size: 20px;
                font-weight: bold;
            }
        
            QLabel#inbox-count {
                color: #6c757d;
                font-size: 13px;
            }
        
            /* COMBOBOX FILTRE */
            QComboBox#filter-combo {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
                color: #000000;  /* CORRECTION: Texte noir */
                font-size: 13px;
                min-width: 150px;
            }
        
            QComboBox#filter-combo:hover {
                border-color: #007bff;
            }
        
            QComboBox#filter-combo::drop-down {
                border: none;
                padding-right: 10px;
            }
        
            QComboBox#filter-combo QAbstractItemView {
                background-color: #ffffff;
                color: #000000;  /* CORRECTION: Texte noir dans dropdown */
                selection-background-color: #007bff;
                selection-color: #ffffff;
                border: 1px solid #dee2e6;
            }
        
            /* SCROLL AREA */
            QScrollArea#emails-scroll-area {
                border: none;
                background-color: #ffffff;
            }
        
            /* LABEL VIDE */
            QLabel#empty-label {
                color: #6c757d;
                font-size: 14px;
            }
        """)

    def _create_sidebar(self):
        """Crée la barre latérale - VERSION ULTRA CORRIGÉE."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
    
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(5)
        sidebar_layout.setContentsMargins(10, 20, 10, 10)
    
    # === SECTION DOSSIERS ===
        folders_label = QLabel("📁 DOSSIERS")
        folders_label.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        folders_label.setStyleSheet("color: #000000; padding: 5px;")  # CORRECTION: Noir au lieu de gris
        sidebar_layout.addWidget(folders_label)
    
    # Groupe de boutons pour dossiers
        self.folder_btn_group = QButtonGroup(self)
        self.folder_btn_group.setExclusive(True)
    
        folders = [
            ("📥 Boîte de réception", "INBOX"),
            ("📤 Envoyés", "SENT"),
            ("📂 Archivés", "ARCHIVES"),
            ("🗑️ Corbeille", "TRASH")
        ]
    
        for label, folder_id in folders:
            btn = QPushButton(label)
            btn.setObjectName("sidebar-btn")
            btn.setCheckable(True)
            btn.setProperty("folder", folder_id)
            btn.clicked.connect(lambda checked, fid=folder_id: self._on_folder_changed(fid))
        
            if folder_id == "INBOX":
                btn.setChecked(True)
        
            self.folder_btn_group.addButton(btn)
            sidebar_layout.addWidget(btn)
    
        sidebar_layout.addSpacing(20)
    
    # === SECTION CATÉGORIES ===
        categories_label = QLabel("🏷️ CATÉGORIES")
        categories_label.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        categories_label.setStyleSheet("color: #000000; padding: 5px;")  # CORRECTION: Noir
        sidebar_layout.addWidget(categories_label)
    
    # IMPORTANT: Créer le groupe AVANT de l'utiliser
        self.category_btn_group = QButtonGroup(self)
        self.category_btn_group.setExclusive(True)
    
        categories = [
            ("📋 Tous", "Tous"),
            ("📄 CV/Candidatures", "cv"),
            ("📅 Rendez-vous", "rdv"),
            ("🧾 Factures", "facture"),
            ("🛠️ Support", "support"),
            ("🤝 Partenariat", "partenariat"),
            ("🛡️ Spam", "spam"),
            ("📰 Newsletter", "newsletter")
        ]
    
        for label, category in categories:
            btn = QPushButton(label)
            btn.setObjectName("sidebar-btn")
            btn.setCheckable(True)
            btn.setProperty("category", category)
            btn.clicked.connect(lambda checked, cat=category: self._on_category_changed(cat))
        
            if category == "Tous":
                btn.setChecked(True)
        
            self.category_btn_group.addButton(btn)
            sidebar_layout.addWidget(btn)
    
        sidebar_layout.addStretch()
    
    # Bouton rafraîchir
        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.setObjectName("refresh-btn")
        refresh_btn.clicked.connect(self.refresh_emails)
        sidebar_layout.addWidget(refresh_btn)
    
        return sidebar
    def _on_folder_changed(self, folder: str):
        """Appelé quand le dossier change - CORRIGÉ."""
        if self.current_folder == folder:
            return
    
        logger.info(f"Changement de dossier: {self.current_folder} -> {folder}")
        self.current_folder = folder
        self.current_category = "Tous"
    
    # Reset catégorie à "Tous"
        if hasattr(self, 'category_btn_group'):
            for btn in self.category_btn_group.buttons():
                if btn.property("category") == "Tous":
                    btn.setChecked(True)
                    break
    
        self.refresh_emails()

    def _on_category_changed(self, category: str):
        """Appelé quand la catégorie change - CORRIGÉ."""
        if self.current_category == category:
            return
    
        logger.info(f"Changement de catégorie: {self.current_category} -> {category}")
        self.current_category = category
        self._filter_and_display_emails()

    def _create_header(self):
        """Crée l'en-tête avec titre et filtres."""
        header = QFrame()
        header.setObjectName("inbox-header")
        header.setFixedHeight(80)
    
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
    
    # Colonne gauche: Titre + Compteur
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)
    
        self.title_label = QLabel("📧 Boîte de réception")
        self.title_label.setObjectName("inbox-title")
        self.title_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #000000;")
        left_layout.addWidget(self.title_label)
    
        self.count_label = QLabel("0 emails")
        self.count_label.setObjectName("inbox-count")
        self.count_label.setFont(QFont("Inter", 12))
        self.count_label.setStyleSheet("color: #6c757d;")
        left_layout.addWidget(self.count_label)
    
        layout.addLayout(left_layout)
        layout.addStretch()
    
    # Filtre de tri
        sort_label = QLabel("Trier par:")
        sort_label.setFont(QFont("Inter", 12))
        sort_label.setStyleSheet("color: #000000;")
        layout.addWidget(sort_label)
    
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("filter-combo")
        self.sort_combo.addItems([
            "📅 Plus récent",
            "📅 Plus ancien",
            "⚠️ Priorité haute",
            "👤 Expéditeur A-Z"
        ])
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        layout.addWidget(self.sort_combo)
    
        return header

    def _on_sort_changed(self, index: int):
        """Appelé quand le tri change."""
        sort_options = {
            0: 'date_desc',
            1: 'date_asc',
            2: 'priority',
            3: 'sender'
        }
        sort_type = sort_options.get(index, 'date_desc')
        logger.info(f"Tri changé: {sort_type}")
        self._filter_and_display_emails()

    def _display_emails(self, emails: List[Email]):
        """Affiche la liste des emails."""
        try:
        # Vider le container
            while self.emails_layout.count() > 1:  # Garder le stretch
                item = self.emails_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
            if not emails:
            # Afficher message vide
                empty_label = QLabel("📭 Aucun email dans cette catégorie")
                empty_label.setObjectName("empty-label")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setFont(QFont("Inter", 14))
                empty_label.setStyleSheet("color: #6c757d; padding: 40px;")
                self.emails_layout.insertWidget(0, empty_label)
                return
        
        # Créer les cartes
            for email in emails:
                card = SmartEmailCard(email)
                card.clicked.connect(self._on_email_clicked)
                self.emails_layout.insertWidget(self.emails_layout.count() - 1, card)
        
            logger.info(f"{len(emails)} cartes emails créées")
        
        except Exception as e:
            logger.error(f"Erreur affichage emails: {e}")

    def _on_email_clicked(self, email: Email):
        """Appelé quand un email est cliqué."""
        self.selected_email = email
        self.email_selected.emit(email)
        logger.info(f"Email sélectionné: {email.subject}")