#!/usr/bin/env python3
"""
Assistant IA - VERSION FINALE RÉVOLUTIONNAIRE
Toutes les fonctionnalités utiles + Chatbot
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
    """Dialogue Chatbot pour générer des emails."""
    
    def __init__(self, parent=None, ai_processor=None, gmail_client=None):
        super().__init__(parent)
        
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.generated_email = None
        
        self.setWindowTitle("🤖 Chatbot - Générateur d'emails")
        self.setFixedSize(700, 600)
        self.setStyleSheet("background-color: #ffffff;")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface du chatbot."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("🤖 Générateur d'emails intelligent")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)
        
        subtitle = QLabel("Décrivez l'email que vous souhaitez envoyer")
        subtitle.setFont(QFont("Arial", 13))
        subtitle.setStyleSheet("color: #718096;")
        layout.addWidget(subtitle)
        
        # Destinataire
        dest_label = QLabel("À qui voulez-vous écrire ?")
        dest_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        dest_label.setStyleSheet("color: #2d3748;")
        layout.addWidget(dest_label)
        
        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Ex: Jean Dupont, entreprise ABC, mon client...")
        self.recipient_input.setFont(QFont("Arial", 13))
        self.recipient_input.setFixedHeight(45)
        self.recipient_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 0 16px;
                background-color: #ffffff;
                color: #1a202c;
            }
            QLineEdit:focus {
                border-color: #667eea;
            }
        """)
        layout.addWidget(self.recipient_input)
        
        # Sujet/Contexte
        subject_label = QLabel("Quel est le sujet / contexte ?")
        subject_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        subject_label.setStyleSheet("color: #2d3748;")
        layout.addWidget(subject_label)
        
        self.context_input = QTextEdit()
        self.context_input.setPlaceholderText("Ex: Relancer pour obtenir un devis, demander un rendez-vous, suivre une commande...")
        self.context_input.setFont(QFont("Arial", 13))
        self.context_input.setFixedHeight(120)
        self.context_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                background-color: #ffffff;
                color: #1a202c;
            }
            QTextEdit:focus {
                border-color: #667eea;
            }
        """)
        layout.addWidget(self.context_input)
        
        # Ton
        tone_label = QLabel("Ton du message")
        tone_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        tone_label.setStyleSheet("color: #2d3748;")
        layout.addWidget(tone_label)
        
        tone_layout = QHBoxLayout()
        tone_layout.setSpacing(10)
        
        self.tone_buttons = {}
        tones = [
            ("Professionnel", "professional"),
            ("Amical", "friendly"),
            ("Formel", "formal")
        ]
        
        for label, tone_id in tones:
            btn = QPushButton(label)
            btn.setFont(QFont("Arial", 12))
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=tone_id: self._select_tone(t))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #4a5568;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                }
                QPushButton:checked {
                    background-color: #667eea;
                    color: white;
                    border-color: #667eea;
                }
                QPushButton:hover {
                    border-color: #667eea;
                }
            """)
            self.tone_buttons[tone_id] = btn
            tone_layout.addWidget(btn)
        
        self.tone_buttons["professional"].setChecked(True)
        self.selected_tone = "professional"
        
        layout.addLayout(tone_layout)
        
        layout.addSpacing(10)
        
        # Bouton générer
        generate_btn = QPushButton("✨ Générer l'email")
        generate_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        generate_btn.setFixedHeight(50)
        generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        generate_btn.clicked.connect(self._generate_email)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: #5a67d8;
            }
        """)
        layout.addWidget(generate_btn)
        
        # Résultat
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet("""
            QFrame {
                background-color: #f7fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        self.result_frame.hide()
        
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setSpacing(12)
        
        result_title = QLabel("📧 Email généré")
        result_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        result_title.setStyleSheet("color: #2d3748;")
        result_layout.addWidget(result_title)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Arial", 12))
        self.result_text.setFixedHeight(150)
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                padding: 12px;
                background-color: #ffffff;
                color: #1a202c;
            }
        """)
        result_layout.addWidget(self.result_text)
        
        # Boutons action
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        copy_btn = QPushButton("📋 Copier")
        copy_btn.setFont(QFont("Arial", 11))
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_email)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #48bb78;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #38a169;
            }
        """)
        action_layout.addWidget(copy_btn)
        
        regenerate_btn = QPushButton("🔄 Régénérer")
        regenerate_btn.setFont(QFont("Arial", 11))
        regenerate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        regenerate_btn.clicked.connect(self._generate_email)
        regenerate_btn.setStyleSheet("""
            QPushButton {
                background-color: #ed8936;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #dd6b20;
            }
        """)
        action_layout.addWidget(regenerate_btn)
        
        action_layout.addStretch()
        result_layout.addLayout(action_layout)
        
        layout.addWidget(self.result_frame)
        
        layout.addStretch()
    
    def _select_tone(self, tone_id: str):
        """Sélectionne un ton."""
        self.selected_tone = tone_id
        for tid, btn in self.tone_buttons.items():
            btn.setChecked(tid == tone_id)
    
    def _generate_email(self):
        """Génère l'email."""
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
            
            # Mots-clés RDV
            meeting_keywords = ['réunion', 'meeting', 'rdv', 'rendez-vous', 'entretien', 'call', 'visio', 'zoom', 'teams', 'skype']
            
            has_meeting = any(kw in subject_lower or kw in snippet_lower for kw in meeting_keywords)
            
            if has_meeting:
                # Extraire date
                import re
                
                date_found = "Date à confirmer"
                
                # Patterns
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
        self.progress.emit("🚨 Détection des urgents...", 20)
        
        emails = self.gmail_client.list_emails(folder="INBOX", max_results=30)
        
        urgent = []
        
        for i, email in enumerate(emails, 1):
            if not self._running:
                break
            
            progress = 20 + int((i / len(emails)) * 70)
            self.progress.emit(f"⚡ {i}/{len(emails)}", progress)
            
            subject_lower = email.subject.lower()
            snippet_lower = (email.snippet or '').lower()
            
            # Détection urgence
            urgent_keywords = ['urgent', 'asap', 'immédiat', "aujourd'hui", 'deadline', 'rappel', 'important']
            
            is_urgent = any(kw in subject_lower for kw in urgent_keywords)
            
            if is_urgent:
                reason = next((kw for kw in urgent_keywords if kw in subject_lower), 'urgent')
                urgent.append({
                    'email': email,
                    'reason': f"Contient '{reason}'"
                })
        
        self.progress.emit("✅ Terminé !", 100)
        
        self.analysis_complete.emit({
            'type': 'urgent_emails',
            'total': len(emails),
            'urgent': urgent
        })
    
    def _needs_reply(self):
        """Emails nécessitant réponse."""
        self.progress.emit("💬 Analyse des emails...", 20)
        
        emails = self.gmail_client.list_emails(folder="INBOX", max_results=20)
        unread = [e for e in emails if not getattr(e, 'read', True)][:10]
        
        needs_reply = []
        
        for i, email in enumerate(unread, 1):
            if not self._running:
                break
            
            progress = 20 + int((i / len(unread)) * 70)
            self.progress.emit(f"💬 {i}/{len(unread)}", progress)
            
            subject_lower = email.subject.lower()
            snippet_lower = (email.snippet or '').lower()
            
            # Mots-clés nécessitant réponse
            reply_keywords = ['?', 'question', 'pouvez-vous', 'pourriez-vous', 'merci de', 'besoin', 'demande', 'confirmer']
            
            needs_response = any(kw in subject_lower or kw in snippet_lower for kw in reply_keywords)
            
            if needs_response:
                # Générer suggestion
                suggestion = f"Bonjour,\n\nMerci pour votre message. Je prends note et reviens vers vous rapidement.\n\nCordialement"
                
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
        
        # Score
        score = 100
        if total > 50:
            score -= 15
        if unread > 20:
            score -= 20
        if read_rate < 50:
            score -= 25
        
        score = max(0, score)
        
        # Recommandations
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
    """Vue Assistant IA - FINALE."""
    
    email_selected = pyqtSignal(Email)
    
    def __init__(self, ai_processor: AIProcessor, gmail_client: GmailClient):
        super().__init__()
        
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.analysis_thread = None
        
        self._setup_ui()
        self._load_stats()
    
    def _setup_ui(self):
        """Interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f8f9fa; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        
        # Header gradient
        header = QFrame()
        header.setFixedHeight(200)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
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
        
        self.stat_widgets = {}
        stats = [
            ("inbox", "📥", "0", "Inbox"),
            ("unread", "✉️", "0", "Non lus"),
            ("health", "💚", "0%", "Santé")
        ]
        
        for key, icon, value, label in stats:
            stat = self._create_stat(icon, value, label)
            self.stat_widgets[key] = stat
            stats_layout.addWidget(stat)
        
        stats_layout.addStretch()
        header_layout.addLayout(stats_layout)
        
        scroll_layout.addWidget(header)
        
        # Corps
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(48, 36, 48, 36)
        body_layout.setSpacing(28)
        
        # Titre
        main_title = QLabel("🚀 Fonctionnalités")
        main_title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        main_title.setStyleSheet("color: #1a202c;")
        body_layout.addWidget(main_title)
        
        # Grid
        grid = QVBoxLayout()
        grid.setSpacing(16)
        
        # Ligne 1
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        
        row1.addWidget(self._create_card(
            "upcoming_meetings",
            "📅 RDV à venir",
            "Trouve tous vos rendez-vous à venir dans vos emails",
            "#667eea"
        ))
        
        row1.addWidget(self._create_card(
            "urgent_emails",
            "🚨 Emails Urgents",
            "Détecte les emails qui nécessitent une action immédiate",
            "#f093fb"
        ))
        
        grid.addLayout(row1)
        
        # Ligne 2
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        
        row2.addWidget(self._create_card(
            "needs_reply",
            "💬 Nécessitent Réponse",
            "Emails qui attendent une réponse + suggestions",
            "#764ba2"
        ))
        
        row2.addWidget(self._create_card(
            "inbox_health",
            "💚 Santé Inbox",
            "Analyse complète avec score et recommandations",
            "#00d2ff"
        ))
        
        grid.addLayout(row2)
        
        # Ligne 3 - Chatbot
        chatbot_card = self._create_chatbot_card()
        grid.addWidget(chatbot_card)
        
        body_layout.addLayout(grid)
        
        # Résultats
        self.results_container = QFrame()
        self.results_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: 2px solid #e2e8f0;
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
                border: 2px solid #667eea;
            }
        """)
        self.progress_container.hide()
        
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(24, 18, 24, 18)
        progress_layout.setSpacing(12)
        
        self.progress_label = QLabel("⏳ Analyse en cours...")
        self.progress_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.progress_label.setStyleSheet("color: #667eea;")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #e2e8f0;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        body_layout.addWidget(self.progress_container)
        
        body_layout.addStretch()
        
        scroll_layout.addWidget(body)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def _create_stat(self, icon: str, value: str, label: str) -> QFrame:
        """Crée une stat."""
        frame = QFrame()
        frame.setFixedSize(160, 65)
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.25);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 26))
        layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        value_label = QLabel(value)
        value_label.setObjectName("stat-value")
        value_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #ffffff;")
        text_layout.addWidget(value_label)
        
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 10))
        label_widget.setStyleSheet("color: rgba(255, 255, 255, 0.85);")
        text_layout.addWidget(label_widget)
        
        layout.addLayout(text_layout)
        
        return frame
    
    def _create_card(self, action_id: str, title: str, desc: str, color: str) -> QFrame:
        """Crée une carte."""
        card = QFrame()
        card.setFixedSize(400, 180)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
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
        desc_label.setStyleSheet("color: #4a5568;")
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
        """Crée la carte chatbot."""
        card = QFrame()
        card.setFixedHeight(180)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #fa709a, stop:1 #fee140);
                border-radius: 16px;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f77062, stop:1 #fe5196);
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
        title.setStyleSheet("color: #1a202c;")
        self.results_layout.addWidget(title)
        
        if not meetings:
            empty = QLabel("Aucun rendez-vous détecté dans vos emails récents.")
            empty.setFont(QFont("Arial", 14))
            empty.setStyleSheet("color: #718096; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_layout.addWidget(empty)
            return
        
        for item in meetings:
            email = item['email']
            date_info = item['date_info']
            
            card = QFrame()
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setStyleSheet("""
                QFrame {
                    background-color: #fffaf0;
                    border: 2px solid #fbd38d;
                    border-radius: 12px;
                    padding: 20px;
                }
                QFrame:hover {
                    border-color: #f6ad55;
                    background-color: #fef5e7;
                }
            """)
            
            card.mousePressEvent = lambda e, em=email: self.email_selected.emit(em)
            
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(10)
            
            sender = QLabel(f"De: {email.sender}")
            sender.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            sender.setStyleSheet("color: #744210;")
            card_layout.addWidget(sender)
            
            subject = QLabel(email.subject)
            subject.setFont(QFont("Arial", 12))
            subject.setStyleSheet("color: #975a16;")
            subject.setWordWrap(True)
            card_layout.addWidget(subject)
            
            date_label = QLabel(f"📅 {date_info}")
            date_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            date_label.setStyleSheet("color: #c05621;")
            card_layout.addWidget(date_label)
            
            self.results_layout.addWidget(card)
    
    def _show_urgent(self, results: dict):
        """Affiche les urgents."""
        urgent = results['urgent']
        
        title = QLabel(f"🚨 {len(urgent)} emails urgents")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #e53e3e;")
        self.results_layout.addWidget(title)
        
        if not urgent:
            empty_frame = QFrame()
            empty_frame.setStyleSheet("""
                QFrame {
                    background-color: #f0fff4;
                    border: 2px solid #9ae6b4;
                    border-radius: 12px;
                    padding: 32px;
                }
            """)
            
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setSpacing(12)
            
            emoji = QLabel("🎉")
            emoji.setFont(QFont("Arial", 48))
            emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(emoji)
            
            msg = QLabel("Aucun email urgent !\nVous êtes à jour.")
            msg.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            msg.setStyleSheet("color: #22543d;")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(msg)
            
            self.results_layout.addWidget(empty_frame)
            return
        
        for item in urgent:
            email = item['email']
            reason = item['reason']
            
            card = QFrame()
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setStyleSheet("""
                QFrame {
                    background-color: #fff5f5;
                    border: 3px solid #fc8181;
                    border-radius: 12px;
                    padding: 20px;
                }
                QFrame:hover {
                    background-color: #fed7d7;
                    border-color: #f56565;
                }
            """)
            
            card.mousePressEvent = lambda e, em=email: self.email_selected.emit(em)
            
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(10)
            
            badge = QLabel("🚨 URGENT")
            badge.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            badge.setFixedWidth(90)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet("""
                background-color: #e53e3e;
                color: white;
                padding: 6px 12px;
                border-radius: 12px;
            """)
            card_layout.addWidget(badge)
            
            sender = QLabel(email.sender)
            sender.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            sender.setStyleSheet("color: #742a2a;")
            card_layout.addWidget(sender)
            
            subject = QLabel(email.subject)
            subject.setFont(QFont("Arial", 13))
            subject.setStyleSheet("color: #9b2c2c;")
            subject.setWordWrap(True)
            card_layout.addWidget(subject)
            
            reason_label = QLabel(f"💡 {reason}")
            reason_label.setFont(QFont("Arial", 11))
            reason_label.setStyleSheet("color: #c53030; font-style: italic;")
            card_layout.addWidget(reason_label)
            
            self.results_layout.addWidget(card)
    
    def _show_needs_reply(self, results: dict):
        """Affiche les emails nécessitant réponse."""
        needs_reply = results['needs_reply']
        
        title = QLabel(f"💬 {len(needs_reply)} emails nécessitent une réponse")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a202c;")
        self.results_layout.addWidget(title)
        
        if not needs_reply:
            empty = QLabel("Tous vos emails ont été traités !")
            empty.setFont(QFont("Arial", 14))
            empty.setStyleSheet("color: #718096; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_layout.addWidget(empty)
            return
        
        for item in needs_reply:
            email = item['email']
            suggestion = item['suggestion']
            
            # Email
            email_label = QLabel(f"De: {email.sender}")
            email_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            email_label.setStyleSheet("color: #2d3748;")
            self.results_layout.addWidget(email_label)
            
            subject_label = QLabel(f"Sujet: {email.subject}")
            subject_label.setFont(QFont("Arial", 12))
            subject_label.setStyleSheet("color: #4a5568;")
            self.results_layout.addWidget(subject_label)
            
            # Suggestion
            suggestion_frame = QFrame()
            suggestion_frame.setStyleSheet("""
                QFrame {
                    background-color: #f0fff4;
                    border: 2px solid #9ae6b4;
                    border-radius: 10px;
                    padding: 16px;
                }
            """)
            
            suggestion_layout = QVBoxLayout(suggestion_frame)
            suggestion_layout.setSpacing(10)
            
            suggestion_title = QLabel("💡 Suggestion de réponse")
            suggestion_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            suggestion_title.setStyleSheet("color: #22543d;")
            suggestion_layout.addWidget(suggestion_title)
            
            suggestion_text = QLabel(suggestion)
            suggestion_text.setFont(QFont("Arial", 11))
            suggestion_text.setStyleSheet("color: #2f855a;")
            suggestion_text.setWordWrap(True)
            suggestion_layout.addWidget(suggestion_text)
            
            copy_btn = QPushButton("📋 Copier cette réponse")
            copy_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            copy_btn.clicked.connect(lambda checked, s=suggestion: self._copy_text(s))
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #48bb78;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #38a169;
                }
            """)
            suggestion_layout.addWidget(copy_btn)
            
            self.results_layout.addWidget(suggestion_frame)
            
            # Séparateur
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("background-color: #e2e8f0; max-height: 1px;")
            self.results_layout.addWidget(sep)
    
    def _show_health(self, results: dict):
        """Affiche la santé inbox."""
        total = results['total']
        unread = results['unread']
        read_rate = results['read_rate']
        score = results['score']
        recommendations = results['recommendations']
        
        title = QLabel("💚 Santé de votre Inbox")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a202c;")
        self.results_layout.addWidget(title)
        
        # Score
        health_frame = QFrame()
        health_frame.setFixedHeight(130)
        
        if score >= 80:
            bg_color = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #48bb78, stop:1 #38a169)"
            emoji = "🎉"
        elif score >= 60:
            bg_color = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ed8936, stop:1 #dd6b20)"
            emoji = "👍"
        else:
            bg_color = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fc8181, stop:1 #f56565)"
            emoji = "⚠️"
        
        health_frame.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-radius: 12px;
            }}
        """)
        
        health_layout = QHBoxLayout(health_frame)
        health_layout.setContentsMargins(32, 24, 32, 24)
        
        score_layout = QVBoxLayout()
        score_layout.setSpacing(6)
        
        score_label = QLabel(f"{score}/100")
        score_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        score_label.setStyleSheet("color: #ffffff;")
        score_layout.addWidget(score_label)
        
        score_desc = QLabel("Score de santé")
        score_desc.setFont(QFont("Arial", 15))
        score_desc.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        score_layout.addWidget(score_desc)
        
        health_layout.addLayout(score_layout)
        health_layout.addStretch()
        
        emoji_label = QLabel(emoji)
        emoji_label.setFont(QFont("Arial", 64))
        health_layout.addWidget(emoji_label)
        
        self.results_layout.addWidget(health_frame)
        
        # Stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f7fafc;
                border: 2px solid #cbd5e0;
                border-radius: 12px;
                padding: 24px;
            }
        """)
        
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setSpacing(16)
        
        stats_title = QLabel("📊 Métriques")
        stats_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        stats_title.setStyleSheet("color: #2d3748;")
        stats_layout.addWidget(stats_title)
        
        stat_items = [
            ("📧 Total emails", str(total)),
            ("✉️ Non lus", str(unread)),
            ("📖 Taux de lecture", f"{read_rate}%")
        ]
        
        for label, value in stat_items:
            row = QHBoxLayout()
            
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 13))
            label_widget.setStyleSheet("color: #4a5568;")
            row.addWidget(label_widget)
            
            row.addStretch()
            
            value_widget = QLabel(value)
            value_widget.setFont(QFont("Arial", 15, QFont.Weight.Bold))
            value_widget.setStyleSheet("color: #1a202c;")
            row.addWidget(value_widget)
            
            stats_layout.addLayout(row)
        
        self.results_layout.addWidget(stats_frame)
        
        # Recommandations
        reco_title = QLabel("💡 Recommandations")
        reco_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        reco_title.setStyleSheet("color: #2d3748;")
        self.results_layout.addWidget(reco_title)
        
        for reco in recommendations:
            reco_label = QLabel(reco)
            reco_label.setFont(QFont("Arial", 13))
            reco_label.setStyleSheet("""
                color: #4a5568;
                background-color: #edf2f7;
                padding: 12px 16px;
                border-radius: 8px;
            """)
            reco_label.setWordWrap(True)
            self.results_layout.addWidget(reco_label)
    
    def _copy_text(self, text: str):
        """Copie le texte."""
        from PyQt6.QtWidgets import QApplication, QMessageBox
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "✅ Copié", "Le texte a été copié !")