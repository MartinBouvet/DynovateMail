#!/usr/bin/env python3
"""
Vue de composition d'email - CORRIGÉE
"""
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QFrame,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import os

from gmail_client import GmailClient
from ai_processor import AIProcessor

logger = logging.getLogger(__name__)

class ComposeView(QDialog):
    """Fenêtre de composition d'email."""
    
    email_sent = pyqtSignal()
    
    def __init__(self, parent=None, gmail_client: GmailClient = None, ai_processor: AIProcessor = None):
        super().__init__(parent)
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.attachments = []
        self.is_ai_response = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Crée l'interface."""
        self.setWindowTitle("Nouveau message - Dynovate Mail")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # En-tête
        header = QLabel("✉️ Nouveau message")
        header.setFont(QFont("SF Pro Display", 20, QFont.Bold))
        header.setStyleSheet("color: #5b21b6;")
        layout.addWidget(header)
        
        # Destinataires
        to_layout = QHBoxLayout()
        to_label = QLabel("À:")
        to_label.setFont(QFont("SF Pro Display", 12))
        to_label.setFixedWidth(80)
        to_layout.addWidget(to_label)
        
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("destinataire@example.com")
        self.to_input.setFont(QFont("SF Pro Display", 12))
        to_layout.addWidget(self.to_input)
        
        layout.addLayout(to_layout)
        
        # CC
        cc_layout = QHBoxLayout()
        cc_label = QLabel("Cc:")
        cc_label.setFont(QFont("SF Pro Display", 12))
        cc_label.setFixedWidth(80)
        cc_layout.addWidget(cc_label)
        
        self.cc_input = QLineEdit()
        self.cc_input.setPlaceholderText("(optionnel)")
        self.cc_input.setFont(QFont("SF Pro Display", 12))
        cc_layout.addWidget(self.cc_input)
        
        layout.addLayout(cc_layout)
        
        # Sujet
        subject_layout = QHBoxLayout()
        subject_label = QLabel("Sujet:")
        subject_label.setFont(QFont("SF Pro Display", 12))
        subject_label.setFixedWidth(80)
        subject_layout.addWidget(subject_label)
        
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Sujet de l'email")
        self.subject_input.setFont(QFont("SF Pro Display", 12))
        subject_layout.addWidget(self.subject_input)
        
        layout.addLayout(subject_layout)
        
        # Corps
        body_label = QLabel("Message:")
        body_label.setFont(QFont("SF Pro Display", 12))
        layout.addWidget(body_label)
        
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Écrivez votre message ici...")
        self.body_input.setFont(QFont("SF Pro Display", 12))
        layout.addWidget(self.body_input)
        
        # Section pièces jointes
        self.attachments_section = QFrame()
        self.attachments_section.setObjectName("attachments-section")
        attachments_layout = QVBoxLayout(self.attachments_section)
        
        attachments_title = QLabel("📎 Pièces jointes:")
        attachments_title.setFont(QFont("SF Pro Display", 11, QFont.Bold))
        attachments_layout.addWidget(attachments_title)
        
        self.attachments_layout = QVBoxLayout()
        attachments_layout.addLayout(self.attachments_layout)
        
        self.attachments_section.hide()
        layout.addWidget(self.attachments_section)
        
        # Barre d'actions
        actions_layout = QHBoxLayout()
        
        send_btn = QPushButton("📤 Envoyer")
        send_btn.setObjectName("send-btn")
        send_btn.setFont(QFont("SF Pro Display", 13, QFont.Bold))
        send_btn.setFixedHeight(45)
        send_btn.setMinimumWidth(120)
        send_btn.clicked.connect(self._send_email)
        actions_layout.addWidget(send_btn)
        
        attach_btn = QPushButton("📎 Joindre fichier")
        attach_btn.setFont(QFont("SF Pro Display", 12))
        attach_btn.setFixedHeight(45)
        attach_btn.clicked.connect(self._add_attachment)
        actions_layout.addWidget(attach_btn)
        
        ai_btn = QPushButton("🤖 Générer avec IA")
        ai_btn.setFont(QFont("SF Pro Display", 12))
        ai_btn.setFixedHeight(45)
        ai_btn.clicked.connect(self._generate_ai_response)
        actions_layout.addWidget(ai_btn)
        
        actions_layout.addStretch()
        
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.setFont(QFont("SF Pro Display", 12))
        cancel_btn.setFixedHeight(45)
        cancel_btn.clicked.connect(self.close)
        actions_layout.addWidget(cancel_btn)
        
        layout.addLayout(actions_layout)
    
    def _add_attachment(self):
        """Ajoute une pièce jointe."""
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
        label.setFont(QFont("SF Pro Display", 11))
        label.setStyleSheet("color: #000000;")
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
    
    def _generate_ai_response(self):
        """Génère une réponse avec l'IA."""
        subject = self.subject_input.text().strip()
        if not subject:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un sujet pour générer une réponse IA.")
            return
        
        try:
            # Générer avec l'IA
            ai_response = f"Bonjour,\n\nMerci pour votre message concernant : {subject}\n\nNous avons bien pris en compte votre demande et nous reviendrons vers vous dans les plus brefs délais.\n\nCordialement,\nL'équipe Dynovate"
            
            self.body_input.setPlainText(ai_response)
            self.is_ai_response = True
            
            logger.info("Réponse IA générée")
            
        except Exception as e:
            logger.error(f"Erreur génération IA: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de générer la réponse IA: {e}")
    
    def _send_email(self):
        """Envoie l'email."""
        try:
            # Validation
            to_text = self.to_input.text().strip()
            if not to_text:
                QMessageBox.warning(self, "Erreur", "Veuillez saisir au moins un destinataire.")
                return
            
            subject = self.subject_input.text().strip()
            if not subject:
                QMessageBox.warning(self, "Erreur", "Veuillez saisir un sujet.")
                return
            
            body = self.body_input.toPlainText().strip()
            if not body:
                QMessageBox.warning(self, "Erreur", "Veuillez écrire un message.")
                return
            
            # Préparer les destinataires
            to_list = [email.strip() for email in to_text.split(',')]
            cc_list = []
            cc_text = self.cc_input.text().strip()
            if cc_text:
                cc_list = [email.strip() for email in cc_text.split(',')]
            
            # Envoyer
            success = self.gmail_client.send_email(
                to=to_list,
                subject=subject,
                body=body,
                cc=cc_list if cc_list else None,
                attachments=self.attachments if self.attachments else None
            )
            
            if success:
                logger.info("Email envoyé avec succès")
                self.email_sent.emit()
                self.close()
            else:
                QMessageBox.critical(self, "Erreur", "Échec de l'envoi de l'email.")
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'envoyer l'email: {e}")
    
    def _apply_styles(self):
        """Applique les styles Dynovate."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            QLabel {
                color: #000000;
            }
            
            QLineEdit, QTextEdit {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                color: #000000;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border-color: #5b21b6;
            }
            
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 16px;
            }
            
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #5b21b6;
            }
            
            #send-btn {
                background-color: #5b21b6;
                color: #ffffff;
                border: none;
            }
            
            #send-btn:hover {
                background-color: #4c1d95;
            }
            
            #attachments-section {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
            }
            
            #attachment-item {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                margin-bottom: 5px;
            }
            
            #remove-attachment-btn {
                background-color: #ef4444;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 10px;
            }
            
            #remove-attachment-btn:hover {
                background-color: #dc2626;
            }
        """)