#!/usr/bin/env python3
"""
Vue Smart Inbox ORIGINALE CORRIGÉE - Juste le signal fixé.
"""
import logging
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLabel, QPushButton, QFrame, QButtonGroup, QSplitter, QTextEdit
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
    """Thread pour charger et analyser les emails avec l'IA."""
    
    emails_loaded = pyqtSignal(list)
    analysis_complete = pyqtSignal()
    progress_updated = pyqtSignal(int, int)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.should_stop = False
        self.emails_with_analysis = []
    
    def run(self):
        """Charge et analyse les emails."""
        try:
            emails = self.gmail_client.get_recent_emails(limit=20)
            self.emails_loaded.emit(emails)
            
            self.emails_with_analysis = []
            total_emails = len(emails)
            
            for i, email in enumerate(emails):
                if self.should_stop:
                    break
                
                analysis = self.ai_processor.process_email(email)
                email.ai_analysis = analysis
                self.emails_with_analysis.append(email)
                
                self.progress_updated.emit(i + 1, total_emails)
                self.msleep(100)
            
            self.analysis_complete.emit()
            logger.info(f"Analyse terminée pour {len(self.emails_with_analysis)} emails")
            
        except Exception as e:
            logger.error(f"Erreur EmailLoaderThread: {e}")
    
    def stop(self):
        """Arrête le thread."""
        self.should_stop = True


class CategoryFilter(QPushButton):
    """Bouton de filtre PARFAITEMENT ALIGNÉ."""
    
    def __init__(self, name: str, category: str, count: int = 0):
        super().__init__(f"{name} ({count})")
        self.category = category
        self.count = count
        self.is_active = False
        self.original_name = name
        
        self.setCheckable(True)
        self.setFixedHeight(38)
        self.setMinimumWidth(90)
        self._apply_style()
    
    def update_count(self, count: int):
        """Met à jour le compteur."""
        self.count = count
        self.setText(f"{self.original_name} ({count})")
    
    def set_active(self, active: bool):
        """Active/désactive le filtre."""
        self.is_active = active
        self.setChecked(active)
        
        if active:
            self.setStyleSheet("""
                CategoryFilter {
                    background-color: #1976d2;
                    color: #ffffff;
                    border: 3px solid #1565c0;
                    border-radius: 19px;
                    font-weight: 700;
                    padding: 8px 16px;
                }
            """)
        else:
            self._apply_style()
    
    def _apply_style(self):
        """Applique le style par défaut."""
        self.setStyleSheet("""
            CategoryFilter {
                background-color: #ffffff;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 19px;
                font-weight: 600;
                padding: 8px 16px;
            }
            
            CategoryFilter:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
        """)


