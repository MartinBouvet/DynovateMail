#!/usr/bin/env python3
"""
Vue Assistant IA - VERSION RÉVOLUTIONNAIRE POUR ENTREPRISES
"""
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from app.ai_processor import AIProcessor
from app.gmail_client import GmailClient
from app.models.email_model import Email

logger = logging.getLogger(__name__)


class AIAnalysisThread(QThread):
    """Thread pour analyses IA lourdes."""
    
    analysis_complete = pyqtSignal(dict)
    progress = pyqtSignal(str)
    
    def __init__(self, ai_processor, gmail_client, task_type, params=None):
        super().__init__()
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.task_type = task_type
        self.params = params or {}
    
    def run(self):
        """Exécute l'analyse."""
        try:
            if self.task_type == "email_summary":
                self._summarize_emails()
            elif self.task_type == "priority_analysis":
                self._analyze_priorities()
            elif self.task_type == "sentiment_report":
                self._sentiment_report()
            elif self.task_type == "auto_categorize":
                self._auto_categorize()
        except Exception as e:
            logger.error(f"Erreur analyse IA: {e}")
            self.analysis_complete.emit({"error": str(e)})
    
    def _summarize_emails(self):
        """Résume les emails récents."""
        self.progress.emit("📧 Récupération des emails...")
        
        emails = self.gmail_client.list_emails(folder="INBOX", max_results=50)
        
        # Filtrer les non lus
        unread = [e for e in emails if not getattr(e, 'read', True)]
        
        self.progress.emit(f"🤖 Analyse de {len(unread)} emails non lus...")
        
        summaries = []
        for i, email in enumerate(unread[:10], 1):
            self.progress.emit(f"📝 Analyse {i}/{min(len(unread), 10)}...")
            
            # Générer résumé
            prompt = f"""Résume cet email en 1 phrase concise et actionnable:

Expéditeur: {email.sender}
Sujet: {email.subject}
Contenu: {email.snippet or email.body[:500]}

Résumé (1 phrase):"""
            
            try:
                summary = self.ai_processor.ollama_client.generate(prompt, max_tokens=100)
                summaries.append({
                    'email': email,
                    'summary': summary.strip()
                })
            except:
                summaries.append({
                    'email': email,
                    'summary': f"Email de {email.sender}: {email.subject}"
                })
        
        self.analysis_complete.emit({
            'type': 'email_summary',
            'total': len(emails),
            'unread': len(unread),
            'summaries': summaries
        })
    
    def _analyze_priorities(self):
        """Analyse les priorités."""
        self.progress.emit("🎯 Analyse des priorités...")
        
        emails = self.gmail_client.list_emails(folder="INBOX", max_results=50)
        
        urgent = []
        important = []
        can_wait = []
        
        for email in emails[:20]:
            self.progress.emit(f"🔍 Analyse: {email.subject[:30]}...")
            
            # Analyse de priorité
            prompt = f"""Analyse la priorité de cet email. Réponds uniquement par: URGENT, IMPORTANT ou PEUT_ATTENDRE

Expéditeur: {email.sender}
Sujet: {email.subject}
Contenu: {email.snippet or ''}

Priorité:"""
            
            try:
                priority = self.ai_processor.ollama_client.generate(prompt, max_tokens=10).strip().upper()
                
                if 'URGENT' in priority:
                    urgent.append(email)
                elif 'IMPORTANT' in priority:
                    important.append(email)
                else:
                    can_wait.append(email)
            except:
                can_wait.append(email)
        
        self.analysis_complete.emit({
            'type': 'priority_analysis',
            'urgent': urgent,
            'important': important,
            'can_wait': can_wait
        })
    
    def _sentiment_report(self):
        """Analyse le sentiment global."""
        self.progress.emit("😊 Analyse du sentiment...")
        
        emails = self.gmail_client.list_emails(folder="INBOX", max_results=30)
        
        positive = 0
        negative = 0
        neutral = 0
        
        for email in emails:
            prompt = f"""Quel est le sentiment de cet email? Réponds uniquement: POSITIF, NÉGATIF ou NEUTRE

Sujet: {email.subject}
Contenu: {email.snippet or ''}

Sentiment:"""
            
            try:
                sentiment = self.ai_processor.ollama_client.generate(prompt, max_tokens=10).strip().upper()
                
                if 'POSITIF' in sentiment:
                    positive += 1
                elif 'NÉGATIF' in sentiment or 'NEGATIF' in sentiment:
                    negative += 1
                else:
                    neutral += 1
            except:
                neutral += 1
        
        self.analysis_complete.emit({
            'type': 'sentiment_report',
            'total': len(emails),
            'positive': positive,
            'negative': negative,
            'neutral': neutral
        })
    
    def _auto_categorize(self):
        """Catégorise automatiquement les emails."""
        self.progress.emit("🏷️ Catégorisation automatique...")
        
        emails = self.gmail_client.list_emails(folder="INBOX", max_results=50)
        
        categories = {
            'cv': [],
            'meeting': [],
            'invoice': [],
            'newsletter': [],
            'support': [],
            'important': [],
            'spam': []
        }
        
        for email in emails:
            prompt = f"""Catégorise cet email. Réponds uniquement par: CV, MEETING, INVOICE, NEWSLETTER, SUPPORT, IMPORTANT ou SPAM

Expéditeur: {email.sender}
Sujet: {email.subject}

Catégorie:"""
            
            try:
                category = self.ai_processor.ollama_client.generate(prompt, max_tokens=10).strip().lower()
                
                for cat_key in categories.keys():
                    if cat_key in category:
                        categories[cat_key].append(email)
                        break
            except:
                pass
        
        self.analysis_complete.emit({
            'type': 'auto_categorize',
            'categories': categories
        })


