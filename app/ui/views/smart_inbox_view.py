#!/usr/bin/env python3
"""
Vue Smart Inbox avec tri intelligent et filtres IA fonctionnels.
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
    """Thread pour charger et analyser les emails avec l'IA."""
    
    emails_loaded = pyqtSignal(list)
    analysis_complete = pyqtSignal()
    progress_updated = pyqtSignal(int, int)  # current, total
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor):
        super().__init__()
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.should_stop = False
        self.emails_with_analysis = []
    
    def run(self):
        """Charge et analyse les emails."""
        try:
            # Charger les emails
            emails = self.gmail_client.get_recent_emails(limit=50)
            self.emails_loaded.emit(emails)
            
            # Analyser chaque email avec l'IA
            self.emails_with_analysis = []
            total_emails = len(emails)
            
            for i, email in enumerate(emails):
                if self.should_stop:
                    break
                
                # Analyser avec l'IA
                analysis = self.ai_processor.process_email(email)
                email.ai_analysis = analysis
                self.emails_with_analysis.append(email)
                
                # Émettre le progrès
                self.progress_updated.emit(i + 1, total_emails)
                
                # Petite pause pour ne pas surcharger
                self.msleep(50)
            
            self.analysis_complete.emit()
            logger.info(f"Analyse IA terminée pour {len(self.emails_with_analysis)} emails")
            
        except Exception as e:
            logger.error(f"Erreur dans EmailLoaderThread: {e}")
    
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
    """Vue Smart Inbox avec IA fonctionnelle."""
    
    email_selected = pyqtSignal(object)
    ai_suggestion_requested = pyqtSignal(object)  # Signal ajouté
    
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
        
        # Auto-refresh timer
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
        layout.setContentsMargins(20, 15, 20, 15)
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
            ("Factures", "facture", 0),
            ("Spam", "spam", 0)
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
        self.loading_label.setFont(QFont("Arial", 14))
        self.loading_label.setStyleSheet("color: #6c757d; padding: 40px;")
        self.email_layout.addWidget(self.loading_label)
        
        # Barre de progression
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Arial", 12))
        self.progress_label.setStyleSheet("color: #007bff; padding: 10px;")
        self.progress_label.hide()
        self.email_layout.addWidget(self.progress_label)
        
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
        self.email_loader.analysis_complete.connect(self._on_analysis_complete)
        self.email_loader.progress_updated.connect(self._on_progress_updated)
    
    def refresh_emails(self):
        """Actualise la liste des emails."""
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
        self.category_filters["all"].set_active(True)
        for cat, btn in self.category_filters.items():
            if cat != "all":
                btn.set_active(False)
        
        # Démarrer le chargement
        self.email_loader.start()
    
    def _on_emails_loaded(self, emails: List[Email]):
        """Gère la réception des emails."""
        self.all_emails = emails
        self.loading_label.setText("🤖 Analyse IA en cours...")
        self.progress_label.setText("Analyse 0 / 0")
        self.progress_label.show()
        
        logger.info(f"{len(emails)} emails chargés, analyse IA en cours...")
    
    def _on_progress_updated(self, current: int, total: int):
        """Met à jour la barre de progression."""
        self.progress_label.setText(f"🤖 Analyse IA: {current} / {total}")
    
    def _on_analysis_complete(self):
        """Gère la fin de l'analyse IA."""
        # Récupérer les emails avec analyse
        self.all_emails = self.email_loader.emails_with_analysis
        
        # Cacher les messages de chargement
        self.loading_label.hide()
        self.progress_label.hide()
        
        # Créer les cartes d'emails
        self._create_email_cards()
        
        # Mettre à jour les compteurs de filtres
        self._update_filter_counts()
        
        self.is_loading = False
        
        logger.info(f"Interface mise à jour avec {len(self.all_emails)} emails analysés")
    
    def _create_email_cards(self):
        """Crée les cartes pour tous les emails filtrés."""
        self._clear_email_list()
        
        emails_to_show = self.filtered_emails if self.filtered_emails else self.all_emails
        
        if not emails_to_show:
            # Message si aucun email
            no_email_label = QLabel("📭 Aucun email à afficher")
            no_email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_email_label.setFont(QFont("Arial", 14))
            no_email_label.setStyleSheet("color: #6c757d; padding: 40px;")
            self.email_layout.insertWidget(self.email_layout.count() - 1, no_email_label)
            return
        
        for email in emails_to_show:
            # Créer la carte avec l'analyse IA
            card = SmartEmailCard(email, getattr(email, 'ai_analysis', None))
            card.clicked.connect(self._on_email_card_clicked)
            card.action_requested.connect(self._handle_email_action)
            
            self.email_cards.append(card)
            self.email_layout.insertWidget(self.email_layout.count() - 1, card)
        
        logger.info(f"Créé {len(self.email_cards)} cartes d'emails")
    
    def _clear_email_list(self):
        """Vide la liste des emails."""
        for card in self.email_cards:
            card.setParent(None)
            card.deleteLater()
        self.email_cards.clear()
        
        # Nettoyer aussi les autres widgets
        for i in reversed(range(self.email_layout.count() - 1)):  # Garder le stretch
            item = self.email_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget not in [self.loading_label, self.progress_label]:
                    widget.setParent(None)
                    widget.deleteLater()
    
    def _apply_filter(self, category: str):
        """Applique un filtre par catégorie."""
        self.current_filter = category
        
        # Mettre à jour l'apparence des filtres
        for cat, filter_btn in self.category_filters.items():
            filter_btn.set_active(cat == category)
        
        # Filtrer les emails selon la catégorie
        if category == "all":
            self.filtered_emails = self.all_emails.copy()
        elif category == "urgent":
            # Emails avec priorité <= 2
            self.filtered_emails = [
                email for email in self.all_emails 
                if hasattr(email, 'ai_analysis') and email.ai_analysis and 
                getattr(email.ai_analysis, 'priority', 5) <= 2
            ]
        else:
            # Filtrer par catégorie IA
            self.filtered_emails = [
                email for email in self.all_emails 
                if hasattr(email, 'ai_analysis') and email.ai_analysis and 
                getattr(email.ai_analysis, 'category', 'general') == category
            ]
        
        # Recréer les cartes
        self._create_email_cards()
        
        logger.info(f"Filtre '{category}' appliqué: {len(self.filtered_emails)} emails")
    
    def _update_filter_counts(self):
        """Met à jour les compteurs des filtres."""
        counts = {
            "all": len(self.all_emails),
            "urgent": 0,
            "cv": 0,
            "rdv": 0,
            "support": 0,
            "facture": 0,
            "spam": 0
        }
        
        # Compter les emails par catégorie
        for email in self.all_emails:
            if hasattr(email, 'ai_analysis') and email.ai_analysis:
                analysis = email.ai_analysis
                
                # Compteur urgent (priorité <= 2)
                if getattr(analysis, 'priority', 5) <= 2:
                    counts["urgent"] += 1
                
                # Compteurs par catégorie
                category = getattr(analysis, 'category', 'general')
                if category in counts:
                    counts[category] += 1
        
        # Mettre à jour les boutons
        for category, count in counts.items():
            if category in self.category_filters:
                self.category_filters[category].update_count(count)
        
        logger.info(f"Compteurs mis à jour: {counts}")
    
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
        
        # Marquer comme lu si pas déjà lu
        if not email.is_read:
            email.is_read = True
            self.gmail_client.mark_as_read(email.id)
            
            # Mettre à jour la carte
            for card in self.email_cards:
                if card.email.id == email.id:
                    card._apply_style()
                    break
        
        # Émettre les signaux
        self.email_selected.emit(email)
        
        # Déclencher suggestion IA si pertinente
        if (hasattr(email, 'ai_analysis') and email.ai_analysis and 
            getattr(email.ai_analysis, 'should_auto_respond', False)):
            self.ai_suggestion_requested.emit(email)
        
        logger.info(f"Email sélectionné: {email.id}")
    
    def _handle_email_action(self, action_type: str, email: Email):
        """Gère les actions sur les emails."""
        logger.info(f"Action '{action_type}' demandée pour email {email.id}")
        
        if action_type == "reply":
            self._reply_to_email(email)
        elif action_type == "archive":
            self._archive_email(email)
        elif action_type == "add_to_calendar":
            self._add_to_calendar(email)
        elif action_type == "mark_urgent":
            self._mark_urgent(email)
        elif action_type == "delete":
            self._delete_email(email)
        elif action_type == "report_spam":
            self._report_spam(email)
    
    def _reply_to_email(self, email: Email):
        """Ouvre la fenêtre de réponse."""
        try:
            from ui.compose_view import ComposeView
            
            # Préparer la réponse
            subject = email.subject or ""
            if not subject.lower().startswith('re:'):
                subject = f"Re: {subject}"
            
            # Créer le corps de réponse
            original_body = email.body or email.snippet or ""
            if len(original_body) > 500:
                original_body = original_body[:500] + "..."
            
            body = f"\n\n--- Message original ---\nDe: {email.sender}\nObjet: {email.subject}\nDate: {email.received_date}\n\n{original_body}"
            
            compose_dialog = ComposeView(
                self.gmail_client,
                parent=self,
                to=email.sender,
                subject=subject,
                body=body,
                is_reply=True
            )
            compose_dialog.exec()
            
        except Exception as e:
            logger.error(f"Erreur ouverture compose: {e}")
    
    def _archive_email(self, email: Email):
        """Archive un email."""
        success = self.gmail_client.archive_email(email.id)
        if success:
            # Supprimer de la liste
            self.all_emails = [e for e in self.all_emails if e.id != email.id]
            if self.filtered_emails:
                self.filtered_emails = [e for e in self.filtered_emails if e.id != email.id]
            
            # Recréer l'affichage
            self._create_email_cards()
            self._update_filter_counts()
            
            # Effacer la vue détail si c'était l'email sélectionné
            if self.selected_email and self.selected_email.id == email.id:
                self.detail_view.clear_selection()
                self.selected_email = None
            
            logger.info(f"Email {email.id} archivé")
    
    def _delete_email(self, email: Email):
        """Supprime un email."""
        success = self.gmail_client.delete_email(email.id)
        if success:
            # Supprimer de la liste (même logique que archive)
            self.all_emails = [e for e in self.all_emails if e.id != email.id]
            if self.filtered_emails:
                self.filtered_emails = [e for e in self.filtered_emails if e.id != email.id]
            
            self._create_email_cards()
            self._update_filter_counts()
            
            if self.selected_email and self.selected_email.id == email.id:
                self.detail_view.clear_selection()
                self.selected_email = None
            
            logger.info(f"Email {email.id} supprimé")
    
    def _add_to_calendar(self, email: Email):
        """Ajoute un événement au calendrier depuis l'email."""
        # TODO: Implémenter l'extraction automatique de RDV avec l'IA
        logger.info(f"Ajout au calendrier pour email {email.id} - À implémenter")
    
    def _mark_urgent(self, email: Email):
        """Marque un email comme urgent."""
        if hasattr(email, 'ai_analysis') and email.ai_analysis:
            email.ai_analysis.priority = 1
            self._update_filter_counts()
            
            # Mettre à jour la carte affichée
            for card in self.email_cards:
                if card.email.id == email.id:
                    card.update_ai_analysis(email.ai_analysis)
                    break
            
            logger.info(f"Email {email.id} marqué comme urgent")
    
    def _report_spam(self, email: Email):
        """Signale un email comme spam."""
        # TODO: Implémenter signalement spam
        logger.info(f"Email {email.id} signalé comme spam - À implémenter")
    
    def filter_emails(self, search_text: str):
        """Filtre les emails par texte de recherche."""
        if not search_text:
            self.filtered_emails = self.all_emails.copy()
        else:
            search_lower = search_text.lower()
            self.filtered_emails = [
                email for email in self.all_emails
                if (search_lower in (email.subject or '').lower() or
                    search_lower in (email.body or '').lower() or
                    search_lower in (email.sender or '').lower() or
                    search_lower in (email.snippet or '').lower())
            ]
        
        self._create_email_cards()
        logger.info(f"Recherche '{search_text}': {len(self.filtered_emails)} résultats")
    
    def clear_filter(self):
        """Supprime le filtre de recherche."""
        self.filtered_emails = self.all_emails.copy()
        self._create_email_cards()
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de la boîte mail."""
        unread_count = len([e for e in self.all_emails if not e.is_read])
        analyzed_count = len([e for e in self.all_emails if hasattr(e, 'ai_analysis') and e.ai_analysis])
        
        return {
            'total_emails': len(self.all_emails),
            'unread_emails': unread_count,
            'analyzed_emails': analyzed_count,
            'ai_accuracy': analyzed_count / len(self.all_emails) if self.all_emails else 0
        }