"""
Vue des paramètres avec sauvegarde instantanée et application immédiate.
"""
import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QLineEdit, QTextEdit, QCheckBox, QSpinBox,
    QComboBox, QGroupBox, QFormLayout, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from utils.config import get_config_manager

logger = logging.getLogger(__name__)

class SettingsView(QWidget):
    """Vue des paramètres avec sauvegarde instantanée et application en temps réel."""
    
    settings_applied = pyqtSignal(dict)  # Signal émis quand les paramètres sont appliqués
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Gestionnaire de configuration
        self.config_manager = get_config_manager()
        
        # Timer pour la sauvegarde différée (éviter de sauvegarder à chaque caractère)
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._delayed_save)
        
        # Flag pour éviter les boucles de mise à jour
        self._updating_ui = False
        
        self._setup_ui()
        self._apply_style()
        self._load_settings()
        
        # S'abonner aux changements de configuration
        self.config_manager.config_changed.connect(self._on_config_changed)
        
        logger.info("Vue des paramètres initialisée avec configuration réactive")
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("⚙️ Paramètres")
        title_label.setObjectName("page-title")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Indicateur de sauvegarde
        self.save_indicator = QLabel("✅ Sauvegardé")
        self.save_indicator.setObjectName("save-indicator")
        self.save_indicator.setFont(QFont("Arial", 12))
        self.save_indicator.setVisible(False)
        header_layout.addWidget(self.save_indicator)
        
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
        
        export_btn = QPushButton("📤 Exporter")
        export_btn.setObjectName("export-button")
        export_btn.clicked.connect(self._export_settings)
        buttons_layout.addWidget(export_btn)
        
        import_btn = QPushButton("📥 Importer")
        import_btn.setObjectName("import-button")
        import_btn.clicked.connect(self._import_settings)
        buttons_layout.addWidget(import_btn)
        
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
        self.user_name_input.textChanged.connect(self._on_user_name_changed)
        form_layout.addRow("Nom d'utilisateur :", self.user_name_input)
        
        # Signature
        self.signature_input = QTextEdit()
        self.signature_input.setObjectName("settings-text")
        self.signature_input.setMaximumHeight(80)
        self.signature_input.setPlaceholderText("Votre signature email...")
        self.signature_input.textChanged.connect(self._on_signature_changed)
        form_layout.addRow("Signature :", self.signature_input)
        
        # Rafraîchissement automatique
        refresh_layout = QHBoxLayout()
        self.auto_refresh_check = QCheckBox("Activé")
        self.auto_refresh_check.setObjectName("settings-checkbox")
        self.auto_refresh_check.toggled.connect(self._on_auto_refresh_changed)
        refresh_layout.addWidget(self.auto_refresh_check)
        
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setObjectName("settings-spin")
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setSuffix(" min")
        self.refresh_interval_spin.valueChanged.connect(self._on_refresh_interval_changed)
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
        self.ai_classification_check.toggled.connect(self._on_ai_classification_changed)
        form_layout.addRow("Classification :", self.ai_classification_check)
        
        # Détection de spam
        self.spam_detection_check = QCheckBox("Détecter les spams")
        self.spam_detection_check.setObjectName("settings-checkbox")
        self.spam_detection_check.toggled.connect(self._on_spam_detection_changed)
        form_layout.addRow("Anti-spam :", self.spam_detection_check)
        
        # Analyse de sentiment
        self.sentiment_analysis_check = QCheckBox("Analyser le sentiment")
        self.sentiment_analysis_check.setObjectName("settings-checkbox")
        self.sentiment_analysis_check.toggled.connect(self._on_sentiment_analysis_changed)
        form_layout.addRow("Sentiment :", self.sentiment_analysis_check)
        
        # Extraction de rendez-vous
        self.meeting_extraction_check = QCheckBox("Extraire les rendez-vous")
        self.meeting_extraction_check.setObjectName("settings-checkbox")
        self.meeting_extraction_check.toggled.connect(self._on_meeting_extraction_changed)
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
        self.auto_respond_check.toggled.connect(self._on_auto_respond_changed)
        form_layout.addRow("Activation :", self.auto_respond_check)
        
        # Délai avant réponse
        delay_layout = QHBoxLayout()
        self.response_delay_spin = QSpinBox()
        self.response_delay_spin.setObjectName("settings-spin")
        self.response_delay_spin.setRange(0, 60)
        self.response_delay_spin.setSuffix(" min")
        self.response_delay_spin.valueChanged.connect(self._on_response_delay_changed)
        delay_layout.addWidget(self.response_delay_spin)
        delay_layout.addStretch()
        
        delay_widget = QWidget()
        delay_widget.setLayout(delay_layout)
        form_layout.addRow("Délai :", delay_widget)
        
        # Types d'emails à traiter
        types_layout = QVBoxLayout()
        
        self.auto_respond_cv_check = QCheckBox("Candidatures (CV)")
        self.auto_respond_cv_check.setObjectName("settings-checkbox")
        self.auto_respond_cv_check.toggled.connect(self._on_respond_cv_changed)
        types_layout.addWidget(self.auto_respond_cv_check)
        
        self.auto_respond_rdv_check = QCheckBox("Demandes de rendez-vous")
        self.auto_respond_rdv_check.setObjectName("settings-checkbox")
        self.auto_respond_rdv_check.toggled.connect(self._on_respond_rdv_changed)
        types_layout.addWidget(self.auto_respond_rdv_check)
        
        self.auto_respond_support_check = QCheckBox("Demandes de support")
        self.auto_respond_support_check.setObjectName("settings-checkbox")
        self.auto_respond_support_check.toggled.connect(self._on_respond_support_changed)
        types_layout.addWidget(self.auto_respond_support_check)
        
        self.auto_respond_partenariat_check = QCheckBox("Propositions de partenariat")
        self.auto_respond_partenariat_check.setObjectName("settings-checkbox")
        self.auto_respond_partenariat_check.toggled.connect(self._on_respond_partenariat_changed)
        types_layout.addWidget(self.auto_respond_partenariat_check)
        
        types_widget = QWidget()
        types_widget.setLayout(types_layout)
        form_layout.addRow("Types d'emails :", types_widget)
        
        # Éviter les boucles
        self.avoid_loops_check = QCheckBox("Éviter les réponses en boucle")
        self.avoid_loops_check.setObjectName("settings-checkbox")
        self.avoid_loops_check.setChecked(True)
        self.avoid_loops_check.toggled.connect(self._on_avoid_loops_changed)
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
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
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
        self.font_size_spin.valueChanged.connect(self._on_font_size_changed)
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch()
        
        font_widget = QWidget()
        font_widget.setLayout(font_layout)
        form_layout.addRow("Taille de police :", font_widget)
        
        # Options d'affichage
        display_layout = QVBoxLayout()
        
        self.preview_pane_check = QCheckBox("Afficher le volet de prévisualisation")
        self.preview_pane_check.setObjectName("settings-checkbox")
        self.preview_pane_check.toggled.connect(self._on_preview_pane_changed)
        display_layout.addWidget(self.preview_pane_check)
        
        self.notifications_check = QCheckBox("Notifications")
        self.notifications_check.setObjectName("settings-checkbox")
        self.notifications_check.toggled.connect(self._on_notifications_changed)
        display_layout.addWidget(self.notifications_check)
        
        self.minimize_to_tray_check = QCheckBox("Minimiser dans la barre système")
        self.minimize_to_tray_check.setObjectName("settings-checkbox")
        self.minimize_to_tray_check.toggled.connect(self._on_minimize_to_tray_changed)
        display_layout.addWidget(self.minimize_to_tray_check)
        
        display_widget = QWidget()
        display_widget.setLayout(display_layout)
        form_layout.addRow("Affichage :", display_widget)
        
        return group
    
    # Callbacks pour les changements de paramètres (sauvegarde instantanée)
    
    def _on_user_name_changed(self):
        """Callback pour le changement de nom d'utilisateur."""
        if not self._updating_ui:
            self.config_manager.set('user.name', self.user_name_input.text())
            self._show_save_indicator()
    
    def _on_signature_changed(self):
        """Callback pour le changement de signature."""
        if not self._updating_ui:
            self.config_manager.set('user.signature', self.signature_input.toPlainText())
            self._show_save_indicator()
    
    def _on_auto_refresh_changed(self, checked):
        """Callback pour le changement de rafraîchissement automatique."""
        if not self._updating_ui:
            self.config_manager.set('app.auto_refresh', checked)
            self._show_save_indicator()
    
    def _on_refresh_interval_changed(self, value):
        """Callback pour le changement d'intervalle de rafraîchissement."""
        if not self._updating_ui:
            self.config_manager.set('email.refresh_interval_minutes', value)
            self._show_save_indicator()
    
    def _on_ai_classification_changed(self, checked):
        """Callback pour la classification IA."""
        if not self._updating_ui:
            self.config_manager.set('ai.enable_classification', checked)
            self._show_save_indicator()
    
    def _on_spam_detection_changed(self, checked):
        """Callback pour la détection de spam."""
        if not self._updating_ui:
            self.config_manager.set('ai.enable_spam_detection', checked)
            self._show_save_indicator()
    
    def _on_sentiment_analysis_changed(self, checked):
        """Callback pour l'analyse de sentiment."""
        if not self._updating_ui:
            self.config_manager.set('ai.enable_sentiment_analysis', checked)
            self._show_save_indicator()
    
    def _on_meeting_extraction_changed(self, checked):
        """Callback pour l'extraction de rendez-vous."""
        if not self._updating_ui:
            self.config_manager.set('ai.enable_meeting_extraction', checked)
            self._show_save_indicator()
    
    def _on_auto_respond_changed(self, checked):
        """Callback pour l'activation des réponses automatiques."""
        if not self._updating_ui:
            self.config_manager.set('auto_respond.enabled', checked)
            self._show_save_indicator()
            logger.info(f"Réponses automatiques {'activées' if checked else 'désactivées'}")
    
    def _on_response_delay_changed(self, value):
        """Callback pour le délai de réponse."""
        if not self._updating_ui:
            self.config_manager.set('auto_respond.delay_minutes', value)
            self._show_save_indicator()
    
    def _on_respond_cv_changed(self, checked):
        """Callback pour les réponses aux CV."""
        if not self._updating_ui:
            self.config_manager.set('auto_respond.respond_to_cv', checked)
            self._show_save_indicator()
    
    def _on_respond_rdv_changed(self, checked):
        """Callback pour les réponses aux RDV."""
        if not self._updating_ui:
            self.config_manager.set('auto_respond.respond_to_rdv', checked)
            self._show_save_indicator()
    
    def _on_respond_support_changed(self, checked):
        """Callback pour les réponses au support."""
        if not self._updating_ui:
            self.config_manager.set('auto_respond.respond_to_support', checked)
            self._show_save_indicator()
    
    def _on_respond_partenariat_changed(self, checked):
        """Callback pour les réponses aux partenariats."""
        if not self._updating_ui:
            self.config_manager.set('auto_respond.respond_to_partenariat', checked)
            self._show_save_indicator()
    
    def _on_avoid_loops_changed(self, checked):
        """Callback pour éviter les boucles."""
        if not self._updating_ui:
            self.config_manager.set('auto_respond.avoid_loops', checked)
            self._show_save_indicator()
    
    def _on_theme_changed(self, text):
        """Callback pour le changement de thème."""
        if not self._updating_ui:
            theme_map = {'Clair': 'light', 'Sombre': 'dark', 'Automatique': 'auto'}
            self.config_manager.set('ui.theme', theme_map.get(text, 'light'))
            self._show_save_indicator()
    
    def _on_font_size_changed(self, value):
        """Callback pour la taille de police."""
        if not self._updating_ui:
            self.config_manager.set('ui.font_size', value)
            self._show_save_indicator()
    
    def _on_preview_pane_changed(self, checked):
        """Callback pour le volet de prévisualisation."""
        if not self._updating_ui:
            self.config_manager.set('ui.show_preview_pane', checked)
            self._show_save_indicator()
    
    def _on_notifications_changed(self, checked):
        """Callback pour les notifications."""
        if not self._updating_ui:
            self.config_manager.set('ui.notifications', checked)
            self._show_save_indicator()
    
    def _on_minimize_to_tray_changed(self, checked):
        """Callback pour minimiser dans la barre système."""
        if not self._updating_ui:
            self.config_manager.set('ui.minimize_to_tray', checked)
            self._show_save_indicator()
    
    def _show_save_indicator(self):
        """Affiche l'indicateur de sauvegarde."""
        self.save_indicator.setText("💾 Sauvegarde...")
        self.save_indicator.setStyleSheet("color: #ff9800;")
        self.save_indicator.setVisible(True)
        
        # Programmer la mise à jour de l'indicateur
        QTimer.singleShot(1000, self._update_save_indicator)
    
    def _update_save_indicator(self):
        """Met à jour l'indicateur de sauvegarde."""
        self.save_indicator.setText("✅ Sauvegardé")
        self.save_indicator.setStyleSheet("color: #4caf50;")
        
        # Masquer après 2 secondes
        QTimer.singleShot(2000, lambda: self.save_indicator.setVisible(False))
    
    def _delayed_save(self):
        """Sauvegarde différée pour éviter trop d'écritures."""
        # Cette méthode est appelée par le timer mais la sauvegarde
        # est déjà faite dans les callbacks individuels
        pass
    
    def _load_settings(self):
        """Charge les paramètres depuis la configuration."""
        self._updating_ui = True
        
        try:
            config = self.config_manager.get_config()
            
            # Paramètres généraux
            self.user_name_input.setText(config.get('user', {}).get('name', ''))
            self.signature_input.setPlainText(config.get('user', {}).get('signature', ''))
            self.auto_refresh_check.setChecked(config.get('app', {}).get('auto_refresh', True))
            self.refresh_interval_spin.setValue(config.get('email', {}).get('refresh_interval_minutes', 5))
            
            # Paramètres IA
            ai_config = config.get('ai', {})
            self.ai_classification_check.setChecked(ai_config.get('enable_classification', True))
            self.spam_detection_check.setChecked(ai_config.get('enable_spam_detection', True))
            self.sentiment_analysis_check.setChecked(ai_config.get('enable_sentiment_analysis', True))
            self.meeting_extraction_check.setChecked(ai_config.get('enable_meeting_extraction', True))
            
            # Paramètres de réponse automatique
            auto_respond_config = config.get('auto_respond', {})
            self.auto_respond_check.setChecked(auto_respond_config.get('enabled', False))
            self.response_delay_spin.setValue(auto_respond_config.get('delay_minutes', 5))
            self.auto_respond_cv_check.setChecked(auto_respond_config.get('respond_to_cv', True))
            self.auto_respond_rdv_check.setChecked(auto_respond_config.get('respond_to_rdv', True))
            self.auto_respond_support_check.setChecked(auto_respond_config.get('respond_to_support', True))
            self.auto_respond_partenariat_check.setChecked(auto_respond_config.get('respond_to_partenariat', True))
            self.avoid_loops_check.setChecked(auto_respond_config.get('avoid_loops', True))
            
            # Paramètres UI
            ui_config = config.get('ui', {})
            theme_map = {'light': 'Clair', 'dark': 'Sombre', 'auto': 'Automatique'}
            self.theme_combo.setCurrentText(theme_map.get(ui_config.get('theme', 'light'), 'Clair'))
            self.font_size_spin.setValue(ui_config.get('font_size', 12))
            self.preview_pane_check.setChecked(ui_config.get('show_preview_pane', True))
            self.notifications_check.setChecked(ui_config.get('notifications', True))
            self.minimize_to_tray_check.setChecked(ui_config.get('minimize_to_tray', True))
            
            logger.info("Paramètres chargés dans l'interface")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des paramètres: {e}")
        finally:
            self._updating_ui = False
    
    def _on_config_changed(self, new_config):
        """Callback appelé quand la configuration change externement."""
        if not self._updating_ui:
            logger.info("Configuration changée externement, mise à jour de l'interface")
            self._load_settings()
            self.settings_applied.emit(new_config)
    
    def _reset_settings(self):
        """Réinitialise les paramètres par défaut."""
        reply = QMessageBox.question(
            self,
            "⚠️ Réinitialiser",
            "Êtes-vous sûr de vouloir réinitialiser tous les paramètres ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.reset_to_defaults()
            QMessageBox.information(self, "Succès", "✅ Paramètres réinitialisés!")
    
    def _export_settings(self):
        """Exporte la configuration."""
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter la configuration",
            "dynovate_config.json",
            "Fichiers JSON (*.json)"
        )
        
        if filename:
            try:
                config = self.config_manager.get_config()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                
                QMessageBox.information(self, "Succès", f"✅ Configuration exportée vers {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"❌ Erreur lors de l'export: {e}")
    
    def _import_settings(self):
        """Importe une configuration."""
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Importer une configuration",
            "",
            "Fichiers JSON (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                # Validation basique
                if not isinstance(imported_config, dict):
                    raise ValueError("Le fichier ne contient pas une configuration valide")
                
                # Appliquer la configuration
                self.config_manager.config = imported_config
                self.config_manager.save_config()
                
                QMessageBox.information(self, "Succès", f"✅ Configuration importée depuis {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"❌ Erreur lors de l'import: {e}")
    
    def _apply_style(self):
        """Applique le style aux paramètres."""
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            
            QLabel#page-title {
                color: #000000;
                margin-bottom: 10px;
            }
            
            QLabel#save-indicator {
                font-weight: bold;
                margin-left: 10px;
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
            
            QComboBox#settings-combo QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                selection-background-color: #f0f0f0;
                outline: none;
            }
            
            QPushButton#reset-button, QPushButton#export-button, QPushButton#import-button {
                background-color: #ffffff;
                color: #666666;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                min-width: 120px;
            }
            
            QPushButton#reset-button:hover, QPushButton#export-button:hover, QPushButton#import-button:hover {
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