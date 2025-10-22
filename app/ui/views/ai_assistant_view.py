#!/usr/bin/env python3
"""
Assistant IA - VERSION CORRIGÉE avec design noir/blanc/violet et scroll
"""
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QProgressBar, QLineEdit, QTextEdit, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from app.ai_processor import AIProcessor
from app.gmail_client import GmailClient
from app.models.email_model import Email

logger = logging.getLogger(__name__)


class ChatbotDialog(QDialog):
    """Dialogue Chatbot pour générer des emails - AVEC SCROLL CORRIGÉ."""
    
    def __init__(self, parent=None, ai_processor=None, gmail_client=None):
        super().__init__(parent)
        
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.generated_email = None
        self.selected_tone = 'professional'
        
        self.setWindowTitle("🤖 Chatbot - Générateur d'emails")
        self.setMinimumSize(750, 700)
        self.setStyleSheet("background-color: #ffffff;")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface avec scroll activé."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # CRITIQUE : Tout dans une zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #ffffff; }")
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #ffffff;")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("🤖 Générateur d'emails intelligent")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        layout.addWidget(title)
        
        subtitle = QLabel("Décrivez l'email que vous souhaitez envoyer")
        subtitle.setFont(QFont("Arial", 13))
        subtitle.setStyleSheet("color: #6b7280;")
        layout.addWidget(subtitle)
        
        # Destinataire
        dest_label = QLabel("À qui voulez-vous écrire ?")
        dest_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        dest_label.setStyleSheet("color: #000000;")
        layout.addWidget(dest_label)
        
        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Ex: Jean Dupont, entreprise ABC, mon client...")
        self.recipient_input.setFont(QFont("Arial", 13))
        self.recipient_input.setFixedHeight(45)
        self.recipient_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 0 16px;
                background-color: #ffffff;
                color: #000000;
            }
            QLineEdit:focus {
                border-color: #5b21b6;
            }
        """)
        layout.addWidget(self.recipient_input)
        
        # Sujet/Contexte
        subject_label = QLabel("Quel est le sujet / contexte ?")
        subject_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        subject_label.setStyleSheet("color: #000000;")
        layout.addWidget(subject_label)
        
        self.context_input = QTextEdit()
        self.context_input.setPlaceholderText("Ex: Je souhaite relancer un client concernant un devis envoyé il y a 2 semaines...")
        self.context_input.setFont(QFont("Arial", 13))
        self.context_input.setMaximumHeight(120)
        self.context_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
                background-color: #ffffff;
                color: #000000;
            }
            QTextEdit:focus {
                border-color: #5b21b6;
            }
        """)
        layout.addWidget(self.context_input)
        
        # Ton
        tone_label = QLabel("Choisissez le ton de l'email")
        tone_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        tone_label.setStyleSheet("color: #000000;")
        layout.addWidget(tone_label)
        
        # Boutons de ton
        tone_layout = QHBoxLayout()
        tone_layout.setSpacing(12)
        
        self.tone_buttons = {}
        tones = [
            ('professional', '💼 Professionnel'),
            ('friendly', '😊 Amical'),
            ('formal', '🎩 Formel')
        ]
        
        for tone_id, tone_text in tones:
            btn = QPushButton(tone_text)
            btn.setFont(QFont("Arial", 12))
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(tone_id == 'professional')
            btn.clicked.connect(lambda checked, t=tone_id: self._select_tone(t))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f3f4f6;
                    color: #000000;
                    border: 2px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 8px 16px;
                }
                QPushButton:checked {
                    background-color: #5b21b6;
                    color: #ffffff;
                    border-color: #5b21b6;
                }
                QPushButton:hover {
                    border-color: #5b21b6;
                }
            """)
            self.tone_buttons[tone_id] = btn
            tone_layout.addWidget(btn)
        
        layout.addLayout(tone_layout)
        
        # Bouton générer
        generate_btn = QPushButton("✨ Générer l'email")
        generate_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        generate_btn.setFixedHeight(50)
        generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        generate_btn.clicked.connect(self._generate_email)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)
        layout.addWidget(generate_btn)
        
        # Résultat - AVEC SCROLL
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 2px solid #5b21b6;
                border-radius: 12px;
            }
        """)
        self.result_frame.hide()
        
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setContentsMargins(20, 20, 20, 20)
        result_layout.setSpacing(15)
        
        result_title = QLabel("📧 Email généré :")
        result_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        result_title.setStyleSheet("color: #000000;")
        result_layout.addWidget(result_title)
        
        # CRITIQUE : Scroll pour le résultat
        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setMinimumHeight(200)
        result_scroll.setMaximumHeight(300)
        result_scroll.setFrameShape(QFrame.Shape.NoFrame)
        result_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Arial", 13))
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: #ffffff;
                color: #000000;
                padding: 12px;
            }
        """)
        
        result_scroll.setWidget(self.result_text)
        result_layout.addWidget(result_scroll)
        
        # Boutons d'action
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        
        copy_btn = QPushButton("📋 Copier")
        copy_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        copy_btn.setFixedHeight(40)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_email)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)
        action_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("Fermer")
        close_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        close_btn.setFixedHeight(40)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        action_layout.addWidget(close_btn)
        
        result_layout.addLayout(action_layout)
        layout.addWidget(self.result_frame)
        
        # Ajouter au scroll
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def _select_tone(self, tone_id: str):
        """Sélectionne un ton."""
        self.selected_tone = tone_id
        for tid, btn in self.tone_buttons.items():
            btn.setChecked(tid == tone_id)
    
    def _generate_email(self):
        """Génère l'email avec l'IA."""
        recipient = self.recipient_input.text().strip()
        context = self.context_input.toPlainText().strip()
        
        if not recipient or not context:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "⚠️ Champs requis", "Veuillez remplir le destinataire et le contexte.")
            return
        
        # Générer avec l'IA
        tone_names = {
            'professional': 'professionnel et courtois',
            'friendly': 'amical et chaleureux',
            'formal': 'très formel et respectueux'
        }
        
        tone_text = tone_names.get(self.selected_tone, 'professionnel')
        
        prompt = f"""Génère un email {tone_text} en français.

