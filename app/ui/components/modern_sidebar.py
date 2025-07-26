#!/usr/bin/env python3
"""
Sidebar moderne CORRIGÉE avec alignement parfait des statistiques.
"""
import logging
from typing import Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)

class StatCard(QFrame):
    """Carte de statistique PARFAITEMENT ALIGNÉE."""
    
    def __init__(self, title: str, value: str = "0", icon: str = "📊"):
        super().__init__()
        self.setObjectName("stat-card")
        self.setFixedHeight(75)  # Hauteur légèrement augmentée
        
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 12, 15, 12)
        main_layout.setSpacing(12)
        
        # Colonne gauche: Icône
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 16))
        icon_label.setFixedSize(24, 24)  # Taille fixe pour alignement
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(icon_label)
        
        # Colonne droite: Titre et valeur
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)
        
        # Titre
        title_label = QLabel(title)
        title_label.setObjectName("stat-title")
        title_label.setFont(QFont("Inter", 11, QFont.Weight.Medium))
        text_layout.addWidget(title_label)
        
        # Valeur
        self.value_label = QLabel(value)
        self.value_label.setObjectName("stat-value")
        self.value_label.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        text_layout.addWidget(self.value_label)
        
        main_layout.addWidget(text_container)
        
        # Spacer pour pousser à droite
        main_layout.addStretch()
        
        self._apply_style()
    
    def update_value(self, value: str):
        """Met à jour la valeur."""
        self.value_label.setText(value)
    
    def _apply_style(self):
        """Style CORRIGÉ pour un alignement parfait."""
        self.setStyleSheet("""
            QFrame#stat-card {
                background-color: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                margin: 3px 0;
            }
            
            QFrame#stat-card:hover {
                background-color: #f0f0f0;
                border-color: #bdbdbd;
            }
            
            QLabel#stat-title {
                color: #757575;
                font-weight: 500;
                margin: 0;
                padding: 0;
            }
            
            QLabel#stat-value {
                color: #1a1a1a;
                font-weight: 700;
                margin: 0;
                padding: 0;
            }
        """)

class NavButton(QPushButton):
    """Bouton de navigation PARFAITEMENT ALIGNÉ."""
    
    def __init__(self, text: str, icon: str, view_name: str):
        super().__init__()
        self.view_name = view_name
        self.is_active = False
        
        # Layout avec icône et texte
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(15)
        
        # Icône avec taille fixe
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Arial", 16))
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # Texte
        self.text_label = QLabel(text)
        self.text_label.setFont(QFont("Inter", 14, QFont.Weight.Medium))
        layout.addWidget(self.text_label)
        
        # Spacer pour aligner à gauche
        layout.addStretch()
        
        self.setFixedHeight(48)
        self._apply_style()
    
    def set_active(self, active: bool):
        """Active/désactive le bouton."""
        self.is_active = active
        self._apply_style()
    
    def _apply_style(self):
        """Style CORRIGÉ selon l'état."""
        if self.is_active:
            style = """
                QPushButton {
                    background-color: #1976d2;
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                }
                QLabel {
                    color: #ffffff;
                }
            """
        else:
            style = """
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #f5f5f5;
                }
                QLabel {
                    color: #424242;
                }
                QLabel:hover {
                    color: #1976d2;
                }
            """
        
        self.setStyleSheet(style)

