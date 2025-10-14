#!/usr/bin/env python3
"""
Vue composition email - CORRIGÉE COMPLÈTEMENT
"""
import logging
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QFrame,
    QFileDialog, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from app.gmail_client import GmailClient
from app.ai_processor import AIProcessor

logger = logging.getLogger(__name__)

class ComposeView(QDialog):
    """Composition email."""
    
    email_sent = pyqtSignal()
    
    def __init__(self, parent=None, gmail_client: GmailClient = None, 
                 ai_processor: AIProcessor = None, reply_to: object = None):
        super().__init__(parent)
        
        self.gmail_client = gmail_client
        self.ai_processor = ai_processor
        self.reply_to = reply_to
        self.attachments = []
        
        self._setup_ui()
        
        if reply_to:
            self._populate_reply()
    
    def _setup_ui(self):
        """Interface."""
        self.setWindowTitle("✉️ Nouveau message - Dynovate Mail")
        self.setMinimumSize(900, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # En-tête
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background-color: #5b21b6;
                border-bottom: 2px solid #4c1d95;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 15, 30, 15)
        
        title = QLabel("✉️ Nouveau message")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Bouton aide IA
        ai_btn = QPushButton("🤖 Aide IA")
        ai_btn.setFont(QFont("Arial", 11, QFont.Bold))
        ai_btn.setFixedHeight(40)
        ai_btn.setCursor(Qt.PointingHandCursor)
        ai_btn.clicked.connect(self._request_ai_help)
        ai_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 2px solid white;
                border-radius: 20px;
                padding: 0 25px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        header_layout.addWidget(ai_btn)
        
        layout.addWidget(header)
        
        # Formulaire
        form_container = QWidget()
        form_container.setStyleSheet("background-color: #ffffff;")
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)
        
        # Destinataire
        to_layout = QHBoxLayout()
        to_label = QLabel("À:")
        to_label.setFont(QFont("Arial", 13, QFont.Bold))
        to_label.setFixedWidth(100)
        to_label.setStyleSheet("color: #1a1a1a;")
        to_layout.addWidget(to_label)
        
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("destinataire@example.com")
        self.to_input.setFont(QFont("Arial", 13))
        self.to_input.setFixedHeight(45)
        to_layout.addWidget(self.to_input)
        form_layout.addLayout(to_layout)
        
        # CC
        cc_layout = QHBoxLayout()
        cc_label = QLabel("Cc:")
        cc_label.setFont(QFont("Arial", 13, QFont.Bold))
        cc_label.setFixedWidth(100)
        cc_label.setStyleSheet("color: #1a1a1a;")
        cc_layout.addWidget(cc_label)
        
        self.cc_input = QLineEdit()
        self.cc_input.setPlaceholderText("(optionnel)")
        self.cc_input.setFont(QFont("Arial", 13))
        self.cc_input.setFixedHeight(45)
        cc_layout.addWidget(self.cc_input)
        form_layout.addLayout(cc_layout)
        
        # Sujet
        subject_layout = QHBoxLayout()
        subject_label = QLabel("Sujet:")
        subject_label.setFont(QFont("Arial", 13, QFont.Bold))
        subject_label.setFixedWidth(100)
        subject_label.setStyleSheet("color: #1a1a1a;")
        subject_layout.addWidget(subject_label)
        
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Objet du message")
        self.subject_input.setFont(QFont("Arial", 13))
        self.subject_input.setFixedHeight(45)
        subject_layout.addWidget(self.subject_input)
        form_layout.addLayout(subject_layout)
        
        # Message
        message_label = QLabel("Message:")
        message_label.setFont(QFont("Arial", 13, QFont.Bold))
        message_label.setStyleSheet("color: #1a1a1a;")
        form_layout.addWidget(message_label)
        
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Écrivez votre message ici...")
        self.body_input.setFont(QFont("Arial", 13))
        self.body_input.setMinimumHeight(300)
        form_layout.addWidget(self.body_input)
        
        # Pièces jointes
        attachments_label = QLabel("📎 Pièces jointes:")
        attachments_label.setFont(QFont("Arial", 13, QFont.Bold))
        attachments_label.setStyleSheet("color: #1a1a1a;")
        form_layout.addWidget(attachments_label)
        
        self.attachments_container = QFrame()
        self.attachments_container.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 2px dashed #d1d5db;
                border-radius: 10px;
                padding: 15px;
                min-height: 80px;
            }
        """)
        
        self.attachments_layout = QVBoxLayout(self.attachments_container)
        self.attachments_layout.setSpacing(8)
        
        no_attachments = QLabel("Aucune pièce jointe")
        no_attachments.setFont(QFont("Arial", 11))
        no_attachments.setStyleSheet("color: #9ca3af;")
        no_attachments.setAlignment(Qt.AlignCenter)
        self.attachments_layout.addWidget(no_attachments)
        
        form_layout.addWidget(self.attachments_container)
        
        # Bouton ajouter pièce jointe
        attach_btn = QPushButton("📎 Ajouter une pièce jointe")
        attach_btn.setFont(QFont("Arial", 11))
        attach_btn.setFixedHeight(40)
        attach_btn.setCursor(Qt.PointingHandCursor)
        attach_btn.clicked.connect(self._add_attachment)
        attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 2px solid #d1d5db;
                border-radius: 20px;
                padding: 0 25px;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
                border-color: #9ca3af;
            }
        """)
        form_layout.addWidget(attach_btn)
        
        layout.addWidget(form_container)
        
        # Footer
        footer = QFrame()
        footer.setFixedHeight(90)
        footer.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border-top: 2px solid #e5e7eb;
            }
        """)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(30, 20, 30, 20)
        footer_layout.setSpacing(15)
        
        footer_layout.addStretch()
        
        # Bouton annuler
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.setFont(QFont("Arial", 12, QFont.Bold))
        cancel_btn.setFixedHeight(50)
        cancel_btn.setFixedWidth(140)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #d1d5db;
                border-radius: 25px;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                border-color: #9ca3af;
            }
        """)
        footer_layout.addWidget(cancel_btn)
        
        # Bouton envoyer
        send_btn = QPushButton("📤 Envoyer")
        send_btn.setFont(QFont("Arial", 12, QFont.Bold))
        send_btn.setFixedHeight(50)
        send_btn.setFixedWidth(150)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self._send_email)
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
        footer_layout.addWidget(send_btn)
        
        layout.addWidget(footer)
        
        self._apply_input_styles()
    
    def _apply_input_styles(self):
        """Styles des inputs."""
        style = """
            QLineEdit, QTextEdit {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                padding: 12px 15px;
                color: #000000;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #5b21b6;
                background-color: #faf5ff;
            }
        """
        
        self.to_input.setStyleSheet(style)
        self.cc_input.setStyleSheet(style)
        self.subject_input.setStyleSheet(style)
        self.body_input.setStyleSheet(style)
    
    def _populate_reply(self):
        """Pré-remplir pour réponse."""
        if not self.reply_to:
            return
        
        self.to_input.setText(self.reply_to.sender or "")
        
        subject = self.reply_to.subject or ""
        if not subject.startswith("Re:"):
            self.subject_input.setText(f"Re: {subject}")
        else:
            self.subject_input.setText(subject)
        
        if self.reply_to.body:
            date_str = self.reply_to.received_date.strftime("%d/%m/%Y à %H:%M") if self.reply_to.received_date else "Date inconnue"
            quoted = f"\n\n---\nLe {date_str}, {self.reply_to.sender} a écrit :\n> {self.reply_to.body[:500]}"
            self.body_input.setPlainText(quoted)
            
            cursor = self.body_input.textCursor()
            cursor.setPosition(0)
            self.body_input.setTextCursor(cursor)
    
    def _add_attachment(self):
        """Ajouter pièce jointe."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier",
            "",
            "Tous les fichiers (*.*)"
        )
        
        if filepath:
            if self.attachments_layout.count() == 1:
                item = self.attachments_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            self.attachments.append(filepath)
            widget = self._create_attachment_widget(filepath)
            self.attachments_layout.addWidget(widget)
            
            logger.info(f"Pièce jointe: {filepath}")
    
    def _create_attachment_widget(self, filepath: str) -> QFrame:
        """Widget pièce jointe."""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 10px 15px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        
        icon = QLabel("📄")
        icon.setFont(QFont("Arial", 20))
        layout.addWidget(icon)
        
        filename = os.path.basename(filepath)
        name = QLabel(filename)
        name.setFont(QFont("Arial", 11))
        name.setStyleSheet("color: #374151;")
        layout.addWidget(name, 1)
        
        try:
            size = os.path.getsize(filepath)
            size_str = self._format_size(size)
            size_label = QLabel(size_str)
            size_label.setFont(QFont("Arial", 10))
            size_label.setStyleSheet("color: #6b7280;")
            layout.addWidget(size_label)
        except:
            pass
        
        remove_btn = QPushButton("✖")
        remove_btn.setFont(QFont("Arial", 12))
        remove_btn.setFixedSize(30, 30)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.clicked.connect(lambda: self._remove_attachment(filepath, widget))
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                border: none;
                border-radius: 15px;
                color: #dc2626;
            }
            QPushButton:hover {
                background-color: #dc2626;
                color: white;
            }
        """)
        layout.addWidget(remove_btn)
        
        return widget
    
    def _remove_attachment(self, filepath: str, widget: QFrame):
        """Supprimer pièce jointe."""
        if filepath in self.attachments:
            self.attachments.remove(filepath)
        
        widget.deleteLater()
        
        if len(self.attachments) == 0:
            no_att = QLabel("Aucune pièce jointe")
            no_att.setFont(QFont("Arial", 11))
            no_att.setStyleSheet("color: #9ca3af;")
            no_att.setAlignment(Qt.AlignCenter)
            self.attachments_layout.addWidget(no_att)
        
        logger.info(f"Pièce jointe supprimée: {filepath}")
    
    def _format_size(self, size: int) -> str:
        """Formate taille."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    
    def _request_ai_help(self):
        """Aide IA."""
        if not self.ai_processor:
            QMessageBox.warning(self, "Non disponible", "L'assistant IA n'est pas disponible.")
            return
        
        subject = self.subject_input.text()
        body = self.body_input.toPlainText()
        
        if not subject and not body:
            QMessageBox.information(
                self, "Aide IA",
                "Commencez à écrire et je pourrai vous aider !"
            )
            return
        
        try:
            prompt = f"Sujet: {subject}\n\nContenu: {body}"
            response = self.ai_processor.generate_response(prompt, context="Améliore ce texte")
            
            if response:
                reply = QMessageBox.question(
                    self, "Suggestion IA",
                    f"Suggestion:\n\n{response}\n\nUtiliser ?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.body_input.setPlainText(response)
        except Exception as e:
            logger.error(f"Erreur IA: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de générer:\n{e}")
    
    def _send_email(self):
        """Envoyer email."""
        to = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()
        
        if not to:
            QMessageBox.warning(self, "Erreur", "Veuillez spécifier un destinataire.")
            self.to_input.setFocus()
            return
        
        if not subject:
            reply = QMessageBox.question(
                self, "Confirmation",
                "Envoyer sans sujet ?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                self.subject_input.setFocus()
                return
        
        try:
            cc = self.cc_input.text().strip() if self.cc_input.text().strip() else None
            
            if self.gmail_client:
                self.gmail_client.send_email(
                    to=to,
                    subject=subject,
                    body=body,
                    cc=cc,
                    attachments=self.attachments
                )
                
                QMessageBox.information(self, "Succès", "✅ Email envoyé !")
                logger.info(f"Email envoyé à {to}")
                
                self.email_sent.emit()
                self.accept()
            else:
                QMessageBox.critical(self, "Erreur", "Client Gmail non disponible.")
        
        except Exception as e:
            logger.error(f"Erreur envoi: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'envoyer:\n{e}")