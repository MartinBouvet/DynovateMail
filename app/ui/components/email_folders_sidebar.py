#!/usr/bin/env python3
"""
Sidebar des dossiers d'emails - ICÔNES CORRIGÉES
"""
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class EmailFoldersSidebar(QWidget):
    """Sidebar avec les dossiers d'emails."""
    
    folder_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_folder = "INBOX"
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(5)
        
        # Titre
        title = QLabel("📧 Dossiers")
        title.setFont(QFont("SF Pro Display", 16, QFont.Bold))
        title.setStyleSheet("color: #5b21b6; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(separator)
        
        # Dossiers principaux
        folders = [
            ("📥 Réception", "INBOX"),
            ("⭐ Favoris", "STARRED"),
            ("📤 Envoyés", "SENT"),
            ("📝 Brouillons", "DRAFTS"),
            ("🗑 Corbeille", "TRASH"),
            ("🚫 Spam", "SPAM"),
        ]
        
        self.folder_buttons = {}
        
        for label, folder_id in folders:
            btn = self._create_folder_button(label, folder_id)
            layout.addWidget(btn)
            self.folder_buttons[folder_id] = btn
        
        # Espace
        layout.addStretch()
        
        # Séparateur avant boutons du bas
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(separator2)
        
        # Boutons du bas avec icônes Unicode simples
        settings_btn = QPushButton("⚙ Paramètres")
        settings_btn.setFont(QFont("SF Pro Display", 12))
        settings_btn.setFixedHeight(40)
        settings_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 15px;
                border: none;
                border-radius: 8px;
                background-color: transparent;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        settings_btn.clicked.connect(lambda: self._on_folder_click("SETTINGS"))
        layout.addWidget(settings_btn)
        
        support_btn = QPushButton("❓ Support")
        support_btn.setFont(QFont("SF Pro Display", 12))
        support_btn.setFixedHeight(40)
        support_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 15px;
                border: none;
                border-radius: 8px;
                background-color: transparent;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        support_btn.clicked.connect(lambda: self._on_folder_click("SUPPORT"))
        layout.addWidget(support_btn)
        
        # Sélectionner INBOX par défaut
        self._update_selection("INBOX")
    
    def _create_folder_button(self, label: str, folder_id: str) -> QPushButton:
        """Crée un bouton de dossier."""
        btn = QPushButton(label)
        btn.setFont(QFont("SF Pro Display", 12))
        btn.setFixedHeight(45)
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 15px;
                border: none;
                border-radius: 8px;
                background-color: transparent;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        
        btn.clicked.connect(lambda: self._on_folder_click(folder_id))
        
        return btn
    
    def _on_folder_click(self, folder_id: str):
        """Gère le clic sur un dossier."""
        logger.info(f"Dossier sélectionné: {folder_id}")
        self.current_folder = folder_id
        self._update_selection(folder_id)
        self.folder_changed.emit(folder_id)
    
    def _update_selection(self, folder_id: str):
        """Met à jour la sélection visuelle."""
        for fid, btn in self.folder_buttons.items():
            if fid == folder_id:
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding-left: 15px;
                        border: none;
                        border-radius: 8px;
                        background-color: #5b21b6;
                        color: white;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding-left: 15px;
                        border: none;
                        border-radius: 8px;
                        background-color: transparent;
                        color: #333333;
                    }
                    QPushButton:hover {
                        background-color: #f3f4f6;
                    }
                """)