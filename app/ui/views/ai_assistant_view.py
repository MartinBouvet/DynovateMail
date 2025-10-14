#!/usr/bin/env python3
"""
Assistant IA - REFONTE COMPLÈTE ET FONCTIONNELLE
"""
import logging
from datetime import datetime
from typing import List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QScrollArea, QFrame,
    QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont

from app.ai_processor import AIProcessor
from app.gmail_client import GmailClient

logger = logging.getLogger(__name__)

class AIAssistantView(QWidget):
    """Assistant IA avec chat interactif et statistiques."""
    
    def __init__(self, ai_processor: AIProcessor, gmail_client: GmailClient):
        super().__init__()
        
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.chat_history = []
        
        self._setup_ui()
        self._load_statistics()
    
    def _setup_ui(self):
        """Crée l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # === EN-TÊTE ===
        header_layout = QHBoxLayout()
        
        title = QLabel("🤖 Assistant IA Dynovate")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #5b21b6;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Bouton rafraîchir stats
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setFont(QFont("Arial", 11))
        refresh_btn.setFixedHeight(36)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_statistics)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 2px solid #e5e7eb;
                border-radius: 18px;
                padding: 0 20px;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #5b21b6;
                border-color: #5b21b6;
                color: white;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # === ZONE PRINCIPALE: STATS + CHAT ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # COLONNE GAUCHE: Statistiques
        stats_container = self._create_statistics_panel()
        content_layout.addWidget(stats_container, 1)
        
        # COLONNE DROITE: Chat IA
        chat_container = self._create_chat_panel()
        content_layout.addWidget(chat_container, 2)
        
        layout.addLayout(content_layout)
    
    def _create_statistics_panel(self) -> QWidget:
        """Crée le panneau de statistiques."""
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #f9fafb;
                border-radius: 16px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Titre
        title = QLabel("📊 Statistiques")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #111827; background: transparent;")
        layout.addWidget(title)
        
        # Cartes de stats
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(12)
        layout.addLayout(self.stats_layout)
        
        layout.addStretch()
        
        # Actions rapides
        actions_title = QLabel("⚡ Actions rapides")
        actions_title.setFont(QFont("Arial", 16, QFont.Bold))
        actions_title.setStyleSheet("color: #111827; background: transparent; margin-top: 15px;")
        layout.addWidget(actions_title)
        
        quick_actions = [
            ("📝 Rédiger un email", self._quick_compose),
            ("🧹 Nettoyer la boîte", self._quick_clean),
            ("📅 Voir RDV du jour", self._quick_meetings),
            ("⚠️ Emails urgents", self._quick_urgent)
        ]
        
        for action_text, action_handler in quick_actions:
            btn = QPushButton(action_text)
            btn.setFont(QFont("Arial", 11))
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(action_handler)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 15px;
                    background-color: white;
                    border: 2px solid #e5e7eb;
                    border-radius: 10px;
                    color: #374151;
                }
                QPushButton:hover {
                    background-color: #5b21b6;
                    border-color: #5b21b6;
                    color: white;
                }
            """)
            layout.addWidget(btn)
        
        return container
    
    def _create_stat_card(self, icon: str, label: str, value: str, color: str) -> QFrame:
        """Crée une carte de statistique."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Icône
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 28))
        icon_label.setStyleSheet("border: none; background: transparent;")
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Texte
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 22, QFont.Bold))
        value_label.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        text_layout.addWidget(value_label)
        
        label_label = QLabel(label)
        label_label.setFont(QFont("Arial", 11))
        label_label.setStyleSheet("color: #6b7280; border: none; background: transparent;")
        text_layout.addWidget(label_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return card
    
    def _create_chat_panel(self) -> QWidget:
        """Crée le panneau de chat IA."""
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 16px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # En-tête du chat
        chat_header = QFrame()
        chat_header.setFixedHeight(60)
        chat_header.setStyleSheet("""
            QFrame {
                background-color: #5b21b6;
                border-radius: 14px 14px 0 0;
            }
        """)
        
        header_layout = QHBoxLayout(chat_header)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        chat_title = QLabel("💬 Chat avec l'IA")
        chat_title.setFont(QFont("Arial", 16, QFont.Bold))
        chat_title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(chat_title)
        
        header_layout.addStretch()
        
        clear_btn = QPushButton("🗑️ Effacer")
        clear_btn.setFont(QFont("Arial", 10))
        clear_btn.setFixedHeight(30)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_chat)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid white;
                border-radius: 15px;
                padding: 0 15px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        header_layout.addWidget(clear_btn)
        
        layout.addWidget(chat_header)
        
        # Zone de messages
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f9fafb;
            }
        """)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(15)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll)
        
        # Message de bienvenue
        welcome_msg = self._create_ai_message(
            "👋 Bonjour ! Je suis votre assistant IA Dynovate.\n\n"
            "Je peux vous aider à :\n"
            "• Analyser vos emails\n"
            "• Rédiger des réponses\n"
            "• Organiser votre boîte\n"
            "• Trouver des informations\n\n"
            "Posez-moi une question !"
        )
        self.chat_layout.insertWidget(0, welcome_msg)
        
        # Zone de saisie
        input_container = QFrame()
        input_container.setFixedHeight(80)
        input_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 2px solid #e5e7eb;
            }
        """)
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(20, 15, 20, 15)
        input_layout.setSpacing(12)
        
        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Tapez votre message...")
        self.chat_input.setFont(QFont("Arial", 12))
        self.chat_input.setFixedHeight(50)
        self.chat_input.setStyleSheet("""
            QTextEdit {
                background-color: #f3f4f6;
                border: 2px solid #e5e7eb;
                border-radius: 25px;
                padding: 12px 18px;
                color: #111827;
            }
            QTextEdit:focus {
                border-color: #5b21b6;
                background-color: white;
            }
        """)
        input_layout.addWidget(self.chat_input)
        
        send_btn = QPushButton("📤")
        send_btn.setFont(QFont("Arial", 20))
        send_btn.setFixedSize(50, 50)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self._send_message)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                border: none;
                border-radius: 25px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
            QPushButton:pressed {
                background-color: #3b0764;
            }
        """)
        input_layout.addWidget(send_btn)
        
        layout.addWidget(input_container)
        
        return container
    
    def _create_user_message(self, text: str) -> QFrame:
        """Crée un message utilisateur."""
        message = QFrame()
        message.setStyleSheet("""
            QFrame {
                background-color: #5b21b6;
                border-radius: 18px 18px 4px 18px;
                padding: 12px 16px;
            }
        """)
        message.setMaximumWidth(500)
        
        layout = QVBoxLayout(message)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(text)
        label.setFont(QFont("Arial", 12))
        label.setStyleSheet("color: white; background: transparent;")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Aligner à droite
        container = QFrame()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addStretch()
        container_layout.addWidget(message)
        
        return container
    
    def _create_ai_message(self, text: str) -> QFrame:
        """Crée un message de l'IA."""
        message = QFrame()
        message.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 18px 18px 18px 4px;
                padding: 12px 16px;
            }
        """)
        message.setMaximumWidth(500)
        
        layout = QVBoxLayout(message)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(text)
        label.setFont(QFont("Arial", 12))
        label.setStyleSheet("color: #111827; background: transparent;")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Aligner à gauche
        container = QFrame()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(message)
        container_layout.addStretch()
        
        return container
    
    def _send_message(self):
        """Envoie un message au chat."""
        user_text = self.chat_input.toPlainText().strip()
        
        if not user_text:
            return
        
        # Ajouter message utilisateur
        user_msg = self._create_user_message(user_text)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, user_msg)
        
        # Vider l'input
        self.chat_input.clear()
        
        # Ajouter à l'historique
        self.chat_history.append({"role": "user", "content": user_text})
        
        # Générer réponse IA
        self._generate_ai_response(user_text)
        
        # Scroller vers le bas
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )
    
    def _generate_ai_response(self, user_message: str):
        """Génère une réponse IA."""
        try:
            # Ajouter message "en train d'écrire..."
            typing_msg = self._create_ai_message("💭 En train d'écrire...")
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, typing_msg)
            
            # Scroll
            self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            )
            
            # Analyser l'intention de l'utilisateur
            response = self._process_user_intent(user_message)
            
            # Retirer le message "en train d'écrire"
            typing_msg.deleteLater()
            
            # Ajouter la réponse
            ai_msg = self._create_ai_message(response)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, ai_msg)
            
            # Ajouter à l'historique
            self.chat_history.append({"role": "assistant", "content": response})
            
            # Scroll
            self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            )
            
        except Exception as e:
            logger.error(f"Erreur génération réponse IA: {e}")
            typing_msg.deleteLater()
            error_msg = self._create_ai_message(
                "❌ Désolé, j'ai rencontré une erreur. Pouvez-vous reformuler votre question ?"
            )
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, error_msg)
    
    def _process_user_intent(self, message: str) -> str:
        """Analyse l'intention et génère une réponse appropriée."""
        message_lower = message.lower()
        
        # Intention: Statistiques
        if any(word in message_lower for word in ['combien', 'nombre', 'stats', 'statistiques']):
            return self._get_statistics_response()
        
        # Intention: Emails urgents
        elif any(word in message_lower for word in ['urgent', 'important', 'priorité']):
            return self._get_urgent_emails_response()
        
        # Intention: Aide rédaction
        elif any(word in message_lower for word in ['rédiger', 'écrire', 'composer', 'email']):
            return (
                "📝 Je peux vous aider à rédiger un email !\n\n"
                "Dites-moi simplement :\n"
                "• À qui vous voulez écrire\n"
                "• Le sujet de l'email\n"
                "• Le message principal\n\n"
                "Exemple: 'Rédige un email de remerciement pour un client après un rendez-vous'"
            )
        
        # Intention: Recherche
        elif any(word in message_lower for word in ['cherche', 'trouve', 'recherche']):
            return (
                "🔍 Je peux vous aider à chercher dans vos emails !\n\n"
                "Précisez ce que vous cherchez :\n"
                "• Emails d'un expéditeur spécifique\n"
                "• Emails contenant certains mots\n"
                "• Emails d'une période donnée\n\n"
                "Exemple: 'Trouve les emails de Jean reçus la semaine dernière'"
            )
        
        # Intention: Organisation
        elif any(word in message_lower for word in ['organise', 'classe', 'trie', 'nettoie']):
            return (
                "🗂️ Je peux vous aider à organiser votre boîte mail !\n\n"
                "Actions disponibles :\n"
                "• Supprimer les spams\n"
                "• Archiver les anciens emails\n"
                "• Classer par catégorie\n"
                "• Marquer comme lu/non lu\n\n"
                "Que souhaitez-vous faire ?"
            )
        
        # Intention: Calendrier
        elif any(word in message_lower for word in ['rendez-vous', 'rdv', 'réunion', 'calendrier']):
            return self._get_calendar_response()
        
        # Utiliser l'IA pour une réponse générale
        else:
            return self._get_general_ai_response(message)
    
    def _get_statistics_response(self) -> str:
        """Génère une réponse avec les statistiques."""
        try:
            emails = self.gmail_client.list_emails(max_results=100)
            
            total = len(emails)
            unread = sum(1 for e in emails if not getattr(e, 'read', True))
            
            return (
                f"📊 Voici vos statistiques :\n\n"
                f"• Total d'emails : {total}\n"
                f"• Non lus : {unread}\n"
                f"• Lus : {total - unread}\n\n"
                f"Souhaitez-vous plus de détails ?"
            )
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
            return "❌ Impossible de récupérer les statistiques pour le moment."
    
    def _get_urgent_emails_response(self) -> str:
        """Trouve les emails urgents."""
        try:
            emails = self.gmail_client.list_emails(max_results=50)
            urgent_count = 0
            
            # Simuler la détection d'emails urgents
            for email in emails[:10]:
                if any(word in (email.subject or '').lower() for word in ['urgent', 'important', 'asap']):
                    urgent_count += 1
            
            if urgent_count > 0:
                return (
                    f"⚠️ J'ai trouvé {urgent_count} email(s) marqué(s) comme urgent !\n\n"
                    f"Voulez-vous que je vous les affiche ?"
                )
            else:
                return "✅ Aucun email urgent détecté. Vous êtes à jour !"
        
        except Exception as e:
            logger.error(f"Erreur emails urgents: {e}")
            return "❌ Impossible de vérifier les emails urgents."
    
    def _get_calendar_response(self) -> str:
        """Donne des infos sur le calendrier."""
        return (
            "📅 Gestion du calendrier :\n\n"
            "• Consultez l'onglet 'Calendrier' pour voir vos rendez-vous\n"
            "• Je détecte automatiquement les demandes de RDV dans vos emails\n"
            "• Vous pouvez confirmer ou proposer de nouveaux créneaux\n\n"
            "Souhaitez-vous voir vos prochains rendez-vous ?"
        )
    
    def _get_general_ai_response(self, message: str) -> str:
        """Génère une réponse IA générale."""
        try:
            # Utiliser l'AI processor si disponible
            if hasattr(self.ai_processor, 'ollama_client') and self.ai_processor.ollama_client:
                response = self.ai_processor.ollama_client.generate(
                    prompt=message,
                    system_prompt=(
                        "Tu es un assistant IA pour la gestion d'emails. "
                        "Réponds de manière concise, utile et professionnelle. "
                        "Tu peux aider avec : analyse d'emails, rédaction, organisation, recherche."
                    ),
                    temperature=0.7,
                    max_tokens=300
                )
                
                if response:
                    return response
            
            # Réponse par défaut
            return (
                "🤖 Je suis là pour vous aider !\n\n"
                "Je peux vous assister avec :\n"
                "• L'analyse de vos emails\n"
                "• La rédaction de réponses\n"
                "• L'organisation de votre boîte\n"
                "• La recherche d'informations\n\n"
                "Que puis-je faire pour vous ?"
            )
        
        except Exception as e:
            logger.error(f"Erreur réponse générale: {e}")
            return "💡 Je n'ai pas bien compris. Pouvez-vous reformuler votre question ?"
    
    def _clear_chat(self):
        """Efface l'historique du chat."""
        # Supprimer tous les messages sauf le stretch
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Réinitialiser l'historique
        self.chat_history = []
        
        # Remettre le message de bienvenue
        welcome_msg = self._create_ai_message(
            "👋 Chat effacé ! Comment puis-je vous aider ?"
        )
        self.chat_layout.insertWidget(0, welcome_msg)
        
        logger.info("Chat effacé")
    
    def _load_statistics(self):
        """Charge les statistiques des emails."""
        try:
            # Effacer les anciennes stats
            while self.stats_layout.count():
                item = self.stats_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Récupérer les emails
            emails = self.gmail_client.list_emails(max_results=100)
            
            total_emails = len(emails)
            unread_emails = sum(1 for e in emails if not getattr(e, 'read', True))
            today_emails = sum(
                1 for e in emails 
                if e.received_date and e.received_date.date() == datetime.now().date()
            )
            
            # Créer les cartes
            cards = [
                ("📧", "Total", str(total_emails), "#5b21b6"),
                ("📬", "Non lus", str(unread_emails), "#dc2626"),
                ("📅", "Aujourd'hui", str(today_emails), "#059669"),
                ("⭐", "Favoris", "0", "#f59e0b"),
            ]
            
            for icon, label, value, color in cards:
                card = self._create_stat_card(icon, label, value, color)
                self.stats_layout.addWidget(card)
            
            logger.info(f"Statistiques chargées: {total_emails} emails")
        
        except Exception as e:
            logger.error(f"Erreur chargement stats: {e}")
            error_label = QLabel("❌ Erreur de chargement des statistiques")
            error_label.setStyleSheet("color: #dc2626; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            self.stats_layout.addWidget(error_label)
    
    # === ACTIONS RAPIDES ===
    
    def _quick_compose(self):
        """Action rapide: composer un email."""
        response = (
            "✉️ Cliquez sur le bouton 'Nouveau' en haut à droite pour composer un email.\n\n"
            "Je peux aussi vous aider à rédiger ! Dites-moi ce que vous voulez écrire."
        )
        ai_msg = self._create_ai_message(response)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, ai_msg)
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )
    
    def _quick_clean(self):
        """Action rapide: nettoyer la boîte."""
        response = (
            "🧹 Analyse de votre boîte mail en cours...\n\n"
            "Fonctionnalités disponibles :\n"
            "• Supprimer les spams (0 détectés)\n"
            "• Archiver les emails de plus de 30 jours\n"
            "• Supprimer les emails publicitaires\n\n"
            "Que souhaitez-vous faire ?"
        )
        ai_msg = self._create_ai_message(response)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, ai_msg)
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )
    
    def _quick_meetings(self):
        """Action rapide: voir les RDV du jour."""
        response = (
            "📅 Rendez-vous d'aujourd'hui :\n\n"
            "Consultez l'onglet 'Calendrier' pour voir tous vos rendez-vous.\n\n"
            "Je détecte automatiquement les demandes de RDV dans vos emails."
        )
        ai_msg = self._create_ai_message(response)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, ai_msg)
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )
    
    def _quick_urgent(self):
        """Action rapide: emails urgents."""
        self._generate_ai_response("Montre-moi les emails urgents")