class SmartInboxView(QWidget):
    """Vue Smart Inbox ORIGINALE avec signal corrigé."""
    
    email_selected = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        
        self.all_emails = []
        self.filtered_emails = []
        self.email_cards = []
        self.current_filter = "all"
        self.selected_email = None
        self.is_loading = False
        
        self._setup_ui()
        self._setup_loader()
        
        # Auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_emails)
        self.refresh_timer.start(300000)
    
    def _setup_ui(self):
        """Configuration LAYOUT VERTICAL - Alignement parfait."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Filtres en haut - PARFAITEMENT ALIGNÉS
        filters_section = self._create_filters()
        layout.addWidget(filters_section)
        
        # Layout HORIZONTAL pour le contenu principal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(2)
        
        # === COLONNE GAUCHE: Liste emails ===
        email_list = self._create_email_list()
        main_splitter.addWidget(email_list)
        
        # === COLONNE DROITE: Vue détail email ===
        self.detail_view = EmailDetailView()
        self.detail_view.set_gmail_client(self.gmail_client)
        main_splitter.addWidget(self.detail_view)
        
        # Proportions: Liste (35%) - Détail (65%)
        main_splitter.setSizes([400, 700])
        layout.addWidget(main_splitter)
    
    def _create_filters(self) -> QWidget:
        """Crée les filtres PARFAITEMENT ALIGNÉS ET CENTRÉS."""
        filters_frame = QFrame()
        filters_frame.setObjectName("filters-frame")
        filters_frame.setFixedHeight(60)
        
        # Layout principal centré
        main_layout = QHBoxLayout(filters_frame)
        main_layout.setContentsMargins(20, 10, 20, 10)
        main_layout.setSpacing(0)
        
        # Spacer gauche pour centrer
        main_layout.addStretch(1)
        
        # Container des filtres avec espacement contrôlé
        filters_container = QHBoxLayout()
        filters_container.setSpacing(12)
        
        # Groupe de boutons
        self.filter_group = QButtonGroup()
        self.category_filters = {}
        
        # Définition des filtres avec émojis
        filter_definitions = [
            ("Tous", "all", "📧"),
            ("Urgent", "urgent", "🔥"),
            ("RDV", "rdv", "📅"),
            ("CV", "cv", "📄"),
            ("Spam", "spam", "🚫"),
            ("Pièces J.", "attachments", "📎")
        ]
        
        # Créer les boutons de filtre
        for name, category, emoji in filter_definitions:
            filter_btn = CategoryFilter(f"{emoji} {name}", category, 0)
            filter_btn.clicked.connect(lambda checked, cat=category: self._on_filter_clicked(cat))
            
            self.filter_group.addButton(filter_btn)
            self.category_filters[category] = filter_btn
            filters_container.addWidget(filter_btn)
        
        # Activer "Tous" par défaut
        self.category_filters["all"].set_active(True)
        
        # Ajouter les filtres au layout principal
        main_layout.addLayout(filters_container)
        
        # Spacer droit pour centrer
        main_layout.addStretch(1)
        
        # Bouton actualiser à droite
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setObjectName("refresh-btn")
        refresh_btn.setFixedHeight(38)
        refresh_btn.clicked.connect(self.refresh_emails)
        main_layout.addWidget(refresh_btn)
        
        # Styles
        filters_frame.setStyleSheet("""
            QFrame#filters-frame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border-bottom: 3px solid #1976d2;
            }
            
            QPushButton#refresh-btn {
                background-color: #4caf50;
                color: #ffffff;
                border: none;
                border-radius: 19px;
                font-weight: 700;
                font-size: 12px;
                padding: 8px 16px;
                min-width: 100px;
            }
            
            QPushButton#refresh-btn:hover {
                background-color: #45a049;
            }
            
            QPushButton#refresh-btn:pressed {
                background-color: #388e3c;
            }
        """)
        
        return filters_frame
    
    def _create_email_list(self) -> QWidget:
        """Crée la liste des emails avec scroll."""
        # Widget conteneur
        list_widget = QWidget()
        list_widget.setObjectName("email-list-widget")
        
        # Layout vertical pour la liste
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        
        # Zone de scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setObjectName("emails-scroll")
        
        # Widget de contenu scrollable
        scroll_content = QWidget()
        self.email_layout = QVBoxLayout(scroll_content)
        self.email_layout.setContentsMargins(10, 10, 10, 10)
        self.email_layout.setSpacing(8)
        self.email_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Messages de statut
        self.loading_label = QLabel("🔄 Chargement des emails...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setFont(QFont("Inter", 14, QFont.Weight.Medium))
        self.loading_label.setObjectName("loading-label")
        self.email_layout.addWidget(self.loading_label)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Inter", 12))
        self.progress_label.setObjectName("progress-label")
        self.progress_label.hide()
        self.email_layout.addWidget(self.progress_label)
        
        # Spacer pour pousser vers le haut
        self.email_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        list_layout.addWidget(scroll_area)
        
        # Styles
        list_widget.setStyleSheet("""
            QWidget#email-list-widget {
                background-color: #f8f9fa;
                border-right: 2px solid #dee2e6;
            }
            
            QScrollArea#emails-scroll {
                background-color: #ffffff;
                border: none;
            }
            
            QScrollArea#emails-scroll QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            
            QScrollArea#emails-scroll QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 5px;
                min-height: 20px;
                margin: 1px;
            }
            
            QScrollArea#emails-scroll QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
            
            QLabel#loading-label {
                color: #6c757d;
                padding: 40px;
                background-color: #ffffff;
                border-radius: 12px;
                border: 2px dashed #dee2e6;
                margin: 20px;
            }
            
            QLabel#progress-label {
                color: #007bff;
                padding: 10px;
                font-weight: 600;
            }
        """)
        
        return list_widget
    
    def _setup_loader(self):
        """Configure le thread de chargement."""
        self.email_loader = EmailLoaderThread(self.gmail_client, self.ai_processor)
        self.email_loader.emails_loaded.connect(self._on_emails_loaded)
        self.email_loader.analysis_complete.connect(self._on_analysis_complete)
        self.email_loader.progress_updated.connect(self._on_progress_updated)
    
    def refresh_emails(self):
        """Actualise les emails."""
        if self.is_loading or self.email_loader.isRunning():
            return
        
        self.is_loading = True
        
        # Afficher le chargement
        self._clear_email_list()
        self.loading_label.setText("🔄 Connexion à Gmail...")
        self.loading_label.show()
        self.progress_label.hide()
        
        # Réinitialiser le filtre
        self.current_filter = "all"
        for cat, btn in self.category_filters.items():
            btn.set_active(cat == "all")
        
        # Démarrer le chargement
        self.email_loader.start()
    
    def _on_emails_loaded(self, emails: List[Email]):
        """Gère la réception des emails."""
        self.all_emails = emails
        self.loading_label.setText("🤖 Analyse IA en cours...")
        self.progress_label.setText("Analyse IA: 0 / 0")
        self.progress_label.show()
        
        logger.info(f"{len(emails)} emails chargés, analyse en cours...")
    
    def _on_progress_updated(self, current: int, total: int):
        """Met à jour la progression."""
        self.progress_label.setText(f"🤖 Analyse IA: {current} / {total}")
    
    def _on_analysis_complete(self):
        """Fin de l'analyse IA."""
        self.all_emails = self.email_loader.emails_with_analysis
        
        # Cacher les messages
        self.loading_label.hide()
        self.progress_label.hide()
        
        # Créer les cartes
        self._create_email_cards()
        self._update_filter_counts()
        
        self.is_loading = False
        
        # Log des statistiques
        ai_suggestions_count = len([e for e in self.all_emails 
                                   if hasattr(e, 'ai_analysis') and e.ai_analysis and 
                                   getattr(e.ai_analysis, 'should_auto_respond', False)])
        
        attachments_count = len([e for e in self.all_emails if hasattr(e, 'attachments') and e.attachments])
        
        if ai_suggestions_count > 0:
            logger.info(f"🤖 {ai_suggestions_count} réponses IA disponibles")
        
        if attachments_count > 0:
            logger.info(f"📎 {attachments_count} emails avec pièces jointes")
        
        logger.info(f"Interface mise à jour avec {len(self.all_emails)} emails")
    
    def _create_email_cards(self):
        """Crée les cartes d'emails avec indicateur de pièces jointes."""
        self._clear_email_list()
        
        emails_to_show = self.filtered_emails if self.filtered_emails else self.all_emails
        
        if not emails_to_show:
            # Message si aucun email
            no_email_label = QLabel("📭 Aucun email à afficher")
            no_email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_email_label.setFont(QFont("Inter", 14, QFont.Weight.Medium))
            no_email_label.setStyleSheet("""
                QLabel {
                    color: #757575; 
                    padding: 40px;
                    background-color: #f5f5f5;
                    border-radius: 12px;
                    border: 2px dashed #bdbdbd;
                    margin: 20px 0;
                }
            """)
            self.email_layout.insertWidget(self.email_layout.count() - 1, no_email_label)
            return
        
        for email in emails_to_show:
            # Créer la carte avec analyse IA
            card = SmartEmailCard(email, getattr(email, 'ai_analysis', None))
            # CORRECTION: Utiliser le signal 'clicked' qui existe dans SmartEmailCard
            card.clicked.connect(self._on_email_card_clicked)
            
            self.email_cards.append(card)
            self.email_layout.insertWidget(self.email_layout.count() - 1, card)
        
        logger.info(f"Créé {len(self.email_cards)} cartes")
    
    def _clear_email_list(self):
        """Vide la liste des emails."""
        for card in self.email_cards:
            card.setParent(None)
            card.deleteLater()
        self.email_cards.clear()
        
        # Nettoyer les autres widgets sauf les labels de statut
        for i in reversed(range(self.email_layout.count() - 1)):
            item = self.email_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget not in [self.loading_label, self.progress_label]:
                    widget.setParent(None)
                    widget.deleteLater()
    
    def _on_filter_clicked(self, category: str):
        """Gère le clic sur un filtre."""
        # Désactiver tous les filtres
        for cat, btn in self.category_filters.items():
            btn.set_active(cat == category)
        
        self.current_filter = category
        self._apply_filter(category)
        
        logger.info(f"Filtre appliqué: {category}")
    
    def _apply_filter(self, category: str):
        """Applique un filtre."""
        if category == "all":
            self.filtered_emails = []  # Vide = afficher tous
        else:
            self.filtered_emails = []
            
            for email in self.all_emails:
                should_include = False
                
                if category == "attachments":
                    should_include = hasattr(email, 'attachments') and email.attachments
                elif hasattr(email, 'ai_analysis') and email.ai_analysis:
                    email_category = getattr(email.ai_analysis, 'category', '').lower()
                    
                    if category == "urgent" and ('urgent' in email_category or 'important' in email_category):
                        should_include = True
                    elif category == "rdv" and ('rdv' in email_category or 'meeting' in email_category or 'rendez' in email_category):
                        should_include = True
                    elif category == "cv" and ('cv' in email_category or 'candidature' in email_category):
                        should_include = True
                    elif category == "spam" and 'spam' in email_category:
                        should_include = True
                
                if should_include:
                    self.filtered_emails.append(email)
        
        # Recréer les cartes avec le filtre appliqué
        self._create_email_cards()
    
    def _update_filter_counts(self):
        """Met à jour les compteurs des filtres."""
        counts = {
            "all": len(self.all_emails),
            "urgent": 0,
            "rdv": 0,
            "cv": 0,
            "spam": 0,
            "attachments": 0
        }
        
        for email in self.all_emails:
            # Compter les pièces jointes
            if hasattr(email, 'attachments') and email.attachments:
                counts["attachments"] += 1
            
            # Compter les catégories IA
            if hasattr(email, 'ai_analysis') and email.ai_analysis:
                category = getattr(email.ai_analysis, 'category', '').lower()
                
                if 'urgent' in category or 'important' in category:
                    counts["urgent"] += 1
                elif 'rdv' in category or 'meeting' in category or 'rendez' in category:
                    counts["rdv"] += 1
                elif 'cv' in category or 'candidature' in category:
                    counts["cv"] += 1
                elif 'spam' in category:
                    counts["spam"] += 1
        
        # Mettre à jour les boutons
        for category, count in counts.items():
            if category in self.category_filters:
                self.category_filters[category].update_count(count)
    
    def _on_email_card_clicked(self, email: Email):
        """CORRECTION: Gère le clic sur une carte d'email."""
        # Désélectionner toutes les cartes
        for card in self.email_cards:
            if hasattr(card, 'set_selected'):
                card.set_selected(False)
        
        # Sélectionner la carte cliquée
        for card in self.email_cards:
            if card.email.id == email.id:
                if hasattr(card, 'set_selected'):
                    card.set_selected(True)
                break
        
        # Afficher les détails
        self.detail_view.show_email(email)
        self.selected_email = email
        
        # Marquer comme lu
        if not email.is_read:
            email.is_read = True
            # TODO: Marquer comme lu via Gmail API
        
        # Émettre le signal
        self.email_selected.emit(email)
        
        # Log
        attachment_info = f" (📎 {len(email.attachments)} PJ)" if hasattr(email, 'attachments') and email.attachments else ""
        logger.info(f"Email sélectionné: {email.id}{attachment_info}")
    
    def get_selected_email(self) -> Optional[Email]:
        """Retourne l'email sélectionné."""
        return self.selected_email
    
    def get_email_count(self) -> int:
        """Retourne le nombre d'emails."""
        return len(self.all_emails)