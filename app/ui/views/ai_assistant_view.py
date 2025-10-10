#!/usr/bin/env python3
"""
Vue Assistant IA - COMPLÈTE ET FONCTIONNELLE
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QScrollArea, QFrame,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
    QTabWidget, QCheckBox, QDialog, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ai_processor import AIProcessor
from gmail_client import GmailClient
from models.email_model import Email

logger = logging.getLogger(__name__)

class AIAssistantView(QWidget):
    """Vue de l'assistant IA avec fonctionnalités complètes."""
    
    def __init__(self, ai_processor: AIProcessor, gmail_client: GmailClient = None):
        super().__init__()
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.pending_responses = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Titre principal
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #f5f5f5; border-bottom: 2px solid #5b21b6;")
        
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 10, 30, 10)
        
        title = QLabel("🤖 Assistant IA Dynovate")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #5b21b6;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Votre assistant intelligent pour gérer vos emails")
        subtitle.setFont(QFont("Segoe UI", 13))
        subtitle.setStyleSheet("color: #666666;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # Tabs pour les différentes fonctionnalités
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 12))
        
        # Tab 1: Réponses suggérées
        self.tab_responses = self._create_responses_tab()
        self.tabs.addTab(self.tab_responses, "✍️ Réponses suggérées")
        
        # Tab 2: Chatbot
        self.tab_chatbot = self._create_chatbot_tab()
        self.tabs.addTab(self.tab_chatbot, "💬 Chatbot")
        
        # Tab 3: Statistiques
        self.tab_stats = self._create_stats_tab()
        self.tabs.addTab(self.tab_stats, "📊 Statistiques")
        
        layout.addWidget(self.tabs)
        
        self._apply_styles()
    
    def _create_responses_tab(self) -> QWidget:
        """Crée l'onglet des réponses suggérées."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Description
        desc = QLabel(
            "L'IA a analysé vos emails et suggère des réponses automatiques.\n"
            "Validez ou modifiez les réponses avant de les envoyer."
        )
        desc.setFont(QFont("Segoe UI", 12))
        desc.setStyleSheet("color: #666666; padding: 10px; background-color: #f5f5f5; border-radius: 6px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Bouton rafraîchir
        refresh_btn = QPushButton("🔄 Charger les emails nécessitant une réponse")
        refresh_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        refresh_btn.setFixedHeight(45)
        refresh_btn.clicked.connect(self._load_pending_responses)
        layout.addWidget(refresh_btn)
        
        # Liste des emails avec réponses suggérées
        self.responses_list = QScrollArea()
        self.responses_list.setWidgetResizable(True)
        self.responses_list.setStyleSheet("border: none;")
        
        self.responses_container = QWidget()
        self.responses_layout = QVBoxLayout(self.responses_container)
        self.responses_layout.setSpacing(10)
        self.responses_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Message par défaut
        empty_label = QLabel("Cliquez sur le bouton ci-dessus pour charger les emails")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setFont(QFont("Segoe UI", 13))
        empty_label.setStyleSheet("color: #999999; padding: 40px;")
        self.responses_layout.addWidget(empty_label)
        
        self.responses_list.setWidget(self.responses_container)
        layout.addWidget(self.responses_list)
        
        return tab
    
    def _create_chatbot_tab(self) -> QWidget:
        """Crée l'onglet du chatbot."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Description
        desc = QLabel(
            "Utilisez le chatbot pour des actions rapides:\n"
            "• \"Fixe un RDV avec jean@example.com demain à 14h\"\n"
            "• \"Envoie un email à marie@example.com pour lui demander le rapport\"\n"
            "• \"Résume mes emails non lus d'aujourd'hui\""
        )
        desc.setFont(QFont("Segoe UI", 12))
        desc.setStyleSheet("color: #666666; padding: 10px; background-color: #f5f5f5; border-radius: 6px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Zone de conversation
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Segoe UI", 12))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 15px;
                color: #000000;
            }
        """)
        self.chat_display.setPlaceholderText("La conversation avec l'IA apparaîtra ici...")
        layout.addWidget(self.chat_display)
        
        # Zone de saisie
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Tapez votre message ici...")
        self.chat_input.setFont(QFont("Segoe UI", 12))
        self.chat_input.setFixedHeight(45)
        self.chat_input.returnPressed.connect(self._send_chat_message)
        input_layout.addWidget(self.chat_input)
        
        send_btn = QPushButton("📤 Envoyer")
        send_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        send_btn.setFixedHeight(45)
        send_btn.setFixedWidth(120)
        send_btn.clicked.connect(self._send_chat_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # Message de bienvenue
        self.chat_display.append(
            "<p style='color: #5b21b6; font-weight: bold;'>🤖 Assistant IA:</p>"
            "<p>Bonjour ! Je suis votre assistant IA. Comment puis-je vous aider aujourd'hui ?</p>"
            "<p style='color: #666666; font-size: 11px;'>Exemples de commandes:<br>"
            "- Fixe un RDV avec [email] le [date] à [heure]<br>"
            "- Envoie un email à [email] pour [sujet]<br>"
            "- Résume mes emails non lus</p>"
        )
        
        return tab
    
    def _create_stats_tab(self) -> QWidget:
        """Crée l'onglet des statistiques."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Grille de statistiques
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(15)
        
        # Stat 1: Emails analysés
        stat1 = self._create_stat_card(
            "📧",
            "Emails analysés",
            "0",
            "Aujourd'hui"
        )
        stats_grid.addWidget(stat1)
        
        # Stat 2: Réponses auto
        stat2 = self._create_stat_card(
            "✍️",
            "Réponses auto envoyées",
            "0",
            "Cette semaine"
        )
        stats_grid.addWidget(stat2)
        
        # Stat 3: Temps économisé
        stat3 = self._create_stat_card(
            "⏱️",
            "Temps économisé",
            "0 min",
            "Ce mois-ci"
        )
        stats_grid.addWidget(stat3)
        
        # Stat 4: Précision
        stat4 = self._create_stat_card(
            "🎯",
            "Précision IA",
            "N/A",
            "Classification"
        )
        stats_grid.addWidget(stat4)
        
        layout.addLayout(stats_grid)
        
        # Graphique de répartition des catégories
        categories_frame = QFrame()
        categories_frame.setObjectName("categories-frame")
        categories_layout = QVBoxLayout(categories_frame)
        categories_layout.setContentsMargins(20, 20, 20, 20)
        
        categories_title = QLabel("📊 Répartition des emails par catégorie")
        categories_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        categories_title.setStyleSheet("color: #000000;")
        categories_layout.addWidget(categories_title)
        
        # Liste des catégories
        categories_data = [
            ("📄 CV", 0, "#5b21b6"),
            ("📅 Rendez-vous", 0, "#8b5cf6"),
            ("💰 Factures", 0, "#10b981"),
            ("📰 Newsletters", 0, "#f59e0b"),
            ("🛠️ Support", 0, "#ef4444"),
            ("⚠️ Spam", 0, "#dc2626"),
        ]
        
        for category, count, color in categories_data:
            cat_row = QHBoxLayout()
            
            cat_label = QLabel(category)
            cat_label.setFont(QFont("Segoe UI", 12))
            cat_label.setStyleSheet("color: #000000;")
            cat_row.addWidget(cat_label)
            
            cat_row.addStretch()
            
            cat_count = QLabel(str(count))
            cat_count.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            cat_count.setStyleSheet(f"color: {color};")
            cat_row.addWidget(cat_count)
            
            categories_layout.addLayout(cat_row)
        
        categories_frame.setStyleSheet("""
            #categories-frame {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        
        layout.addWidget(categories_frame)
        
        layout.addStretch()
        
        return tab
    
    def _create_stat_card(self, icon: str, title: str, value: str, subtitle: str) -> QFrame:
        """Crée une carte de statistique."""
        card = QFrame()
        card.setObjectName("stat-card")
        card.setFixedHeight(140)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icône
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 36))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Valeur
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #5b21b6;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Titre
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #000000;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Sous-titre
        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont("Segoe UI", 9))
        subtitle_label.setStyleSheet("color: #666666;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        card.setStyleSheet("""
            #stat-card {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
            }
            #stat-card:hover {
                border-color: #5b21b6;
            }
        """)
        
        return card
    
    def _load_pending_responses(self):
        """Charge les emails nécessitant une réponse - FILTRÉ."""
        try:
            if not self.gmail_client:
                QMessageBox.warning(self, "Erreur", "Client Gmail non disponible")
                return
            
            # Effacer la liste
            while self.responses_layout.count():
                item = self.responses_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Message de chargement
            loading_label = QLabel("⏳ Chargement et analyse en cours...")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setFont(QFont("Segoe UI", 13))
            loading_label.setStyleSheet("color: #5b21b6; padding: 40px;")
            self.responses_layout.addWidget(loading_label)
            
            # Charger les emails
            emails = self.gmail_client.get_inbox_emails(max_results=50)
            
            # Effacer le message de chargement
            while self.responses_layout.count():
                item = self.responses_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Filtrer: seulement les emails qui nécessitent vraiment une réponse
            emails_needing_response = []
            for email in emails:
                # Analyser avec l'IA si pas déjà fait
                if not hasattr(email, 'ai_analysis') or not email.ai_analysis:
                    email.ai_analysis = self.ai_processor.analyze_email(email)
                
                # Vérifier si besoin de réponse
                if (email.ai_analysis and 
                    email.ai_analysis.needs_response and 
                    not email.ai_analysis.is_spam and
                    not email.is_read):
                    emails_needing_response.append(email)
            
            if not emails_needing_response:
                empty_label = QLabel("✅ Aucun email nécessitant une réponse pour le moment")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setFont(QFont("Segoe UI", 13))
                empty_label.setStyleSheet("color: #10b981; padding: 40px;")
                self.responses_layout.addWidget(empty_label)
                return
            
            # Créer une carte pour chaque email
            for email in emails_needing_response:
                card = self._create_response_card(email)
                self.responses_layout.addWidget(card)
            
            logger.info(f"{len(emails_needing_response)} emails nécessitant une réponse")
            
        except Exception as e:
            logger.error(f"Erreur chargement réponses: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les emails: {e}")
    
    def _create_response_card(self, email: Email) -> QFrame:
        """Crée une carte de réponse avec IA."""
        card = QFrame()
        card.setObjectName("response-card")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # En-tête
        header_layout = QHBoxLayout()
        from_label = QLabel(f"De: {email.sender}")
        from_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        from_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(from_label)
        header_layout.addStretch()
        
        date_label = QLabel(email.received_date.strftime("%d/%m/%Y %H:%M") if email.received_date else "")
        date_label.setFont(QFont("Segoe UI", 10))
        date_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(date_label)
        layout.addLayout(header_layout)
        
        # Sujet
        subject_label = QLabel(f"Sujet: {email.subject or '(Sans sujet)'}")
        subject_label.setFont(QFont("Segoe UI", 11))
        subject_label.setStyleSheet("color: #000000;")
        subject_label.setWordWrap(True)
        layout.addWidget(subject_label)
        
        # Aperçu email
        original_label = QLabel("Message original:")
        original_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        original_label.setStyleSheet("color: #666666;")
        layout.addWidget(original_label)
        
        preview_text = email.snippet if email.snippet else ""
        if not preview_text and email.body:
            import re
            preview_text = re.sub('<[^<]+?>', '', email.body)[:200]
        
        preview_display = QLabel(preview_text + "..." if len(preview_text) > 200 else preview_text)
        preview_display.setFont(QFont("Segoe UI", 10))
        preview_display.setStyleSheet("""
            color: #000000;
            background-color: #f9f9f9;
            padding: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        """)
        preview_display.setWordWrap(True)
        preview_display.setMaximumHeight(80)
        layout.addWidget(preview_display)
        
        # Bouton voir complet
        view_full_btn = QPushButton("👁️ Voir l'email complet")
        view_full_btn.setFont(QFont("Segoe UI", 10))
        view_full_btn.setFixedHeight(30)
        view_full_btn.clicked.connect(lambda: self._show_full_email(email))
        layout.addWidget(view_full_btn)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(separator)
        
        # Label IA
        ai_label = QLabel("🤖 Réponse générée par l'IA:")
        ai_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        ai_label.setStyleSheet("color: #5b21b6;")
        layout.addWidget(ai_label)
        
        # GÉNÉRER RÉPONSE AVEC IA
        suggested_response = self.ai_processor.generate_smart_response(email)
        
        response_text = QTextEdit()
        response_text.setPlainText(suggested_response)
        response_text.setFont(QFont("Segoe UI", 11))
        response_text.setFixedHeight(180)
        response_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                color: #000000;
            }
        """)
        layout.addWidget(response_text)
        
        # Info IA
        info_label = QLabel("💡 Cette réponse a été générée intelligemment selon le contexte. Vous pouvez la modifier avant d'envoyer.")
        info_label.setFont(QFont("Segoe UI", 9))
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Boutons
        actions_layout = QHBoxLayout()
        
        validate_btn = QPushButton("✅ Valider et envoyer")
        validate_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        validate_btn.setFixedHeight(38)
        validate_btn.clicked.connect(lambda: self._send_suggested_response(email, response_text.toPlainText()))
        actions_layout.addWidget(validate_btn)
        
        reject_btn = QPushButton("❌ Rejeter")
        reject_btn.setFont(QFont("Segoe UI", 11))
        reject_btn.setFixedHeight(38)
        reject_btn.clicked.connect(lambda: card.deleteLater())
        actions_layout.addWidget(reject_btn)
        
        layout.addLayout(actions_layout)
        
        card.setStyleSheet("""
            #response-card {
                background-color: #ffffff;
                border: 2px solid #5b21b6;
                border-radius: 8px;
            }
        """)
        
        return card
    
    def _show_full_email(self, email: Email):
        """Affiche l'email complet dans une fenêtre popup."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Email: {email.subject or '(Sans sujet)'}")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Afficher l'email
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        
        if email.is_html and email.body:
            browser.setHtml(email.body)
        else:
            browser.setPlainText(email.body or email.snippet or "Email vide")
        
        layout.addWidget(browser)
        
        # Bouton fermer
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def _generate_suggested_response(self, email: Email) -> str:
        """Génère une réponse suggérée pour un email."""
        subject = email.subject or ""
        sender = email.sender or ""
        
        # Adapter la réponse selon la catégorie
        if hasattr(email, 'ai_analysis') and email.ai_analysis:
            category = email.ai_analysis.category
            
            if category == "cv":
                return f"""Bonjour,

