#!/usr/bin/env python3
"""
Sidebar des dossiers - VERSION CORRIGÉE
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class EmailFoldersSidebar(QWidget):
    """Sidebar avec dossiers."""
    
    folder_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_folder = "INBOX"
        self.folder_counts = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Interface."""
        self.setFixedWidth(250)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-right: 1px solid #e5e7eb;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 25, 15, 15)
        layout.setSpacing(8)
        
        # Logo + Titre app
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        logo = QLabel("📧")
        logo.setFont(QFont("Arial", 36))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo)
        
        title = QLabel("Dynovate Mail")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #000000;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Assistant IA")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #6b7280;")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        # Séparateur
        layout.addSpacing(20)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #e5e7eb;")
        layout.addWidget(line)
        layout.addSpacing(15)
        
        # Section titre
        section_title = QLabel("DOSSIERS")
        section_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #9ca3af; padding-left: 10px;")
        layout.addWidget(section_title)
        layout.addSpacing(5)
        
        # Dossiers
        folders = [
            ("📥 Réception", "INBOX", True),
            ("⭐ Favoris", "STARRED", False),
            ("📤 Envoyés", "SENT", False),
            ("📝 Brouillons", "DRAFTS", False),
            ("🗑️ Corbeille", "TRASH", False),
            ("🚫 Spam", "SPAM", False),
        ]
        
        self.folder_buttons = {}
        
        for label, folder_id, show_count in folders:
            btn = self._create_folder_button(label, folder_id, show_count)
            layout.addWidget(btn)
            self.folder_buttons[folder_id] = btn
        
        layout.addStretch()
        
        # Séparateur
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFixedHeight(1)
        line2.setStyleSheet("background-color: #e5e7eb;")
        layout.addWidget(line2)
        layout.addSpacing(10)
        
        # Boutons du bas
        settings_btn = self._create_bottom_button("⚙️ Paramètres", "SETTINGS")
        layout.addWidget(settings_btn)
        
        support_btn = self._create_bottom_button("❓ Support", "SUPPORT")
        layout.addWidget(support_btn)
        
        layout.addSpacing(10)
        
        # Activer INBOX
        self._update_selection("INBOX")
    
    def _create_folder_button(self, label: str, folder_id: str, show_count: bool = False) -> QPushButton:
        """Bouton dossier."""
        btn = QPushButton(label)
        btn.setFont(QFont("Arial", 13))
        btn.setFixedHeight(42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_folder_clicked(folder_id))
        
        # Style par défaut
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #374151;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        
        return btn
    
    def _create_bottom_button(self, label: str, action_id: str) -> QPushButton:
        """Bouton du bas."""
        btn = QPushButton(label)
        btn.setFont(QFont("Arial", 12))
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_folder_clicked(action_id))
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6b7280;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                color: #000000;
            }
        """)
        
        return btn
    
    def _on_folder_clicked(self, folder_id: str):
        """Clic sur dossier."""
        if folder_id != self.current_folder:
            self.current_folder = folder_id
            self._update_selection(folder_id)
            self.folder_changed.emit(folder_id)
    
    def _update_selection(self, folder_id: str):
        """Met à jour la sélection."""
        for fid, btn in self.folder_buttons.items():
            if fid == folder_id:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ede9fe;
                        color: #5b21b6;
                        border: none;
                        border-radius: 8px;
                        text-align: left;
                        padding-left: 15px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #374151;
                        border: none;
                        border-radius: 8px;
                        text-align: left;
                        padding-left: 15px;
                    }
                    QPushButton:hover {
                        background-color: #f3f4f6;
                    }
                """)
    
    def update_folder_count(self, folder_id: str, count: int):
        """Met à jour le compteur."""
        self.folder_counts[folder_id] = count
        
        if folder_id in self.folder_buttons:
            btn = self.folder_buttons[folder_id]
            base_text = btn.text().split(" (")[0]
            if count > 0:
                btn.setText(f"{base_text} ({count})")
            else:
                btn.setText(base_text)