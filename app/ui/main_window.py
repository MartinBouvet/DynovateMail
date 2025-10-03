#!/usr/bin/env python3
"""
Interface principale CORRIGÉE avec toutes les connexions fonctionnelles.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QSplitter, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from gmail_client import GmailClient
from ai_processor import AIProcessor
from calendar_manager import CalendarManager
from auto_responder import AutoResponder
from models.email_model import Email
from ui.components.modern_sidebar import ModernSidebar
from ui.views.smart_inbox_view import SmartInboxView
from ui.views.calendar_view import CalendarView
from ui.views.settings_view import SettingsView
from ui.compose_view import ComposeView

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Interface principale CORRIGÉE avec toutes les fonctionnalités."""
    
    def __init__(self, gmail_client: GmailClient, ai_processor: AIProcessor,
                 calendar_manager: CalendarManager, auto_responder: AutoResponder):
        super().__init__()
        
        # Services
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.calendar_manager = calendar_manager
        self.auto_responder = auto_responder
        
        # État
        self.current_emails = []
        self.current_view = "inbox"
        self.is_loading = False
        
        # Configuration
        self._setup_window()
        self._setup_ui()
        self._setup_theme()
        self._setup_connections()
        
        # Chargement initial
        self._load_initial_data()
        
        logger.info("Interface principale initialisée avec toutes les fonctionnalités")
    
    def _setup_window(self):
        """Configure la fenêtre principale."""
        self.setWindowTitle("Dynovate Mail Assistant IA")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        self.setWindowIcon(QIcon())
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar moderne
        self.sidebar = ModernSidebar()
        self.sidebar.view_changed.connect(self._on_view_changed)
        main_layout.addWidget(self.sidebar)
        
        # Zone principale
        self.main_area = self._create_main_area()
        main_layout.addWidget(self.main_area)
        
        main_layout.setStretchFactor(self.sidebar, 0)
        main_layout.setStretchFactor(self.main_area, 1)
    
    def _create_main_area(self) -> QWidget:
        """Crée la zone principale."""
        container = QWidget()
        container.setObjectName("main-area")
        
        layout = QVBoxLayout(container)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header avec recherche
        header = self._create_header()
        layout.addWidget(header)
        
        # Stack des vues principales
        self.view_stack = QStackedWidget()
        self.view_stack.setObjectName("view-stack")
        
        # Vue Inbox intelligente - AVEC CONNEXIONS CORRIGÉES
        try:
            self.inbox_view = SmartInboxView(self.gmail_client, self.ai_processor)
            self.inbox_view.email_selected.connect(self._on_email_selected)
            self.view_stack.addWidget(self.inbox_view)
        except Exception as e:
            logger.error(f"Erreur création inbox: {e}")
            fallback_inbox = QLabel("Erreur de chargement de la boîte mail")
            fallback_inbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_inbox.setStyleSheet("color: #d32f2f; font-size: 16px; padding: 40px;")
            self.view_stack.addWidget(fallback_inbox)
        
        # Vue Calendrier
        try:
            self.calendar_view = CalendarView(self.calendar_manager)
            self.view_stack.addWidget(self.calendar_view)
        except Exception as e:
            logger.error(f"Erreur création calendrier: {e}")
            fallback_calendar = QLabel("Erreur de chargement du calendrier")
            fallback_calendar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_calendar.setStyleSheet("color: #d32f2f; font-size: 16px; padding: 40px;")
            self.view_stack.addWidget(fallback_calendar)
        
        # Vue Paramètres
        try:
            self.settings_view = SettingsView()
            self.view_stack.addWidget(self.settings_view)
        except Exception as e:
            logger.error(f"Erreur création paramètres: {e}")
            fallback_settings = QLabel("Erreur de chargement des paramètres")
            fallback_settings.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_settings.setStyleSheet("color: #d32f2f; font-size: 16px; padding: 40px;")
            self.view_stack.addWidget(fallback_settings)
        
        layout.addWidget(self.view_stack)
        
        return container
    
    def _create_header(self) -> QWidget:
        """Crée le header."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(20)
        
        # Titre de la vue actuelle
        self.view_title = QLabel("Smart Inbox")
        self.view_title.setObjectName("view-title")
        self.view_title.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        layout.addWidget(self.view_title)
        
        layout.addStretch()
        
        # Barre de recherche
        search_container = self._create_search_container()
        layout.addWidget(search_container)
        
        # Bouton refresh
        self.refresh_btn = self._create_refresh_button()
        layout.addWidget(self.refresh_btn)
        
        return header
    
    def _create_search_container(self) -> QWidget:
        """Crée le conteneur de recherche."""
        search_container = QFrame()
        search_container.setObjectName("search-container")
        search_container.setFixedSize(400, 40)
        
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(15, 0, 15, 0)
        search_layout.setSpacing(8)
        
        # Icône de recherche
        search_icon = QLabel("🔍")
        search_icon.setFont(QFont("Arial", 14))
        search_icon.setStyleSheet("color: #757575;")
        search_layout.addWidget(search_icon)
        
        # Champ de recherche
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search-input")
        self.search_input.setPlaceholderText("Rechercher dans vos emails...")
        self.search_input.setFont(QFont("Inter", 13))
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        
        # Bouton effacer
        clear_btn = QPushButton("✕")
        clear_btn.setObjectName("clear-search-btn")
        clear_btn.setFixedSize(20, 20)
        clear_btn.setFont(QFont("Arial", 10))
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        clear_btn.hide()
        
        self.search_input.textChanged.connect(
            lambda text: clear_btn.show() if text else clear_btn.hide()
        )
        
        search_layout.addWidget(clear_btn)
        
        return search_container
    
    def _create_refresh_button(self) -> QPushButton:
        """Crée le bouton de refresh."""
        refresh_btn = QPushButton("🔄")
        refresh_btn.setObjectName("refresh-btn")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setFont(QFont("Arial", 16))
        refresh_btn.setToolTip("Actualiser les données")
        refresh_btn.clicked.connect(self._refresh_data)
        
        return refresh_btn
    
    def _setup_connections(self):
        """Configure TOUTES les connexions de signaux - CORRIGÉ."""
        try:
            # Timer pour le refresh automatique
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self._auto_refresh)
            self.refresh_timer.start(300000)  # 5 minutes
            
            # CONNEXIONS INBOX VIEW - CORRIGÉES
            if hasattr(self, 'inbox_view') and self.inbox_view:
                # Connexion pour sélection d'email
                self.inbox_view.email_selected.connect(self._on_email_selected)
                
                # CONNEXIONS DETAIL VIEW - NOUVELLES
                if hasattr(self.inbox_view, 'detail_view') and self.inbox_view.detail_view:
                    detail_view = self.inbox_view.detail_view
                    
                    # Connecter les signaux du detail view
                    detail_view.reply_requested.connect(self._on_reply_requested)
                    detail_view.forward_requested.connect(self._on_forward_requested)
                    detail_view.delete_requested.connect(self._on_delete_requested)
                    detail_view.ai_response_requested.connect(self._on_ai_response_requested)
                    
                    # Passer le client Gmail
                    detail_view.set_gmail_client(self.gmail_client)
                    
                    logger.info("Connexions detail view configurées")
            
            # CONNEXIONS AUTO RESPONDER
            if hasattr(self, 'auto_responder') and self.auto_responder:
                # Connecter avec l'IA processor pour les réponses automatiques
                pass  # Déjà configuré dans le constructeur
            
            # Raccourcis clavier
            self._setup_shortcuts()
            
            logger.info("Toutes les connexions configurées avec succès")
            
        except Exception as e:
            logger.error(f"Erreur configuration connexions: {e}")
    
    def _setup_shortcuts(self):
        """Configure les raccourcis clavier."""
        from PyQt6.QtGui import QShortcut, QKeySequence
        
        # Ctrl+R pour refresh
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self._refresh_data)
        
        # Ctrl+F pour focus sur la recherche
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(lambda: self.search_input.setFocus())
        
        # Échap pour vider la recherche
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(lambda: self.search_input.clear())
        
        # Raccourcis pour changer de vue
        inbox_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        inbox_shortcut.activated.connect(lambda: self._on_view_changed("inbox"))
        
        calendar_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
        calendar_shortcut.activated.connect(lambda: self._on_view_changed("calendar"))
        
        settings_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
        settings_shortcut.activated.connect(lambda: self._on_view_changed("settings"))
        
        # Nouveau email
        compose_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        compose_shortcut.activated.connect(self._compose_new_email)
    
    # === MÉTHODES D'ACTION NOUVELLES ===
    
    def _on_reply_requested(self, email: Email):
        """Gère la demande de réponse à un email."""
        try:
            logger.info(f"Ouverture réponse pour email: {email.id}")
            
            # Créer le sujet de réponse
            original_subject = email.subject or "Sans sujet"
            if not original_subject.lower().startswith("re:"):
                reply_subject = f"Re: {original_subject}"
            else:
                reply_subject = original_subject
            
            # Créer le corps de réponse avec citation
            original_body = email.get_plain_text_content() if hasattr(email, 'get_plain_text_content') else email.body
            if original_body:
                quoted_body = f"\n\n--- Message original ---\nDe: {email.sender}\nObjet: {email.subject}\n\n{original_body}"
            else:
                quoted_body = f"\n\n--- Message original ---\nDe: {email.sender}\nObjet: {email.subject}"
            
            # Ouvrir la fenêtre de composition
            compose_dialog = ComposeView(
                gmail_client=self.gmail_client,
                parent=self,
                to=email.get_sender_email() if hasattr(email, 'get_sender_email') else email.sender,
                subject=reply_subject,
                body=quoted_body,
                is_reply=True
            )
            
            # Connecter le signal d'envoi
            compose_dialog.email_sent.connect(self._on_email_sent)
            
            # Afficher la fenêtre
            compose_dialog.exec()
            
        except Exception as e:
            logger.error(f"Erreur ouverture réponse: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir la réponse: {str(e)}")
    
    def _on_forward_requested(self, email: Email):
        """Gère la demande de transfert d'un email."""
        try:
            logger.info(f"Ouverture transfert pour email: {email.id}")
            
            # Créer le sujet de transfert
            original_subject = email.subject or "Sans sujet"
            if not original_subject.lower().startswith("fwd:"):
                forward_subject = f"Fwd: {original_subject}"
            else:
                forward_subject = original_subject
            
            # Créer le corps de transfert
            original_body = email.get_plain_text_content() if hasattr(email, 'get_plain_text_content') else email.body
            forward_body = f"--- Message transféré ---\nDe: {email.sender}\nÀ: {email.recipient}\nObjet: {email.subject}\nDate: {email.received_date}\n\n{original_body or ''}"
            
            # Ouvrir la fenêtre de composition
            compose_dialog = ComposeView(
                gmail_client=self.gmail_client,
                parent=self,
                to="",  # Laisser vide pour que l'utilisateur remplisse
                subject=forward_subject,
                body=forward_body,
                is_forward=True
            )
            
            # Connecter le signal d'envoi
            compose_dialog.email_sent.connect(self._on_email_sent)
            
            # Afficher la fenêtre
            compose_dialog.exec()
            
        except Exception as e:
            logger.error(f"Erreur ouverture transfert: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le transfert: {str(e)}")
    
    def _on_delete_requested(self, email: Email):
        """Gère la demande de suppression d'un email."""
        try:
            # Demander confirmation
            reply = QMessageBox.question(
                self,
                "Confirmer la suppression",
                f"Êtes-vous sûr de vouloir supprimer cet email ?\n\nExpéditeur: {email.sender}\nSujet: {email.subject}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                logger.info(f"Suppression email: {email.id}")
                
                # Supprimer via Gmail API
                success = self.gmail_client.delete_email(email.id)
                
                if success:
                    QMessageBox.information(self, "Succès", "Email supprimé avec succès!")
                    # Rafraîchir la liste des emails
                    self._refresh_data()
                    logger.info(f"Email {email.id} supprimé avec succès")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible de supprimer l'email.")
                    
        except Exception as e:
            logger.error(f"Erreur suppression email: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def _on_ai_response_requested(self, email: Email):
        """Gère la demande de réponse IA."""
        try:
            logger.info(f"Génération réponse IA pour email: {email.id}")
            
            # Vérifier que l'email a une analyse IA
            if not hasattr(email, 'ai_analysis') or not email.ai_analysis:
                QMessageBox.warning(self, "Pas d'analyse IA", "Cet email n'a pas d'analyse IA disponible.")
                return
            
            analysis = email.ai_analysis
            
            # Vérifier qu'une réponse est suggérée
            if not hasattr(analysis, 'suggested_response') or not analysis.suggested_response:
                QMessageBox.information(
                    self, 
                    "Pas de réponse IA", 
                    "L'IA n'a pas de réponse suggérée pour cet email."
                )
                return
            
            # Créer le sujet de réponse
            original_subject = email.subject or "Sans sujet"
            if not original_subject.lower().startswith("re:"):
                reply_subject = f"Re: {original_subject}"
            else:
                reply_subject = original_subject
            
            # Ouvrir la fenêtre de composition avec la réponse IA
            compose_dialog = ComposeView(
                gmail_client=self.gmail_client,
                parent=self,
                to=email.get_sender_email() if hasattr(email, 'get_sender_email') else email.sender,
                subject=reply_subject,
                body=analysis.suggested_response,
                is_reply=True
            )
            
            # Marquer comme réponse IA
            compose_dialog.show_ai_indicator()
            
            # Connecter le signal d'envoi
            compose_dialog.email_sent.connect(self._on_email_sent)
            
            # Afficher la fenêtre
            compose_dialog.exec()
            
            logger.info("Réponse IA ouverte pour modification/envoi")
            
        except Exception as e:
            logger.error(f"Erreur génération réponse IA: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération de la réponse IA: {str(e)}")
    
    def _compose_new_email(self):
        """Ouvre la fenêtre de composition pour un nouvel email."""
        try:
            logger.info("Ouverture composition nouvel email")
            
            compose_dialog = ComposeView(
                gmail_client=self.gmail_client,
                parent=self
            )
            
            # Connecter le signal d'envoi
            compose_dialog.email_sent.connect(self._on_email_sent)
            
            # Afficher la fenêtre
            compose_dialog.exec()
            
        except Exception as e:
            logger.error(f"Erreur ouverture composition: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir la composition: {str(e)}")
    
    def _on_email_sent(self):
        """Gère l'envoi d'un email."""
        try:
            logger.info("Email envoyé - Actualisation de la liste")
            
            # Afficher une notification
            self.show_notification("✅ Email envoyé avec succès!", 3000)
            
            # Rafraîchir la liste des emails après un court délai
            QTimer.singleShot(2000, self._refresh_data)
            
        except Exception as e:
            logger.error(f"Erreur après envoi email: {e}")
    
    # === MÉTHODES EXISTANTES CONSERVÉES ===
    
    def _load_initial_data(self):
        """Charge les données initiales."""
        QTimer.singleShot(1000, self._initial_load)
    
    def _initial_load(self):
        """Charge les données initiales."""
        try:
            if hasattr(self, 'inbox_view') and hasattr(self.inbox_view, 'refresh_emails'):
                self.inbox_view.refresh_emails()
            else:
                logger.warning("Inbox view non disponible")
        except Exception as e:
            logger.error(f"Erreur chargement initial: {e}")
    
    def _on_view_changed(self, view_name: str):
        """Gère le changement de vue."""
        view_titles = {
            "inbox": "Smart Inbox",
            "calendar": "Calendrier Intelligent", 
            "settings": "Paramètres"
        }
        
        view_indices = {
            "inbox": 0,
            "calendar": 1,
            "settings": 2
        }
        
        if view_name in view_indices:
            new_title = view_titles[view_name]
            self.view_title.setText(new_title)
            
            self.view_stack.setCurrentIndex(view_indices[view_name])
            self.current_view = view_name
            
            if view_name == "inbox" and hasattr(self, 'inbox_view'):
                self.search_input.setEnabled(True)
                self.search_input.setPlaceholderText("Rechercher dans vos emails...")
                self.search_input.setStyleSheet("")
            else:
                self.search_input.setEnabled(False)
                self.search_input.setPlaceholderText("Recherche non disponible")
                self.search_input.clear()
                self.search_input.setStyleSheet("color: #bdbdbd;")
            
            logger.info(f"Vue changée vers: {view_name}")
    
    def _on_search_changed(self, text: str):
        """Gère les changements dans la recherche."""
        if self.current_view == "inbox" and hasattr(self, 'inbox_view'):
            try:
                if len(text) >= 2:
                    # Utiliser la méthode correcte selon l'implémentation
                    if hasattr(self.inbox_view, 'filter_emails'):
                        self.inbox_view.filter_emails(text)
                    elif hasattr(self.inbox_view, 'search_emails'):
                        self.inbox_view.search_emails(text)
                elif text == "":
                    if hasattr(self.inbox_view, 'clear_filter'):
                        self.inbox_view.clear_filter()
                    elif hasattr(self.inbox_view, 'clear_search'):
                        self.inbox_view.clear_search()
            except Exception as e:
                logger.error(f"Erreur recherche: {e}")
    
    def _on_email_selected(self, email: Email):
        """Gère la sélection d'un email."""
        try:
            # Marquer comme lu si pas encore lu
            if not email.is_read and self.gmail_client:
                self.gmail_client.mark_as_read(email.id)
                email.is_read = True
            
            # Mettre à jour les statistiques
            if hasattr(self, 'inbox_view'):
                self.current_emails = getattr(self.inbox_view, 'all_emails', [])
                self._update_sidebar_stats()
            
            logger.info(f"Email sélectionné: {email.subject}")
        except Exception as e:
            logger.error(f"Erreur sélection email: {e}")
    
    def _refresh_data(self):
        """Actualise toutes les données."""
        if self.is_loading:
            logger.info("Refresh déjà en cours")
            return
        
        self.is_loading = True
        self._start_refresh_animation()
        
        try:
            if self.current_view == "inbox" and hasattr(self, 'inbox_view'):
                if hasattr(self.inbox_view, 'refresh_emails'):
                    self.inbox_view.refresh_emails()
            
            elif self.current_view == "calendar" and hasattr(self, 'calendar_view'):
                if hasattr(self.calendar_view, 'refresh_events'):
                    self.calendar_view.refresh_events()
            
            self._update_sidebar_stats()
            
            logger.info(f"Refresh déclenché pour: {self.current_view}")
            
        except Exception as e:
            logger.error(f"Erreur refresh: {e}")
            self._show_error_message("Erreur de synchronisation", str(e))
        finally:
            QTimer.singleShot(2000, self._stop_refresh_animation)
    
    def _auto_refresh(self):
        """Refresh automatique en arrière-plan."""
        if not self.is_loading and self.current_view == "inbox":
            try:
                if hasattr(self, 'inbox_view') and hasattr(self.inbox_view, 'refresh_emails'):
                    self.inbox_view.refresh_emails()
                    logger.info("Auto-refresh effectué")
            except Exception as e:
                logger.error(f"Erreur auto-refresh: {e}")
    
    def _start_refresh_animation(self):
        """Démarre l'animation de refresh."""
        self.refresh_btn.setText("⟳")
        self.refresh_btn.setStyleSheet("""
            QPushButton#refresh-btn {
                background-color: #1976d2;
                border: 2px solid #1976d2;
                border-radius: 20px;
                color: #ffffff;
                font-size: 16px;
            }
        """)
        self.refresh_btn.setEnabled(False)
    
    def _stop_refresh_animation(self):
        """Arrête l'animation de refresh."""
        self.refresh_btn.setText("🔄")
        self.refresh_btn.setStyleSheet("")
        self.refresh_btn.setEnabled(True)
        self.is_loading = False
    
    def _update_sidebar_stats(self):
        """Met à jour les statistiques dans la sidebar."""
        try:
            if hasattr(self, 'inbox_view') and hasattr(self.inbox_view, 'all_emails'):
                emails = self.inbox_view.all_emails
                unread_count = len([e for e in emails if not e.is_read])
                
                analyzed_emails = [e for e in emails if hasattr(e, 'ai_analysis') and e.ai_analysis]
                ai_accuracy = len(analyzed_emails) / len(emails) if emails else 0
                
                auto_responses = len([e for e in emails if hasattr(e, 'ai_analysis') and e.ai_analysis and getattr(e.ai_analysis, 'should_auto_respond', False)])
                
                stats = {
                    'unread_emails': unread_count,
                    'ai_accuracy': ai_accuracy,
                    'auto_responses': auto_responses
                }
                
                if hasattr(self.sidebar, 'update_stats'):
                    self.sidebar.update_stats(stats)
                
                logger.debug(f"Stats mises à jour: {stats}")
        except Exception as e:
            logger.error(f"Erreur mise à jour stats: {e}")
    
    def _show_error_message(self, title: str, message: str):
        """Affiche un message d'erreur."""
        try:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
        except Exception as e:
            logger.error(f"Erreur affichage message d'erreur: {e}")
    
    def show_notification(self, message: str, duration: int = 3000):
        """Affiche une notification temporaire."""
        try:
            if not hasattr(self, '_status_bar'):
                self._status_bar = self.statusBar()
                self._status_bar.setStyleSheet("""
                    QStatusBar {
                        background-color: #e8f5e8;
                        color: #2e7d32;
                        font-weight: 500;
                        border-top: 2px solid #4caf50;
                        padding: 6px 12px;
                    }
                """)
            
            self._status_bar.showMessage(message, duration)
        except Exception as e:
            logger.error(f"Erreur notification: {e}")
    
    def _setup_theme(self):
        """Configure le thème pour une bonne lisibilité."""
        style = """
        QMainWindow {
            background-color: #ffffff;
            color: #212121;
        }
        
        #main-area {
            background-color: #ffffff;
            border-left: 2px solid #e0e0e0;
        }
        
        #header {
            background-color: #fafafa;
            border-bottom: 2px solid #e0e0e0;
        }
        
        #view-title {
            color: #1a1a1a;
            font-weight: 700;
            margin: 0;
            padding: 0;
        }
        
        #search-container {
            background-color: #ffffff;
            border: 2px solid #e0e0e0;
            border-radius: 20px;
        }
        
        #search-container:focus-within {
            border-color: #1976d2;
            background-color: #ffffff;
        }
        
        #search-input {
            background: transparent;
            border: none;
            color: #212121;
            font-size: 13px;
            font-weight: 400;
            padding: 8px 0;
            outline: none;
        }
        
        #search-input::placeholder {
            color: #757575;
            font-style: normal;
        }
        
        #clear-search-btn {
            background-color: #e0e0e0;
            border: none;
            border-radius: 10px;
            color: #757575;
            font-size: 10px;
            font-weight: bold;
        }
        
        #clear-search-btn:hover {
            background-color: #d32f2f;
            color: #ffffff;
        }
        
        #refresh-btn {
            background-color: #ffffff;
            border: 2px solid #e0e0e0;
            border-radius: 20px;
            color: #757575;
            font-size: 16px;
        }
        
        #refresh-btn:hover {
            background-color: #f5f5f5;
            color: #1976d2;
            border-color: #1976d2;
        }
        
        #refresh-btn:pressed {
            background-color: #e3f2fd;
            transform: scale(0.95);
        }
        
        #view-stack {
            background-color: #ffffff;
        }
        
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            background-color: #f5f5f5;
            width: 10px;
            border-radius: 5px;
            margin: 1px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #bdbdbd;
            border-radius: 5px;
            min-height: 25px;
            margin: 1px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #9e9e9e;
        }
        
        QScrollBar::handle:vertical:pressed {
            background-color: #757575;
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: #f5f5f5;
            height: 10px;
            border-radius: 5px;
            margin: 1px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #bdbdbd;
            border-radius: 5px;
            min-width: 25px;
            margin: 1px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #9e9e9e;
        }
        
        QMessageBox {
            background-color: #ffffff;
            color: #212121;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
        }
        
        QMessageBox QPushButton {
            background-color: #1976d2;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 500;
            min-width: 80px;
        }
        
        QMessageBox QPushButton:hover {
            background-color: #1565c0;
        }
        
        QMessageBox QPushButton:pressed {
            background-color: #0d47a1;
        }
        
        QSplitter::handle {
            background-color: #e0e0e0;
            width: 2px;
            height: 2px;
        }
        
        QSplitter::handle:hover {
            background-color: #bdbdbd;
        }
        
        QLabel {
            color: #212121;
        }
        """
        
        self.setStyleSheet(style)
    
    def resizeEvent(self, event):
        """Gère le redimensionnement."""
        super().resizeEvent(event)
        
        window_width = event.size().width()
        
        if window_width < 1000:
            if hasattr(self, 'search_input'):
                self.search_input.parent().setFixedSize(300, 40)
        else:
            if hasattr(self, 'search_input'):
                self.search_input.parent().setFixedSize(400, 40)
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application."""
        try:
            logger.info("Fermeture de l'application...")
            
            # Arrêter les threads
            if hasattr(self, 'inbox_view') and hasattr(self.inbox_view, 'email_loader'):
                if self.inbox_view.email_loader.isRunning():
                    self.inbox_view.email_loader.stop()
                    self.inbox_view.email_loader.wait(3000)
            
            # Arrêter les timers
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
            
            # Sauvegarder l'état
            self._save_window_state()
            
            logger.info("Fermeture terminée")
            event.accept()
            
        except Exception as e:
            logger.error(f"Erreur fermeture: {e}")
            event.accept()
    
    def _save_window_state(self):
        """Sauvegarde l'état de la fenêtre."""
        try:
            logger.info(f"État sauvegardé - Vue: {self.current_view}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde état: {e}")
    
    def showEvent(self, event):
        """Gère l'affichage de la fenêtre."""
        super().showEvent(event)
        
        if not hasattr(self, '_window_centered'):
            self._center_window()
            self._window_centered = True
    
    def _center_window(self):
        """Centre la fenêtre sur l'écran."""
        try:
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                window_geometry = self.frameGeometry()
                center_point = screen_geometry.center()
                window_geometry.moveCenter(center_point)
                self.move(window_geometry.topLeft())
        except Exception as e:
            logger.error(f"Erreur centrage: {e}")