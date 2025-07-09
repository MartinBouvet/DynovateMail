"""
Vue pour afficher le contenu d'un email.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from models.email_model import Email

class EmailView(QWidget):
    """Widget pour afficher le contenu d'un email."""
    
    reply_requested = pyqtSignal(Email)
    forward_requested = pyqtSignal(Email)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_email = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        
        # En-têtes de l'email
        self.header_frame = QFrame()
        self.header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(self.header_frame)
        
        # Sujet
        self.subject_label = QLabel()
        self.subject_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.subject_label)
        
        # De
        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("De:"))
        self.from_label = QLabel()
        from_layout.addWidget(self.from_label)
        header_layout.addLayout(from_layout)
        
        # À
        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel("À:"))
        self.to_label = QLabel()
        to_layout.addWidget(self.to_label)
        header_layout.addLayout(to_layout)
        
        # Date
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date:"))
        self.date_label = QLabel()
        date_layout.addWidget(self.date_label)
        header_layout.addLayout(date_layout)
        
        layout.addWidget(self.header_frame)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        self.reply_button = QPushButton("Répondre")
        self.reply_button.clicked.connect(self._on_reply)
        actions_layout.addWidget(self.reply_button)
        
        self.forward_button = QPushButton("Transférer")
        self.forward_button.clicked.connect(self._on_forward)
        actions_layout.addWidget(self.forward_button)
        
        self.ai_reply_button = QPushButton("Réponse IA")
        self.ai_reply_button.clicked.connect(self._on_ai_reply)
        actions_layout.addWidget(self.ai_reply_button)
        
        layout.addLayout(actions_layout)
        
        # Corps de l'email
        self.body_text = QTextEdit()
        self.body_text.setReadOnly(True)
        layout.addWidget(self.body_text)
        
        # État initial
        self._clear_view()
    
    def _clear_view(self):
        """Efface le contenu de la vue."""
        self.subject_label.setText("")
        self.from_label.setText("")
        self.to_label.setText("")
        self.date_label.setText("")
        self.body_text.setText("")
        
        # Désactiver les boutons
        self.reply_button.setEnabled(False)
        self.forward_button.setEnabled(False)
        self.ai_reply_button.setEnabled(False)
    
    def display_email(self, email: Email):
        """
        Affiche un email dans la vue.
        
        Args:
            email: L'email à afficher.
        """
        if not email:
            self._clear_view()
            return
        
        self.current_email = email
        
        # Mettre à jour les en-têtes
        self.subject_label.setText(email.subject)
        self.from_label.setText(email.sender)
        self.to_label.setText(email.recipient)
        self.date_label.setText(email.date)
        
        # Mettre à jour le corps
        self.body_text.setText(email.body)
        
        # Activer les boutons
        self.reply_button.setEnabled(True)
        self.forward_button.setEnabled(True)
        self.ai_reply_button.setEnabled(True)
    
    def _on_reply(self):
        """Callback pour le bouton de réponse."""
        if self.current_email:
            self.reply_requested.emit(self.current_email)
    
    def _on_forward(self):
        """Callback pour le bouton de transfert."""
        if self.current_email:
            self.forward_requested.emit(self.current_email)
    
    def _on_ai_reply(self):
        """Callback pour le bouton de réponse IA."""
        if self.current_email:
            # TODO: Implémenter la génération de réponse par IA
            # Ceci sera implémenté dans une future version
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Fonctionnalité à venir",
                "La réponse automatique par IA sera disponible dans une future version."
            )