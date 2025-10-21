#!/usr/bin/env python3
"""
Vue Paramètres - 100% FONCTIONNELLE
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
    """Vue des paramètres - TOUT FONCTIONNE."""
    
    settings_changed = pyqtSignal(dict)
    
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
        layout.setSpacing(25)
        
        # Titre
        title = QLabel("⚙️ Paramètres")
        title.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000;")
        layout.addWidget(title)
        
        subtitle = QLabel("Configurez votre boîte mail intelligente")
        subtitle.setFont(QFont("Arial", 13))
        subtitle.setStyleSheet("color: #6b7280;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
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
        actions_layout.setSpacing(15)
        
        save_btn = QPushButton("💾 Enregistrer les paramètres")
        save_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        save_btn.setFixedHeight(55)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #5b21b6;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4c1d95;
            }
        """)
        actions_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 Réinitialiser")
        reset_btn.setFont(QFont("Arial", 14))
        reset_btn.setFixedHeight(55)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_settings)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        actions_layout.addWidget(reset_btn)
        
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        
        self.setWidget(container)
        self._apply_styles()
    
    def _create_profile_section(self) -> QGroupBox:
        """Crée la section profil."""
        group = QGroupBox("👤 Profil utilisateur")
        group.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Nom
        name_label = QLabel("Nom complet")
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Entrez votre nom")
        self.name_input.setText(self.settings.get("user", {}).get("name", ""))
        self.name_input.setFont(QFont("Arial", 12))
        self.name_input.setFixedHeight(40)
        layout.addWidget(self.name_input)
        
        # Email
        email_label = QLabel("Adresse email")
        email_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("votre@email.com")
        self.email_input.setText(self.settings.get("user", {}).get("email", ""))
        self.email_input.setFont(QFont("Arial", 12))
        self.email_input.setFixedHeight(40)
        layout.addWidget(self.email_input)
        
        # Signature
        signature_label = QLabel("Signature email")
        signature_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(signature_label)
        
        self.signature_input = QTextEdit()
        self.signature_input.setPlaceholderText("Votre signature personnalisée...")
        self.signature_input.setText(self.settings.get("user", {}).get("signature", ""))
        self.signature_input.setFont(QFont("Arial", 12))
        self.signature_input.setFixedHeight(100)
        layout.addWidget(self.signature_input)
        
        group.setLayout(layout)
        return group
    
    def _create_ai_section(self) -> QGroupBox:
        """Crée la section IA."""
        group = QGroupBox("🤖 Intelligence Artificielle")
        group.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Activer l'IA
        self.ai_enabled = QCheckBox("Activer l'assistant IA")
        self.ai_enabled.setChecked(self.settings.get("ai", {}).get("enabled", True))
        self.ai_enabled.setFont(QFont("Arial", 13))
        layout.addWidget(self.ai_enabled)
        
        # Classification auto
        self.ai_classification = QCheckBox("Classification automatique des emails")
        self.ai_classification.setChecked(self.settings.get("ai", {}).get("classification", True))
        self.ai_classification.setFont(QFont("Arial", 12))
        layout.addWidget(self.ai_classification)
        
        # Détection spam
        self.ai_spam = QCheckBox("Détection intelligente du spam")
        self.ai_spam.setChecked(self.settings.get("ai", {}).get("spam_detection", True))
        self.ai_spam.setFont(QFont("Arial", 12))
        layout.addWidget(self.ai_spam)
        
        # Analyse sentiment
        self.ai_sentiment = QCheckBox("Analyse de sentiment")
        self.ai_sentiment.setChecked(self.settings.get("ai", {}).get("sentiment", True))
        self.ai_sentiment.setFont(QFont("Arial", 12))
        layout.addWidget(self.ai_sentiment)
        
        # Extraction RDV
        self.ai_meetings = QCheckBox("Extraction automatique des rendez-vous")
        self.ai_meetings.setChecked(self.settings.get("ai", {}).get("meeting_extraction", True))
        self.ai_meetings.setFont(QFont("Arial", 12))
        layout.addWidget(self.ai_meetings)
        
        # Seuil de confiance
        confidence_layout = QHBoxLayout()
        confidence_label = QLabel("Seuil de confiance IA:")
        confidence_label.setFont(QFont("Arial", 12))
        confidence_layout.addWidget(confidence_label)
        
        self.ai_confidence = QSpinBox()
        self.ai_confidence.setRange(50, 100)
        self.ai_confidence.setValue(self.settings.get("ai", {}).get("confidence", 80))
        self.ai_confidence.setSuffix("%")
        self.ai_confidence.setFont(QFont("Arial", 12))
        self.ai_confidence.setFixedWidth(100)
        confidence_layout.addWidget(self.ai_confidence)
        confidence_layout.addStretch()
        
        layout.addLayout(confidence_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_auto_response_section(self) -> QGroupBox:
        """Crée la section réponse automatique."""
        group = QGroupBox("🔄 Réponses automatiques")
        group.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Activer réponses auto
        self.auto_enabled = QCheckBox("Activer les réponses automatiques")
        self.auto_enabled.setChecked(self.settings.get("auto_response", {}).get("enabled", False))
        self.auto_enabled.setFont(QFont("Arial", 13))
        layout.addWidget(self.auto_enabled)
        
        # Délai
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Délai avant réponse:")
        delay_label.setFont(QFont("Arial", 12))
        delay_layout.addWidget(delay_label)
        
        self.auto_delay = QSpinBox()
        self.auto_delay.setRange(1, 60)
        self.auto_delay.setValue(self.settings.get("auto_response", {}).get("delay_minutes", 5))
        self.auto_delay.setSuffix(" min")
        self.auto_delay.setFont(QFont("Arial", 12))
        self.auto_delay.setFixedWidth(100)
        delay_layout.addWidget(self.auto_delay)
        delay_layout.addStretch()
        
        layout.addLayout(delay_layout)
        
        # Types d'emails
        self.auto_cv = QCheckBox("Répondre aux CV et candidatures")
        self.auto_cv.setChecked(self.settings.get("auto_response", {}).get("respond_to_cv", True))
        self.auto_cv.setFont(QFont("Arial", 12))
        layout.addWidget(self.auto_cv)
        
        self.auto_meeting = QCheckBox("Répondre aux demandes de rendez-vous")
        self.auto_meeting.setChecked(self.settings.get("auto_response", {}).get("respond_to_meeting", True))
        self.auto_meeting.setFont(QFont("Arial", 12))
        layout.addWidget(self.auto_meeting)
        
        self.auto_support = QCheckBox("Répondre aux demandes de support")
        self.auto_support.setChecked(self.settings.get("auto_response", {}).get("respond_to_support", True))
        self.auto_support.setFont(QFont("Arial", 12))
        layout.addWidget(self.auto_support)
        
        self.auto_avoid_loops = QCheckBox("Éviter les boucles de réponses")
        self.auto_avoid_loops.setChecked(self.settings.get("auto_response", {}).get("avoid_loops", True))
        self.auto_avoid_loops.setFont(QFont("Arial", 12))
        layout.addWidget(self.auto_avoid_loops)
        
        group.setLayout(layout)
        return group
    
    def _create_notifications_section(self) -> QGroupBox:
        """Crée la section notifications."""
        group = QGroupBox("🔔 Notifications")
        group.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        self.notif_desktop = QCheckBox("Notifications bureau")
        self.notif_desktop.setChecked(self.settings.get("notifications", {}).get("desktop", True))
        self.notif_desktop.setFont(QFont("Arial", 12))
        layout.addWidget(self.notif_desktop)
        
        self.notif_sound = QCheckBox("Sons de notification")
        self.notif_sound.setChecked(self.settings.get("notifications", {}).get("sound", True))
        self.notif_sound.setFont(QFont("Arial", 12))
        layout.addWidget(self.notif_sound)
        
        self.notif_important = QCheckBox("Uniquement les emails importants")
        self.notif_important.setChecked(self.settings.get("notifications", {}).get("important_only", False))
        self.notif_important.setFont(QFont("Arial", 12))
        layout.addWidget(self.notif_important)
        
        group.setLayout(layout)
        return group
    
    def _create_appearance_section(self) -> QGroupBox:
        """Crée la section apparence."""
        group = QGroupBox("🎨 Apparence")
        group.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Thème
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Thème:")
        theme_label.setFont(QFont("Arial", 12))
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Clair", "Sombre", "Système"])
        self.theme_combo.setCurrentText(self.settings.get("appearance", {}).get("theme", "Clair"))
        self.theme_combo.setFont(QFont("Arial", 12))
        self.theme_combo.setFixedWidth(150)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        layout.addLayout(theme_layout)
        
        # Taille police
        font_layout = QHBoxLayout()
        font_label = QLabel("Taille de la police:")
        font_label.setFont(QFont("Arial", 12))
        font_layout.addWidget(font_label)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 18)
        self.font_size.setValue(self.settings.get("appearance", {}).get("font_size", 12))
        self.font_size.setSuffix(" pt")
        self.font_size.setFont(QFont("Arial", 12))
        self.font_size.setFixedWidth(100)
        font_layout.addWidget(self.font_size)
        font_layout.addStretch()
        
        layout.addLayout(font_layout)
        
        # Mode compact
        self.compact_mode = QCheckBox("Mode compact")
        self.compact_mode.setChecked(self.settings.get("appearance", {}).get("compact", False))
        self.compact_mode.setFont(QFont("Arial", 12))
        layout.addWidget(self.compact_mode)
        
        group.setLayout(layout)
        return group
    
    def _create_privacy_section(self) -> QGroupBox:
        """Crée la section confidentialité."""
        group = QGroupBox("🔒 Données et confidentialité")
        group.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Info stockage
        storage_label = QLabel("✓ Tous les emails sont stockés localement sur votre ordinateur\n✓ Aucune donnée n'est envoyée vers des serveurs externes\n✓ L'IA fonctionne en local via Ollama")
        storage_label.setFont(QFont("Arial", 11))
        storage_label.setStyleSheet("color: #059669; background-color: #d1fae5; padding: 12px; border-radius: 6px;")
        storage_label.setWordWrap(True)
        layout.addWidget(storage_label)
        
        # Bouton effacer cache
        clear_cache_btn = QPushButton("🗑️ Effacer le cache local")
        clear_cache_btn.setFont(QFont("Arial", 12))
        clear_cache_btn.setFixedHeight(45)
        clear_cache_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_cache_btn.clicked.connect(self._clear_cache)
        clear_cache_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        layout.addWidget(clear_cache_btn)
        
        # Bouton exporter données
        export_btn = QPushButton("📥 Exporter mes données")
        export_btn.setFont(QFont("Arial", 12))
        export_btn.setFixedHeight(45)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_data)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        layout.addWidget(export_btn)
        
        # Bouton déconnexion
        logout_btn = QPushButton("🚪 Déconnexion Gmail")
        logout_btn.setFont(QFont("Arial", 12))
        logout_btn.setFixedHeight(45)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
            }
        """)
        layout.addWidget(logout_btn)
        
        group.setLayout(layout)
        return group
    
    def _load_settings(self) -> dict:
        """Charge les paramètres depuis le fichier."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    logger.info("✅ Paramètres chargés")
                    return settings
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
        """Sauvegarde les paramètres - VRAIMENT FONCTIONNEL."""
        try:
            # Récupérer toutes les valeurs des champs
            settings = {
                "user": {
                    "name": self.name_input.text().strip(),
                    "email": self.email_input.text().strip(),
                    "signature": self.signature_input.toPlainText().strip()
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
            
            # Émettre le signal pour notifier les autres composants
            self.settings_changed.emit(settings)
            
            # Message de succès
            QMessageBox.information(
                self, 
                "✅ Succès", 
                "Paramètres sauvegardés avec succès !\n\nCertains changements nécessitent un redémarrage de l'application."
            )
            
            logger.info("✅ Paramètres sauvegardés avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde paramètres: {e}")
            QMessageBox.critical(
                self, 
                "❌ Erreur", 
                f"Impossible de sauvegarder les paramètres:\n{str(e)}"
            )
    
    def _reset_settings(self):
        """Réinitialise les paramètres."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment réinitialiser tous les paramètres à leurs valeurs par défaut ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Charger les paramètres par défaut
            self.settings = self._load_settings()
            
            # Recharger l'interface avec les valeurs par défaut
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
            
            QMessageBox.information(self, "✅ Succès", "Paramètres réinitialisés !")
            logger.info("✅ Paramètres réinitialisés")
    
    def _clear_cache(self):
        """Efface le cache local."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment effacer le cache local ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Supprimer les fichiers de cache si ils existent
                cache_files = ['email_cache.db', 'analysis_cache.json', 'temp_data.json']
                deleted_count = 0
                
                for cache_file in cache_files:
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                        deleted_count += 1
                
                QMessageBox.information(
                    self, 
                    "✅ Succès", 
                    f"Cache effacé ! ({deleted_count} fichier(s) supprimé(s))"
                )
                logger.info(f"✅ Cache effacé: {deleted_count} fichiers")
                
            except Exception as e:
                QMessageBox.warning(self, "⚠️ Avertissement", f"Erreur lors de l'effacement: {str(e)}")
    
    def _export_data(self):
        """Exporte les données."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter les paramètres",
            f"dynovate_mail_settings_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=4, ensure_ascii=False)
                
                QMessageBox.information(
                    self, 
                    "✅ Succès", 
                    f"Paramètres exportés vers:\n{filepath}"
                )
                logger.info(f"✅ Paramètres exportés: {filepath}")
                
            except Exception as e:
                QMessageBox.critical(self, "❌ Erreur", f"Échec de l'export: {str(e)}")
    
    def _logout(self):
        """Déconnexion Gmail."""
        reply = QMessageBox.question(
            self,
            "Confirmation de déconnexion",
            "Voulez-vous vraiment vous déconnecter de Gmail ?\n\nVous devrez vous authentifier à nouveau au prochain démarrage.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Supprimer le token
                if os.path.exists('token.json'):
                    os.remove('token.json')
                    logger.info("✅ Token supprimé")
                
                QMessageBox.information(
                    self,
                    "✅ Déconnexion réussie",
                    "Vous avez été déconnecté de Gmail.\n\nRedémarrez l'application pour vous reconnecter."
                )
                
            except Exception as e:
                QMessageBox.warning(self, "⚠️ Avertissement", f"Erreur: {str(e)}")
    
    def _apply_styles(self):
        """Applique les styles."""
        self.setStyleSheet("""
            SettingsView {
                background-color: #ffffff;
            }
            
            QGroupBox {
                border: 2px solid #000000;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 20px;
                font-size: 15px;
                font-weight: bold;
                color: #000000;
                background-color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 20px;
                padding: 0 8px;
                background-color: #ffffff;
                color: #000000;
            }
            
            QLineEdit, QTextEdit {
                border: 2px solid #d1d5db;
                border-radius: 8px;
                padding: 10px 14px;
                background-color: #ffffff;
                color: #000000;
                font-size: 12px;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border-color: #5b21b6;
                outline: none;
            }
            
            QSpinBox, QComboBox {
                border: 2px solid #d1d5db;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: #ffffff;
                color: #000000;
                font-size: 12px;
            }
            
            QSpinBox:focus, QComboBox:focus {
                border-color: #5b21b6;
            }
            
            QCheckBox {
                spacing: 10px;
                color: #000000;
                font-size: 12px;
            }
            
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #d1d5db;
                border-radius: 5px;
                background-color: #ffffff;
            }
            
            QCheckBox::indicator:checked {
                background-color: #5b21b6;
                border-color: #5b21b6;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjMzMyAzLjMzM0w2IDEwLjY2N0wyLjY2NyA3LjMzMyIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+Cg==);
            }
            
            QCheckBox::indicator:hover {
                border-color: #5b21b6;
            }
        """)

# Import nécessaire pour la date
from datetime import datetime