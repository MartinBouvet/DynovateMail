"""
Vue des paramètres corrigée et simplifiée.
"""
import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QLineEdit, QTextEdit, QCheckBox, QSpinBox,
    QComboBox, QGroupBox, QFormLayout, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from utils.config import save_config

logger = logging.getLogger(__name__)

class SettingsView(QWidget):
    """Vue des paramètres corrigée avec lisibilité améliorée."""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self._apply_style()
        self._load_settings()
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header simple
        header_layout = QHBoxLayout()
        
        title_label = QLabel("⚙️ Paramètres")
        title_label.setObjectName("page-title")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
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
        
        # Paramètres d'interface
        ui_group = self._create_ui_settings()
        main_layout.addWidget(ui_group)
        
        main_layout.addStretch()
        
        scroll_area.setWidget(main_widget)
        layout.addWidget(scroll_area)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("🔄 Réinitialiser")
        reset_btn.setObjectName("reset-button")
        reset_btn.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        
        save_btn = QPushButton("💾 Sauvegarder")
        save_btn.setObjectName("save-button")
        save_btn.clicked.connect(self._save_settings)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_general_settings(self) -> QGroupBox:
        """Crée les paramètres généraux."""
        group = QGroupBox("🏠 Paramètres généraux")
        group.setObjectName("settings-group")
        
        form_layout = QFormLayout(group)
        form_layout.setSpacing(15)
        form_layout.setVerticalSpacing(10)
        
        # Nom d'utilisateur
        self.user_name_input = QLineEdit()
        self.user_name_input.setObjectName("settings-input")
        self.user_name_input.setPlaceholderText("Votre nom complet")
        form_layout.addRow("Nom d'utilisateur :", self.user_name_input)
        
        # Signature
        self.signature_input = QTextEdit()
        self.signature_input.setObjectName("settings-text")
        self.signature_input.setMaximumHeight(80)
        self.signature_input.setPlaceholderText("Votre signature email...")
        form_layout.addRow("Signature :", self.signature_input)
        
        # Rafraîchissement automatique
        refresh_layout = QHBoxLayout()
        self.auto_refresh_check = QCheckBox("Activé")
        self.auto_refresh_check.setObjectName("settings-checkbox")
        refresh_layout.addWidget(self.auto_refresh_check)
        
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setObjectName("settings-spin")
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setSuffix(" min")
        refresh_layout.addWidget(QLabel("Intervalle :"))
        refresh_layout.addWidget(self.refresh_interval_spin)
        refresh_layout.addStretch()
        
        refresh_widget = QWidget()
        refresh_widget.setLayout(refresh_layout)
        form_layout.addRow("Rafraîchissement auto :", refresh_widget)
        
        return group
    
    def _create_ai_settings(self) -> QGroupBox:
        """Crée les paramètres d'IA."""
        group = QGroupBox("🤖 Intelligence artificielle")
        group.setObjectName("settings-group")
        
        form_layout = QFormLayout(group)
        form_layout.setSpacing(15)
        form_layout.setVerticalSpacing(10)
        
        # Classification automatique
        self.ai_classification_check = QCheckBox("Classer automatiquement les emails")
        self.ai_classification_check.setObjectName("settings-checkbox")
        form_layout.addRow("Classification :", self.ai_classification_check)
        
        # Détection de spam
        self.spam_detection_check = QCheckBox("Détecter les spams")
        self.spam_detection_check.setObjectName("settings-checkbox")
        form_layout.addRow("Anti-spam :", self.spam_detection_check)
        
        # Analyse de sentiment
        self.sentiment_analysis_check = QCheckBox("Analyser le sentiment")
        self.sentiment_analysis_check.setObjectName("settings-checkbox")
        form_layout.addRow("Sentiment :", self.sentiment_analysis_check)
        
        # Extraction de rendez-vous
        self.meeting_extraction_check = QCheckBox("Extraire les rendez-vous")
        self.meeting_extraction_check.setObjectName("settings-checkbox")
        form_layout.addRow("Calendrier :", self.meeting_extraction_check)
        
        return group
    
    def _create_auto_respond_settings(self) -> QGroupBox:
        """Crée les paramètres de réponse automatique."""
        group = QGroupBox("📤 Réponse automatique")
        group.setObjectName("settings-group")
        
        form_layout = QFormLayout(group)
        form_layout.setSpacing(15)
        form_layout.setVerticalSpacing(10)
        
        # Activer les réponses automatiques
        self.auto_respond_check = QCheckBox("Activer les réponses automatiques")
        self.auto_respond_check.setObjectName("settings-checkbox")
        form_layout.addRow("Activation :", self.auto_respond_check)
        
        # Délai avant réponse
        delay_layout = QHBoxLayout()
        self.response_delay_spin = QSpinBox()
        self.response_delay_spin.setObjectName("settings-spin")
        self.response_delay_spin.setRange(0, 60)
        self.response_delay_spin.setSuffix(" min")
        delay_layout.addWidget(self.response_delay_spin)
        delay_layout.addStretch()
        
        delay_widget = QWidget()
        delay_widget.setLayout(delay_layout)
        form_layout.addRow("Délai :", delay_widget)
        
        # Types d'emails à traiter
        types_layout = QVBoxLayout()
        
        self.auto_respond_cv_check = QCheckBox("Candidatures (CV)")
        self.auto_respond_cv_check.setObjectName("settings-checkbox")
        types_layout.addWidget(self.auto_respond_cv_check)
        
        self.auto_respond_rdv_check = QCheckBox("Demandes de rendez-vous")
        self.auto_respond_rdv_check.setObjectName("settings-checkbox")
        types_layout.addWidget(self.auto_respond_rdv_check)
        
        self.auto_respond_support_check = QCheckBox("Demandes de support")
        self.auto_respond_support_check.setObjectName("settings-checkbox")
        types_layout.addWidget(self.auto_respond_support_check)
        
        types_widget = QWidget()
        types_widget.setLayout(types_layout)
        form_layout.addRow("Types d'emails :", types_widget)
        
        # Éviter les boucles
        self.avoid_loops_check = QCheckBox("Éviter les réponses en boucle")
        self.avoid_loops_check.setObjectName("settings-checkbox")
        self.avoid_loops_check.setChecked(True)
        form_layout.addRow("Sécurité :", self.avoid_loops_check)
        
        return group
    
    def _create_ui_settings(self) -> QGroupBox:
        """Crée les paramètres d'interface."""
        group = QGroupBox("🎨 Interface utilisateur")
        group.setObjectName("settings-group")
        
        form_layout = QFormLayout(group)
        form_layout.setSpacing(15)
        form_layout.setVerticalSpacing(10)
        
        # Thème
        theme_layout = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("settings-combo")
        self.theme_combo.addItems(["Clair", "Sombre", "Automatique"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        theme_widget = QWidget()
        theme_widget.setLayout(theme_layout)
        form_layout.addRow("Thème :", theme_widget)
        
        # Taille de police
        font_layout = QHBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setObjectName("settings-spin")
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setSuffix(" pt")
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch()
        
        font_widget = QWidget()
        font_widget.setLayout(font_layout)
        form_layout.addRow("Taille de police :", font_widget)
        
        # Options d'affichage
        display_layout = QVBoxLayout()
        
        self.preview_pane_check = QCheckBox("Afficher le volet de prévisualisation")
        self.preview_pane_check.setObjectName("settings-checkbox")
        display_layout.addWidget(self.preview_pane_check)
        
        self.notifications_check = QCheckBox("Notifications")
        self.notifications_check.setObjectName("settings-checkbox")
        display_layout.addWidget(self.notifications_check)
        
        self.minimize_to_tray_check = QCheckBox("Minimiser dans la barre système")
        self.minimize_to_tray_check.setObjectName("settings-checkbox")
        display_layout.addWidget(self.minimize_to_tray_check)
        
        display_widget = QWidget()
        display_widget.setLayout(display_layout)
        form_layout.addRow("Affichage :", display_widget)
        
        return group
    
    def _apply_style(self):
        """Applique le style lisible aux paramètres."""
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            
            QLabel#page-title {
                color: #000000;
                margin-bottom: 10px;
            }
            
            QGroupBox#settings-group {
                font-size: 14px;
                font-weight: bold;
                color: #000000;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #f8f8f8;
            }
            
            QGroupBox#settings-group::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: #ffffff;
                border-radius: 5px;
            }
            
            QLineEdit#settings-input {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
                color: #000000;
                min-height: 20px;
            }
            
            QLineEdit#settings-input:focus {
                border-color: #000000;
            }
            
            QTextEdit#settings-text {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                color: #000000;
            }
            
            QTextEdit#settings-text:focus {
                border-color: #000000;
            }
            
            QCheckBox#settings-checkbox {
                color: #000000;
                font-size: 13px;
                spacing: 8px;
                font-weight: normal;
            }
            
            QCheckBox#settings-checkbox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: #ffffff;
            }
            
            QCheckBox#settings-checkbox::indicator:checked {
                background-color: #000000;
                border-color: #000000;
            }
            
            QCheckBox#settings-checkbox::indicator:hover {
                border-color: #cccccc;
            }
            
            QSpinBox#settings-spin {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
                color: #000000;
                min-width: 80px;
            }
            
            QSpinBox#settings-spin:focus {
                border-color: #000000;
            }
            
            QComboBox#settings-combo {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #000000;
                min-width: 150px;
            }
            
            QComboBox#settings-combo:focus {
                border-color: #000000;
            }
            
            QComboBox#settings-combo::drop-down {
                border: none;
                width: 25px;
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
            
            QComboBox#settings-combo QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                selection-background-color: #f0f0f0;
                outline: none;
            }
            
            QPushButton#save-button {
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #000000;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            
            QPushButton#save-button:hover {
                background-color: #333333;
            }
            
            QPushButton#save-button:pressed {
                background-color: #555555;
            }
            
            QPushButton#reset-button {
                background-color: #ffffff;
                color: #666666;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                min-width: 120px;
            }
            
            QPushButton#reset-button:hover {
                background-color: #f0f0f0;
                color: #000000;
                border-color: #cccccc;
            }
            
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            
            QScrollBar:vertical {
                background-color: #f8f8f8;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #cccccc;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #999999;
            }
            
            QFormLayout QLabel {
                color: #000000;
                font-size: 13px;
                font-weight: bold;
                margin-right: 10px;
                min-width: 120px;
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
            
            # Paramètres de réponse automatique
            auto_respond_config = self.config.get('auto_respond', {})
            self.auto_respond_check.setChecked(auto_respond_config.get('enabled', False))
            self.response_delay_spin.setValue(auto_respond_config.get('delay_minutes', 5))
            self.auto_respond_cv_check.setChecked(auto_respond_config.get('respond_to_cv', True))
            self.auto_respond_rdv_check.setChecked(auto_respond_config.get('respond_to_rdv', True))
            self.auto_respond_support_check.setChecked(auto_respond_config.get('respond_to_support', True))
            self.avoid_loops_check.setChecked(auto_respond_config.get('avoid_loops', True))
            
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
            
            # Réponse automatique
            auto_respond_config = self.config.setdefault('auto_respond', {})
            auto_respond_config['enabled'] = self.auto_respond_check.isChecked()
            auto_respond_config['delay_minutes'] = self.response_delay_spin.value()
            auto_respond_config['respond_to_cv'] = self.auto_respond_cv_check.isChecked()
            auto_respond_config['respond_to_rdv'] = self.auto_respond_rdv_check.isChecked()
            auto_respond_config['respond_to_support'] = self.auto_respond_support_check.isChecked()
            auto_respond_config['avoid_loops'] = self.avoid_loops_check.isChecked()
            
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
                QMessageBox.information(self, "Succès", "✅ Paramètres sauvegardés avec succès!")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Erreur", "❌ Impossible de sauvegarder les paramètres")
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", f"❌ Erreur lors de la sauvegarde: {e}")
    
    def _reset_settings(self):
        """Réinitialise les paramètres par défaut."""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "⚠️ Réinitialiser",
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
            
            QMessageBox.information(self, "Succès", "✅ Paramètres réinitialisés!")