"""
Vue des paramètres de l'application.
"""
import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QLineEdit, QTextEdit, QCheckBox, QSpinBox,
    QComboBox, QGroupBox, QFormLayout, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from utils.config import save_config

logger = logging.getLogger(__name__)

class SettingsView(QWidget):
    """Vue des paramètres de l'application."""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Titre
        title_label = QLabel("⚙️ Paramètres")
        title_label.setObjectName("page-title")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Zone de scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget principal
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        
        # Paramètres généraux
        general_group = self._create_general_settings()
        main_layout.addWidget(general_group)
        
        # Paramètres IA
        ai_group = self._create_ai_settings()
        main_layout.addWidget(ai_group)
        
        # Paramètres de réponse automatique
        auto_respond_group = self._create_auto_respond_settings()
        main_layout.addWidget(auto_respond_group)
        
        # Paramètres d'email
        email_group = self._create_email_settings()
        main_layout.addWidget(email_group)
        
        # Paramètres d'interface
        ui_group = self._create_ui_settings()
        main_layout.addWidget(ui_group)
        
        main_layout.addStretch()
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Sauvegarder")
        save_btn.setObjectName("save-button")
        save_btn.clicked.connect(self._save_settings)
        buttons_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 Réinitialiser")
        reset_btn.setObjectName("reset-button")
        reset_btn.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        
        main_layout.addLayout(buttons_layout)
        
        scroll_area.setWidget(main_widget)
        layout.addWidget(scroll_area)
        
        self._apply_style()
    
    def _create_general_settings(self) -> QGroupBox:
        """Crée les paramètres généraux."""
        group = QGroupBox("🏠 Paramètres généraux")
        group.setObjectName("settings-group")
        
        form_layout = QFormLayout(group)
        
        # Nom d'utilisateur
        self.user_name_input = QLineEdit()
        self.user_name_input.setObjectName("settings-input")
        form_layout.addRow("Nom d'utilisateur:", self.user_name_input)
        
        # Signature
        self.signature_input = QTextEdit()
        self.signature_input.setObjectName("settings-text")
        self.signature_input.setMaximumHeight(100)
        form_layout.addRow("Signature email:", self.signature_input)
        
        # Rafraîchissement automatique
        self.auto_refresh_check = QCheckBox("Rafraîchissement automatique")
        self.auto_refresh_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.auto_refresh_check)
        
        # Intervalle de rafraîchissement
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setObjectName("settings-spin")
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setSuffix(" min")
        form_layout.addRow("Intervalle de rafraîchissement:", self.refresh_interval_spin)
        
        return group
    
    def _create_ai_settings(self) -> QGroupBox:
        """Crée les paramètres d'IA."""
        group = QGroupBox("🤖 Intelligence artificielle")
        group.setObjectName("settings-group")
        
        form_layout = QFormLayout(group)
        
        # Classification automatique
        self.ai_classification_check = QCheckBox("Classification automatique des emails")
        self.ai_classification_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.ai_classification_check)
        
        # Détection de spam
        self.spam_detection_check = QCheckBox("Détection de spam")
        self.spam_detection_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.spam_detection_check)
        
        # Analyse de sentiment
        self.sentiment_analysis_check = QCheckBox("Analyse de sentiment")
        self.sentiment_analysis_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.sentiment_analysis_check)
        
        # Extraction de rendez-vous
        self.meeting_extraction_check = QCheckBox("Extraction automatique de rendez-vous")
        self.meeting_extraction_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.meeting_extraction_check)
        
        # Modèle de réponse
        self.response_model_combo = QComboBox()
        self.response_model_combo.setObjectName("settings-combo")
        self.response_model_combo.addItems(["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"])
        form_layout.addRow("Modèle de réponse:", self.response_model_combo)
        
        return group
    
    def _create_auto_respond_settings(self) -> QGroupBox:
        """Crée les paramètres de réponse automatique."""
        group = QGroupBox("📤 Réponse automatique")
        group.setObjectName("settings-group")
        
        form_layout = QFormLayout(group)
        
        # Activer les réponses automatiques
        self.auto_respond_check = QCheckBox("Activer les réponses automatiques")
        self.auto_respond_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.auto_respond_check)
        
        # Délai avant réponse
        self.response_delay_spin = QSpinBox()
        self.response_delay_spin.setObjectName("settings-spin")
        self.response_delay_spin.setRange(0, 60)
        self.response_delay_spin.setSuffix(" min")
        form_layout.addRow("Délai avant réponse:", self.response_delay_spin)
        
        # Types d'emails à traiter
        self.auto_respond_cv_check = QCheckBox("Répondre aux candidatures")
        self.auto_respond_cv_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.auto_respond_cv_check)
        
        self.auto_respond_rdv_check = QCheckBox("Répondre aux demandes de rendez-vous")
        self.auto_respond_rdv_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.auto_respond_rdv_check)
        
        self.auto_respond_support_check = QCheckBox("Répondre aux demandes de support")
        self.auto_respond_support_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.auto_respond_support_check)
        
        # Éviter les réponses en boucle
        self.avoid_loops_check = QCheckBox("Éviter les réponses en boucle")
        self.avoid_loops_check.setObjectName("settings-checkbox")
        self.avoid_loops_check.setChecked(True)
        form_layout.addRow("", self.avoid_loops_check)
        
        return group
    
    def _create_email_settings(self) -> QGroupBox:
        """Crée les paramètres d'email."""
        group = QGroupBox("📧 Paramètres email")
        group.setObjectName("settings-group")
        
        form_layout = QFormLayout(group)
        
        # Nombre d'emails à charger
        self.max_emails_spin = QSpinBox()
        self.max_emails_spin.setObjectName("settings-spin")
        self.max_emails_spin.setRange(10, 1000)
        form_layout.addRow("Nombre d'emails à charger:", self.max_emails_spin)
        
        # Marquer comme lu automatiquement
        self.auto_mark_read_check = QCheckBox("Marquer comme lu automatiquement")
        self.auto_mark_read_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.auto_mark_read_check)
        
        # Délai avant marquage lu
        self.mark_read_delay_spin = QSpinBox()
        self.mark_read_delay_spin.setObjectName("settings-spin")
        self.mark_read_delay_spin.setRange(1, 60)
        self.mark_read_delay_spin.setSuffix(" sec")
        form_layout.addRow("Délai avant marquage lu:", self.mark_read_delay_spin)
        
        # Archivage automatique
        self.auto_archive_check = QCheckBox("Archivage automatique des emails traités")
        self.auto_archive_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.auto_archive_check)
        
        return group
    
    def _create_ui_settings(self) -> QGroupBox:
        """Crée les paramètres d'interface."""
        group = QGroupBox("🎨 Interface utilisateur")
        group.setObjectName("settings-group")
        
        form_layout = QFormLayout(group)
        
        # Thème
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("settings-combo")
        self.theme_combo.addItems(["Clair", "Sombre", "Automatique"])
        form_layout.addRow("Thème:", self.theme_combo)
        
        # Taille de police
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setObjectName("settings-spin")
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setSuffix(" pt")
        form_layout.addRow("Taille de police:", self.font_size_spin)
        
        # Affichage du volet de prévisualisation
        self.preview_pane_check = QCheckBox("Afficher le volet de prévisualisation")
        self.preview_pane_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.preview_pane_check)
        
        # Notifications
        self.notifications_check = QCheckBox("Notifications")
        self.notifications_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.notifications_check)
        
        # Minimiser dans la barre système
        self.minimize_to_tray_check = QCheckBox("Minimiser dans la barre système")
        self.minimize_to_tray_check.setObjectName("settings-checkbox")
        form_layout.addRow("", self.minimize_to_tray_check)
        
        return group
    
    def _apply_style(self):
        """Applique le style aux paramètres."""
        self.setStyleSheet("""
            QLabel#page-title {
                color: #000000;
                margin-bottom: 10px;
            }
            
            QGroupBox#settings-group {
                font-size: 14px;
                font-weight: bold;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox#settings-group::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: #ffffff;
            }
            
            QLineEdit#settings-input {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            
            QLineEdit#settings-input:focus {
                border-color: #000000;
            }
            
            QTextEdit#settings-text {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            
            QTextEdit#settings-text:focus {
                border-color: #000000;
            }
            
            QCheckBox#settings-checkbox {
                color: #000000;
                font-size: 12px;
                spacing: 5px;
            }
            
            QCheckBox#settings-checkbox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                background-color: #ffffff;
            }
            
            QCheckBox#settings-checkbox::indicator:checked {
                background-color: #000000;
                border-color: #000000;
            }
            
            QSpinBox#settings-spin {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            
            QSpinBox#settings-spin:focus {
                border-color: #000000;
            }
            
            QComboBox#settings-combo {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            
            QComboBox#settings-combo:focus {
                border-color: #000000;
            }
            
            QComboBox#settings-combo::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox#settings-combo::down-arrow {
                image: none;
                border: 2px solid #666666;
                border-top: none;
                border-right: none;
                width: 6px;
                height: 6px;
                transform: rotate(-45deg);
            }
            
            QPushButton#save-button {
                background-color: #000000;
                color: #ffffff;
                border: 1px solid #000000;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            
            QPushButton#save-button:hover {
                background-color: #333333;
            }
            
            QPushButton#reset-button {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
            }
            
            QPushButton#reset-button:hover {
                background-color: #f0f0f0;
            }
            
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
        """)
    
    def _load_settings(self):
        """Charge les paramètres depuis la configuration."""
        try:
            # Paramètres généraux
            self.user_name_input.setText(self.config.get('user', {}).get('name', ''))
            self.signature_input.setPlainText(self.config.get('user', {}).get('signature', ''))
            self.auto_refresh_check.setChecked(self.config.get('app', {}).get('auto_refresh', True))
            self.refresh_interval_spin.setValue(self.config.get('email', {}).get('refresh_interval_minutes', 5))
            
            # Paramètres IA
            ai_config = self.config.get('ai', {})
            self.ai_classification_check.setChecked(ai_config.get('enable_classification', True))
            self.spam_detection_check.setChecked(ai_config.get('enable_spam_detection', True))
            self.sentiment_analysis_check.setChecked(ai_config.get('enable_sentiment_analysis', True))
            self.meeting_extraction_check.setChecked(ai_config.get('enable_meeting_extraction', True))
            self.response_model_combo.setCurrentText(ai_config.get('response_model', 'gpt-3.5-turbo'))
            
            # Paramètres de réponse automatique
            auto_respond_config = self.config.get('auto_respond', {})
            self.auto_respond_check.setChecked(auto_respond_config.get('enabled', False))
            self.response_delay_spin.setValue(auto_respond_config.get('delay_minutes', 5))
            self.auto_respond_cv_check.setChecked(auto_respond_config.get('respond_to_cv', True))
            self.auto_respond_rdv_check.setChecked(auto_respond_config.get('respond_to_rdv', True))
            self.auto_respond_support_check.setChecked(auto_respond_config.get('respond_to_support', True))
            self.avoid_loops_check.setChecked(auto_respond_config.get('avoid_loops', True))
            
            # Paramètres email
            email_config = self.config.get('email', {})
            self.max_emails_spin.setValue(email_config.get('max_emails_to_load', 50))
            self.auto_mark_read_check.setChecked(email_config.get('auto_mark_read', False))
            self.mark_read_delay_spin.setValue(email_config.get('mark_read_delay_seconds', 3))
            self.auto_archive_check.setChecked(email_config.get('auto_archive', False))
            
            # Paramètres UI
            ui_config = self.config.get('ui', {})
            theme_map = {'light': 'Clair', 'dark': 'Sombre', 'auto': 'Automatique'}
            self.theme_combo.setCurrentText(theme_map.get(ui_config.get('theme', 'light'), 'Clair'))
            self.font_size_spin.setValue(ui_config.get('font_size', 12))
            self.preview_pane_check.setChecked(ui_config.get('show_preview_pane', True))
            self.notifications_check.setChecked(ui_config.get('notifications', True))
            self.minimize_to_tray_check.setChecked(ui_config.get('minimize_to_tray', True))
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des paramètres: {e}")
    
    def _save_settings(self):
        """Sauvegarde les paramètres."""
        try:
            # Mettre à jour la configuration
            self.config.setdefault('user', {})['name'] = self.user_name_input.text()
            self.config.setdefault('user', {})['signature'] = self.signature_input.toPlainText()
            self.config.setdefault('app', {})['auto_refresh'] = self.auto_refresh_check.isChecked()
            self.config.setdefault('email', {})['refresh_interval_minutes'] = self.refresh_interval_spin.value()
            
            # IA
            ai_config = self.config.setdefault('ai', {})
            ai_config['enable_classification'] = self.ai_classification_check.isChecked()
            ai_config['enable_spam_detection'] = self.spam_detection_check.isChecked()
            ai_config['enable_sentiment_analysis'] = self.sentiment_analysis_check.isChecked()
            ai_config['enable_meeting_extraction'] = self.meeting_extraction_check.isChecked()
            ai_config['response_model'] = self.response_model_combo.currentText()
            
            # Réponse automatique
            auto_respond_config = self.config.setdefault('auto_respond', {})
            auto_respond_config['enabled'] = self.auto_respond_check.isChecked()
            auto_respond_config['delay_minutes'] = self.response_delay_spin.value()
            auto_respond_config['respond_to_cv'] = self.auto_respond_cv_check.isChecked()
            auto_respond_config['respond_to_rdv'] = self.auto_respond_rdv_check.isChecked()
            auto_respond_config['respond_to_support'] = self.auto_respond_support_check.isChecked()
            auto_respond_config['avoid_loops'] = self.avoid_loops_check.isChecked()
            
            # Email
            email_config = self.config.setdefault('email', {})
            email_config['max_emails_to_load'] = self.max_emails_spin.value()
            email_config['auto_mark_read'] = self.auto_mark_read_check.isChecked()
            email_config['mark_read_delay_seconds'] = self.mark_read_delay_spin.value()
            email_config['auto_archive'] = self.auto_archive_check.isChecked()
            
            # UI
            ui_config = self.config.setdefault('ui', {})
            theme_map = {'Clair': 'light', 'Sombre': 'dark', 'Automatique': 'auto'}
            ui_config['theme'] = theme_map.get(self.theme_combo.currentText(), 'light')
            ui_config['font_size'] = self.font_size_spin.value()
            ui_config['show_preview_pane'] = self.preview_pane_check.isChecked()
            ui_config['notifications'] = self.notifications_check.isChecked()
            ui_config['minimize_to_tray'] = self.minimize_to_tray_check.isChecked()
            
            # Sauvegarder
            if save_config(self.config):
                self.settings_changed.emit(self.config)
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Paramètres", "Paramètres sauvegardés avec succès!")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder les paramètres")
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {e}")
    
    def _reset_settings(self):
        """Réinitialise les paramètres par défaut."""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Réinitialiser",
            "Êtes-vous sûr de vouloir réinitialiser tous les paramètres ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Réinitialiser avec les valeurs par défaut
            from utils.config import DEFAULT_CONFIG
            self.config.clear()
            self.config.update(DEFAULT_CONFIG)
            self._load_settings()
            
            QMessageBox.information(self, "Réinitialisation", "Paramètres réinitialisés!")