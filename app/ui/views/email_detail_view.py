#!/usr/bin/env python3
"""
Vue détaillée d'un email avec actions et informations IA.
"""
import logging
from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor

from models.email_model import Email

logger = logging.getLogger(__name__)

class EmailHeader(QFrame):
    """Header d'email avec informations principales."""
    
    def __init__(self, email: Optional[Email] = None):
        super().__init__()
        self.email = email
        self.setObjectName("email-header")
        self.setFixedHeight(120)
        
        self._setup_ui()
        self._apply_style()
        
        if email:
            self.update_email(email)
    
    def _setup_ui(self):
        """Configure l'interface du header."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Première ligne : Expéditeur et date
        first_row = QHBoxLayout()
        
        self.sender_label = QLabel()
        self.sender_label.setObjectName("sender-label")
        self.sender_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        first_row.addWidget(self.sender_label)
        
        first_row.addStretch()
        
        self.date_label = QLabel()
        self.date_label.setObjectName("date-label")
        self.date_label.setFont(QFont("Inter", 12))
        first_row.addWidget(self.date_label)
        
        layout.addLayout(first_row)
        
        # Deuxième ligne : Email et statuts
        second_row = QHBoxLayout()
        
        self.email_address_label = QLabel()
        self.email_address_label.setObjectName("email-address-label")
        self.email_address_label.setFont(QFont("Inter", 11))
        second_row.addWidget(self.email_address_label)
        
        second_row.addStretch()
        
        # Badges de statut
        self.status_container = QHBoxLayout()
        self.status_container.setSpacing(8)
        second_row.addLayout(self.status_container)
        
        layout.addLayout(second_row)
        
        # Troisième ligne : Sujet
        self.subject_label = QLabel()
        self.subject_label.setObjectName("subject-label")
        self.subject_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.subject_label.setWordWrap(True)
        layout.addWidget(self.subject_label)
    
    def _apply_style(self):
        """Applique le style au header."""
        self.setStyleSheet("""
            #email-header {
                background-color: #ffffff;
                border-bottom: 1px solid #e9ecef;
            }
            
            #sender-label {
                color: #000000;
            }
            
            #date-label {
                color: #6c757d;
            }
            
            #email-address-label {
                color: #6c757d;
            }
            
            #subject-label {
                color: #000000;
                line-height: 1.3;
            }
        """)
    
    def update_email(self, email: Email):
        """Met à jour le header avec un nouvel email."""
        self.email = email
        
        # Expéditeur
        sender_name = email.get_sender_name()
        self.sender_label.setText(sender_name)
       
       # Adresse email
        self.email_address_label.setText(f"<{email.sender}>")
       
       # Date
        if email.received_date:
           date_str = email.received_date.strftime("%d/%m/%Y à %H:%M")
           self.date_label.setText(date_str)
       
       # Sujet
        subject = email.subject or "(Aucun sujet)"
        self.subject_label.setText(subject)
       
       # Mettre à jour les badges de statut
        self._update_status_badges()
   
    def _update_status_badges(self):
       """Met à jour les badges de statut."""
       # Vider les badges existants
       for i in reversed(range(self.status_container.count())):
           child = self.status_container.itemAt(i).widget()
           if child:
               child.setParent(None)
       
       if not self.email:
           return
       
       # Badge non lu
       if not self.email.is_read:
           unread_badge = self._create_badge("Non lu", "#007bff")
           self.status_container.addWidget(unread_badge)
       
       # Badge important
       if hasattr(self.email, 'is_important') and self.email.is_important:
           important_badge = self._create_badge("Important", "#ffc107")
           self.status_container.addWidget(important_badge)
       
       # Badge IA si disponible
       if hasattr(self.email, 'ai_analysis') and self.email.ai_analysis:
           category = self.email.ai_analysis.category
           category_colors = {
               'cv': '#28a745',
               'rdv': '#007bff', 
               'support': '#dc3545',
               'facture': '#ffc107',
               'spam': '#6c757d'
           }
           color = category_colors.get(category, '#17a2b8')
           ai_badge = self._create_badge(f"IA: {category.upper()}", color)
           self.status_container.addWidget(ai_badge)
   
    def _create_badge(self, text: str, color: str) -> QLabel:
       """Crée un badge de statut."""
       badge = QLabel(text)
       badge.setStyleSheet(f"""
           QLabel {{
               background-color: {color};
               color: white;
               padding: 4px 8px;
               border-radius: 12px;
               font-size: 10px;
               font-weight: 600;
           }}
       """)
       badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
       return badge

class EmailActions(QFrame):
   """Barre d'actions pour l'email."""
   
   action_requested = pyqtSignal(str, object)  # action_type, email
   
   def __init__(self, email: Optional[Email] = None):
       super().__init__()
       self.email = email
       self.setObjectName("email-actions")
       self.setFixedHeight(60)
       
       self._setup_ui()
       self._apply_style()
   
   def _setup_ui(self):
       """Configure l'interface des actions."""
       layout = QHBoxLayout(self)
       layout.setContentsMargins(20, 12, 20, 12)
       layout.setSpacing(12)
       
       # Actions principales
       self.reply_btn = self._create_action_button("↩️ Répondre", "reply")
       layout.addWidget(self.reply_btn)
       
       self.forward_btn = self._create_action_button("➡️ Transférer", "forward")
       layout.addWidget(self.forward_btn)
       
       self.archive_btn = self._create_action_button("📁 Archiver", "archive")
       layout.addWidget(self.archive_btn)
       
       layout.addStretch()
       
       # Actions secondaires
       self.spam_btn = self._create_action_button("🚫 Spam", "mark_spam", "danger")
       layout.addWidget(self.spam_btn)
       
       self.delete_btn = self._create_action_button("🗑️ Supprimer", "delete", "danger")
       layout.addWidget(self.delete_btn)
   
   def _create_action_button(self, text: str, action: str, style: str = "default") -> QPushButton:
       """Crée un bouton d'action."""
       btn = QPushButton(text)
       btn.setFixedHeight(36)
       btn.setFont(QFont("Inter", 12, QFont.Weight.Medium))
       btn.clicked.connect(lambda: self.action_requested.emit(action, self.email))
       
       styles = {
           "default": """
               QPushButton {
                   background-color: #f8f9fa;
                   color: #495057;
                   border: 1px solid #dee2e6;
                   border-radius: 18px;
                   padding: 6px 16px;
               }
               QPushButton:hover {
                   background-color: #e9ecef;
                   border-color: #adb5bd;
               }
           """,
           "danger": """
               QPushButton {
                   background-color: #fff5f5;
                   color: #dc3545;
                   border: 1px solid #f5c6cb;
                   border-radius: 18px;
                   padding: 6px 16px;
               }
               QPushButton:hover {
                   background-color: #f8d7da;
                   border-color: #f1b0b7;
               }
           """
       }
       
       btn.setStyleSheet(styles.get(style, styles["default"]))
       return btn
   
   def _apply_style(self):
       """Applique le style à la barre d'actions."""
       self.setStyleSheet("""
           #email-actions {
               background-color: #ffffff;
               border-bottom: 1px solid #e9ecef;
           }
       """)
   
   def update_email(self, email: Email):
       """Met à jour les actions pour un nouvel email."""
       self.email = email
       # Activer/désactiver certains boutons selon le contexte
       # Par exemple, désactiver "Répondre" pour les spams

