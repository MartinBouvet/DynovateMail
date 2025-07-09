"""
Vue pour composer un nouvel email.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..gmail_client import GmailClient

logger = logging.getLogger(__name__)

class ComposeView(QDialog):
    """Fenêtre de dialogue pour composer un nouvel email."""
    
    email_sent = pyqtSignal()
    
    def __init__(self, gmail_client: GmailClient, parent=None, 
                 to="", subject="", body="", is_reply=False, is_forward=False):
        super().__init__(parent)
        self.gmail_client = gmail_client
        self.is_reply = is_reply
        self.is_forward = is_forward
        
        self.setWindowTitle("Nouveau message" if not is_reply and not is_forward else 
                           "Répondre" if is_reply else "Transférer")
        self.setGeometry(200, 200, 800, 600)
        
        self._setup_ui()
        
        # Remplir les champs si des valeurs sont fournies
        if to:
            self.to_input.setText(to)
        if subject:
            self.subject_input.setText(subject)
        if body:
            self.body_input.setText(body)
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        
        # Champ "À"
        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel("À:"))
        self.to_input = QLineEdit()
        to_layout.addWidget(self.to_input)
        layout.addLayout(to_layout)
        
        # Champ "Sujet"
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Sujet:"))
        self.subject_input = QLineEdit()
        subject_layout.addWidget(self.subject_input)
        layout.addLayout(subject_layout)
        
        # Corps du message
        layout.addWidget(QLabel("Message:"))
        self.body_input = QTextEdit()
        layout.addWidget(self.body_input)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Envoyer")
        self.send_button.clicked.connect(self._on_send)
        buttons_layout.addWidget(self.send_button)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def _on_send(self):
        """Callback pour le bouton d'envoi."""
        to = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()
        
        # Validation des champs
        if not to:
            QMessageBox.warning(self, "Champ manquant", "Veuillez spécifier un destinataire.")
            return
        
        if not subject:
            # Demander confirmation si le sujet est vide
            reply = QMessageBox.question(
                self,
                "Sujet vide",
                "Êtes-vous sûr de vouloir envoyer un email sans sujet ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Envoi de l'email
        try:
            success = self.gmail_client.send_email(to, subject, body)
            
            if success:
                self.email_sent.emit()
                self.accept()  # Fermer la fenêtre
            else:
                QMessageBox.critical(
                    self,
                    "Erreur d'envoi",
                    "Une erreur s'est produite lors de l'envoi de l'email."
                )
        
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            QMessageBox.critical(
                self,
                "Erreur d'envoi",
                f"Une erreur s'est produite lors de l'envoi de l'email: {e}"
            )