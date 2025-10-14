#!/usr/bin/env python3
"""
Sidebar des dossiers - OPTIMISÉE
"""
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

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
        self.setStyleSheet("""
            QWidget {
                background-color: #fafafa;
                border-right: 3px solid #e5e7eb;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 30, 18, 20)
        layout.setSpacing(10)
        
        # Titre
        title = QLabel("📁 Dossiers")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #000000; padding: 5px 12px;")
        layout.addWidget(title)
        
        # Ligne
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(2)
        line.setStyleSheet("background-color: #e5e7eb; margin: 12px 0;")
        layout.addWidget(line)
        
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
        
        # Ligne inférieure
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFixedHeight(2)
        line2.setStyleSheet("background-color: #e5e7eb; margin: 12px 0;")
        layout.addWidget(line2)
        
        # Boutons du bas
        settings_btn = self._create_bottom_button("⚙️ Paramètres", "SETTINGS")
        layout.addWidget(settings_btn)
        
        support_btn = self._create_bottom_button("❓ Support", "SUPPORT")
        layout.addWidget(support_btn)
        
        # Activer INBOX
        self._update_selection("INBOX")
    
    def _create_folder_button(self, label: str, folder_id: str, show_count: bool = False) -> QPushButton:
        """Bouton dossier."""
        btn = QPushButton(label)
        btn.setObjectName(folder_id)
        btn.setFont(QFont("Arial", 13, QFont.Bold))
        btn.setFixedHeight(48)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._on_folder_click(folder_id))
        
        if show_count and folder_id in self.folder_counts:
            count = self.folder_counts[folder_id]
            if count > 0:
                btn.setText(f"{label} ({count})")
        
        return btn
    
    def _create_bottom_button(self, label: str, action_id: str) -> QPushButton:
        """Bouton du bas."""
        btn = QPushButton(label)
        btn.setFont(QFont("Arial", 13, QFont.Bold))
        btn.setFixedHeight(48)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_folder_click(action_id))
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 22px;
                border: none;
                border-radius: 12px;
                background-color: transparent;
                color: #6b7280;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
                color: #000000;
            }
        """)
        return btn
    
    def _on_folder_click(self, folder_id: str):
        """Clic dossier."""
        if folder_id not in ["SETTINGS", "SUPPORT"]:
            if folder_id != self.current_folder:
                self.current_folder = folder_id
                self._update_selection(folder_id)
        
        self.folder_changed.emit(folder_id)
        logger.info(f"Dossier: {folder_id}")
    
    def _update_selection(self, folder_id: str):
        """Met à jour sélection."""
        for fid, btn in self.folder_buttons.items():
            btn.setChecked(fid == folder_id)
        
        self._apply_styles()
    
    def update_folder_count(self, folder_id: str, count: int):
        """Met à jour compteur."""
        self.folder_counts[folder_id] = count
        
        if folder_id in self.folder_buttons:
            btn = self.folder_buttons[folder_id]
            original = btn.text().split(" (")[0]
            if count > 0:
                btn.setText(f"{original} ({count})")
            else:
                btn.setText(original)
    
    def _apply_styles(self):
        """Styles boutons."""
        for btn in self.folder_buttons.values():
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 22px;
                    border: none;
                    border-radius: 12px;
                    background-color: transparent;
                    color: #6b7280;
                }
                QPushButton:hover {
                    background-color: #e5e7eb;
                    color: #000000;
                }
                QPushButton:checked {
                    background-color: #5b21b6;
                    color: white;
                }
            """)