class EmailContent(QTabWidget):
   """Contenu de l'email avec onglets (contenu, pièces jointes, IA)."""
   
   def __init__(self, email: Optional[Email] = None):
       super().__init__()
       self.email = email
       self.setObjectName("email-content")
       
       self._setup_ui()
       self._apply_style()
       
       if email:
           self.update_email(email)
   
   def _setup_ui(self):
       """Configure l'interface du contenu."""
       # Onglet contenu principal
       self.content_tab = self._create_content_tab()
       self.addTab(self.content_tab, "📄 Contenu")
       
       # Onglet pièces jointes
       self.attachments_tab = self._create_attachments_tab()
       self.addTab(self.attachments_tab, "📎 Pièces jointes")
       
       # Onglet analyse IA
       self.ai_tab = self._create_ai_tab()
       self.addTab(self.ai_tab, "🤖 Analyse IA")
   
   def _create_content_tab(self) -> QWidget:
       """Crée l'onglet de contenu principal."""
       tab = QWidget()
       layout = QVBoxLayout(tab)
       layout.setContentsMargins(20, 20, 20, 20)
       
       # Zone de contenu scrollable
       scroll_area = QScrollArea()
       scroll_area.setWidgetResizable(True)
       scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
       
       self.content_display = QTextEdit()
       self.content_display.setObjectName("content-display")
       self.content_display.setReadOnly(True)
       self.content_display.setFont(QFont("Inter", 12))
       
       scroll_area.setWidget(self.content_display)
       layout.addWidget(scroll_area)
       
       return tab
   
   def _create_attachments_tab(self) -> QWidget:
       """Crée l'onglet des pièces jointes."""
       tab = QWidget()
       layout = QVBoxLayout(tab)
       layout.setContentsMargins(20, 20, 20, 20)
       
       self.attachments_list = QVBoxLayout()
       layout.addLayout(self.attachments_list)
       
       # Message par défaut
       self.no_attachments_label = QLabel("📎 Aucune pièce jointe")
       self.no_attachments_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
       self.no_attachments_label.setFont(QFont("Inter", 14))
       self.no_attachments_label.setStyleSheet("color: #6c757d; padding: 40px;")
       layout.addWidget(self.no_attachments_label)
       
       layout.addStretch()
       return tab
   
   def _create_ai_tab(self) -> QWidget:
       """Crée l'onglet d'analyse IA."""
       tab = QWidget()
       layout = QVBoxLayout(tab)
       layout.setContentsMargins(20, 20, 20, 20)
       layout.setSpacing(16)
       
       # Informations d'analyse
       self.ai_info_container = QVBoxLayout()
       layout.addLayout(self.ai_info_container)
       
       # Message par défaut
       self.no_ai_label = QLabel("🤖 Aucune analyse IA disponible")
       self.no_ai_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
       self.no_ai_label.setFont(QFont("Inter", 14))
       self.no_ai_label.setStyleSheet("color: #6c757d; padding: 40px;")
       layout.addWidget(self.no_ai_label)
       
       layout.addStretch()
       return tab
   
   def _apply_style(self):
       """Applique le style au contenu."""
       self.setStyleSheet("""
           #email-content {
               background-color: #ffffff;
           }
           
           QTabWidget::pane {
               border: none;
               background-color: #ffffff;
           }
           
           QTabWidget::tab-bar {
               alignment: left;
           }
           
           QTabBar::tab {
               background-color: #f8f9fa;
               color: #495057;
               padding: 12px 20px;
               margin-right: 2px;
               border-top-left-radius: 8px;
               border-top-right-radius: 8px;
               border: 1px solid #dee2e6;
               border-bottom: none;
               font-weight: 500;
           }
           
           QTabBar::tab:selected {
               background-color: #ffffff;
               color: #000000;
               font-weight: 600;
           }
           
           QTabBar::tab:hover:!selected {
               background-color: #e9ecef;
           }
           
           #content-display {
               background-color: #ffffff;
               border: 1px solid #e9ecef;
               border-radius: 8px;
               padding: 16px;
               color: #495057;
               line-height: 1.5;
           }
       """)
   
   def update_email(self, email: Email):
       """Met à jour le contenu pour un nouvel email."""
       self.email = email
       
       # Mettre à jour le contenu
       if email.body:
           # Nettoyer le HTML si nécessaire
           import re
           clean_content = re.sub(r'<[^>]+>', '', email.body)
           self.content_display.setPlainText(clean_content)
       else:
           self.content_display.setPlainText("(Aucun contenu)")
       
       # Mettre à jour les pièces jointes
       self._update_attachments()
       
       # Mettre à jour l'analyse IA
       self._update_ai_analysis()
   
   def _update_attachments(self):
       """Met à jour l'affichage des pièces jointes."""
       # Vider la liste existante
       for i in reversed(range(self.attachments_list.count())):
           child = self.attachments_list.itemAt(i).widget()
           if child:
               child.setParent(None)
       
       if hasattr(self.email, 'attachments') and self.email.attachments:
           self.no_attachments_label.hide()
           
           for attachment in self.email.attachments:
               attachment_widget = self._create_attachment_widget(attachment)
               self.attachments_list.addWidget(attachment_widget)
       else:
           self.no_attachments_label.show()
   
   def _create_attachment_widget(self, attachment) -> QFrame:
       """Crée un widget pour une pièce jointe."""
       widget = QFrame()
       widget.setObjectName("attachment-widget")
       
       layout = QHBoxLayout(widget)
       layout.setContentsMargins(16, 12, 16, 12)
       
       # Icône selon le type de fichier
       file_icon = self._get_file_icon(attachment.get('filename', ''))
       icon_label = QLabel(file_icon)
       icon_label.setFont(QFont("Arial", 20))
       layout.addWidget(icon_label)
       
       # Informations du fichier
       info_layout = QVBoxLayout()
       
       name_label = QLabel(attachment.get('filename', 'Fichier sans nom'))
       name_label.setFont(QFont("Inter", 13, QFont.Weight.Medium))
       info_layout.addWidget(name_label)
       
       size_label = QLabel(f"Taille: {attachment.get('size', 'Inconnue')}")
       size_label.setFont(QFont("Inter", 11))
       size_label.setStyleSheet("color: #6c757d;")
       info_layout.addWidget(size_label)
       
       layout.addLayout(info_layout)
       layout.addStretch()
       
       # Bouton télécharger
       download_btn = QPushButton("⬇️ Télécharger")
       download_btn.setFixedHeight(32)
       download_btn.setStyleSheet("""
           QPushButton {
               background-color: #007bff;
               color: white;
               border: none;
               border-radius: 16px;
               padding: 6px 12px;
               font-weight: 500;
           }
           QPushButton:hover {
               background-color: #0056b3;
           }
       """)
       layout.addWidget(download_btn)
       
       widget.setStyleSheet("""
           #attachment-widget {
               background-color: #f8f9fa;
               border: 1px solid #e9ecef;
               border-radius: 8px;
               margin: 4px 0;
           }
       """)
       
       return widget
   
   def _get_file_icon(self, filename: str) -> str:
       """Retourne l'icône appropriée selon le type de fichier."""
       extension = filename.lower().split('.')[-1] if '.' in filename else ''
       
       icon_map = {
           'pdf': '📄',
           'doc': '📝', 'docx': '📝',
           'xls': '📊', 'xlsx': '📊',
           'ppt': '📊', 'pptx': '📊',
           'zip': '📦', 'rar': '📦',
           'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
           'mp3': '🎵', 'wav': '🎵',
           'mp4': '🎬', 'avi': '🎬'
       }
       
       return icon_map.get(extension, '📎')
   
   def _update_ai_analysis(self):
       """Met à jour l'affichage de l'analyse IA."""
       # Vider l'analyse existante
       for i in reversed(range(self.ai_info_container.count())):
           child = self.ai_info_container.itemAt(i).widget()
           if child:
               child.setParent(None)
       
       if hasattr(self.email, 'ai_analysis') and self.email.ai_analysis:
           self.no_ai_label.hide()
           analysis = self.email.ai_analysis
           
           # Créer les widgets d'information IA
           self._create_ai_info_widgets(analysis)
       else:
           self.no_ai_label.show()
   
   def _create_ai_info_widgets(self, analysis):
       """Crée les widgets d'information IA."""
       # Catégorie et confiance
       category_widget = self._create_ai_info_card(
           "📂 Catégorie détectée",
           f"{analysis.category.upper()} (Confiance: {analysis.confidence:.0%})"
       )
       self.ai_info_container.addWidget(category_widget)
       
       # Priorité
       priority_names = {1: "Très urgent", 2: "Urgent", 3: "Normal", 4: "Faible", 5: "Très faible"}
       priority_widget = self._create_ai_info_card(
           "⚡ Priorité",
           priority_names.get(analysis.priority, f"Niveau {analysis.priority}")
       )
       self.ai_info_container.addWidget(priority_widget)
       
       # Recommandation de réponse
       auto_respond_text = "Oui" if analysis.should_auto_respond else "Non"
       respond_widget = self._create_ai_info_card(
           "🤖 Réponse automatique recommandée",
           auto_respond_text
       )
       self.ai_info_container.addWidget(respond_widget)
       
       # Informations extraites
       if analysis.extracted_info:
           info_text = "\n".join([f"• {k}: {v}" for k, v in analysis.extracted_info.items() if v])
           if info_text:
               extracted_widget = self._create_ai_info_card(
                   "🔍 Informations extraites",
                   info_text
               )
               self.ai_info_container.addWidget(extracted_widget)
       
       # Raisonnement
       if analysis.reasoning:
           reasoning_widget = self._create_ai_info_card(
               "🧠 Raisonnement IA",
               analysis.reasoning
           )
           self.ai_info_container.addWidget(reasoning_widget)
   
   def _create_ai_info_card(self, title: str, content: str) -> QFrame:
       """Crée une carte d'information IA."""
       card = QFrame()
       card.setObjectName("ai-info-card")
       
       layout = QVBoxLayout(card)
       layout.setContentsMargins(16, 12, 16, 12)
       layout.setSpacing(8)
       
       # Titre
       title_label = QLabel(title)
       title_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
       layout.addWidget(title_label)
       
       # Contenu
       content_label = QLabel(content)
       content_label.setFont(QFont("Inter", 11))
       content_label.setWordWrap(True)
       content_label.setStyleSheet("color: #495057;")
       layout.addWidget(content_label)
       
       card.setStyleSheet("""
           #ai-info-card {
               background-color: #f8f9fa;
               border: 1px solid #e9ecef;
               border-radius: 8px;
               margin: 4px 0;
           }
       """)
       
       return card

