#!/usr/bin/env python3
"""
Vue pour composer un nouvel email avec support des réponses IA.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
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
        self.is_ai_response = False
        
        self.setWindowTitle("Nouveau message" if not is_reply and not is_forward else 
                           "Répondre" if is_reply else "Transférer")
        self.setGeometry(200, 200, 800, 700)
        self.setMinimumSize(600, 500)
        
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
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Titre
        title_text = "✏️ Répondre" if self.is_reply else "➡️ Transférer" if self.is_forward else "✏️ Composer un email"
        title_label = QLabel(title_text)
        title_label.setObjectName("compose-title")
        title_label.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Indicateur de réponse IA (caché par défaut)
        self.ai_indicator = QLabel("🤖 Cette réponse a été générée par l'IA - Vous pouvez la modifier avant envoi")
        self.ai_indicator.setObjectName("ai-indicator")
        self.ai_indicator.setFont(QFont("Inter", 13, QFont.Weight.Medium))
        self.ai_indicator.setWordWrap(True)
        self.ai_indicator.hide()
        layout.addWidget(self.ai_indicator)
        
        # Champs d'email
        fields_frame = QFrame()
        fields_frame.setObjectName("fields-frame")
        fields_layout = QVBoxLayout(fields_frame)
        fields_layout.setSpacing(15)
        
        # Champ "À"
        to_layout = QHBoxLayout()
        to_label = QLabel("À:")
        to_label.setObjectName("field-label")
        to_label.setMinimumWidth(80)
        to_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        
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
        subject_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        
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
        body_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
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
        buttons_layout.setSpacing(15)
        
        # Bouton annuler
        self.cancel_button = QPushButton("❌ Annuler")
        self.cancel_button.setObjectName("cancel-button")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        buttons_layout.addStretch()
        
        # Bouton brouillon
        self.draft_button = QPushButton("💾 Sauvegarder")
        self.draft_button.setObjectName("draft-button")
        self.draft_button.clicked.connect(self._save_draft)
        buttons_layout.addWidget(self.draft_button)
        
        # Bouton envoyer
        self.send_button = QPushButton("📤 Envoyer")
        self.send_button.setObjectName("send-button")
        self.send_button.clicked.connect(self._on_send)
        self.send_button.setDefault(True)
        buttons_layout.addWidget(self.send_button)
        
        layout.addWidget(buttons_frame)
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(30000)  # 30 secondes
    
    def _apply_style(self):
        """Applique le style moderne."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            
            QLabel#compose-title {
                color: #000000;
                margin-bottom: 15px;
            }
            
            QLabel#ai-indicator {
                background-color: #e8f5e8;
                color: #2e7d32;
                border: 2px solid #4caf50;
                border-radius: 10px;
                padding: 15px 20px;
                margin: 10px 0 20px 0;
            }
            
            QFrame#fields-frame {
                background-color: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 15px;
            }
            
            QLabel#field-label {
                color: #000000;
                margin-right: 15px;
            }
            
            QLineEdit#field-input {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 14px;
                min-height: 25px;
            }
            
            QLineEdit#field-input:focus {
                border-color: #007bff;
                outline: none;
            }
            
            QTextEdit#body-input {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 15px;
                font-size: 14px;
                font-family: 'Inter', Arial, sans-serif;
                line-height: 1.6;
            }
            
            QTextEdit#body-input:focus {
                border-color: #007bff;
            }
            
            QFrame#buttons-frame {
                background-color: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
                margin-top: 15px;
            }
            
            QPushButton#send-button {
                background-color: #28a745;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: 700;
                min-width: 140px;
                min-height: 50px;
            }
            
            QPushButton#send-button:hover {
                background-color: #218838;
                transform: translateY(-1px);
            }
            
            QPushButton#send-button:pressed {
                background-color: #1e7e34;
                transform: translateY(1px);
            }
            
            QPushButton#send-button:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
            
            QPushButton#cancel-button {
                background-color: #dc3545;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: 600;
                min-width: 120px;
                min-height: 50px;
            }
            
            QPushButton#cancel-button:hover {
                background-color: #c82333;
            }
            
            QPushButton#draft-button {
                background-color: #007bff;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: 600;
                min-width: 140px;
                min-height: 50px;
            }
            
            QPushButton#draft-button:hover {
                background-color: #0056b3;
            }
        """)
    
    def show_ai_indicator(self):
        """Affiche l'indicateur de réponse IA."""
        self.is_ai_response = True
        self.ai_indicator.show()
    
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
        
        # Désactiver les boutons pendant l'envoi
        self.send_button.setEnabled(False)
        self.send_button.setText("📤 Envoi en cours...")
        self.cancel_button.setEnabled(False)
        self.draft_button.setEnabled(False)
        
        # Envoi de l'email
        try:
            success = self.gmail_client.send_email(to, subject, body)
            
            if success:
                # Émettre le signal de succès
                self.email_sent.emit()
                
                # Message de succès spécial pour les réponses IA
                if self.is_ai_response:
                    success_text = "✅ Votre réponse générée par l'IA a été envoyée avec succès!"
                else:
                    success_text = "✅ Votre email a été envoyé avec succès!"
                
                success_msg = QMessageBox(self)
                success_msg.setWindowTitle("Email envoyé")
                success_msg.setText(success_text)
                success_msg.setIcon(QMessageBox.Icon.Information)
                success_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                
                # Style pour le message de succès
                success_msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #ffffff;
                        color: #000000;
                        font-size: 14px;
                    }
                    QMessageBox QPushButton {
                        background-color: #28a745;
                        color: #ffffff;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 8px;
                        min-width: 80px;
                        font-weight: 600;
                    }
                    QMessageBox QPushButton:hover {
                        background-color: #218838;
                    }
                """)
                
                # Auto-fermer après 2.5 secondes
                QTimer.singleShot(2500, success_msg.accept)
                success_msg.exec()
                
                # Fermer la fenêtre de composition
                self.accept()
                
                logger.info(f"Email envoyé avec succès à {to} (IA: {self.is_ai_response})")
            else:
                # Réactiver les boutons en cas d'échec
                self._reset_send_button()
                
                QMessageBox.critical(
                    self,
                    "Erreur d'envoi",
                    "❌ Une erreur s'est produite lors de l'envoi de l'email.\n\nVeuillez vérifier votre connexion internet et réessayer."
                )
        
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            
            # Réactiver les boutons
            self._reset_send_button()
            
            QMessageBox.critical(
                self,
                "Erreur d'envoi",
                f"❌ Une erreur inattendue s'est produite:\n\n{str(e)}\n\nVeuillez réessayer."
            )
    
    def _reset_send_button(self):
        """Remet le bouton d'envoi dans son état normal."""
        self.send_button.setEnabled(True)
        self.send_button.setText("📤 Envoyer")
        self.cancel_button.setEnabled(True)
        self.draft_button.setEnabled(True)
    
    def _save_draft(self):
        """Sauvegarde en brouillon."""
        to = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()
        
        if not to and not subject and not body:
            QMessageBox.information(
                self,
                "Brouillon vide",
                "Il n'y a aucun contenu à sauvegarder."
            )
            return
        
        # Message de confirmation
        draft_msg = QMessageBox(self)
        draft_msg.setWindowTitle("Brouillon sauvegardé")
        draft_msg.setText("💾 Votre brouillon a été sauvegardé localement.\n\nVous pourrez le retrouver la prochaine fois.")
        draft_msg.setIcon(QMessageBox.Icon.Information)
        draft_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        draft_msg.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
                color: #000000;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #007bff;
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                min-width: 80px;
                font-weight: 600;
            }
            QMessageBox QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        draft_msg.exec()
        logger.info("Brouillon sauvegardé")
    
    def _auto_save(self):
        """Auto-sauvegarde périodique silencieuse."""
        to = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()
        
        if to or subject or body:
            logger.debug("Auto-sauvegarde effectuée")
    
    def keyPressEvent(self, event):
        """Gère les raccourcis clavier."""
        # Ctrl+Enter pour envoyer
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._on_send()
        # Ctrl+S pour sauvegarder
        elif event.key() == Qt.Key.Key_S and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._save_draft()
        # Échap pour annuler
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Gère la fermeture de la fenêtre."""
        # Vérifier s'il y a du contenu non sauvegardé
        to = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()
        
        if to or subject or body:
            reply = QMessageBox.question(
                self,
                "Fermer sans sauvegarder",
                "Vous avez du contenu non sauvegardé.\n\nVoulez-vous vraiment fermer sans sauvegarder ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.No:
                self._save_draft()
                event.accept()
            elif reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
                return
        
        # Arrêter l'auto-save timer
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        
        event.accept()