Destinataire: {recipient}
Contexte: {context}

Rédige un email complet avec:
- Une formule de politesse d'ouverture adaptée
- Le corps du message (3-5 phrases, clair et précis)
- Une formule de politesse de clôture
- Une signature simple

Email:"""
        
        try:
            generated = self.ai_processor.ollama_client.generate(prompt, max_tokens=400)
            
            self.generated_email = generated.strip()
            self.result_text.setText(self.generated_email)
            self.result_frame.show()
            
        except Exception as e:
            logger.error(f"Erreur génération: {e}")
            self.result_text.setText("Erreur lors de la génération. Veuillez réessayer.")
            self.result_frame.show()
    
    def _copy_email(self):
        """Copie l'email."""
        from PyQt6.QtWidgets import QApplication, QMessageBox
        clipboard = QApplication.clipboard()
        clipboard.setText(self.generated_email)
        QMessageBox.information(self, "✅ Copié", "L'email a été copié dans le presse-papier !")


class AIAnalysisThread(QThread):
    """Thread pour analyses IA."""
    
    progress = pyqtSignal(str, int)
    analysis_complete = pyqtSignal(dict)
    
    def __init__(self, ai_processor: AIProcessor, gmail_client: GmailClient, action_type: str):
        super().__init__()
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.action_type = action_type
        self._running = True
    
    def run(self):
        """Exécute l'analyse."""
        try:
            if self.action_type == "upcoming_meetings":
                self._upcoming_meetings()
            elif self.action_type == "urgent_emails":
                self._urgent_emails()
            elif self.action_type == "needs_reply":
                self._needs_reply()
            elif self.action_type == "inbox_health":
                self._inbox_health()
        
        except Exception as e:
            logger.error(f"Erreur: {e}")
            self.analysis_complete.emit({'type': 'error', 'message': str(e)})
    
    def stop(self):
        self._running = False
    
    def _upcoming_meetings(self):
        """RDV à venir."""
        self.progress.emit("📅 Recherche des rendez-vous...", 20)
        
        emails = self.gmail_client.list_emails(folder="INBOX", max_results=50)
        
        meetings = []
        
        for i, email in enumerate(emails, 1):
            if not self._running:
                break
            
            progress = 20 + int((i / len(emails)) * 70)
            self.progress.emit(f"🔍 {i}/{len(emails)}", progress)
            
            subject_lower = email.subject.lower()
            snippet_lower = (email.snippet or '').lower()
            
            meeting_keywords = ['réunion', 'meeting', 'rdv', 'rendez-vous', 'entretien', 'call', 'visio', 'zoom', 'teams', 'skype']
            
            has_meeting = any(kw in subject_lower or kw in snippet_lower for kw in meeting_keywords)
            
            if has_meeting:
                import re
                
                date_found = "Date à confirmer"
                
                patterns = [
                    r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                    r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre))',
                    r'(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)',
                    r"(aujourd'hui|demain|ce soir)"
                ]
                
                text_to_search = f"{subject_lower} {snippet_lower}"
                for pattern in patterns:
                    match = re.search(pattern, text_to_search)
                    if match:
                        date_found = match.group(1)
                        break
                
                meetings.append({
                    'email': email,
                    'date_info': date_found
                })
        
        self.progress.emit("✅ Terminé !", 100)
        
        self.analysis_complete.emit({
            'type': 'upcoming_meetings',
            'total': len(emails),
            'meetings': meetings
        })
    
    def _urgent_emails(self):
        """Emails urgents."""
        self.progress.emit("🚨 Recherche emails urgents...", 30)
        
        emails = self.gmail_client.list_emails(folder="INBOX", max_results=50)
        
        urgent = []
        
        for i, email in enumerate(emails, 1):
            if not self._running:
                break
            
            progress = 30 + int((i / len(emails)) * 60)
            self.progress.emit(f"🔍 {i}/{len(emails)}", progress)
            
            subject = email.subject.lower()
            snippet = (email.snippet or '').lower()
            
            urgent_keywords = ['urgent', 'asap', 'immédiat', 'critique', 'important', 'rapidement']
            
            is_urgent = any(kw in subject or kw in snippet for kw in urgent_keywords)
            
            if is_urgent:
                urgent.append(email)
        
        self.progress.emit("✅ Terminé !", 100)
        
        self.analysis_complete.emit({
            'type': 'urgent_emails',
            'total': len(emails),
            'urgent': urgent
        })
    
    def _needs_reply(self):
        """Emails nécessitant réponse."""
        self.progress.emit("💬 Recherche emails à répondre...", 30)
        
        unread = self.gmail_client.list_emails(folder="INBOX", max_results=30)
        unread = [e for e in unread if not getattr(e, 'read', True)]
        
        needs_reply = []
        
        for i, email in enumerate(unread, 1):
            if not self._running:
                break
            
            progress = 30 + int((i / len(unread)) * 60)
            self.progress.emit(f"🔍 {i}/{len(unread)}", progress)
            
            subject = email.subject.lower()
            snippet = (email.snippet or '').lower()
            
            question_keywords = ['?', 'pouvez-vous', 'pourriez-vous', 'merci de', 'svp', 's il vous plait']
            
            needs_response = any(kw in subject or kw in snippet for kw in question_keywords)
            
            if needs_response:
                suggestion = "Bonjour,\n\nMerci pour votre message.\n\nJe prends note et reviens vers vous rapidement.\n\nCordialement"
                
                needs_reply.append({
                    'email': email,
                    'suggestion': suggestion
                })
        
        self.progress.emit("✅ Terminé !", 100)
        
        self.analysis_complete.emit({
            'type': 'needs_reply',
            'total': len(unread),
            'needs_reply': needs_reply
        })
    
    def _inbox_health(self):
        """Santé inbox."""
        self.progress.emit("📊 Analyse santé...", 30)
        
        emails = self.gmail_client.list_emails(folder="INBOX", max_results=100)
        
        self.progress.emit("💡 Calcul...", 60)
        
        total = len(emails)
        unread = len([e for e in emails if not getattr(e, 'read', True)])
        read_rate = int(((total - unread) / total * 100)) if total > 0 else 100
        
        score = 100
        if total > 50:
            score -= 15
        if unread > 20:
            score -= 20
        if read_rate < 50:
            score -= 25
        
        score = max(0, score)
        
        recs = []
        if unread > 20:
            recs.append("📧 Beaucoup d'emails non lus. Utilisez les fonctionnalités IA pour trier.")
        if total > 50:
            recs.append("🗄️ Inbox surchargée. Archivez les emails traités.")
        if len(recs) == 0:
            recs.append("🎉 Excellente gestion !")
        
        self.progress.emit("✅ Terminé !", 100)
        
        self.analysis_complete.emit({
            'type': 'inbox_health',
            'total': total,
            'unread': unread,
            'read_rate': read_rate,
            'score': score,
            'recommendations': recs
        })


