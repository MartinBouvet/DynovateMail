"""
Vue pour composer un nouvel email - Version mise à jour.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from gmail_client import GmailClient

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
        self.setMinimumSize(600, 400)
        
        self._setup_ui()
        self._apply_style()
        
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
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title_label = QLabel("✏️ Composer un email")
        title_label.setObjectName("compose-title")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Champs d'email
        fields_frame = QFrame()
        fields_frame.setObjectName("fields-frame")
        fields_layout = QVBoxLayout(fields_frame)
        fields_layout.setSpacing(10)
        
        # Champ "À"
        to_layout = QHBoxLayout()
        to_label = QLabel("À:")
        to_label.setObjectName("field-label")
        to_label.setMinimumWidth(80)
        to_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.to_input = QLineEdit()
        self.to_input.setObjectName("field-input")
        self.to_input.setPlaceholderText("destinataire@email.com")
        
        to_layout.addWidget(to_label)
        to_layout.addWidget(self.to_input)
        fields_layout.addLayout(to_layout)
        
        # Champ "Sujet"
        subject_layout = QHBoxLayout()
        subject_label = QLabel("Sujet:")
        subject_label.setObjectName("field-label")
        subject_label.setMinimumWidth(80)
        subject_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.subject_input = QLineEdit()
        self.subject_input.setObjectName("field-input")
        self.subject_input.setPlaceholderText("Sujet de l'email")
        
        subject_layout.addWidget(subject_label)
        subject_layout.addWidget(self.subject_input)
        fields_layout.addLayout(subject_layout)
        
        layout.addWidget(fields_frame)
        
        # Corps du message
        body_label = QLabel("Message:")
        body_label.setObjectName("field-label")
        body_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(body_label)
        
        self.body_input = QTextEdit()
        self.body_input.setObjectName("body-input")
        self.body_input.setPlaceholderText("Tapez votre message ici...")
        self.body_input.setMinimumHeight(300)
        layout.addWidget(self.body_input)
        
        # Boutons d'action
        buttons_frame = QFrame()
        buttons_frame.setObjectName("buttons-frame")
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(10)
        
        # Bouton annuler
        self.cancel_button = QPushButton("❌ Annuler")
        self.cancel_button.setObjectName("cancel-button")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        buttons_layout.addStretch()
        
        # Bouton envoyer
        self.send_button = QPushButton("📤 Envoyer")
        self.send_button.setObjectName("send-button")
        self.send_button.clicked.connect(self._on_send)
        self.send_button.setDefault(True)  # Bouton par défaut
        buttons_layout.addWidget(self.send_button)
        
        layout.addWidget(buttons_frame)
    
    def _apply_style(self):
        """Applique le style Dynovate noir et blanc."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            
            QLabel#compose-title {
                color: #000000;
                margin-bottom: 20px;
            }
            
            QFrame#fields-frame {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            
            QLabel#field-label {
                color: #000000;
                margin-right: 10px;
            }
            
            QLineEdit#field-input {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            
            QLineEdit#field-input:focus {
                border-color: #000000;
                outline: none;
            }
            
            QTextEdit#body-input {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-family: Arial, sans-serif;
                line-height: 1.4;
            }
            
            QTextEdit#body-input:focus {
                border-color: #000000;
            }
            
            QFrame#buttons-frame {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            
            QPushButton#send-button {
                background-color: #000000;
                color: #ffffff;
                border: 1px solid #000000;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            
            QPushButton#send-button:hover {
                background-color: #333333;
            }
            
            QPushButton#send-button:pressed {
                background-color: #555555;
            }
            
            QPushButton#cancel-button {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 100px;
            }
            
            QPushButton#cancel-button:hover {
                background-color: #f0f0f0;
            }
            
            QPushButton#cancel-button:pressed {
                background-color: #e0e0e0;
            }
        """)
    
    def _on_send(self):
        """Callback pour le bouton d'envoi."""
        to = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()
        
        # Validation des champs
        if not to:
            QMessageBox.warning(self, "Champ manquant", "Veuillez spécifier un destinataire.")
            self.to_input.setFocus()
            return
        
        # Validation basique de l'email
        if '@' not in to or '.' not in to:
            QMessageBox.warning(self, "Email invalide", "Veuillez entrer une adresse email valide.")
            self.to_input.setFocus()
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
                self.subject_input.setFocus()
                return
        
        if not body:
            # Demander confirmation si le corps est vide
            reply = QMessageBox.question(
                self,
                "Message vide",
                "Êtes-vous sûr de vouloir envoyer un email sans contenu ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                self.body_input.setFocus()
                return
        
        # Désactiver le bouton d'envoi pendant l'envoi
        self.send_button.setEnabled(False)
        self.send_button.setText("📤 Envoi en cours...")
        
        # Envoi de l'email
        try:
            success = self.gmail_client.send_email(to, subject, body)
            
            if success:
                self.email_sent.emit()
                QMessageBox.information(self, "Email envoyé", "Votre email a été envoyé avec succès!")
                self.accept()  # Fermer la fenêtre
            else:
                QMessageBox.critical(
                    self,
                    "Erreur d'envoi",
                    "Une erreur s'est produite lors de l'envoi de l'email.\nVeuillez réessayer."
                )
                # Réactiver le bouton
                self.send_button.setEnabled(True)
                self.send_button.setText("📤 Envoyer")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            QMessageBox.critical(
                self,
                "Erreur d'envoi",
                f"Une erreur inattendue s'est produite:\n{str(e)}"
            )
            # Réactiver le bouton
            self.send_button.setEnabled(True)
            self.send_button.setText("📤 Envoyer")
    
    def keyPressEvent(self, event):
        """Gère les raccourcis clavier."""
        # Ctrl+Enter pour envoyer
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._on_send()
        # Échap pour annuler
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)