class ModernSidebar(QWidget):
    """Sidebar moderne CORRIGÉE avec navigation et statistiques parfaitement alignées."""
    
    view_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(280)  # Largeur légèrement augmentée
        
        self.nav_buttons = {}
        self.stat_cards = {}
        self.current_view = "inbox"
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Configure l'interface PARFAITEMENT ALIGNÉE."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(0)
        
        # Logo et titre
        header = self._create_header()
        layout.addWidget(header)
        
        layout.addSpacing(35)
        
        # Navigation principale
        nav_section = self._create_navigation()
        layout.addWidget(nav_section)
        
        layout.addSpacing(35)
        
        # Statistiques
        stats_section = self._create_stats()
        layout.addWidget(stats_section)
        
        # Spacer pour pousser vers le bas
        layout.addStretch()
        
        # Informations utilisateur
        user_section = self._create_user_info()
        layout.addWidget(user_section)
    
    def _create_header(self) -> QWidget:
        """Crée le header PARFAITEMENT CENTRÉ."""
        header = QFrame()
        layout = QVBoxLayout(header)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo
        logo = QLabel("⚡")
        logo.setFont(QFont("Arial", 32))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("color: #1976d2;")
        layout.addWidget(logo)
        
        # Titre
        title = QLabel("Dynovate")
        title.setObjectName("app-title")
        title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Sous-titre
        subtitle = QLabel("Mail Assistant IA")
        subtitle.setObjectName("app-subtitle")
        subtitle.setFont(QFont("Inter", 12, QFont.Weight.Normal))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        return header
    
    def _create_navigation(self) -> QWidget:
        """Crée la section de navigation PARFAITEMENT ALIGNÉE."""
        nav_frame = QFrame()
        nav_frame.setObjectName("nav-section")
        layout = QVBoxLayout(nav_frame)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre de section
        section_title = QLabel("Navigation")
        section_title.setObjectName("section-title")
        section_title.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        section_title.setContentsMargins(5, 0, 0, 0)
        layout.addWidget(section_title)
        
        layout.addSpacing(10)
        
        # Boutons de navigation
        nav_items = [
            ("Smart Inbox", "📧", "inbox"),
            ("Calendrier", "📅", "calendar"),
            ("Paramètres", "⚙️", "settings")
        ]
        
        for text, icon, view_name in nav_items:
            btn = NavButton(text, icon, view_name)
            btn.clicked.connect(lambda checked, vn=view_name: self._on_nav_clicked(vn))
            
            if view_name == self.current_view:
                btn.set_active(True)
            
            self.nav_buttons[view_name] = btn
            layout.addWidget(btn)
        
        return nav_frame
    
    def _create_stats(self) -> QWidget:
        """Crée la section des statistiques PARFAITEMENT ALIGNÉES."""
        stats_frame = QFrame()
        stats_frame.setObjectName("stats-section")
        layout = QVBoxLayout(stats_frame)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre de section
        section_title = QLabel("Statistiques")
        section_title.setObjectName("section-title")
        section_title.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        section_title.setContentsMargins(5, 0, 0, 0)
        layout.addWidget(section_title)
        
        layout.addSpacing(10)
        
        # Cartes de statistiques avec alignement parfait
        stats_data = [
            ("Emails non lus", "0", "📬", "unread_emails"),
            ("IA Précision", "0%", "🤖", "ai_accuracy"),
            ("Réponses auto", "0", "⚡", "auto_responses")
        ]
        
        for title, value, icon, key in stats_data:
            card = StatCard(title, value, icon)
            self.stat_cards[key] = card
            layout.addWidget(card)
        
        return stats_frame
    
    def _create_user_info(self) -> QWidget:
        """Crée la section d'informations utilisateur PARFAITEMENT CENTRÉE."""
        user_frame = QFrame()
        user_frame.setObjectName("user-section")
        layout = QVBoxLayout(user_frame)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 15, 10, 15)
        
        # Avatar
        avatar = QLabel("👤")
        avatar.setFont(QFont("Arial", 24))
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(avatar)
        
        # Nom utilisateur
        username = QLabel("Utilisateur")
        username.setObjectName("username")
        username.setFont(QFont("Inter", 13, QFont.Weight.Medium))
        username.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(username)
        
        # Status
        status = QLabel("🟢 En ligne")
        status.setObjectName("user-status")
        status.setFont(QFont("Inter", 11))
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status)
        
        return user_frame
    
    def _apply_style(self):
        """Style CORRIGÉ pour la sidebar avec alignement parfait."""
        self.setStyleSheet("""
            QWidget#sidebar {
                background-color: #ffffff;
                border-right: 2px solid #e0e0e0;
            }
            
            QLabel#app-title {
                color: #1a1a1a;
                font-weight: 700;
                margin: 0;
                padding: 0;
            }
            
            QLabel#app-subtitle {
                color: #757575;
                font-weight: 400;
                margin: 0;
                padding: 0;
            }
            
            QLabel#section-title {
                color: #1a1a1a;
                margin: 0;
                padding: 5px 0;
                font-weight: 600;
            }
            
            QFrame#user-section {
                background-color: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 15px;
                margin-top: 10px;
            }
            
            QLabel#username {
                color: #1a1a1a;
                font-weight: 500;
                margin: 0;
                padding: 0;
            }
            
            QLabel#user-status {
                color: #757575;
                font-weight: 400;
                margin: 0;
                padding: 0;
            }
        """)
    
    def _on_nav_clicked(self, view_name: str):
        """Gère le clic sur un bouton de navigation."""
        # Désactiver tous les boutons
        for btn in self.nav_buttons.values():
            btn.set_active(False)
        
        # Activer le bouton cliqué
        self.nav_buttons[view_name].set_active(True)
        
        self.current_view = view_name
        self.view_changed.emit(view_name)
    
    def update_stats(self, stats: Dict):
        """Met à jour les statistiques avec formatage propre."""
        stat_mapping = {
            'unread_emails': str(stats.get('unread_emails', 0)),
            'ai_accuracy': f"{stats.get('ai_accuracy', 0) * 100:.0f}%",
            'auto_responses': str(stats.get('auto_responses', 0))
        }
        
        for key, value in stat_mapping.items():
            if key in self.stat_cards:
                self.stat_cards[key].update_value(value)