class AIAssistantView(QWidget):
    """Vue Assistant IA - DESIGN CORRIGÉ noir/blanc/violet."""
    
    email_selected = pyqtSignal(Email)
    
    def __init__(self, ai_processor: AIProcessor, gmail_client: GmailClient):
        super().__init__()
        
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.analysis_thread = None
        self.stat_widgets = {}
        
        self._setup_ui()
        self._load_stats()
    
    def _setup_ui(self):
        """Interface avec design professionnel."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll principal
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f8f9fa; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        
        # Header avec gradient violet
        header = QFrame()
        header.setFixedHeight(200)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5b21b6, stop:0.5 #7c3aed, stop:1 #a78bfa);
            }
        """)
        
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(48, 28, 48, 28)
        header_layout.setSpacing(10)
        
        title = QLabel("🤖 Assistant IA Dynovate")
        title.setFont(QFont("Arial", 30, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("L'intelligence artificielle au service de votre productivité")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.95);")
        header_layout.addWidget(subtitle)
        
        header_layout.addSpacing(16)
        
        # Stats
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(18)
        
        stats_data = [
            ('inbox', '📥 Inbox', '0', '#ffffff'),
            ('unread', '✉️ Non lus', '0', '#ffffff'),
            ('health', '💚 Santé', '100%', '#ffffff')
        ]
        
        for stat_id, stat_label, stat_value, color in stats_data:
            stat_card = self._create_stat_card(stat_id, stat_label, stat_value, color)
            self.stat_widgets[stat_id] = stat_card
            stats_layout.addWidget(stat_card)
        
        header_layout.addLayout(stats_layout)
        scroll_layout.addWidget(header)
        
        # Body avec padding
        body = QWidget()
        body.setStyleSheet("background-color: #f8f9fa;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(48, 40, 48, 40)
        body_layout.setSpacing(24)
        
        # Cartes d'action
        grid = QVBoxLayout()
        grid.setSpacing(20)
        
        # Ligne 1
        row1 = QHBoxLayout()
        row1.setSpacing(20)
        
        row1.addWidget(self._create_card(
            "upcoming_meetings",
            "📅 Prochains RDV",
            "Détectez automatiquement les rendez-vous dans vos emails",
            "#5b21b6"
        ))
        
        row1.addWidget(self._create_card(
            "urgent_emails",
            "🚨 Emails Urgents",
            "Identifiez rapidement les messages prioritaires",
            "#dc2626"
        ))
        
        grid.addLayout(row1)
        
        # Ligne 2
        row2 = QHBoxLayout()
        row2.setSpacing(20)
        
        row2.addWidget(self._create_card(
            "needs_reply",
            "💬 Nécessitent Réponse",
            "Emails qui attendent une réponse + suggestions",
            "#0891b2"
        ))
        
        row2.addWidget(self._create_card(
            "inbox_health",
            "💚 Santé Inbox",
            "Analyse complète avec score et recommandations",
            "#059669"
        ))
        
        grid.addLayout(row2)
        
        # Ligne 3 - Chatbot (carte spéciale)
        chatbot_card = self._create_chatbot_card()
        grid.addWidget(chatbot_card)
        
        body_layout.addLayout(grid)
        
        # Résultats
        self.results_container = QFrame()
        self.results_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: 2px solid #e5e7eb;
            }
        """)
        self.results_container.hide()
        
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(32, 32, 32, 32)
        self.results_layout.setSpacing(20)
        
        body_layout.addWidget(self.results_container)
        
        # Progress
        self.progress_container = QFrame()
        self.progress_container.setFixedHeight(90)
        self.progress_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 2px solid #5b21b6;
            }
        """)
        self.progress_container.hide()
        
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(24, 20, 24, 20)
        progress_layout.setSpacing(12)
        
        self.progress_label = QLabel("Analyse en cours...")
        self.progress_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.progress_label.setStyleSheet("color: #000000;")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e5e7eb;
                border-radius: 6px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #5b21b6;
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        body_layout.addWidget(self.progress_container)
        
        scroll_layout.addWidget(body)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def _create_stat_card(self, stat_id: str, label: str, value: str, color: str) -> QFrame:
        """Crée une carte de statistique."""
        card = QFrame()
        card.setFixedSize(200, 85)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 11))
        label_widget.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setObjectName("stat-value")
        value_widget.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        value_widget.setStyleSheet("color: #ffffff;")
        layout.addWidget(value_widget)
        
        return card
    
    def _create_card(self, action_id: str, title: str, desc: str, color: str) -> QFrame:
        """Crée une carte d'action - DESIGN CORRIGÉ."""
        card = QFrame()
        card.setFixedSize(400, 180)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 2px solid #e5e7eb;
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {color};
                border-width: 3px;
            }}
        """)
        
        card.mousePressEvent = lambda e: self._run_action(action_id)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color};")
        layout.addWidget(title_label)
        
        desc_label = QLabel(desc)
        desc_label.setFont(QFont("Arial", 12))
        desc_label.setStyleSheet("color: #4b5563;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        btn = QPushButton("Lancer →")
        btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn.setFixedHeight(38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 19px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        layout.addWidget(btn)
        
        return card
    
    def _create_chatbot_card(self) -> QFrame:
        """Crée la carte chatbot - DESIGN CORRIGÉ."""
        card = QFrame()
        card.setFixedHeight(180)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5b21b6, stop:1 #7c3aed);
                border-radius: 16px;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4c1d95, stop:1 #6d28d9);
            }
        """)
        
        card.mousePressEvent = lambda e: self._open_chatbot()
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)
        
        # Icône
        icon = QLabel("🤖")
        icon.setFont(QFont("Arial", 56))
        layout.addWidget(icon)
        
        # Texte
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        
        title = QLabel("Chatbot - Générateur d'emails")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        text_layout.addWidget(title)
        
        desc = QLabel("Générez des emails personnalisés en quelques clics\nRelances, demandes de RDV, suivis clients...")
        desc.setFont(QFont("Arial", 13))
        desc.setStyleSheet("color: rgba(255, 255, 255, 0.95);")
        text_layout.addWidget(desc)
        
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # Flèche
        arrow = QLabel("→")
        arrow.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        arrow.setStyleSheet("color: #ffffff;")
        layout.addWidget(arrow)
        
        return card
    
    def _load_stats(self):
        """Charge les stats."""
        try:
            emails = self.gmail_client.list_emails(folder="INBOX", max_results=100)
            unread = len([e for e in emails if not getattr(e, 'read', True)])
            read_rate = int(((len(emails) - unread) / len(emails) * 100)) if len(emails) > 0 else 100
            
            self._update_stat('inbox', str(len(emails)))
            self._update_stat('unread', str(unread))
            self._update_stat('health', f"{read_rate}%")
        except:
            pass
    
    def _update_stat(self, key: str, value: str):
        """Met à jour une stat."""
        if key in self.stat_widgets:
            widget = self.stat_widgets[key]
            value_label = widget.findChild(QLabel, "stat-value")
            if value_label:
                value_label.setText(value)
    
    def _open_chatbot(self):
        """Ouvre le chatbot."""
        logger.info("🤖 Ouverture chatbot")
        
        dialog = ChatbotDialog(self, self.ai_processor, self.gmail_client)
        dialog.exec()
    
    def _run_action(self, action_id: str):
        """Lance une action."""
        logger.info(f"🚀 Action: {action_id}")
        
        # Afficher progress
        self.progress_container.show()
        self.progress_bar.setValue(0)
        self.results_container.hide()
        
        # Nettoyer résultats
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Thread
        self.analysis_thread = AIAnalysisThread(
            self.ai_processor,
            self.gmail_client,
            action_id
        )
        self.analysis_thread.progress.connect(self._update_progress)
        self.analysis_thread.analysis_complete.connect(self._show_results)
        self.analysis_thread.start()
    
    def _update_progress(self, message: str, percent: int):
        """Met à jour la progression."""
        self.progress_label.setText(message)
        self.progress_bar.setValue(percent)
    
    def _show_results(self, results: dict):
        """Affiche les résultats."""
        self.progress_container.hide()
        self.results_container.show()
        
        result_type = results.get('type')
        
        if result_type == 'upcoming_meetings':
            self._show_meetings(results)
        elif result_type == 'urgent_emails':
            self._show_urgent(results)
        elif result_type == 'needs_reply':
            self._show_needs_reply(results)
        elif result_type == 'inbox_health':
            self._show_health(results)
    
    def _show_meetings(self, results: dict):
        """Affiche les RDV."""
        meetings = results['meetings']
        
        title = QLabel(f"📅 {len(meetings)} rendez-vous trouvés")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        self.results_layout.addWidget(title)
        
        if not meetings:
            empty = QLabel("Aucun rendez-vous détecté dans vos emails récents.")
            empty.setFont(QFont("Arial", 14))
            empty.setStyleSheet("color: #6b7280;")
            self.results_layout.addWidget(empty)
            return
        
        # Liste scrollable des RDV
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        scroll.setMaximumHeight(500)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        
        for meeting in meetings:
            card = self._create_meeting_card(meeting)
            scroll_layout.addWidget(card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        self.results_layout.addWidget(scroll)
    
    def _create_meeting_card(self, meeting: dict) -> QFrame:
        """Crée une carte RDV."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        email = meeting['email']
        
        subject = QLabel(email.subject)
        subject.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        subject.setStyleSheet("color: #000000;")
        subject.setWordWrap(True)
        layout.addWidget(subject)
        
        from_label = QLabel(f"De: {email.sender}")
        from_label.setFont(QFont("Arial", 12))
        from_label.setStyleSheet("color: #6b7280;")
        layout.addWidget(from_label)
        
        date_label = QLabel(f"📅 {meeting['date_info']}")
        date_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        date_label.setStyleSheet("color: #5b21b6;")
        layout.addWidget(date_label)
        
        return card
    
    def _show_urgent(self, results: dict):
        """Affiche les emails urgents."""
        urgent = results['urgent']
        
        title = QLabel(f"🚨 {len(urgent)} emails urgents")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        self.results_layout.addWidget(title)
        
        if not urgent:
            empty = QLabel("Aucun email urgent détecté. Vous êtes à jour !")
            empty.setFont(QFont("Arial", 14))
            empty.setStyleSheet("color: #6b7280;")
            self.results_layout.addWidget(empty)
            return
        
        # Liste scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        scroll.setMaximumHeight(500)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        
        for email in urgent:
            card = self._create_email_card(email)
            scroll_layout.addWidget(card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        self.results_layout.addWidget(scroll)
    
    def _show_needs_reply(self, results: dict):
        """Affiche les emails nécessitant réponse."""
        needs_reply = results['needs_reply']
        
        title = QLabel(f"💬 {len(needs_reply)} emails nécessitent une réponse")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        self.results_layout.addWidget(title)
        
        if not needs_reply:
            empty = QLabel("Aucun email en attente de réponse.")
            empty.setFont(QFont("Arial", 14))
            empty.setStyleSheet("color: #6b7280;")
            self.results_layout.addWidget(empty)
            return
        
        # Liste scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        scroll.setMaximumHeight(500)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        
        for item in needs_reply:
            card = self._create_reply_card(item)
            scroll_layout.addWidget(card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        self.results_layout.addWidget(scroll)
    
    def _create_email_card(self, email: Email) -> QFrame:
        """Crée une carte email."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        subject = QLabel(email.subject)
        subject.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        subject.setStyleSheet("color: #000000;")
        subject.setWordWrap(True)
        layout.addWidget(subject)
        
        from_label = QLabel(f"De: {email.sender}")
        from_label.setFont(QFont("Arial", 12))
        from_label.setStyleSheet("color: #6b7280;")
        layout.addWidget(from_label)
        
        snippet = QLabel(email.snippet[:100] + "..." if len(email.snippet) > 100 else email.snippet)
        snippet.setFont(QFont("Arial", 11))
        snippet.setStyleSheet("color: #9ca3af;")
        snippet.setWordWrap(True)
        layout.addWidget(snippet)
        
        return card
    
    def _create_reply_card(self, item: dict) -> QFrame:
        """Crée une carte avec suggestion de réponse."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        
        email = item['email']
        
        subject = QLabel(email.subject)
        subject.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        subject.setStyleSheet("color: #000000;")
        subject.setWordWrap(True)
        layout.addWidget(subject)
        
        from_label = QLabel(f"De: {email.sender}")
        from_label.setFont(QFont("Arial", 12))
        from_label.setStyleSheet("color: #6b7280;")
        layout.addWidget(from_label)
        
        suggestion_label = QLabel("💡 Suggestion de réponse :")
        suggestion_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        suggestion_label.setStyleSheet("color: #059669;")
        layout.addWidget(suggestion_label)
        
        suggestion_text = QLabel(item['suggestion'][:150] + "...")
        suggestion_text.setFont(QFont("Arial", 11))
        suggestion_text.setStyleSheet("color: #6b7280;")
        suggestion_text.setWordWrap(True)
        layout.addWidget(suggestion_text)
        
        return card
    
    def _show_health(self, results: dict):
        """Affiche la santé de l'inbox."""
        score = results['score']
        
        title = QLabel(f"💚 Score de santé : {score}/100")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        self.results_layout.addWidget(title)
        
        # Barre de score
        score_bar = QProgressBar()
        score_bar.setValue(score)
        score_bar.setFixedHeight(30)
        score_bar.setTextVisible(True)
        
        if score >= 80:
            color = "#10b981"
        elif score >= 60:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        
        score_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #e5e7eb;
                border-radius: 15px;
                text-align: center;
                color: #000000;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 15px;
            }}
        """)
        self.results_layout.addWidget(score_bar)
        
        # Stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(30)
        
        stats_data = [
            ("Total", results['total']),
            ("Non lus", results['unread']),
            ("Taux de lecture", f"{results['read_rate']}%")
        ]
        
        for label, value in stats_data:
            stat_layout = QVBoxLayout()
            stat_layout.setSpacing(4)
            
            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
            value_label.setStyleSheet("color: #5b21b6;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(value_label)
            
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 12))
            label_widget.setStyleSheet("color: #6b7280;")
            label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(label_widget)
            
            stats_layout.addLayout(stat_layout)
        
        self.results_layout.addWidget(stats_frame)
        
        # Recommandations
        recs_label = QLabel("📋 Recommandations :")
        recs_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        recs_label.setStyleSheet("color: #000000;")
        self.results_layout.addWidget(recs_label)
        
        for rec in results['recommendations']:
            rec_label = QLabel(f"• {rec}")
            rec_label.setFont(QFont("Arial", 13))
            rec_label.setStyleSheet("color: #4b5563;")
            rec_label.setWordWrap(True)
            self.results_layout.addWidget(rec_label)