class AIAssistantView(QWidget):
    """Vue Assistant IA révolutionnaire."""
    
    email_selected = pyqtSignal(Email)
    
    def __init__(self, ai_processor: AIProcessor, gmail_client: GmailClient):
        super().__init__()
        
        self.ai_processor = ai_processor
        self.gmail_client = gmail_client
        self.conversation_history = []
        self.analysis_thread = None
        
        self._setup_ui()
        self._load_statistics()
    
    def _setup_ui(self):
        """Interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Colonne gauche: Actions IA puissantes
        left_panel = QWidget()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet("background-color: #fafafa; border-right: 1px solid #e5e7eb;")
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 25, 20, 25)
        left_layout.setSpacing(20)
        
        # Titre
        title = QLabel("🤖 Assistant IA Dynovate")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        left_layout.addWidget(title)
        
        subtitle = QLabel("Propulsé par Ollama • 100% Local • 0€/mois")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setStyleSheet("color: #6b7280;")
        left_layout.addWidget(subtitle)
        
        # Séparateur
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #e5e7eb;")
        left_layout.addWidget(line)
        
        # Section: Statistiques
        stats_title = QLabel("📊 VUE D'ENSEMBLE")
        stats_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        stats_title.setStyleSheet("color: #6b7280;")
        left_layout.addWidget(stats_title)
        
        # Cartes stats
        self.stats_cards = {}
        
        stat_configs = [
            ("emails", "📧 Total", "0", "#5b21b6"),
            ("unread", "📬 Non lus", "0", "#ef4444"),
            ("today", "📅 Aujourd'hui", "0", "#10b981"),
        ]
        
        for key, label, default_value, color in stat_configs:
            card = self._create_mini_stat_card(label, default_value, color)
            self.stats_cards[key] = card
            left_layout.addWidget(card)
        
        left_layout.addSpacing(10)
        
        # Section: Actions IA
        actions_title = QLabel("⚡ ACTIONS IA PUISSANTES")
        actions_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        actions_title.setStyleSheet("color: #6b7280;")
        left_layout.addWidget(actions_title)
        
        # Boutons d'action
        actions = [
            ("📝 Résumer mes emails", "email_summary", "#5b21b6"),
            ("🎯 Analyser les priorités", "priority_analysis", "#ef4444"),
            ("😊 Rapport de sentiment", "sentiment_report", "#10b981"),
            ("🏷️ Catégoriser auto", "auto_categorize", "#f59e0b"),
        ]
        
        for label, action_type, color in actions:
            btn = self._create_action_button(label, action_type, color)
            left_layout.addWidget(btn)
        
        left_layout.addStretch()
        
        # Status
        self.status_label = QLabel("✅ IA prête")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("""
            color: #10b981;
            padding: 8px;
            background-color: #d1fae5;
            border-radius: 6px;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.status_label)
        
        layout.addWidget(left_panel)
        
        # Colonne droite: Résultats et Chat
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #ffffff;")
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(30, 25, 30, 25)
        right_layout.setSpacing(20)
        
        # Zone de résultats
        results_header = QHBoxLayout()
        
        self.results_title = QLabel("💡 Résultats de l'analyse")
        self.results_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.results_title.setStyleSheet("color: #000000;")
        results_header.addWidget(self.results_title)
        
        results_header.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualiser stats")
        refresh_btn.setFont(QFont("Arial", 11))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_statistics)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px 16px;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #5b21b6;
                color: white;
            }
        """)
        results_header.addWidget(refresh_btn)
        
        right_layout.addLayout(results_header)
        
        # Zone de scroll pour résultats
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #f9fafb;
            }
        """)
        
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(20, 20, 20, 20)
        self.results_layout.setSpacing(15)
        
        # Message initial
        welcome = QLabel(
            "👋 <b>Bienvenue dans votre Assistant IA Dynovate</b><br><br>"
            "Cet assistant utilise <b>Ollama en local</b> pour analyser vos emails.<br><br>"
            "✨ <b>Fonctionnalités uniques:</b><br>"
            "• Résumés intelligents de vos emails<br>"
            "• Analyse de priorité automatique<br>"
            "• Détection de sentiment<br>"
            "• Catégorisation automatique<br>"
            "• 100% privé et gratuit<br><br>"
            "👈 <b>Choisissez une action à gauche pour commencer</b>"
        )
        welcome.setFont(QFont("Arial", 12))
        welcome.setStyleSheet("color: #374151; line-height: 1.8;")
        welcome.setWordWrap(True)
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(welcome)
        
        self.results_layout.addStretch()
        
        self.results_scroll.setWidget(self.results_container)
        right_layout.addWidget(self.results_scroll, 1)
        
        layout.addWidget(right_panel, 1)
    
    def _create_mini_stat_card(self, label: str, value: str, color: str) -> QFrame:
        """Crée une mini carte stat."""
        card = QFrame()
        card.setFixedHeight(70)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)
        card_layout.setSpacing(4)
        
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 10))
        label_widget.setStyleSheet("color: #ffffff;")
        card_layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setObjectName("stat-value")
        value_widget.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        value_widget.setStyleSheet("color: #ffffff;")
        card_layout.addWidget(value_widget)
        
        return card
    
    def _create_action_button(self, label: str, action_type: str, color: str) -> QPushButton:
        """Crée un bouton d'action."""
        btn = QPushButton(label)
        btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._run_ai_action(action_type))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 15px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}bb;
            }}
        """)
        
        return btn
    
    def _load_statistics(self):
        """Charge les statistiques."""
        try:
            emails = self.gmail_client.list_emails(folder="INBOX", max_results=100)
            
            total = len(emails)
            unread = sum(1 for e in emails if not getattr(e, 'read', True))
            
            # Emails d'aujourd'hui
            today = datetime.now().date()
            today_emails = sum(1 for e in emails if 
                             e.received_date and e.received_date.date() == today)
            
            self._update_stat_value('emails', str(total))
            self._update_stat_value('unread', str(unread))
            self._update_stat_value('today', str(today_emails))
            
            logger.info(f"✅ Stats: {total} emails, {unread} non lus, {today_emails} aujourd'hui")
        
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
    
    def _update_stat_value(self, key: str, value: str):
        """Met à jour une valeur statistique."""
        if key in self.stats_cards:
            card = self.stats_cards[key]
            value_label = card.findChild(QLabel, "stat-value")
            if value_label:
                value_label.setText(value)
    
    def _run_ai_action(self, action_type: str):
        """Lance une action IA."""
        logger.info(f"🤖 Lancement: {action_type}")
        
        # Nettoyer les résultats
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Message de chargement
        loading = QLabel("⏳ Analyse en cours...")
        loading.setFont(QFont("Arial", 14))
        loading.setStyleSheet("color: #6b7280;")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(loading)
        
        # Status
        self.status_label.setText("🔄 Analyse en cours...")
        self.status_label.setStyleSheet("""
            color: #f59e0b;
            padding: 8px;
            background-color: #fef3c7;
            border-radius: 6px;
        """)
        
        # Lancer le thread
        self.analysis_thread = AIAnalysisThread(
            self.ai_processor,
            self.gmail_client,
            action_type
        )
        self.analysis_thread.progress.connect(self._update_progress)
        self.analysis_thread.analysis_complete.connect(self._show_results)
        self.analysis_thread.start()
    
    def _update_progress(self, message: str):
        """Met à jour le progrès."""
        self.status_label.setText(message)
    
    def _show_results(self, results: dict):
        """Affiche les résultats."""
        # Nettoyer
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        result_type = results.get('type')
        
        if result_type == 'email_summary':
            self._show_email_summary(results)
        elif result_type == 'priority_analysis':
            self._show_priority_analysis(results)
        elif result_type == 'sentiment_report':
            self._show_sentiment_report(results)
        elif result_type == 'auto_categorize':
            self._show_categorization(results)
        
        # Reset status
        self.status_label.setText("✅ Analyse terminée")
        self.status_label.setStyleSheet("""
            color: #10b981;
            padding: 8px;
            background-color: #d1fae5;
            border-radius: 6px;
        """)
    
    def _show_email_summary(self, results: dict):
        """Affiche le résumé des emails."""
        title = QLabel(f"📧 Résumé de vos {results['unread']} emails non lus")
        title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2937;")
        self.results_layout.addWidget(title)
        
        for item in results['summaries']:
            email = item['email']
            summary = item['summary']
            
            card = self._create_email_result_card(email, summary)
            self.results_layout.addWidget(card)
        
        self.results_layout.addStretch()
    
    def _show_priority_analysis(self,results: dict):
        """Affiche l'analyse de priorité."""
        title = QLabel("🎯 Analyse de priorité de vos emails")
        title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2937;")
        self.results_layout.addWidget(title)
        
        # Urgent
        if results['urgent']:
            urgent_title = QLabel(f"🚨 URGENT ({len(results['urgent'])})")
            urgent_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            urgent_title.setStyleSheet("color: #dc2626;")
            self.results_layout.addWidget(urgent_title)
            
            for email in results['urgent'][:5]:
                card = self._create_email_result_card(email, "Action requise immédiatement", "#dc2626")
                self.results_layout.addWidget(card)
        
        # Important
        if results['important']:
            important_title = QLabel(f"⚠️ IMPORTANT ({len(results['important'])})")
            important_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            important_title.setStyleSheet("color: #f59e0b;")
            self.results_layout.addWidget(important_title)
            
            for email in results['important'][:5]:
                card = self._create_email_result_card(email, "À traiter aujourd'hui", "#f59e0b")
                self.results_layout.addWidget(card)
        
        # Peut attendre
        if results['can_wait']:
            wait_title = QLabel(f"✅ PEUT ATTENDRE ({len(results['can_wait'])})")
            wait_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            wait_title.setStyleSheet("color: #10b981;")
            self.results_layout.addWidget(wait_title)
            
            for email in results['can_wait'][:3]:
                card = self._create_email_result_card(email, "Pas urgent", "#10b981")
                self.results_layout.addWidget(card)
        
        self.results_layout.addStretch()
    
    def _show_sentiment_report(self, results: dict):
        """Affiche le rapport de sentiment."""
        title = QLabel(f"😊 Analyse du sentiment sur {results['total']} emails")
        title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2937;")
        self.results_layout.addWidget(title)
        
        # Graphique texte
        total = results['total']
        positive_pct = int((results['positive'] / total) * 100) if total > 0 else 0
        negative_pct = int((results['negative'] / total) * 100) if total > 0 else 0
        neutral_pct = 100 - positive_pct - negative_pct
        
        # Cartes de sentiment
        sentiments = [
            ("😊 Positif", results['positive'], positive_pct, "#10b981"),
            ("😐 Neutre", results['neutral'], neutral_pct, "#6b7280"),
            ("😞 Négatif", results['negative'], negative_pct, "#ef4444"),
        ]
        
        for label, count, pct, color in sentiments:
            card = QFrame()
            card.setFixedHeight(80)
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border-radius: 10px;
                }}
            """)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 12, 20, 12)
            
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            label_widget.setStyleSheet("color: #ffffff;")
            card_layout.addWidget(label_widget)
            
            value_widget = QLabel(f"{count} emails ({pct}%)")
            value_widget.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            value_widget.setStyleSheet("color: #ffffff;")
            card_layout.addWidget(value_widget)
            
            self.results_layout.addWidget(card)
        
        # Interprétation
        interpretation = QLabel()
        interpretation.setFont(QFont("Arial", 12))
        interpretation.setWordWrap(True)
        
        if positive_pct > 50:
            interpretation.setText("✅ <b>Excellente ambiance !</b> La majorité de vos emails sont positifs.")
            interpretation.setStyleSheet("color: #10b981; background-color: #d1fae5; padding: 15px; border-radius: 8px;")
        elif negative_pct > 30:
            interpretation.setText("⚠️ <b>Attention</b> : Beaucoup d'emails négatifs. Priorisez la gestion des conflits.")
            interpretation.setStyleSheet("color: #dc2626; background-color: #fee2e2; padding: 15px; border-radius: 8px;")
        else:
            interpretation.setText("ℹ️ <b>Sentiment équilibré</b> dans votre boîte mail.")
            interpretation.setStyleSheet("color: #0ea5e9; background-color: #e0f2fe; padding: 15px; border-radius: 8px;")
        
        self.results_layout.addWidget(interpretation)
        self.results_layout.addStretch()
    
    def _show_categorization(self, results: dict):
        """Affiche la catégorisation."""
        title = QLabel("🏷️ Catégorisation automatique de vos emails")
        title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2937;")
        self.results_layout.addWidget(title)
        
        categories = results['categories']
        
        category_config = {
            'cv': ("📄 CV / Candidatures", "#8b5cf6"),
            'meeting': ("📅 Réunions / RDV", "#10b981"),
            'invoice': ("💰 Factures / Paiements", "#f59e0b"),
            'newsletter': ("📰 Newsletters", "#3b82f6"),
            'support': ("🛠️ Support / SAV", "#ef4444"),
            'important': ("⭐ Important", "#eab308"),
            'spam': ("🚫 Spam potentiel", "#dc2626"),
        }
        
        for cat_key, (cat_label, cat_color) in category_config.items():
            emails = categories.get(cat_key, [])
            
            if emails:
                cat_title = QLabel(f"{cat_label} ({len(emails)})")
                cat_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
                cat_title.setStyleSheet(f"color: {cat_color};")
                self.results_layout.addWidget(cat_title)
                
                for email in emails[:3]:
                    card = self._create_email_result_card(email, f"Catégorie: {cat_label}", cat_color)
                    self.results_layout.addWidget(card)
        
        self.results_layout.addStretch()
    
    def _create_email_result_card(self, email: Email, description: str, color: str = "#5b21b6") -> QFrame:
        """Crée une carte de résultat email cliquable."""
        card = QFrame()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame:hover {{
                background-color: #f9fafb;
                border-left-width: 6px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(6)
        
        # Expéditeur
        sender = email.sender.split('<')[0].strip() if '<' in email.sender else email.sender
        sender_label = QLabel(f"<b>{sender}</b>")
        sender_label.setFont(QFont("Arial", 12))
        sender_label.setStyleSheet("color: #1f2937;")
        card_layout.addWidget(sender_label)
        
        # Sujet
        subject_label = QLabel(email.subject or "(Sans sujet)")
        subject_label.setFont(QFont("Arial", 11))
        subject_label.setStyleSheet("color: #374151;")
        subject_label.setWordWrap(True)
        card_layout.addWidget(subject_label)
        
        # Description / Résumé
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setStyleSheet("color: #6b7280; font-style: italic;")
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)
        
        # Ajouter événement de clic
        card.mousePressEvent = lambda event: self._on_email_card_clicked(email)
        
        return card
    
    def _on_email_card_clicked(self, email: Email):
        """Gère le clic sur une carte email."""
        logger.info(f"📧 Clic sur email: {email.subject}")
        self.email_selected.emit(email)