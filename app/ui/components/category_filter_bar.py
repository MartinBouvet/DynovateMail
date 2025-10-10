#!/usr/bin/env python3
"""
Barre de filtres par catégories - CORRIGÉE
"""
import logging
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class CategoryFilterBar(QWidget):
    """Barre de filtres par catégories."""
    
    category_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_category = "Tous"
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée la barre de filtres."""
        self.setFixedHeight(60)
        self.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e0e0e0;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Catégories
        categories = [
            ("Tous", "📊 Tous"),
            ("cv", "📄 CV"),
            ("meeting", "📅 RDV"),
            ("invoice", "💰 Factures"),
            ("newsletter", "📰 News"),
            ("support", "🛠️ Support"),
            ("important", "⭐ Important"),
            ("spam", "⚠️ Spam")
        ]
        
        self.category_buttons = {}
        
        for cat_id, cat_label in categories:
            btn = QPushButton(cat_label)
            btn.setObjectName(f"category-{cat_id}")
            btn.setCheckable(True)
            btn.setFont(QFont("SF Pro Display", 12))
            btn.setFixedHeight(38)
            btn.clicked.connect(lambda checked, c=cat_id: self._on_category_clicked(c))
            layout.addWidget(btn)
            self.category_buttons[cat_id] = btn
        
        layout.addStretch()
        
        self._update_active_category("Tous")
        self._apply_styles()
    
    def _on_category_clicked(self, category: str):
        """Catégorie cliquée."""
        if category != self.current_category:
            self.current_category = category
            self._update_active_category(category)
            self.category_changed.emit(category)
    
    def set_category(self, category: str):
        """Définit la catégorie active."""
        self.current_category = category
        self._update_active_category(category)
    
    def _update_active_category(self, category: str):
        """Met à jour l'apparence de la catégorie active."""
        for cat_id, btn in self.category_buttons.items():
            if cat_id == category:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
    
    def _apply_styles(self):
        """Applique les styles Dynovate."""
        self.setStyleSheet("""
            CategoryFilterBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
            }
            
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 18px;
                padding: 6px 18px;
                font-size: 12px;
                color: #000000;
            }
            
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #5b21b6;
            }
            
            QPushButton:checked {
                background-color: #5b21b6;
                color: #ffffff;
                border-color: #5b21b6;
                font-weight: bold;
            }
        """)