class EmailDetailView(QWidget):
   """Vue détaillée complète d'un email."""
   
   action_requested = pyqtSignal(str, object)  # action_type, email
   
   def __init__(self):
       super().__init__()
       self.current_email = None
       
       self.setObjectName("email-detail-view")
       self._setup_ui()
       self._apply_style()
   
   def _setup_ui(self):
       """Configure l'interface de la vue détaillée."""
       layout = QVBoxLayout(self)
       layout.setContentsMargins(0, 0, 0, 0)
       layout.setSpacing(0)
       
       # Header de l'email
       self.header = EmailHeader()
       layout.addWidget(self.header)
       
       # Barre d'actions
       self.actions = EmailActions()
       self.actions.action_requested.connect(self.action_requested.emit)
       layout.addWidget(self.actions)
       
       # Contenu de l'email
       self.content = EmailContent()
       layout.addWidget(self.content)
       
       # Message par défaut quand aucun email sélectionné
       self.no_selection_widget = self._create_no_selection_widget()
       layout.addWidget(self.no_selection_widget)
       
       # Cacher le contenu par défaut
       self.header.hide()
       self.actions.hide()
       self.content.hide()
   
   def _create_no_selection_widget(self) -> QWidget:
       """Crée le widget affiché quand aucun email n'est sélectionné."""
       widget = QWidget()
       layout = QVBoxLayout(widget)
       layout.setContentsMargins(40, 40, 40, 40)
       
       # Icône
       icon_label = QLabel("📧")
       icon_label.setFont(QFont("Arial", 64))
       icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
       icon_label.setStyleSheet("color: #dee2e6;")
       layout.addWidget(icon_label)
       
       # Texte principal
       title_label = QLabel("Sélectionnez un email")
       title_label.setFont(QFont("Inter", 20, QFont.Weight.Bold))
       title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
       title_label.setStyleSheet("color: #6c757d; margin: 16px 0;")
       layout.addWidget(title_label)
       
       # Texte descriptif
       desc_label = QLabel("Cliquez sur un email dans la liste pour voir son contenu et les suggestions IA.")
       desc_label.setFont(QFont("Inter", 14))
       desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
       desc_label.setWordWrap(True)
       desc_label.setStyleSheet("color: #adb5bd; line-height: 1.5;")
       layout.addWidget(desc_label)
       
       layout.addStretch()
       
       return widget
   
   def _apply_style(self):
       """Applique le style à la vue."""
       self.setStyleSheet("""
           #email-detail-view {
               background-color: #ffffff;
           }
       """)
   
   def show_email(self, email: Email):
       """Affiche un email dans la vue détaillée."""
       self.current_email = email
       
       # Mettre à jour tous les composants
       self.header.update_email(email)
       self.actions.update_email(email)
       self.content.update_email(email)
       
       # Afficher le contenu, cacher le message par défaut
       self.no_selection_widget.hide()
       self.header.show()
       self.actions.show()
       self.content.show()
       
       logger.info(f"Affichage email détaillé: {email.id}")
   
   def clear_selection(self):
       """Efface la sélection et affiche le message par défaut."""
       self.current_email = None
       
       # Cacher le contenu, afficher le message par défaut
       self.header.hide()
       self.actions.hide()
       self.content.hide()
       self.no_selection_widget.show()