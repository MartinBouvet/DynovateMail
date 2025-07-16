#!/usr/bin/env python3
"""
Vue Smart Inbox avec tri intelligent et filtres IA.
"""
import logging
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLabel, QPushButton, QFrame, QButtonGroup, QSplitter
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
    """Thread pour charger les emails en arrière-plan."""
    
    emails_loaded = pyqtSignal(list)
    email_processed = pyqtSignal(object, object)  # email, ai_analysis
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.should_stop = False
    
    def run(self):
        """Charge et traite les emails."""
        try:
            # Charger les emails récents
            emails = self.gmail_client.get_recent_emails(limit=50)
            self.emails_loaded.emit(emails)
            
            # Traiter chaque email avec l'IA
            for email in emails:
                if self.should_stop:
                    break
                
                analysis = self.ai_processor.process_email(email)
                self.email_processed.emit(email, analysis)
                
                # Petite pause pour éviter la surcharge
                self.msleep(100)
                
        except Exception as e:
            logger.error(f"Erreur chargement emails: {e}")
    
    def stop(self):
        """Arrête le thread."""
        self.should_stop = True

class CategoryFilter(QPushButton):
    """Bouton de filtre par catégorie."""
    
    def __init__(self, name: str, category: str, count: int = 0):
        super().__init__(f"{name} ({count})")
        self.category = category
        self.count = count
        self.is_active = False
        
        self.setCheckable(True)
        self.setFixedHeight(36)
        self._apply_style()
    
    def update_count(self, count: int):
        """Met à jour le compteur."""
        self.count = count
        name = self.text().split(' (')[0]
        self.setText(f"{name} ({count})")
    
    def set_active(self, active: bool):
        """Active/désactive le filtre."""
        self.is_active = active
        self.setChecked(active)
        self._apply_style()
    
    def _apply_style(self):
        """Applique le style au bouton."""
        if self.is_active:
            style = """
                QPushButton {
                    background-color: #000000;
                    color: #ffffff;
                    border: none;
                    border-radius: 18px;
                    font-weight: 600;
                    padding: 8px 16px;
                }
            """
        else:
            style = """
                QPushButton {
                    background-color: #f8f9fa;
                    color: #495057;
                    border: 1px solid #dee2e6;
                    border-radius: 18px;
                    font-weight: 500;
                    padding: 8px 16px;
                }
                
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #adb5bd;
                }
            """
        
        self.setStyleSheet(style)

