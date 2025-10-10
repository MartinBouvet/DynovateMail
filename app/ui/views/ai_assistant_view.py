#!/usr/bin/env python3
"""
Vue Assistant IA avec chatbot Ollama - SUPER PUISSANT
"""
import logging
from typing import List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QScrollArea, QFrame, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont

from ai_processor import AIProcessor
from gmail_client import GmailClient

logger = logging.getLogger(__name__)

class ChatThread(QThread):
    """Thread pour les requêtes IA sans bloquer l'UI."""
    
    response_ready = pyqtSignal(str)
    
    def __init__(self, ai_processor: AIProcessor, message: str, history: List[Dict]):
        super().__init__()
        self.ai_processor = ai_processor
        self.message = message
        self.history = history
    
    def run(self):
        """Exécute la génération dans un thread séparé."""
        try:
            response = self.ai_processor.chat_with_assistant(self.message, self.history)
            self.response_ready.emit(response)
        except Exception as e:
            logger.error(f"Erreur chatbot: {e}")
            self.response_ready.emit(f"❌ Erreur: {e}")

class AIAssistantView(QWidget):
    """Vue Assistant IA avec chatbot super puissant."""
    
    def __init__(self, ai_processor: AIProcessor, gmail_client: GmailClient):
        super().__init__()
        
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.conversation_history = []
        self.chat_thread = None
        
        self._setup_ui()
        self._add_welcome_message()
    
    def _setup_ui(self):
        """Crée l'interface du chatbot."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # === EN-TÊTE ===
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5b21b6, stop:1 #7c3aed);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        header_layout = QVBoxLayout(header)
        
        title = QLabel("🤖 Assistant IA Dynovate")
        title.setFont(QFont("SF Pro Display", 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Posez-moi vos questions sur vos emails, la productivité, ou demandez-moi d'effectuer des tâches !")
        subtitle.setFont(QFont("SF Pro Display", 12))
        subtitle.setStyleSheet("color: #e9d5ff; background: transparent;")
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # === ZONE DE CONVERSATION ===
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #f9fafb;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(15, 15, 15, 15)
        self.chat_layout.setSpacing(15)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, stretch=1)
        
        # === ZONE DE SAISIE ===
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #5b21b6;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        input_layout = QHBoxLayout(input_frame)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("💬 Tapez votre message ici...")
        self.message_input.setFont(QFont("SF Pro Display", 13))
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                padding: 10px;
            }
        """)
        self.message_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton("📤 Envoyer")
        send_btn.setFont(QFont("SF Pro Display", 12, QFont.Bold))
        send_btn.setFixedSize(120, 45)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
            QPushButton:pressed {
                background-color: #4c1d95;
            }
        """)
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        
        layout.addWidget(input_frame)
        
        # === SUGGESTIONS RAPIDES ===
        suggestions_frame = QFrame()
        suggestions_layout = QHBoxLayout(suggestions_frame)
        suggestions_layout.setSpacing(10)
        
        suggestions = [
            "📊 Résume mes emails d'aujourd'hui",
            "⚡ Quels emails sont urgents ?",
            "📅 Ai-je des rendez-vous cette semaine ?",
            "🤖 Aide-moi à rédiger un email"
        ]
        
        for suggestion in suggestions:
            btn = QPushButton(suggestion)
            btn.setFont(QFont("SF Pro Display", 10))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f3f4f6;
                    border: 1px solid #d1d5db;
                    border-radius: 15px;
                    padding: 8px 15px;
                }
                QPushButton:hover {
                    background-color: #e5e7eb;
                }
            """)
            btn.clicked.connect(lambda checked, s=suggestion: self._use_suggestion(s))
            suggestions_layout.addWidget(btn)
        
        suggestions_layout.addStretch()
        layout.addWidget(suggestions_frame)
    
    def _add_welcome_message(self):
        """Ajoute le message de bienvenue."""
        welcome = """Bonjour ! 👋

Je suis votre assistant IA personnel, propulsé par Ollama et le modèle Ministral-8B.

Je peux vous aider à :
- 📧 Analyser et résumer vos emails
- ✍️ Rédiger des réponses professionnelles
- 📅 Gérer vos rendez-vous
- 🎯 Prioriser vos tâches
- 🤔 Répondre à vos questions

N'hésitez pas à me poser vos questions !"""
        
        self._add_message("assistant", welcome)
    
    def _add_message(self, role: str, content: str):
        """Ajoute un message à la conversation."""
        # Retirer le stretch temporairement
        if self.chat_layout.count() > 0:
            stretch_item = self.chat_layout.takeAt(self.chat_layout.count() - 1)
        
        message_frame = QFrame()
        
        if role == "user":
            message_frame.setStyleSheet("""
                QFrame {
                    background-color: #5b21b6;
                    border-radius: 15px;
                    padding: 15px;
                    margin-left: 100px;
                }
            """)
            alignment = Qt.AlignRight
            label_style = "color: white; background: transparent;"
        else:
            message_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 15px;
                    padding: 15px;
                    margin-right: 100px;
                }
            """)
            alignment = Qt.AlignLeft
            label_style = "color: #000000; background: transparent;"
        
        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(10, 10, 10, 10)
        
        # Icône + rôle
        header_layout = QHBoxLayout()
        icon = "👤" if role == "user" else "🤖"
        role_label = QLabel(f"{icon} {'Vous' if role == 'user' else 'Assistant IA'}")
        role_label.setFont(QFont("SF Pro Display", 10, QFont.Bold))
        role_label.setStyleSheet(label_style)
        header_layout.addWidget(role_label)
        header_layout.addStretch()
        message_layout.addLayout(header_layout)
        
        # Contenu
        content_label = QLabel(content)
        content_label.setFont(QFont("SF Pro Display", 12))
        content_label.setStyleSheet(label_style)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_layout.addWidget(content_label)
        
        self.chat_layout.addWidget(message_frame, alignment=alignment)
        
        # Remettre le stretch
        self.chat_layout.addStretch()
        
        # Scroller vers le bas
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))
    
    def _send_message(self):
        """Envoie un message au chatbot."""
        message = self.message_input.text().strip()
        
        if not message:
            return
        
        # Afficher le message utilisateur
        self._add_message("user", message)
        self.message_input.clear()
        
        # Ajouter à l'historique
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Afficher "En train d'écrire..."
        self._add_message("assistant", "💭 En train de réfléchir...")
        
        # Lancer la génération dans un thread
        self.chat_thread = ChatThread(self.ai_processor, message, self.conversation_history.copy())
        self.chat_thread.response_ready.connect(self._on_response_ready)
        self.chat_thread.start()
        
        # Désactiver l'input pendant la génération
        self.message_input.setEnabled(False)
    
    def _on_response_ready(self, response: str):
        """Callback quand la réponse IA est prête."""
        # Retirer le message "En train d'écrire..."
        if self.chat_layout.count() > 1:
            last_item = self.chat_layout.takeAt(self.chat_layout.count() - 2)
            if last_item and last_item.widget():
                last_item.widget().deleteLater()
        
        # Afficher la vraie réponse
        self._add_message("assistant", response)
        
        # Ajouter à l'historique
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Limiter l'historique à 20 messages
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        # Réactiver l'input
        self.message_input.setEnabled(True)
        self.message_input.setFocus()
    
    def _use_suggestion(self, suggestion: str):
        """Utilise une suggestion rapide."""
        self.message_input.setText(suggestion)
        self._send_message()