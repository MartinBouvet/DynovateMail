#!/usr/bin/env python3
"""
Vue Smart Inbox CORRIGÉE avec navigation Archives/Supprimés.
"""
import logging
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QLabel, QPushButton, QFrame, QButtonGroup, QSplitter, QTextEdit, QComboBox
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
    """Thread pour charger et analyser les emails réels."""
    
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
        """Charge et analyse les emails réels."""
        try:
            # Charger selon le dossier
            if self.current_folder == "INBOX":
                emails = self.gmail_client.get_inbox_emails(limit=30)
            elif self.current_folder == "SENT":
                emails = self.gmail_client.get_sent_emails(limit=30)
            elif self.current_folder == "ARCHIVED":
                emails = self.gmail_client.get_archived_emails(limit=30)
            elif self.current_folder == "TRASH":
                emails = self.gmail_client.get_trash_emails(limit=30)
            elif self.current_folder == "SPAM":
                emails = self.gmail_client.get_spam_emails(limit=30)
            else:
                emails = self.gmail_client.get_inbox_emails(limit=30)
            
            self.emails_loaded.emit(emails)
            
            self.emails_with_analysis = []
            total_emails = len(emails)
            
            # Analyser avec l'IA seulement pour INBOX
            if self.current_folder == "INBOX":
                for i, email in enumerate(emails):
                    if self.should_stop:
                        break
                    
                    analysis = self.ai_processor.process_email(email)
                    email.ai_analysis = analysis
                    self.emails_with_analysis.append(email)
                    
                    self.progress_updated.emit(i + 1, total_emails)
                    self.msleep(100)
            else:
                # Pas d'analyse IA pour les autres dossiers
                self.emails_with_analysis = emails
                self.progress_updated.emit(total_emails, total_emails)
            
            self.analysis_complete.emit()
            logger.info(f"Chargement terminé pour {self.current_folder}: {len(self.emails_with_analysis)} emails")
            
        except Exception as e:
            logger.error(f"Erreur EmailLoaderThread: {e}")
    
    def stop(self):
        """Arrête le thread."""
        self.should_stop = True