class SmartInboxView(QWidget):
    """Vue Smart Inbox avec tri intelligent et actions IA."""
    
    email_selected = pyqtSignal(object)
    ai_suggestion_requested = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        
        self.all_emails = []
        self.filtered_emails = []
        self.email_cards = []
        self.current_filter = "all"
        self.selected_email = None
        
        self._setup_ui()
        self._setup_loader()
        
        # Auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_emails)
        self.refresh_timer.start(300000)  # 5 minutes
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Filtres par catégorie
        filters_section = self._create_filters()
        layout.addWidget(filters_section)
        
        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Liste des emails
        email_list = self._create_email_list()
        splitter.addWidget(email_list)
        
        # Vue détail
        self.detail_view = EmailDetailView()
        self.detail_view.action_requested.connect(self._handle_email_action)
        splitter.addWidget(self.detail_view)
        
        # Proportions du splitter
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
    
    def _create_filters(self) -> QWidget:
        """Crée la section des filtres."""
        filters_frame = QFrame()
        filters_frame.setObjectName("filters-section")
        filters_frame.setFixedHeight(70)
        
        layout = QHBoxLayout(filters_frame)
        layout.setContentsMargins(0, 15, 0, 15)
        layout.setSpacing(12)
        
        # Groupe de boutons pour exclusivité
        self.filter_group = QButtonGroup()
        
        # Filtres disponibles
        filters_data = [
            ("Tous", "all", 0),
            ("Urgent", "urgent", 0),
            ("CV", "cv", 0),
            ("RDV", "rdv", 0),
            ("Support", "support", 0),
            ("Factures", "facture", 0)
        ]
        
        self.category_filters = {}
        
        for name, category, count in filters_data:
            filter_btn = CategoryFilter(name, category, count)
            filter_btn.clicked.connect(lambda checked, cat=category: self._apply_filter(cat))
            
            self.filter_group.addButton(filter_btn)
            self.category_filters[category] = filter_btn
            layout.addWidget(filter_btn)
            
            if category == "all":
                filter_btn.set_active(True)
        
        layout.addStretch()
        
        # Bouton de refresh
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self.refresh_emails)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 18px;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        layout.addWidget(refresh_btn)
        
        filters_frame.setStyleSheet("""
            #filters-section {
                background-color: #ffffff;
                border-bottom: 1px solid #e9ecef;
            }
        """)
        
        return filters_frame
    
    def _create_email_list(self) -> QWidget:
        """Crée la liste scrollable des emails."""
        container = QFrame()
        container.setObjectName("email-list-container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)
        
        # Zone de scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget contenant les cartes d'emails
        self.email_container = QWidget()
        self.email_layout = QVBoxLayout(self.email_container)
        self.email_layout.setSpacing(8)
        self.email_layout.setContentsMargins(0, 0, 0, 0)
        
        # Message de chargement
        self.loading_label = QLabel("🔄 Chargement des emails...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setFont(QFont("Inter", 14))
        self.email_layout.addWidget(self.loading_label)
        
        self.email_layout.addStretch()
        
        self.scroll_area.setWidget(self.email_container)
        layout.addWidget(self.scroll_area)
        
        container.setStyleSheet("""
            #email-list-container {
                background-color: #ffffff;
                border-right: 1px solid #e9ecef;
            }
        """)
        
        return container
    
    def _setup_loader(self):
        """Configure le loader d'emails."""
        self.email_loader = EmailLoaderThread(self.gmail_client, self.ai_processor)
        self.email_loader.emails_loaded.connect(self._on_emails_loaded)
        self.email_loader.email_processed.connect(self._on_email_processed)
    
    def refresh_emails(self):
        """Actualise la liste des emails."""
        if self.email_loader.isRunning():
            return
        
        # Afficher le chargement
        self._clear_email_list()
        self.loading_label.setText("🔄 Chargement des emails...")
        self.loading_label.show()
        
        # Démarrer le chargement
        self.email_loader.start()
    
    def _on_emails_loaded(self, emails: List[Email]):
        """Gère la réception des emails."""
        self.all_emails = emails
        self.loading_label.hide()
        
        # Créer les cartes d'emails (sans IA pour l'instant)
        self._create_email_cards()
        
        # Mettre à jour les compteurs de filtres
        self._update_filter_counts()
        
        logger.info(f"{len(emails)} emails chargés")
    
    def _on_email_processed(self, email: Email, ai_analysis):
        """Gère le traitement IA d'un email."""
        # Trouver la carte correspondante et mettre à jour avec l'IA
        for card in self.email_cards:
            if card.email.id == email.id:
                card.update_ai_analysis(ai_analysis)
                break
        
        # Mettre à jour les compteurs
        self._update_filter_counts()
    
    def _create_email_cards(self):
        """Crée les cartes pour tous les emails."""
        self._clear_email_list()
        
        for email in self.filtered_emails or self.all_emails:
            card = SmartEmailCard(email)
            card.clicked.connect(self._on_email_card_clicked)
            card.action_requested.connect(self._handle_email_action)
            
            self.email_cards.append(card)
            self.email_layout.insertWidget(self.email_layout.count() - 1, card)
    
    def _clear_email_list(self):
        """Vide la liste des emails."""
        for card in self.email_cards:
            card.setParent(None)
        self.email_cards.clear()
    
    def _apply_filter(self, category: str):
        """Applique un filtre par catégorie."""
        self.current_filter = category
        
        # Mettre à jour l'apparence des filtres
        for cat, filter_btn in self.category_filters.items():
            filter_btn.set_active(cat == category)
        
        # Filtrer les emails
        if category == "all":
            self.filtered_emails = self.all_emails
        elif category == "urgent":
            self.filtered_emails = [e for e in self.all_emails 
                                   if hasattr(e, 'ai_analysis') and e.ai_analysis and e.ai_analysis.priority <= 2]
        else:
            self.filtered_emails = [e for e in self.all_emails 
                                   if hasattr(e, 'ai_analysis') and e.ai_analysis and e.ai_analysis.category == category]
        
        # Recréer les cartes
        self._create_email_cards()
        
        logger.info(f"Filtre appliqué: {category}, {len(self.filtered_emails)} emails")
    
    def _update_filter_counts(self):
        """Met à jour les compteurs des filtres."""
        counts = {
            "all": len(self.all_emails),
            "urgent": 0,
            "cv": 0,
            "rdv": 0,
            "support": 0,
            "facture": 0
        }
        
        for email in self.all_emails:
            if hasattr(email, 'ai_analysis') and email.ai_analysis:
                analysis = email.ai_analysis
                
                # Compteur urgent
                if analysis.priority <= 2:
                    counts["urgent"] += 1
                
                # Compteurs par catégorie
                if analysis.category in counts:
                    counts[analysis.category] += 1
        
        # Mettre à jour les boutons
        for category, count in counts.items():
            if category in self.category_filters:
                self.category_filters[category].update_count(count)
    
    def _on_email_card_clicked(self, email: Email):
        """Gère le clic sur une carte d'email."""
        # Désélectionner toutes les cartes
        for card in self.email_cards:
            card.set_selected(False)
        
        # Sélectionner la carte cliquée
        for card in self.email_cards:
            if card.email.id == email.id:
                card.set_selected(True)
                break
        
        # Afficher les détails
        self.detail_view.show_email(email)
        self.selected_email = email
        
        # Marquer comme lu
        if not email.is_read:
            email.is_read = True
            # TODO: Synchroniser avec Gmail
        
        self.email_selected.emit(email)
    
    def _handle_email_action(self, action_type: str, email: Email):
        """Gère les actions sur les emails."""
        if action_type == "reply_cv":
            self._suggest_cv_reply(email)
        elif action_type == "add_to_calendar":
            self._add_to_calendar(email)
        elif action_type == "reply_meeting":
            self._suggest_meeting_reply(email)
        elif action_type == "reply_support":
            self._suggest_support_reply(email)
        elif action_type == "archive":
            self._archive_email(email)
        elif action_type == "mark_urgent":
            self._mark_urgent(email)
        
        logger.info(f"Action {action_type} sur email {email.id}")
    
    def _suggest_cv_reply(self, email: Email):
        """Suggère une réponse pour un CV."""
        if hasattr(email, 'ai_analysis') and email.ai_analysis.suggested_response:
            self.ai_suggestion_requested.emit(email)
    
    def _add_to_calendar(self, email: Email):
        """Ajoute un événement au calendrier."""
        # TODO: Implémenter l'ajout au calendrier
        pass
    
    def _suggest_meeting_reply(self, email: Email):
        """Suggère une réponse pour un RDV."""
        if hasattr(email, 'ai_analysis') and email.ai_analysis.suggested_response:
            self.ai_suggestion_requested.emit(email)
    
    def _suggest_support_reply(self, email: Email):
        """Suggère une réponse pour le support."""
        if hasattr(email, 'ai_analysis') and email.ai_analysis.suggested_response:
            self.ai_suggestion_requested.emit(email)
    
    def _archive_email(self, email: Email):
        """Archive un email."""
        # TODO: Implémenter l'archivage
        pass
    
    def _mark_urgent(self, email: Email):
        """Marque un email comme urgent."""
        if hasattr(email, 'ai_analysis') and email.ai_analysis:
            email.ai_analysis.priority = 1
            # Recréer la carte pour mettre à jour l'affichage
            self._create_email_cards()
    
    def filter_emails(self, search_text: str):
        """Filtre les emails par texte de recherche."""
        if not search_text:
            self.filtered_emails = self.all_emails
        else:
            search_lower = search_text.lower()
            self.filtered_emails = [
                email for email in self.all_emails
                if (search_lower in (email.subject or '').lower() or
                    search_lower in (email.body or '').lower() or
                    search_lower in (email.sender or '').lower())
            ]
        
        self._create_email_cards()
    
    def clear_filter(self):
        """Supprime le filtre de recherche."""
        self.filtered_emails = self.all_emails
        self._create_email_cards()