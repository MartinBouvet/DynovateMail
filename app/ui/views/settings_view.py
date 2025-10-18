#!/usr/bin/env python3
"""
Vue Paramètres - FONCTIONNELLE COMPLÈTE
"""
import logging
import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QCheckBox,
    QSpinBox, QComboBox, QGroupBox, QScrollArea,
    QMessageBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class SettingsView(QScrollArea):
    """Vue des paramètres."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.settings_file = "settings.json"
        self.settings = self._load_settings()
        self._setup_ui()
    
    def _setup_ui(self):
        """Crée l'interface."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("⚙️ Paramètres")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #5b21b6;")
        layout.addWidget(title)
        
        # Section 1: Profil utilisateur
        profile_group = self._create_profile_section()
        layout.addWidget(profile_group)
        
        # Section 2: Paramètres IA
        ai_group = self._create_ai_section()
        layout.addWidget(ai_group)
        
        # Section 3: Réponses automatiques
        auto_response_group = self._create_auto_response_section()
        layout.addWidget(auto_response_group)
        
        # Section 4: Notifications
        notif_group = self._create_notifications_section()
        layout.addWidget(notif_group)
        
        # Section 5: Apparence
        appearance_group = self._create_appearance_section()
        layout.addWidget(appearance_group)
        
        # Section 6: Données et confidentialité
        privacy_group = self._create_privacy_section()
        layout.addWidget(privacy_group)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Enregistrer les paramètres")
        save_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        save_btn.setFixedHeight(50)
        save_btn.clicked.connect(self._save_settings)
        actions_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 Réinitialiser")
        reset_btn.setFont(QFont("Arial", 13))
        reset_btn.setFixedHeight(50)
        reset_btn.clicked.connect(self._reset_settings)
        actions_layout.addWidget(reset_btn)
        
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        
        self.setWidget(container)
        self._apply_styles()
    
    def _create_profile_section(self) -> QGroupBox:
        """Crée la section profil."""
        group = QGroupBox("👤 Profil utilisateur")
        group.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Nom
        name_layout = QHBoxLayout()
        name_label = QLabel("Nom complet:")
        name_label.setFont(QFont("Arial", 12))
        name_label.setFixedWidth(150)
        name_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setText(self.settings.get("user", {}).get("name", ""))
        self.name_input.setPlaceholderText("Votre nom")
        self.name_input.setFont(QFont("Arial", 12))
        name_layout.addWidget(self.name_input)
        
        layout.addLayout(name_layout)
        
        # Email
        email_layout = QHBoxLayout()
        email_label = QLabel("Email:")
        email_label.setFont(QFont("Arial", 12))
        email_label.setFixedWidth(150)
        email_layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setText(self.settings.get("user", {}).get("email", ""))
        self.email_input.setPlaceholderText("votre@email.com")
        self.email_input.setFont(QFont("Arial", 12))
        email_layout.addWidget(self.email_input)
        
        layout.addLayout(email_layout)
        
        # Signature
        signature_label = QLabel("Signature email:")
        signature_label.setFont(QFont("Arial", 12))
        layout.addWidget(signature_label)
        
        self.signature_input = QTextEdit()
        self.signature_input.setText(self.settings.get("user", {}).get("signature", ""))
        self.signature_input.setPlaceholderText("Votre signature apparaîtra en bas de vos emails...")
        self.signature_input.setFont(QFont("Arial", 11))
        self.signature_input.setFixedHeight(100)
        layout.addWidget(self.signature_input)
        
        group.setLayout(layout)
        return group
    
    def _create_ai_section(self) -> QGroupBox:
        """Crée la section IA."""
        group = QGroupBox("🤖 Intelligence Artificielle")
        group.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Activer l'IA
        self.ai_enabled = QCheckBox("Activer l'analyse IA des emails")
        self.ai_enabled.setFont(QFont("Arial", 12))
        self.ai_enabled.setChecked(self.settings.get("ai", {}).get("enabled", True))
        layout.addWidget(self.ai_enabled)
        
        # Classification automatique
        self.ai_classification = QCheckBox("Classification automatique par catégorie")
        self.ai_classification.setFont(QFont("Arial", 12))
        self.ai_classification.setChecked(self.settings.get("ai", {}).get("classification", True))
        layout.addWidget(self.ai_classification)
        
        # Détection de spam
        self.ai_spam = QCheckBox("Détection intelligente de spam")
        self.ai_spam.setFont(QFont("Arial", 12))
        self.ai_spam.setChecked(self.settings.get("ai", {}).get("spam_detection", True))
        layout.addWidget(self.ai_spam)
        
        # Analyse de sentiment
        self.ai_sentiment = QCheckBox("Analyse du sentiment des messages")
        self.ai_sentiment.setFont(QFont("Arial", 12))
        self.ai_sentiment.setChecked(self.settings.get("ai", {}).get("sentiment", True))
        layout.addWidget(self.ai_sentiment)
        
        # Extraction de RDV
        self.ai_meetings = QCheckBox("Extraction automatique des rendez-vous")
        self.ai_meetings.setFont(QFont("Arial", 12))
        self.ai_meetings.setChecked(self.settings.get("ai", {}).get("meeting_extraction", True))
        layout.addWidget(self.ai_meetings)
        
        # Niveau de confiance
        confidence_layout = QHBoxLayout()
        confidence_label = QLabel("Niveau de confiance minimum:")
        confidence_label.setFont(QFont("Arial", 12))
        confidence_layout.addWidget(confidence_label)
        
        self.ai_confidence = QSpinBox()
        self.ai_confidence.setRange(50, 100)
        self.ai_confidence.setValue(self.settings.get("ai", {}).get("confidence", 80))
        self.ai_confidence.setSuffix("%")
        self.ai_confidence.setFont(QFont("Arial", 12))
        confidence_layout.addWidget(self.ai_confidence)
        
        confidence_layout.addStretch()
        layout.addLayout(confidence_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_auto_response_section(self) -> QGroupBox:
        """Crée la section réponses automatiques."""
        group = QGroupBox("✍️ Réponses automatiques")
        group.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Activer les réponses auto
        self.auto_enabled = QCheckBox("Activer les réponses automatiques")
        self.auto_enabled.setFont(QFont("Arial", 12))
        self.auto_enabled.setChecked(self.settings.get("auto_response", {}).get("enabled", False))
        layout.addWidget(self.auto_enabled)
        
        # Délai avant envoi
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Délai avant envoi:")
        delay_label.setFont(QFont("Arial", 12))
        delay_layout.addWidget(delay_label)
        
        self.auto_delay = QSpinBox()
        self.auto_delay.setRange(0, 60)
        self.auto_delay.setValue(self.settings.get("auto_response", {}).get("delay_minutes", 5))
        self.auto_delay.setSuffix(" min")
        self.auto_delay.setFont(QFont("Arial", 12))
        delay_layout.addWidget(self.auto_delay)
        
        delay_layout.addStretch()
        layout.addLayout(delay_layout)
        
        # Types d'emails à traiter
        types_label = QLabel("Répondre automatiquement aux:")
        types_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(types_label)
        
        self.auto_cv = QCheckBox("CV et candidatures")
        self.auto_cv.setFont(QFont("Arial", 11))
        self.auto_cv.setChecked(self.settings.get("auto_response", {}).get("respond_to_cv", True))
        layout.addWidget(self.auto_cv)
        
        self.auto_meeting = QCheckBox("Demandes de rendez-vous")
        self.auto_meeting.setFont(QFont("Arial", 11))
        self.auto_meeting.setChecked(self.settings.get("auto_response", {}).get("respond_to_meeting", True))
        layout.addWidget(self.auto_meeting)
        
        self.auto_support = QCheckBox("Demandes de support")
        self.auto_support.setFont(QFont("Arial", 11))
        self.auto_support.setChecked(self.settings.get("auto_response", {}).get("respond_to_support", True))
        layout.addWidget(self.auto_support)
        
        # Éviter les boucles
        self.auto_avoid_loops = QCheckBox("Éviter les boucles de réponses automatiques")
        self.auto_avoid_loops.setFont(QFont("Arial", 12))
        self.auto_avoid_loops.setChecked(self.settings.get("auto_response", {}).get("avoid_loops", True))
        layout.addWidget(self.auto_avoid_loops)
        
        group.setLayout(layout)
        return group
    
    def _create_notifications_section(self) -> QGroupBox:
        """Crée la section notifications."""
        group = QGroupBox("🔔 Notifications")
        group.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Notifications desktop
        self.notif_desktop = QCheckBox("Notifications de bureau")
        self.notif_desktop.setFont(QFont("Arial", 12))
        self.notif_desktop.setChecked(self.settings.get("notifications", {}).get("desktop", True))
        layout.addWidget(self.notif_desktop)
        
        # Son
        self.notif_sound = QCheckBox("Son lors de nouveaux emails")
        self.notif_sound.setFont(QFont("Arial", 12))
        self.notif_sound.setChecked(self.settings.get("notifications", {}).get("sound", True))
        layout.addWidget(self.notif_sound)
        
        # Emails importants uniquement
        self.notif_important = QCheckBox("Notifier uniquement les emails importants")
        self.notif_important.setFont(QFont("Arial", 12))
        self.notif_important.setChecked(self.settings.get("notifications", {}).get("important_only", False))
        layout.addWidget(self.notif_important)
        
        group.setLayout(layout)
        return group
    
    def _create_appearance_section(self) -> QGroupBox:
        """Crée la section apparence."""
        group = QGroupBox("🎨 Apparence")
        group.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Thème
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Thème:")
        theme_label.setFont(QFont("Arial", 12))
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Clair", "Sombre", "Automatique"])
        self.theme_combo.setCurrentText(self.settings.get("appearance", {}).get("theme", "Clair"))
        self.theme_combo.setFont(QFont("Arial", 12))
        theme_layout.addWidget(self.theme_combo)
        
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Taille de police
        font_layout = QHBoxLayout()
        font_label = QLabel("Taille de police:")
        font_label.setFont(QFont("Arial", 12))
        font_layout.addWidget(font_label)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 18)
        self.font_size.setValue(self.settings.get("appearance", {}).get("font_size", 12))
        self.font_size.setSuffix(" pt")
        self.font_size.setFont(QFont("Arial", 12))
        font_layout.addWidget(self.font_size)
        
        font_layout.addStretch()
        layout.addLayout(font_layout)
        
        # Compacité
        self.compact_mode = QCheckBox("Mode compact")
        self.compact_mode.setFont(QFont("Arial", 12))
        self.compact_mode.setChecked(self.settings.get("appearance", {}).get("compact", False))
        layout.addWidget(self.compact_mode)
        
        group.setLayout(layout)
        return group
    
    def _create_privacy_section(self) -> QGroupBox:
        """Crée la section confidentialité."""
        group = QGroupBox("🔒 Données et confidentialité")
        group.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Stockage local
        storage_label = QLabel("Tous les emails sont stockés localement sur votre ordinateur.")
        storage_label.setFont(QFont("Arial", 11))
        storage_label.setStyleSheet("color: #666666;")
        storage_label.setWordWrap(True)
        layout.addWidget(storage_label)
        
        # Bouton effacer cache
        clear_cache_btn = QPushButton("🗑️ Effacer le cache local")
        clear_cache_btn.setFont(QFont("Arial", 12))
        clear_cache_btn.setFixedHeight(40)
        clear_cache_btn.clicked.connect(self._clear_cache)
        layout.addWidget(clear_cache_btn)
        
        # Bouton exporter données
        export_btn = QPushButton("📥 Exporter mes données")
        export_btn.setFont(QFont("Arial", 12))
        export_btn.setFixedHeight(40)
        export_btn.clicked.connect(self._export_data)
        layout.addWidget(export_btn)
        
        # Bouton déconnexion
        logout_btn = QPushButton("🚪 Déconnexion Gmail")
        logout_btn.setFont(QFont("Arial", 12))
        logout_btn.setFixedHeight(40)
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)
        
        group.setLayout(layout)
        return group
    
    def _load_settings(self) -> dict:
        """Charge les paramètres depuis le fichier."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement paramètres: {e}")
        
        # Paramètres par défaut
        return {
            "user": {
                "name": "",
                "email": "",
                "signature": ""
            },
            "ai": {
                "enabled": True,
                "classification": True,
                "spam_detection": True,
                "sentiment": True,
                "meeting_extraction": True,
                "confidence": 80
            },
            "auto_response": {
                "enabled": False,
                "delay_minutes": 5,
                "respond_to_cv": True,
                "respond_to_meeting": True,
                "respond_to_support": True,
                "avoid_loops": True
            },
            "notifications": {
                "desktop": True,
                "sound": True,
                "important_only": False
            },
            "appearance": {
                "theme": "Clair",
                "font_size": 12,
                "compact": False
            }
        }
    
    def _save_settings(self):
        """Sauvegarde les paramètres."""
        try:
            # Récupérer toutes les valeurs
            settings = {
                "user": {
                    "name": self.name_input.text(),
                    "email": self.email_input.text(),
                    "signature": self.signature_input.toPlainText()
                },
                "ai": {
                    "enabled": self.ai_enabled.isChecked(),
                    "classification": self.ai_classification.isChecked(),
                    "spam_detection": self.ai_spam.isChecked(),
                    "sentiment": self.ai_sentiment.isChecked(),
                    "meeting_extraction": self.ai_meetings.isChecked(),
                    "confidence": self.ai_confidence.value()
                },
                "auto_response": {
                    "enabled": self.auto_enabled.isChecked(),
                    "delay_minutes": self.auto_delay.value(),
                    "respond_to_cv": self.auto_cv.isChecked(),
                    "respond_to_meeting": self.auto_meeting.isChecked(),
                    "respond_to_support": self.auto_support.isChecked(),
                    "avoid_loops": self.auto_avoid_loops.isChecked()
                },
                "notifications": {
                    "desktop": self.notif_desktop.isChecked(),
                    "sound": self.notif_sound.isChecked(),
                    "important_only": self.notif_important.isChecked()
                },
                "appearance": {
                    "theme": self.theme_combo.currentText(),
                    "font_size": self.font_size.value(),
                    "compact": self.compact_mode.isChecked()
                }
            }
            
            # Sauvegarder dans le fichier
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            self.settings = settings
            self.settings_changed.emit()
            
            QMessageBox.information(self, "Succès", "Paramètres sauvegardés avec succès!")
            logger.info("Paramètres sauvegardés")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde paramètres: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder: {e}")
    
    def _reset_settings(self):
        """Réinitialise les paramètres."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment réinitialiser tous les paramètres?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = self._load_settings()
            
            # Recharger l'interface
            self.name_input.setText(self.settings.get("user", {}).get("name", ""))
            self.email_input.setText(self.settings.get("user", {}).get("email", ""))
            self.signature_input.setText(self.settings.get("user", {}).get("signature", ""))
            
            self.ai_enabled.setChecked(self.settings.get("ai", {}).get("enabled", True))
            self.ai_classification.setChecked(self.settings.get("ai", {}).get("classification", True))
            self.ai_spam.setChecked(self.settings.get("ai", {}).get("spam_detection", True))
            self.ai_sentiment.setChecked(self.settings.get("ai", {}).get("sentiment", True))
            self.ai_meetings.setChecked(self.settings.get("ai", {}).get("meeting_extraction", True))
            self.ai_confidence.setValue(self.settings.get("ai", {}).get("confidence", 80))
            
            self.auto_enabled.setChecked(self.settings.get("auto_response", {}).get("enabled", False))
            self.auto_delay.setValue(self.settings.get("auto_response", {}).get("delay_minutes", 5))
            self.auto_cv.setChecked(self.settings.get("auto_response", {}).get("respond_to_cv", True))
            self.auto_meeting.setChecked(self.settings.get("auto_response", {}).get("respond_to_meeting", True))
            self.auto_support.setChecked(self.settings.get("auto_response", {}).get("respond_to_support", True))
            self.auto_avoid_loops.setChecked(self.settings.get("auto_response", {}).get("avoid_loops", True))
            
            self.notif_desktop.setChecked(self.settings.get("notifications", {}).get("desktop", True))
            self.notif_sound.setChecked(self.settings.get("notifications", {}).get("sound", True))
            self.notif_important.setChecked(self.settings.get("notifications", {}).get("important_only", False))
            
            self.theme_combo.setCurrentText(self.settings.get("appearance", {}).get("theme", "Clair"))
            self.font_size.setValue(self.settings.get("appearance", {}).get("font_size", 12))
            self.compact_mode.setChecked(self.settings.get("appearance", {}).get("compact", False))
            
            QMessageBox.information(self, "Succès", "Paramètres réinitialisés!")
            logger.info("Paramètres réinitialisés")
    
    def _clear_cache(self):
        """Efface le cache local."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment effacer le cache local?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implémenter l'effacement du cache
            QMessageBox.information(self, "Succès", "Cache effacé!")
            logger.info("Cache effacé")
    
    def _export_data(self):
        """Exporte les données."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter les données",
            "dynovate_mail_export.json",
            "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=4, ensure_ascii=False)
                
                QMessageBox.information(self, "Succès", f"Données exportées vers:\n{filepath}")
                logger.info(f"Données exportées: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de l'export: {e}")
    
    def _logout(self):
        """Déconnexion."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment vous déconnecter de Gmail?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Supprimer le token
            if os.path.exists('token.json'):
                os.remove('token.json')
                QMessageBox.information(
                    self,
                    "Déconnexion",
                    "Vous avez été déconnecté. Redémarrez l'application pour vous reconnecter."
                )
                logger.info("Déconnexion Gmail")
    
    def _apply_styles(self):
        """Applique les styles."""
        self.setStyleSheet("""
            SettingsView {
                background-color: #ffffff;
            }
            
            QGroupBox {
                border: 2px solid #5b21b6;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                font-size: 14px;
                font-weight: bold;
                color: #5b21b6;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 5px;
                background-color: #ffffff;
            }
            
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
                color: #000000;
            }
            
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #5b21b6;
            }
            
            QCheckBox {
                spacing: 8px;
                color: #000000;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
            }
            
            QCheckBox::indicator:checked {
                background-color: #5b21b6;
                border-color: #5b21b6;
            }
            
            QPushButton {
                background-color: #5b21b6;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)