class CategoryFilter(QPushButton):
    """Bouton de filtre."""
    
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
    """Vue Smart Inbox avec NAVIGATION COMPLÈTE."""
    
    email_selected = pyqtSignal(object)
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        
        self.all_emails = []
        self.filtered_emails = []
        self.email_cards = []
        self.current_filter = "all"
        self.current_folder = "INBOX"
        self.selected_email = None
        self.is_loading = False
        
        self._setup_ui()
        self._setup_loader()
        
        # Auto-refresh seulement pour INBOX
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(300000)  # 5 minutes
    
    def _setup_ui(self):
        """Configuration interface avec navigation."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Navigation dossiers + Filtres
        navigation_section = self._create_navigation()
        layout.addWidget(navigation_section)
        
        # Layout horizontal pour le contenu principal
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
    
    def _create_navigation(self) -> QWidget:
        """Crée la navigation COMPLÈTE avec dossiers."""
        nav_frame = QFrame()
        nav_frame.setObjectName("navigation-frame")
        nav_frame.setFixedHeight(100)
        
        layout = QVBoxLayout(nav_frame)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        
        # === LIGNE 1: NAVIGATION DOSSIERS ===
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(15)
        
        # Label
        folder_label = QLabel("Dossier:")
        folder_label.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        folder_label.setStyleSheet("color: #1a1a1a;")
        folder_layout.addWidget(folder_label)
        
        # Sélecteur de dossier
        self.folder_selector = QComboBox()
        self.folder_selector.addItems([
            "Boîte de réception",
            "Envoyés", 
            "Archivés",
            "Supprimés",
            "Spam"
        ])
        self.folder_selector.setMinimumWidth(200)
        self.folder_selector.setFixedHeight(35)
        self.folder_selector.currentTextChanged.connect(self._on_folder_changed)
        folder_layout.addWidget(self.folder_selector)
        
        folder_layout.addStretch()
        
        # Bouton actualiser
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.setObjectName("refresh-btn")
        refresh_btn.setFixedHeight(35)
        refresh_btn.setMinimumWidth(120)
        refresh_btn.clicked.connect(self.refresh_emails)
        folder_layout.addWidget(refresh_btn)
        
        layout.addLayout(folder_layout)
        
        # === LIGNE 2: FILTRES CATÉGORIES (seulement pour INBOX) ===
        self.filters_container = QHBoxLayout()
        self.filters_container.setSpacing(12)
        
        # Label filtres
        filter_label = QLabel("Filtres:")
        filter_label.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        filter_label.setStyleSheet("color: #1a1a1a;")
        self.filters_container.addWidget(filter_label)
        
        # Groupe de boutons filtres
        self.filter_group = QButtonGroup()
        self.category_filters = {}
        
        filter_definitions = [
            ("Tous", "all", ""),
            ("Urgent", "urgent", ""),
            ("RDV", "rdv", ""),
            ("CV", "cv", ""),
            ("Spam", "spam", ""),
            ("Pièces J.", "attachments", "")
        ]
        
        for name, category, emoji in filter_definitions:
            filter_btn = CategoryFilter(f"{name}", category, 0)
            filter_btn.clicked.connect(lambda checked, cat=category: self._on_filter_clicked(cat))
            
            self.filter_group.addButton(filter_btn)
            self.category_filters[category] = filter_btn
            self.filters_container.addWidget(filter_btn)
        
        self.category_filters["all"].set_active(True)
        
        self.filters_container.addStretch()
        
        layout.addLayout(self.filters_container)
        
        # Styles
        nav_frame.setStyleSheet("""
            QFrame#navigation-frame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border-bottom: 3px solid #1976d2;
            }
            
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #1976d2;
                border-radius: 8px;
                padding: 8px 12px;
                color: #1a1a1a;
                font-weight: 600;
                font-size: 13px;
            }
            
            QComboBox:focus {
                border-color: #1565c0;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #1976d2;
            }
            
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #1976d2;
                border-radius: 8px;
                selection-background-color: #e3f2fd;
                selection-color: #1a1a1a;
                padding: 4px;
            }
            
            QPushButton#refresh-btn {
                background-color: #4caf50;
                color: #ffffff;
                border: none;
                border-radius: 17px;
                font-weight: 700;
                font-size: 12px;
                padding: 8px 16px;
            }
            
            QPushButton#refresh-btn:hover {
                background-color: #45a049;
            }
            
            QPushButton#refresh-btn:pressed {
                background-color: #388e3c;
            }
        """)
        
        return nav_frame
    
    def _create_email_list(self) -> QWidget:
        """Crée la liste des emails."""
        list_widget = QWidget()
        list_widget.setObjectName("email-list-widget")
        
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setObjectName("emails-scroll")
        
        scroll_content = QWidget()
        self.email_layout = QVBoxLayout(scroll_content)
        self.email_layout.setContentsMargins(10, 10, 10, 10)
        self.email_layout.setSpacing(8)
        self.email_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Messages de statut
        self.loading_label = QLabel("Chargement des emails...")
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
        
        self.email_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        list_layout.addWidget(scroll_area)
        
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
    
    def _on_folder_changed(self, folder_text: str):
        """Gère le changement de dossier."""
        # Mapping des textes vers les codes
        folder_mapping = {
            "Boîte de réception": "INBOX",
            "Envoyés": "SENT", 
            "Archivés": "ARCHIVED",
            "Supprimés": "TRASH",
            "Spam": "SPAM"
        }
        
        new_folder = folder_mapping.get(folder_text, "INBOX")
        
        if new_folder != self.current_folder:
            self.current_folder = new_folder
            
            # Masquer/afficher les filtres selon le dossier
            if new_folder == "INBOX":
                self._show_filters(True)
            else:
                self._show_filters(False)
            
            # Charger les emails du nouveau dossier
            self.refresh_emails()
            
            logger.info(f"Changement vers dossier: {new_folder}")
    
    def _show_filters(self, show: bool):
        """Affiche ou masque les filtres."""
        for i in range(self.filters_container.count()):
            item = self.filters_container.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(show)
        
        if not show:
            # Réinitialiser le filtre à "all"
            self.current_filter = "all"
            for cat, btn in self.category_filters.items():
                btn.set_active(cat == "all")
    
    def refresh_emails(self):
        """Actualise les emails selon le dossier actuel."""
        if self.is_loading or self.email_loader.isRunning():
            return
        
        self.is_loading = True
        
        # Afficher le chargement
        self._clear_email_list()
        folder_names = {
            "INBOX": "boîte de réception",
            "SENT": "emails envoyés", 
            "ARCHIVED": "emails archivés",
            "TRASH": "emails supprimés",
            "SPAM": "emails spam"
        }
        folder_name = folder_names.get(self.current_folder, "emails")
        
        self.loading_label.setText(f"Chargement des {folder_name}...")
        self.loading_label.show()
        self.progress_label.hide()
        
        # Réinitialiser le filtre
        self.current_filter = "all"
        for cat, btn in self.category_filters.items():
            btn.set_active(cat == "all")
        
        # Configurer le dossier et démarrer le chargement
        self.email_loader.set_folder(self.current_folder)
        self.email_loader.start()
    
    def _auto_refresh(self):
        """Auto-refresh seulement pour INBOX."""
        if not self.is_loading and self.current_folder == "INBOX":
            self.refresh_emails()
    
    def _on_emails_loaded(self, emails: List[Email]):
        """Gère la réception des emails."""
        self.all_emails = emails
        
        if self.current_folder == "INBOX":
            self.loading_label.setText("Analyse IA en cours...")
            self.progress_label.setText("Analyse IA: 0 / 0")
            self.progress_label.show()
        else:
            # Pas d'analyse IA pour les autres dossiers
            self.loading_label.setText("Organisation des emails...")
        
        logger.info(f"{len(emails)} emails chargés depuis {self.current_folder}")
    
    def _on_progress_updated(self, current: int, total: int):
        """Met à jour la progression."""
        if self.current_folder == "INBOX":
            self.progress_label.setText(f"Analyse IA: {current} / {total}")
        else:
            self.progress_label.setText(f"Traitement: {current} / {total}")
    
    def _on_analysis_complete(self):
        """Fin de l'analyse."""
        self.all_emails = self.email_loader.emails_with_analysis
        
        self.loading_label.hide()
        self.progress_label.hide()
        
        self._create_email_cards()
        
        # Mettre à jour les compteurs seulement pour INBOX
        if self.current_folder == "INBOX":
            self._update_filter_counts()
        
        self.is_loading = False
        
        # Log des statistiques
        if self.current_folder == "INBOX":
            ai_suggestions_count = len([e for e in self.all_emails 
                                       if hasattr(e, 'ai_analysis') and e.ai_analysis and 
                                       getattr(e.ai_analysis, 'should_auto_respond', False)])
            
            if ai_suggestions_count > 0:
                logger.info(f"{ai_suggestions_count} réponses IA disponibles")
        
        attachments_count = len([e for e in self.all_emails if hasattr(e, 'attachments') and e.attachments])
        
        if attachments_count > 0:
            logger.info(f"{attachments_count} emails avec pièces jointes")
        
        logger.info(f"Interface mise à jour avec {len(self.all_emails)} emails ({self.current_folder})")
    
    def _create_email_cards(self):
        """Crée les cartes d'emails."""
        self._clear_email_list()
        
        emails_to_show = self.filtered_emails if self.filtered_emails else self.all_emails
        
        if not emails_to_show:
            folder_messages = {
                "INBOX": "Aucun email dans la boîte de réception",
                "SENT": "Aucun email envoyé",
                "ARCHIVED": "Aucun email archivé", 
                "TRASH": "Aucun email dans la corbeille",
                "SPAM": "Aucun email spam"
            }
            
            no_email_label = QLabel(folder_messages.get(self.current_folder, "Aucun email"))
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
            # Utiliser l'analyse IA seulement pour INBOX
            ai_analysis = getattr(email, 'ai_analysis', None) if self.current_folder == "INBOX" else None
            card = SmartEmailCard(email, ai_analysis)
            card.clicked.connect(self._on_email_card_clicked)
            
            self.email_cards.append(card)
            self.email_layout.insertWidget(self.email_layout.count() - 1, card)
        
        logger.info(f"Créé {len(self.email_cards)} cartes pour {self.current_folder}")
    
    def _clear_email_list(self):
        """Vide la liste des emails."""
        for card in self.email_cards:
            card.setParent(None)
            card.deleteLater()
        self.email_cards.clear()
        
        for i in reversed(range(self.email_layout.count() - 1)):
            item = self.email_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget not in [self.loading_label, self.progress_label]:
                    widget.setParent(None)
                    widget.deleteLater()
    
    def _on_filter_clicked(self, category: str):
        """Gère le clic sur un filtre (seulement INBOX)."""
        if self.current_folder != "INBOX":
            return
        
        for cat, btn in self.category_filters.items():
            btn.set_active(cat == category)
        
        self.current_filter = category
        self._apply_filter(category)
        
        logger.info(f"Filtre appliqué: {category}")
    
    def _apply_filter(self, category: str):
        """Applique un filtre (seulement INBOX)."""
        if self.current_folder != "INBOX":
            return
        
        if category == "all":
            self.filtered_emails = []
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
        
        self._create_email_cards()
    
    def _update_filter_counts(self):
        """Met à jour les compteurs des filtres (seulement INBOX)."""
        if self.current_folder != "INBOX":
            return
        
        counts = {
            "all": len(self.all_emails),
            "urgent": 0,
            "rdv": 0,
            "cv": 0,
            "spam": 0,
            "attachments": 0
        }
        
        for email in self.all_emails:
            if hasattr(email, 'attachments') and email.attachments:
                counts["attachments"] += 1
            
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
        
        for category, count in counts.items():
            if category in self.category_filters:
                self.category_filters[category].update_count(count)
    
    def _on_email_card_clicked(self, email: Email):
        """Gère le clic sur une carte d'email."""
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
        
        # Marquer comme lu (seulement pour INBOX)
        if not email.is_read and self.current_folder == "INBOX":
            if self.gmail_client.mark_as_read(email.id):
                email.is_read = True
        
        # Émettre le signal
        self.email_selected.emit(email)
        
        attachment_info = f" ({len(email.attachments)} PJ)" if hasattr(email, 'attachments') and email.attachments else ""
        logger.info(f"Email sélectionné: {email.id}{attachment_info} ({self.current_folder})")
    
    def filter_emails(self, search_text: str):
        """Filtre les emails selon un texte de recherche."""
        try:
            if not search_text or len(search_text) < 2:
                self.clear_filter()
                return
            
            search_lower = search_text.lower()
            filtered = []
            
            for email in self.all_emails:
                if (search_lower in (email.subject or "").lower() or
                    search_lower in (email.sender or "").lower() or
                    search_lower in (email.body or "").lower() or
                    search_lower in (email.snippet or "").lower()):
                    filtered.append(email)
            
            self.filtered_emails = filtered
            self._create_email_cards()
            
            logger.info(f"Recherche '{search_text}' dans {self.current_folder}: {len(filtered)} résultats")
            
        except Exception as e:
            logger.error(f"Erreur filtre emails: {e}")
    
    def clear_filter(self):
        """Supprime le filtre de recherche."""
        try:
            if self.current_folder == "INBOX":
                self._apply_filter(self.current_filter)
            else:
                self.filtered_emails = []
                self._create_email_cards()
            logger.info("Filtre de recherche supprimé")
        except Exception as e:
            logger.error(f"Erreur suppression filtre: {e}")
    
    def get_selected_email(self) -> Optional[Email]:
        """Retourne l'email sélectionné."""
        return self.selected_email
    
    def get_email_count(self) -> int:
        """Retourne le nombre d'emails."""
        return len(self.all_emails)
    
    def get_current_folder(self) -> str:
        """Retourne le dossier actuel."""
        return self.current_folder