#!/usr/bin/env python3
"""
Vue détaillée d'un email CORRIGÉE avec gestion des pièces jointes.
"""
import logging
from typing import Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from models.email_model import Email, EmailAttachment
from gmail_client import GmailClient

logger = logging.getLogger(__name__)

class AttachmentCard(QFrame):
    """Carte d'affichage d'une pièce jointe."""
    
    download_requested = pyqtSignal(object)  # EmailAttachment
    
    def __init__(self, attachment: EmailAttachment):
        super().__init__()
        self.attachment = attachment
        
        self.setObjectName("attachment-card")
        self.setFixedHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface de la carte de pièce jointe."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Icône du fichier
        icon_label = QLabel(self.attachment.icon)
        icon_label.setFont(QFont("Arial", 18))
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Informations du fichier
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # Nom du fichier
        filename = self.attachment.filename
        if len(filename) > 35:
            filename = filename[:32] + "..."
        
        name_label = QLabel(filename)
        name_label.setObjectName("attachment-name")
        name_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        info_layout.addWidget(name_label)
        
        # Taille et type
        size_type_label = QLabel(f"{self.attachment.size} • {self.attachment.mime_type.split('/')[-1].upper()}")
        size_type_label.setObjectName("attachment-info")
        size_type_label.setFont(QFont("Inter", 10))
        info_layout.addWidget(size_type_label)
        
        layout.addWidget(info_container)
        layout.addStretch()
        
        # Bouton de téléchargement
        if self.attachment.downloadable:
            download_btn = QPushButton("📥")
            download_btn.setObjectName("download-btn")
            download_btn.setFixedSize(36, 36)
            download_btn.setFont(QFont("Arial", 14))
            download_btn.setToolTip("Télécharger")
            download_btn.clicked.connect(lambda: self.download_requested.emit(self.attachment))
            layout.addWidget(download_btn)
        else:
            unavailable_label = QLabel("❌")
            unavailable_label.setFont(QFont("Arial", 14))
            unavailable_label.setToolTip("Non téléchargeable")
            layout.addWidget(unavailable_label)
    
    def _apply_style(self):
        """Applique le style à la carte."""
        self.setStyleSheet("""
            QFrame#attachment-card {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin: 2px 0;
            }
            
            QFrame#attachment-card:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            
            QLabel#attachment-name {
                color: #495057;
                font-weight: 600;
            }
            
            QLabel#attachment-info {
                color: #6c757d;
                font-weight: 400;
            }
            
            QPushButton#download-btn {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
            }
            
            QPushButton#download-btn:hover {
                background-color: #0056b3;
            }
            
            QPushButton#download-btn:pressed {
                background-color: #004085;
            }
        """)

