#!/usr/bin/env python3
"""
Vue de composition d'emails - VERSION CORRIGÉE COMPLÈTE
Corrections: Envoi, pièces jointes, validation
"""
import logging
import os
from typing import Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFileDialog, QMessageBox, QFrame,
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from gmail_client import GmailClient
from models.email_model import Email

logger = logging.getLogger(__name__)


class ComposeView(QDialog):
    """Dialogue de composition d'email - CORRIGÉ."""
    
    email_sent = pyqtSignal()
    
    def __init__(self, gmail_client: GmailClient, parent=None,
                 to: str = "", subject: str = "", body: str = "",
                 is_reply: bool = False, is_forward: bool = False):
        super().__init__(parent)
        
        self.gmail_client = gmail_client
        self.is_reply = is_reply
        self.is_forward = is_forward
        self.attachments = []
        self.is_ai_response = False
        
        # Configuration
        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        # Initialisation UI
        self._setup_ui()
        
        # Pré-remplir si nécessaire
        if to:
            self.to_input.setText(to)
        if subject:
            self.subject_input.setText(subject)
        if body:
            self.body_input.setPlainText(body)
    
    def _get_window_title(self) -> str:
        """Retourne le titre de la fenêtre."""
        if self.is_reply:
            return "Répondre à l'email"
        elif self.is_forward:
            return "Transférer l'email"
        else:
            return "Nouveau message"
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header avec indicateur IA
        self.ai_indicator = QLabel("✨ Réponse générée par IA")
        self.ai_indicator.setObjectName("ai-indicator")
        self.ai_indicator.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.ai_indicator.setStyleSheet("""
            QLabel#ai-indicator {
                background-color: #e7f3ff;
                color: #007bff;
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid #b3d9ff;
            }
        """)
        self.ai_indicator.hide()
        layout.addWidget(self.ai_indicator)
        
        # === CHAMPS DU FORMULAIRE ===
        
        # Destinataire(s)
        to_layout = QHBoxLayout()
        to_layout.setSpacing(10)
        
        to_label = QLabel("À:")
        to_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        to_label.setFixedWidth(80)
        to_layout.addWidget(to_label)
        
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("destinataire@example.com (séparer par des virgules)")
        self.to_input.setFont(QFont("Inter", 12))
        to_layout.addWidget(self.to_input)
        
        layout.addLayout(to_layout)
        
        # CC (optionnel)
        cc_layout = QHBoxLayout()
        cc_layout.setSpacing(10)
        
        cc_label = QLabel("CC:")
        cc_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        cc_label.setFixedWidth(80)
        cc_layout.addWidget(cc_label)
        
        self.cc_input = QLineEdit()
        self.cc_input.setPlaceholderText("(optionnel)")
        self.cc_input.setFont(QFont("Inter", 12))
        cc_layout.addWidget(self.cc_input)
        
        layout.addLayout(cc_layout)
        
        # Sujet
        subject_layout = QHBoxLayout()
        subject_layout.setSpacing(10)
        
        subject_label = QLabel("Sujet:")
        subject_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        subject_label.setFixedWidth(80)
        subject_layout.addWidget(subject_label)
        
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Sujet de l'email")
        self.subject_input.setFont(QFont("Inter", 12))
        subject_layout.addWidget(self.subject_input)
        
        layout.addLayout(subject_layout)
        
        # Section pièces jointes
        self.attachments_section = self._create_attachments_section()
        layout.addWidget(self.attachments_section)
        
        # Corps du message
        body_label = QLabel("Message:")
        body_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        layout.addWidget(body_label)
        
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Écrivez votre message ici...")
        self.body_input.setFont(QFont("Inter", 12))
        self.body_input.setMinimumHeight(250)
        layout.addWidget(self.body_input)
        
        # Barre d'actions en bas
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        # Bouton ajouter pièce jointe
        attach_btn = QPushButton("📎 Ajouter pièce jointe")
        attach_btn.setObjectName("secondary-btn")
        attach_btn.clicked.connect(self._add_attachment)
        actions_layout.addWidget(attach_btn)
        
        actions_layout.addStretch()
        
        # Bouton Annuler
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setObjectName("cancel-btn")
        cancel_btn.clicked.connect(self.reject)
        actions_layout.addWidget(cancel_btn)
        
        # Bouton Envoyer
        send_btn = QPushButton("✉️ Envoyer")
        send_btn.setObjectName("send-btn")
        send_btn.clicked.connect(self._send_email)
        actions_layout.addWidget(send_btn)
        
        layout.addLayout(actions_layout)
        
        self._apply_styles()
    
    def _create_attachments_section(self) -> QFrame:
        """Crée la section des pièces jointes."""
        frame = QFrame()
        frame.setObjectName("attachments-frame")
        frame.hide()
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("📎 Pièces jointes:")
        title.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Container scrollable pour les pièces jointes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(100)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.attachments_container = QWidget()
        self.attachments_layout = QVBoxLayout(self.attachments_container)
        self.attachments_layout.setSpacing(5)
        self.attachments_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.attachments_container)
        layout.addWidget(scroll)
        
        return frame
    
    def show_ai_indicator(self):
        """Affiche l'indicateur de réponse IA."""
        self.is_ai_response = True
        self.ai_indicator.show()
    
    def _add_attachment(self):
        """Ajoute une pièce jointe - CORRIGÉ."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner des fichiers",
            "",
            "Tous les fichiers (*.*)"
        )
        
        if not file_paths:
            return
        
        for file_path in file_paths:
            # Vérifier la taille (max 25MB)
            file_size = os.path.getsize(file_path)
            if file_size > 25 * 1024 * 1024:
                QMessageBox.warning(
                    self,
                    "Fichier trop volumineux",
                    f"Le fichier {os.path.basename(file_path)} dépasse 25MB."
                )
                continue
            
            # Ajouter à la liste
            if file_path not in self.attachments:
                self.attachments.append(file_path)
                self._add_attachment_item(file_path)
        
        # Afficher la section si des pièces jointes
        if self.attachments:
            self.attachments_section.show()
    
    def _add_attachment_item(self, file_path: str):
        """Ajoute un item de pièce jointe à l'UI."""
        item_frame = QFrame()
        item_frame.setObjectName("attachment-item")
        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(5, 5, 5, 5)
        
        # Nom du fichier
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / 1024  # KB
        
        label = QLabel(f"📄 {filename} ({file_size:.1f} KB)")
        label.setFont(QFont("Inter", 10))
        item_layout.addWidget(label)
        
        item_layout.addStretch()
        
        # Bouton supprimer
        remove_btn = QPushButton("✖")
        remove_btn.setObjectName("remove-attachment-btn")
        remove_btn.setFixedSize(25, 25)
        remove_btn.clicked.connect(lambda: self._remove_attachment(file_path, item_frame))
        item_layout.addWidget(remove_btn)
        
        self.attachments_layout.addWidget(item_frame)
    
    def _remove_attachment(self, file_path: str, item_frame: QFrame):
        """Supprime une pièce jointe."""
        if file_path in self.attachments:
            self.attachments.remove(file_path)
        
        item_frame.deleteLater()
        
        # Cacher la section si plus de pièces jointes
        if not self.attachments:
            self.attachments_section.hide()
    
    def _send_email(self):
        """Envoie l'email - CORRIGÉ avec validation."""
        try:
            # === VALIDATION ===
            
            # Destinataire(s)
            to_text = self.to_input.text().strip()
            if not to_text:
                QMessageBox.warning(self, "Erreur", "Veuillez saisir au moins un destinataire.")
                self.to_input.setFocus()
                return
            
            # Valider les emails
            to_emails = [email.strip() for email in to_text.split(',')]
            for email in to_emails:
                if '@' not in email or '.' not in email:
                    QMessageBox.warning(
                        self, 
                        "Erreur", 
                        f"Email invalide: {email}"
                    )
                    return
            
            # Sujet
            subject = self.subject_input.text().strip()
            if not subject:
                reply = QMessageBox.question(
                    self,
                    "Sujet vide",
                    "Voulez-vous vraiment envoyer un email sans sujet ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    self.subject_input.setFocus()
                    return
            
            # Corps
            body = self.body_input.toPlainText().strip()
            if not body:
                reply = QMessageBox.question(
                    self,
                    "Corps vide",
                    "Voulez-vous vraiment envoyer un email vide ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    self.body_input.setFocus()
                    return
            
            # CC (optionnel)
            cc_text = self.cc_input.text().strip()
            cc_emails = [email.strip() for email in cc_text.split(',') if email.strip()] if cc_text else []
            
            # === ENVOI ===
            
            logger.info(f"Envoi email à {to_emails}...")
            
            # Dialogue de progression
            progress_msg = QMessageBox(self)
            progress_msg.setWindowTitle("Envoi en cours")
            progress_msg.setText("⏳ Envoi de l'email en cours...")
            progress_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
            progress_msg.setModal(True)
            progress_msg.show()
            
            # Envoyer via Gmail Client
            success = self.gmail_client.send_email(
                to=to_emails,
                subject=subject,
                body=body,
                cc=cc_emails if cc_emails else None,
                attachments=self.attachments if self.attachments else None
            )
            
            progress_msg.close()
            
            if success:
                logger.info("Email envoyé avec succès")
                
                QMessageBox.information(
                    self,
                    "Succès",
                    "✅ Email envoyé avec succès!"
                )
                
                # Émettre le signal
                self.email_sent.emit()
                
                # Fermer le dialogue
                self.accept()
            else:
                logger.error("Échec de l'envoi de l'email")
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "❌ Impossible d'envoyer l'email.\nVérifiez votre connexion et réessayez."
                )
        
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"❌ Erreur lors de l'envoi:\n{str(e)}"
            )
    
    def _apply_styles(self):
        """Applique les styles."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            QLabel {
                color: #495057;
            }
            
            QLineEdit, QTextEdit {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 12px;
                color: #212529;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border-color: #007bff;
            }
            
            QPushButton#send-btn {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 13px;
                min-width: 120px;
            }
            QPushButton#send-btn:hover {
                background-color: #0056b3;
            }
            
            QPushButton#cancel-btn {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton#cancel-btn:hover {
                background-color: #545b62;
            }
            
            QPushButton#secondary-btn {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton#secondary-btn:hover {
                background-color: #218838;
            }
            
            QFrame#attachments-frame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            
            QFrame#attachment-item {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            
            QPushButton#remove-attachment-btn {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton#remove-attachment-btn:hover {
                background-color: #c82333;
            }
        """)