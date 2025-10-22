#!/usr/bin/env python3
"""
Vue composition d'email - AVEC SCROLL CORRIGÉ
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFrame, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.gmail_client import GmailClient

logger = logging.getLogger(__name__)


class ComposeView(QWidget):
    """Vue pour composer un email - SCROLL ACTIVÉ."""
    
    email_sent = pyqtSignal()
    
    def __init__(self, gmail_client: GmailClient):
        super().__init__()
        
        self.gmail_client = gmail_client
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface avec scroll."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # CRITIQUE : Zone scrollable pour tout le formulaire
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #ffffff;")
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setContentsMargins(40, 30, 40, 30)
        form_layout.setSpacing(20)
        
        # En-tête
        header = QLabel("✉️ Nouveau message")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #000000;")
        form_layout.addWidget(header)
        
        # Destinataire
        to_label = QLabel("À *")
        to_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        to_label.setStyleSheet("color: #000000;")
        form_layout.addWidget(to_label)
        
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("destinataire@example.com")
        self.to_input.setFont(QFont("Arial", 13))
        self.to_input.setFixedHeight(45)
        self.to_input.setStyleSheet("""
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
        form_layout.addWidget(self.to_input)
        
        # CC (optionnel)
        cc_label = QLabel("Cc")
        cc_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        cc_label.setStyleSheet("color: #000000;")
        form_layout.addWidget(cc_label)
        
        self.cc_input = QLineEdit()
        self.cc_input.setPlaceholderText("copie@example.com (optionnel)")
        self.cc_input.setFont(QFont("Arial", 13))
        self.cc_input.setFixedHeight(45)
        self.cc_input.setStyleSheet("""
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
        form_layout.addWidget(self.cc_input)
        
        # Sujet
        subject_label = QLabel("Sujet *")
        subject_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        subject_label.setStyleSheet("color: #000000;")
        form_layout.addWidget(subject_label)
        
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Objet du message")
        self.subject_input.setFont(QFont("Arial", 13))
        self.subject_input.setFixedHeight(45)
        self.subject_input.setStyleSheet("""
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
        form_layout.addWidget(self.subject_input)
        
        # Corps du message
        body_label = QLabel("Message *")
        body_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        body_label.setStyleSheet("color: #000000;")
        form_layout.addWidget(body_label)
        
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Rédigez votre message ici...")
        self.body_input.setFont(QFont("Arial", 13))
        self.body_input.setMinimumHeight(250)
        self.body_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                background-color: #ffffff;
                color: #000000;
            }
            QTextEdit:focus {
                border-color: #5b21b6;
            }
        """)
        form_layout.addWidget(self.body_input)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Bouton Envoyer
        send_btn = QPushButton("📤 Envoyer")
        send_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        send_btn.setFixedHeight(50)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._send_email)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)
        buttons_layout.addWidget(send_btn)
        
        # Bouton Annuler
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        cancel_btn.setFixedHeight(50)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self._clear_form)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        buttons_layout.addWidget(cancel_btn)
        
        buttons_layout.addStretch()
        form_layout.addLayout(buttons_layout)
        
        # Ajouter au scroll
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def _send_email(self):
        """Envoie l'email."""
        to = self.to_input.text().strip()
        cc = self.cc_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()
        
        # Validation
        if not to:
            QMessageBox.warning(self, "⚠️ Champ requis", "Veuillez entrer un destinataire.")
            return
        
        if not subject:
            QMessageBox.warning(self, "⚠️ Champ requis", "Veuillez entrer un sujet.")
            return
        
        if not body:
            QMessageBox.warning(self, "⚠️ Champ requis", "Veuillez rédiger un message.")
            return
        
        # Confirmation
        reply = QMessageBox.question(
            self,
            "Confirmer l'envoi",
            f"Envoyer cet email à {to} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Envoyer via Gmail
                self.gmail_client.send_email(
                    to=to,
                    subject=subject,
                    body=body,
                    cc=cc if cc else None
                )
                
                QMessageBox.information(self, "✅ Envoyé", "Votre email a été envoyé avec succès !")
                logger.info(f"✅ Email envoyé à {to}")
                
                # Nettoyer le formulaire
                self._clear_form()
                
                # Signal
                self.email_sent.emit()
                
            except Exception as e:
                logger.error(f"❌ Erreur envoi: {e}")
                QMessageBox.critical(self, "❌ Erreur", f"Impossible d'envoyer l'email:\n{str(e)}")
    
    def _clear_form(self):
        """Vide le formulaire."""
        self.to_input.clear()
        self.cc_input.clear()
        self.subject_input.clear()
        self.body_input.clear()
        
        logger.info("📝 Formulaire réinitialisé")
    
    def set_reply_to(self, email):
        """Prérempli pour une réponse."""
        self.to_input.setText(email.sender)
        self.subject_input.setText(f"Re: {email.subject}")
        
        quote = f"\n\n---\nLe {email.received_date.strftime('%d/%m/%Y à %H:%M')}, {email.sender} a écrit :\n> {email.snippet or ''}"
        self.body_input.setText(quote)
        
        logger.info(f"📧 Réponse à {email.sender}")
    
    def set_forward(self, email):
        """Prérempli pour un transfert."""
        self.subject_input.setText(f"Fwd: {email.subject}")
        
        forward_text = f"---------- Message transféré ----------\nDe: {email.sender}\nSujet: {email.subject}\n\n{email.body or email.snippet or ''}"
        self.body_input.setText(forward_text)
        
        logger.info(f"➡️ Transfert de {email.subject}")