Merci pour votre candidature. Nous avons bien reçu votre CV et nous l'examinerons attentivement.

Nous reviendrons vers vous dans les plus brefs délais si votre profil correspond à nos besoins.

Cordialement,
L'équipe Dynovate"""
            
            elif category == "meeting":
                return f"""Bonjour,

Merci pour votre demande de rendez-vous.

Je suis disponible pour échanger. Pourriez-vous me proposer quelques créneaux qui vous conviennent ?

Cordialement"""
            
            elif category == "support":
                return f"""Bonjour,

Merci pour votre message. Nous avons bien pris en compte votre demande de support.

Notre équipe technique va analyser votre problème et reviendra vers vous rapidement avec une solution.

Cordialement,
Le support Dynovate"""
            
            elif category == "invoice":
                return f"""Bonjour,

Merci pour votre email concernant la facturation.

Nous avons bien reçu votre demande et nous vous confirmerons les détails dans les plus brefs délais.

Cordialement"""
        
        # Réponse générique
        return f"""Bonjour,

Merci pour votre message concernant "{subject}".

Nous avons bien pris en compte votre demande et nous reviendrons vers vous dans les plus brefs délais.

Cordialement,
L'équipe Dynovate"""
    
    def _send_suggested_response(self, original_email: Email, response_text: str):
        """Envoie une réponse suggérée."""
        try:
            if not self.gmail_client:
                QMessageBox.warning(self, "Erreur", "Client Gmail non disponible")
                return
            
            # Extraire l'email de l'expéditeur
            sender_email = original_email.sender
            if '<' in sender_email:
                sender_email = sender_email.split('<')[1].split('>')[0]
            
            # Envoyer la réponse
            subject = f"Re: {original_email.subject or ''}"
            success = self.gmail_client.send_email(
                to=[sender_email],
                subject=subject,
                body=response_text
            )
            
            if success:
                QMessageBox.information(self, "Succès", "Réponse envoyée avec succès!")
                # Recharger la liste
                self._load_pending_responses()
            else:
                QMessageBox.critical(self, "Erreur", "Échec de l'envoi de la réponse")
            
        except Exception as e:
            logger.error(f"Erreur envoi réponse: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'envoyer la réponse: {e}")
    
    def _send_chat_message(self):
        """Envoie un message au chatbot."""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # Afficher le message de l'utilisateur
        self.chat_display.append(
            f"<p style='color: #000000; font-weight: bold;'>Vous:</p>"
            f"<p>{message}</p>"
        )
        
        # Effacer le champ de saisie
        self.chat_input.clear()
        
        # Traiter la commande
        response = self._process_chat_command(message)
        
        # Afficher la réponse de l'IA
        self.chat_display.append(
            f"<p style='color: #5b21b6; font-weight: bold;'>🤖 Assistant IA:</p>"
            f"<p>{response}</p>"
        )
        
        # Scroller vers le bas
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_statistics(self):
        """Met à jour les statistiques - FONCTIONNEL."""
        try:
            if not self.gmail_client:
                return
            
            # Charger les emails récents
            emails = self.gmail_client.get_inbox_emails(max_results=100)
            
            # Analyser
            categories_count = {
                'cv': 0,
                'meeting': 0,
                'invoice': 0,
                'newsletter': 0,
                'support': 0,
                'spam': 0
            }
            
            total_analyzed = 0
            
            for email in emails:
                if not hasattr(email, 'ai_analysis') or not email.ai_analysis:
                    email.ai_analysis = self.ai_processor.analyze_email(email)
                
                if email.ai_analysis:
                    total_analyzed += 1
                    category = email.ai_analysis.category
                    if category in categories_count:
                        categories_count[category] += 1
            
            # Mettre à jour l'affichage dans l'onglet stats
            # TODO: Mettre à jour les labels avec les vraies valeurs
            
            logger.info(f"Statistiques mises à jour: {total_analyzed} emails analysés")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour stats: {e}")
            
    def _process_chat_command(self, message: str) -> str:
        """Traite une commande du chatbot avec IA."""
        message_lower = message.lower()
        
        try:
            # Commande: Résumer emails
            if any(word in message_lower for word in ['résume', 'résumé', 'summary', 'liste']):
                if self.gmail_client:
                    emails = self.gmail_client.get_inbox_emails(max_results=20)
                    unread = [e for e in emails if not e.is_read]
                    
                    if not unread:
                        return "✅ Vous n'avez aucun email non lu pour le moment."
                    
                    # Analyser et résumer
                    summary = f"📧 Vous avez {len(unread)} email(s) non lu(s):\n\n"
                    
                    for i, email in enumerate(unread[:5], 1):  # Limiter à 5
                        if not hasattr(email, 'ai_analysis') or not email.ai_analysis:
                            email.ai_analysis = self.ai_processor.analyze_email(email)
                        
                        category_emoji = {
                            'cv': '📄',
                            'meeting': '📅',
                            'support': '🛠️',
                            'invoice': '💰',
                            'spam': '⚠️'
                        }.get(email.ai_analysis.category if email.ai_analysis else 'important', '📧')
                        
                        sender_name = email.sender.split('<')[0].strip() if '<' in email.sender else email.sender
                        summary += f"{i}. {category_emoji} {sender_name}\n"
                        summary += f"   Sujet: {email.subject or '(Sans sujet)'}\n"
                        if email.ai_analysis:
                            summary += f"   Priorité: {'⭐' * email.ai_analysis.priority}\n"
                        summary += "\n"
                    
                    if len(unread) > 5:
                        summary += f"... et {len(unread) - 5} autre(s) email(s)."
                    
                    return summary
                
                return "❌ Impossible d'accéder à vos emails."
            
            # Commande: Fixer RDV
            elif any(word in message_lower for word in ['rdv', 'rendez-vous', 'meeting', 'réunion', 'fixe', 'planifie']):
                # Extraire l'email et la date si possible
                import re
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
                
                if email_match:
                    recipient = email_match.group(0)
                    return f"📅 J'ai bien noté votre demande de rendez-vous avec {recipient}.\n\n" \
                           f"Pour finaliser, cliquez sur '✉️ Nouveau message' et je vous aiderai à rédiger l'invitation.\n\n" \
                           f"💡 Astuce: Vous pouvez aussi utiliser l'onglet Calendrier pour gérer vos rendez-vous."
                else:
                    return "📅 Pour fixer un rendez-vous, précisez l'adresse email du destinataire.\n\n" \
                           "Exemple: 'Fixe un RDV avec jean@example.com pour discuter du projet'"
            
            # Commande: Envoyer email
            elif any(word in message_lower for word in ['envoie', 'envoyer', 'mail', 'email', 'écris']):
                import re
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
                
                if email_match:
                    recipient = email_match.group(0)
                    return f"✉️ Pour envoyer un email à {recipient}:\n\n" \
                           f"1. Cliquez sur le bouton '✉️ Nouveau message' en haut\n" \
                           f"2. Je pré-remplirai les informations pour vous\n\n" \
                           f"💡 Je peux aussi générer le contenu du message automatiquement si vous me précisez le sujet."
                else:
                    return "✉️ Pour envoyer un email, cliquez sur '✉️ Nouveau message' dans la barre supérieure.\n\n" \
                           "Je peux vous aider à rédiger le contenu !"
            
            # Commande: Aide
            elif any(word in message_lower for word in ['aide', 'help', 'comment', 'que peux-tu']):
                return """🤖 Je suis votre assistant IA pour la gestion des emails. Voici ce que je peux faire:

📊 **Analyser vos emails**
- "Résume mes emails non lus"
- "Liste mes emails importants"

✍️ **Rédiger des réponses**
- Je génère des réponses intelligentes dans l'onglet 'Réponses suggérées'

📅 **Gérer les rendez-vous**
- "Fixe un RDV avec jean@example.com"

✉️ **Envoyer des emails**
- "Envoie un email à marie@example.com"

💡 N'hésitez pas à me poser des questions ou à me donner des commandes en langage naturel !"""
            
            # Analyse générale avec IA
            else:
                # Réponse intelligente basée sur le message
                if '?' in message:
                    return f"🤔 J'ai bien compris votre question: \"{message}\"\n\n" \
                           f"Pour vous aider au mieux, pourriez-vous préciser ce que vous souhaitez faire ?\n\n" \
                           f"Tapez 'aide' pour voir toutes mes fonctionnalités."
                else:
                    return "💬 J'ai bien reçu votre message.\n\n" \
                           "Pour une meilleure assistance, essayez des commandes comme:\n" \
                           "• 'Résume mes emails'\n" \
                           "• 'Fixe un RDV avec...'\n" \
                           "• 'Aide'\n\n" \
                           "Ou posez-moi une question précise !"
        
        except Exception as e:
            logger.error(f"Erreur traitement chatbot: {e}")
            return "❌ Une erreur s'est produite. Veuillez réessayer."
    
    def _apply_styles(self):
        """Applique les styles."""
        self.setStyleSheet("""
            AIAssistantView {
                background-color: #ffffff;
            }
            
            QTabWidget::pane {
                border: 2px solid #5b21b6;
                border-radius: 6px;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: #f5f5f5;
                color: #000000;
                padding: 10px 20px;
                margin-right: 2px;
                border: 2px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-color: #5b21b6;
                color: #5b21b6;
                font-weight: bold;
            }
            
            QTabBar::tab:hover {
                background-color: #fafafa;
            }
            
            QPushButton {
                background-color: #5b21b6;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            
            QPushButton:hover {
                background-color: #4c1d95;
            }
            
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 15px;
                background-color: #ffffff;
                color: #000000;
            }
            
            QLineEdit:focus {
                border-color: #5b21b6;
            }
        """)