class EmailDetailView(QWidget):
    """Vue détaillée CORRIGÉE d'un email avec gestion des pièces jointes."""
    
    action_requested = pyqtSignal(str, object)
    
    def __init__(self, gmail_client: GmailClient = None):
        super().__init__()
        self.current_email = None
        self.gmail_client = gmail_client
        
        self.setObjectName("email-detail-view")
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface CORRIGÉE avec gestion des pièces jointes."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Zone de scroll pour tout le contenu
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget de contenu scrollable
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        
        # Message par défaut
        self.no_selection_widget = self._create_no_selection_widget()
        self.content_layout.addWidget(self.no_selection_widget)
        
        # Contenu de l'email (caché par défaut)
        self.email_content_widget = self._create_email_content_widget()
        self.email_content_widget.hide()
        self.content_layout.addWidget(self.email_content_widget)
        
        # Spacer pour pousser le contenu vers le haut
        self.content_layout.addStretch()
        
        # Configurer le scroll
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
    
    def _create_no_selection_widget(self) -> QWidget:
        """Widget quand aucun email n'est sélectionné."""
        widget = QWidget()
        widget.setObjectName("no-selection-widget")
        
        # Layout principal centré
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(40, 0, 40, 0)
        main_layout.setSpacing(0)
        
        # Spacer du haut pour centrer verticalement
        main_layout.addStretch(1)
        
        # Container centré
        center_container = QWidget()
        center_container.setFixedSize(500, 300)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(25)
        
        # Icône
        icon_label = QLabel("📧")
        icon_label.setFont(QFont("Arial", 64))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #e0e0e0;")
        center_layout.addWidget(icon_label)
        
        # Texte principal
        title_label = QLabel("Sélectionnez un email")
        title_label.setFont(QFont("Inter", 22, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #616161; margin: 0;")
        center_layout.addWidget(title_label)
        
        # Texte descriptif
        desc_label = QLabel("Cliquez sur un email dans la liste de gauche pour voir son contenu détaillé et les pièces jointes.")
        desc_label.setFont(QFont("Inter", 14))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #9e9e9e; line-height: 1.6; margin: 0; padding: 0;")
        center_layout.addWidget(desc_label)
        
        # Centrer le container horizontalement
        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        h_layout.addWidget(center_container)
        h_layout.addStretch(1)
        
        main_layout.addLayout(h_layout)
        
        # Spacer du bas pour centrer verticalement
        main_layout.addStretch(1)
        
        return widget
    
    def _create_email_content_widget(self) -> QWidget:
        """Widget de contenu d'email CORRIGÉ avec pièces jointes."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(25)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header de l'email
        self.email_header = self._create_email_header()
        layout.addWidget(self.email_header)
        
        # Section des pièces jointes (cachée par défaut)
        self.attachments_section = self._create_attachments_section()
        self.attachments_section.hide()
        layout.addWidget(self.attachments_section)
        
        # Actions
        self.email_actions = self._create_email_actions()
        layout.addWidget(self.email_actions)
        
        # Contenu
        self.email_body = self._create_email_body()
        layout.addWidget(self.email_body)
        
        # Analyse IA
        self.ai_analysis_section = self._create_ai_analysis_section()
        layout.addWidget(self.ai_analysis_section)
        
        return widget
    
    def _create_email_header(self) -> QFrame:
        """Header de l'email CORRIGÉ."""
        header = QFrame()
        header.setObjectName("email-header")
        header.setMinimumHeight(140)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # Ligne 1: Expéditeur et date
        first_row = QHBoxLayout()
        first_row.setSpacing(20)
        
        self.sender_label = QLabel()
        self.sender_label.setObjectName("sender-name")
        self.sender_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self.sender_label.setWordWrap(True)
        first_row.addWidget(self.sender_label)
        
        first_row.addStretch()
        
        self.date_label = QLabel()
        self.date_label.setObjectName("email-date")
        self.date_label.setFont(QFont("Inter", 13))
        first_row.addWidget(self.date_label)
        
        layout.addLayout(first_row)
        
        # Ligne 2: Email address
        self.email_address_label = QLabel()
        self.email_address_label.setObjectName("email-address")
        self.email_address_label.setFont(QFont("Inter", 12))
        self.email_address_label.setWordWrap(True)
        layout.addWidget(self.email_address_label)
        
        # Ligne 3: Sujet
        self.subject_label = QLabel()
        self.subject_label.setObjectName("email-subject")
        self.subject_label.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        self.subject_label.setWordWrap(True)
        self.subject_label.setMinimumHeight(50)
        layout.addWidget(self.subject_label)
        
        return header
    
    def _create_attachments_section(self) -> QFrame:
        """Section des pièces jointes."""
        attachments_frame = QFrame()
        attachments_frame.setObjectName("attachments-section")
        
        layout = QVBoxLayout(attachments_frame)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 15, 25, 15)
        
        # Titre
        title_layout = QHBoxLayout()
        title_icon = QLabel("📎")
        title_icon.setFont(QFont("Arial", 16))
        title_layout.addWidget(title_icon)
        
        self.attachments_title = QLabel("Pièces jointes")
        self.attachments_title.setObjectName("section-title")
        self.attachments_title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        title_layout.addWidget(self.attachments_title)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Container pour les cartes de pièces jointes
        self.attachments_container = QWidget()
        self.attachments_layout = QVBoxLayout(self.attachments_container)
        self.attachments_layout.setSpacing(6)
        self.attachments_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.attachments_container)
        
        return attachments_frame
    
    def _create_email_actions(self) -> QFrame:
        """Barre d'actions."""
        actions = QFrame()
        actions.setObjectName("email-actions")
        actions.setFixedHeight(80)
        
        # Layout principal avec centrage parfait
        main_layout = QVBoxLayout(actions)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Spacer vertical pour centrer
        main_layout.addStretch(1)
        
        # Container des boutons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(25, 0, 25, 0)
        buttons_layout.setSpacing(0)
        
        # Centrage parfait avec des spacers
        buttons_layout.addStretch(2)
        
        # Boutons principaux
        self.reply_btn = QPushButton("↩️ Répondre")
        self.reply_btn.setObjectName("action-btn")
        self.reply_btn.setFixedSize(140, 45)
        self.reply_btn.clicked.connect(lambda: self.action_requested.emit("reply", self.current_email))
        buttons_layout.addWidget(self.reply_btn)
        
        buttons_layout.addSpacing(15)
        
        self.forward_btn = QPushButton("➡️ Transférer")
        self.forward_btn.setObjectName("action-btn")
        self.forward_btn.setFixedSize(140, 45)
        self.forward_btn.clicked.connect(lambda: self.action_requested.emit("forward", self.current_email))
        buttons_layout.addWidget(self.forward_btn)
        
        buttons_layout.addSpacing(15)
        
        self.archive_btn = QPushButton("📁 Archiver")
        self.archive_btn.setObjectName("action-btn")
        self.archive_btn.setFixedSize(140, 45)
        self.archive_btn.clicked.connect(lambda: self.action_requested.emit("archive", self.current_email))
        buttons_layout.addWidget(self.archive_btn)
        
        buttons_layout.addSpacing(30)
        
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.setObjectName("delete-btn")
        self.delete_btn.setFixedSize(140, 45)
        self.delete_btn.clicked.connect(lambda: self.action_requested.emit("delete", self.current_email))
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch(2)
        
        main_layout.addWidget(buttons_container)
        main_layout.addStretch(1)
        
        return actions
    
    def _create_email_body(self) -> QFrame:
        """Zone de contenu CORRIGÉE."""
        body_frame = QFrame()
        body_frame.setObjectName("email-body-frame")
        body_frame.setMinimumHeight(300)
        
        layout = QVBoxLayout(body_frame)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)
        
        # Titre
        title = QLabel("📄 Contenu de l'email")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Zone de texte avec scroll interne
        self.content_display = QTextEdit()
        self.content_display.setObjectName("email-content")
        self.content_display.setReadOnly(True)
        self.content_display.setFont(QFont("Inter", 13))
        self.content_display.setMinimumHeight(250)
        layout.addWidget(self.content_display)
        
        return body_frame
    
    def _create_ai_analysis_section(self) -> QFrame:
        """Section d'analyse IA."""
        ai_frame = QFrame()
        ai_frame.setObjectName("ai-analysis-frame")
        ai_frame.setMinimumHeight(200)
        
        layout = QVBoxLayout(ai_frame)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)
        
        # Titre
        title = QLabel("🤖 Analyse Intelligence Artificielle")
        title.setObjectName("section-title")
        title.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Contenu de l'analyse
        self.ai_content = QLabel("Aucune analyse disponible")
        self.ai_content.setObjectName("ai-analysis-content")
        self.ai_content.setWordWrap(True)
        self.ai_content.setFont(QFont("Inter", 13))
        self.ai_content.setMinimumHeight(120)
        self.ai_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.ai_content)
        
        return ai_frame
    
    def _apply_style(self):
        """Style CORRIGÉ pour une excellente lisibilité."""
        self.setStyleSheet("""
            QWidget#email-detail-view {
                background-color: #ffffff;
            }
            
            QWidget#no-selection-widget {
                background-color: #ffffff;
            }
            
            /* === SCROLLBAR === */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #cbd3da;
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #9ea7ad;
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* === HEADER EMAIL === */
            QFrame#email-header {
                background-color: #f8fafe;
                border: 3px solid #e3f2fd;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            QLabel#sender-name {
                color: #0d47a1;
                font-weight: 700;
                line-height: 1.3;
            }
            
            QLabel#email-date {
                color: #546e7a;
                font-weight: 500;
                background-color: #eceff1;
                padding: 8px 12px;
                border-radius: 20px;
            }
            
            QLabel#email-address {
                color: #607d8b;
                font-weight: 400;
                font-style: italic;
            }
            
            QLabel#email-subject {
                color: #1a237e;
                font-weight: 700;
                margin-top: 10px;
                line-height: 1.4;
                padding: 10px 0;
            }
            
            /* === PIÈCES JOINTES === */
            QFrame#attachments-section {
                background-color: #fff3e0;
                border: 3px solid #ffcc02;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            /* === ACTIONS === */
            QFrame#email-actions {
                background-color: #f8f9fa;
                border: 2px solid #e3f2fd;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            QPushButton#action-btn {
                background-color: #1976d2;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                font-weight: 700;
                font-size: 13px;
                text-align: center;
                margin: 0px;
            }
            
            QPushButton#action-btn:hover {
                background-color: #1565c0;
                transform: translateY(-1px);
            }
            
            QPushButton#action-btn:pressed {
                background-color: #0d47a1;
                transform: translateY(0px);
            }
            
            QPushButton#delete-btn {
                background-color: #d32f2f;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                font-weight: 700;
                font-size: 13px;
                text-align: center;
                margin: 0px;
            }
            
            QPushButton#delete-btn:hover {
                background-color: #c62828;
                transform: translateY(-1px);
            }
            
            QPushButton#delete-btn:pressed {
                background-color: #b71c1c;
                transform: translateY(0px);
            }
            
            /* === CONTENU EMAIL === */
            QFrame#email-body-frame {
                background-color: #ffffff;
                border: 3px solid #e8eaf6;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            QLabel#section-title {
                color: #1a237e;
                font-weight: 700;
                margin-bottom: 10px;
                padding: 5px 0;
            }
            
            QTextEdit#email-content {
                background-color: #fafbfc;
                border: 2px solid #e3f2fd;
                border-radius: 12px;
                padding: 20px;
                color: #263238;
                line-height: 1.7;
                font-family: 'Inter', Arial, sans-serif;
                font-size: 13px;
            }
            
            QTextEdit#email-content:focus {
                border-color: #1976d2;
                background-color: #ffffff;
            }
            
            /* === ANALYSE IA === */
            QFrame#ai-analysis-frame {
                background-color: #f3e5f5;
                border: 3px solid #ce93d8;
                border-radius: 15px;
                margin-bottom: 20px;
            }
            
            QLabel#ai-analysis-content {
                background-color: #ffffff;
                border: 2px solid #e1bee7;
                border-radius: 12px;
                padding: 20px;
                color: #4a148c;
                line-height: 1.6;
                font-family: 'Inter', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
        """)
    
    def show_email(self, email: Email):
        """Affiche un email CORRIGÉ avec pièces jointes."""
        self.current_email = email
        
        # Cacher le message par défaut, afficher le contenu
        self.no_selection_widget.hide()
        self.email_content_widget.show()
        
        # Mettre à jour le header
        sender_name = email.get_sender_name()
        self.sender_label.setText(sender_name)
        
        self.email_address_label.setText(f"<{email.sender}>")
        
        subject = email.subject or "(Aucun sujet)"
        self.subject_label.setText(subject)
        
        if email.received_date:
            date_str = email.received_date.strftime("%d/%m/%Y à %H:%M")
            self.date_label.setText(date_str)
        else:
            self.date_label.setText("Date inconnue")
        
        # Mettre à jour les pièces jointes
        self._update_attachments()
        
        # Mettre à jour le contenu
        body_text = email.body or email.snippet or "(Aucun contenu)"
        
        # Le contenu est déjà nettoyé par le GmailClient
        self.content_display.setPlainText(body_text)
        
        # Mettre à jour l'analyse IA
        self._update_ai_analysis()
        
        # Scroller vers le haut
        self.scroll_area.verticalScrollBar().setValue(0)
        
        logger.info(f"Affichage email: {email.id} avec {len(email.attachments)} pièces jointes")
    
    def _update_attachments(self):
        """Met à jour l'affichage des pièces jointes."""
        # Vider le container existant
        for i in reversed(range(self.attachments_layout.count())):
            item = self.attachments_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
        
        if not self.current_email or not self.current_email.has_attachments:
            self.attachments_section.hide()
            return
        
        # Mettre à jour le titre
        count = self.current_email.attachments_count
        total_size = self.current_email._format_total_size()
        
        if count == 1:
            title_text = f"1 pièce jointe ({total_size})"
        else:
            title_text = f"{count} pièces jointes ({total_size})"
        
        self.attachments_title.setText(title_text)
        
        # Créer les cartes de pièces jointes
        for attachment in self.current_email.attachments:
            card = AttachmentCard(attachment)
            card.download_requested.connect(self._download_attachment)
            self.attachments_layout.addWidget(card)
        
        self.attachments_section.show()
    
    def _download_attachment(self, attachment: EmailAttachment):
        """Télécharge une pièce jointe."""
        if not self.gmail_client or not self.current_email:
            QMessageBox.warning(self, "Erreur", "Impossible de télécharger la pièce jointe.")
            return
        
        try:
            # Demander où sauvegarder
            suggested_name = attachment.filename
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Sauvegarder la pièce jointe",
                suggested_name,
                "Tous les fichiers (*.*)"
            )
            
            if not file_path:
                return
            
            # Télécharger et sauvegarder
            success = self.gmail_client.save_attachment(
                self.current_email.id,
                attachment.attachment_id,
                attachment.filename,
                file_path
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Téléchargement réussi",
                    f"La pièce jointe '{attachment.filename}' a été sauvegardée."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur de téléchargement",
                    f"Impossible de télécharger '{attachment.filename}'."
                )
                
        except Exception as e:
            logger.error(f"Erreur téléchargement pièce jointe: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur s'est produite lors du téléchargement:\n{str(e)}"
            )
    
    def _update_ai_analysis(self):
        """Met à jour l'analyse IA."""
        if not self.current_email or not hasattr(self.current_email, 'ai_analysis'):
            self.ai_content.setText("🔍 Aucune analyse IA disponible pour cet email.")
            return
        
        analysis = self.current_email.ai_analysis
        if not analysis:
            self.ai_content.setText("🔍 Aucune analyse IA disponible pour cet email.")
            return
        
        # Construire le texte d'analyse
        category_names = {
            'cv': '📄 Candidature/CV',
            'rdv': '📅 Rendez-vous',
            'support': '🛠️ Support technique',
            'facture': '💰 Facture',
            'spam': '🚫 Spam',
            'general': '📧 Email général'
        }
        
        category_display = category_names.get(getattr(analysis, 'category', 'general'), '📝 Autre')
        confidence = getattr(analysis, 'confidence', 0) * 100
        priority = getattr(analysis, 'priority', 3)
        should_respond = getattr(analysis, 'should_auto_respond', False)
        reasoning = getattr(analysis, 'reasoning', 'Aucun raisonnement disponible')
       
        ai_text = f"""📂 CATÉGORIE DÉTECTÉE
    {category_display}

    📊 NIVEAU DE CONFIANCE
    {confidence:.0f}% de certitude

⚡ NIVEAU DE PRIORITÉ
    {self._get_priority_text(priority)}

🤖 RÉPONSE AUTOMATIQUE
    {'✅ Recommandée par l\'IA' if should_respond else '❌ Non recommandée'}

🧠 ANALYSE DÉTAILLÉE
    {reasoning}"""
       
       # Ajouter des informations extraites si disponibles
        extracted_info = getattr(analysis, 'extracted_info', {})
        if extracted_info:
            ai_text += "\n\n📋 INFORMATIONS EXTRAITES"
            for key, value in extracted_info.items():
                if value:
                    ai_text += f"\n• {key.title()}: {value}"
       
        self.ai_content.setText(ai_text)
   
    def _get_priority_text(self, priority: int) -> str:
       """Convertit la priorité en texte."""
       priority_map = {
           1: "🔴 Très urgent (priorité maximale)",
           2: "🟠 Urgent (traitement rapide)", 
           3: "🟡 Normal (priorité standard)",
           4: "🟢 Faible (peut attendre)",
           5: "⚪ Très faible (non prioritaire)"
       }
       return priority_map.get(priority, f"❓ Priorité {priority}")
   
    def clear_selection(self):
       """Efface la sélection."""
       self.current_email = None
       self.email_content_widget.hide()
       self.no_selection_widget.show()
       
       # Scroller vers le haut
       self.scroll_area.verticalScrollBar().setValue(0)