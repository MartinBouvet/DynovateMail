#!/usr/bin/env python3
"""
Vue des paramètres corrigée avec affichage propre.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
    QSlider, QSpinBox, QComboBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any

class SettingCard(QFrame):
    """Carte de paramètre moderne corrigée."""
    
    def __init__(self, title: str, description: str, control_widget: QWidget):
        super().__init__()
        self.setObjectName("setting-card")
        self.setMinimumHeight(100)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Titre
        title_label = QLabel(title)
        title_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #000000;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Inter", 13))
        desc_label.setStyleSheet("color: #6c757d; line-height: 1.5;")
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(60)
        layout.addWidget(desc_label)
        
        # Contrôle
        control_container = QWidget()
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(0, 8, 0, 0)
        control_layout.addWidget(control_widget)
        control_layout.addStretch()
        layout.addWidget(control_container)
        
        self.setStyleSheet("""
            QFrame#setting-card {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 12px;
                margin: 8px 0;
            }
            QFrame#setting-card:hover {
                border-color: #adb5bd;
            }
        """)

class AIConfigSection(QWidget):
    """Section de configuration IA corrigée."""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface de la section IA."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre de section
        title = QLabel("🤖 Configuration IA")
        title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000; margin-bottom: 16px;")
        layout.addWidget(title)
        
        # Classification automatique
        self.auto_classify_cb = QCheckBox("Activer la classification automatique")
        self.auto_classify_cb.setChecked(True)
        self.auto_classify_cb.setFont(QFont("Inter", 14))
        self.auto_classify_cb.stateChanged.connect(self._on_settings_changed)
        
        classify_card = SettingCard(
            "Classification automatique",
            "Active la classification intelligente des emails par l'IA pour trier automatiquement vos messages.",
            self.auto_classify_cb
        )
        layout.addWidget(classify_card)
        
        # Seuil de confiance
        confidence_container = QWidget()
        confidence_layout = QHBoxLayout(confidence_container)
        confidence_layout.setContentsMargins(0, 0, 0, 0)
        confidence_layout.setSpacing(15)
        
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(50, 95)
        self.confidence_slider.setValue(75)
        self.confidence_slider.setMinimumWidth(200)
        self.confidence_slider.valueChanged.connect(self._on_settings_changed)
        confidence_layout.addWidget(self.confidence_slider)
        
        self.confidence_label = QLabel("75%")
        self.confidence_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        self.confidence_label.setMinimumWidth(50)
        self.confidence_label.setStyleSheet("color: #007bff;")
        confidence_layout.addWidget(self.confidence_label)
        
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v}%")
        )
        
        confidence_card = SettingCard(
            "Seuil de confiance IA",
            "Niveau minimum de confiance requis pour que l'IA classe automatiquement un email.",
            confidence_container
        )
        layout.addWidget(confidence_card)
        
        # Réponses automatiques
        self.auto_respond_cb = QCheckBox("Permettre les réponses automatiques")
        self.auto_respond_cb.setChecked(False)
        self.auto_respond_cb.setFont(QFont("Inter", 14))
        self.auto_respond_cb.stateChanged.connect(self._on_settings_changed)
        
        auto_respond_card = SettingCard(
            "Réponses automatiques",
            "Permet à l'IA d'envoyer des réponses automatiques selon vos règles prédéfinies.",
            self.auto_respond_cb
        )
        layout.addWidget(auto_respond_card)
        
        # Délai de réponse
        self.response_delay_spin = QSpinBox()
        self.response_delay_spin.setRange(1, 60)
        self.response_delay_spin.setValue(5)
        self.response_delay_spin.setSuffix(" minutes")
        self.response_delay_spin.setFont(QFont("Inter", 14))
        self.response_delay_spin.setMinimumWidth(120)
        self.response_delay_spin.valueChanged.connect(self._on_settings_changed)
        
        delay_card = SettingCard(
            "Délai avant envoi automatique",
            "Temps d'attente avant l'envoi automatique d'une réponse pour vous laisser le temps d'intervenir.",
            self.response_delay_spin
        )
        layout.addWidget(delay_card)
        
        # Modèle IA
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.addItems([
            "Modèle local (rapide)",
            "GPT-3.5 Turbo (équilibré)",
            "GPT-4 (précis)",
            "Claude (créatif)"
        ])
        self.ai_model_combo.setFont(QFont("Inter", 14))
        self.ai_model_combo.setMinimumWidth(200)
        self.ai_model_combo.currentTextChanged.connect(self._on_settings_changed)
        
        model_card = SettingCard(
            "Modèle d'intelligence artificielle",
            "Choisissez le modèle d'IA à utiliser pour l'analyse et la génération de réponses.",
            self.ai_model_combo
        )
        layout.addWidget(model_card)
        
        # Apprentissage
        self.learning_cb = QCheckBox("Activer l'apprentissage automatique")
        self.learning_cb.setChecked(True)
        self.learning_cb.setFont(QFont("Inter", 14))
        self.learning_cb.stateChanged.connect(self._on_settings_changed)
        
        learning_card = SettingCard(
            "Apprentissage automatique",
            "L'IA apprend de vos corrections et décisions pour améliorer ses performances au fil du temps.",
            self.learning_cb
        )
        layout.addWidget(learning_card)
        
        # Appliquer les styles
        self._apply_styles()
    
    def _apply_styles(self):
        """Applique les styles aux contrôles."""
        checkbox_style = """
            QCheckBox {
                color: #000000;
                font-size: 14px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            QCheckBox::indicator:hover {
                border-color: #007bff;
            }
        """
        
        slider_style = """
            QSlider::groove:horizontal {
                background-color: #dee2e6;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background-color: #007bff;
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -6px 0;
                border: 2px solid #ffffff;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            QSlider::handle:horizontal:hover {
                background-color: #0056b3;
            }
            QSlider::sub-page:horizontal {
                background-color: #007bff;
                border-radius: 4px;
            }
        """
        
        spinbox_style = """
            QSpinBox {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px 12px;
                color: #495057;
                font-size: 14px;
            }
            QSpinBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                background-color: #f8f9fa;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e9ecef;
            }
        """
        
        combo_style = """
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px 12px;
                color: #495057;
                font-size: 14px;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6c757d;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                selection-background-color: #e3f2fd;
                selection-color: #000000;
                padding: 4px;
            }
        """
        
        # Appliquer les styles
        for widget in self.findChildren(QCheckBox):
            widget.setStyleSheet(checkbox_style)
        
        for widget in self.findChildren(QSlider):
            widget.setStyleSheet(slider_style)
        
        for widget in self.findChildren(QSpinBox):
            widget.setStyleSheet(spinbox_style)
        
        for widget in self.findChildren(QComboBox):
            widget.setStyleSheet(combo_style)
    
    def _on_settings_changed(self):
        """Émet le signal de changement de paramètres."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres actuels."""
        return {
            'auto_classify': self.auto_classify_cb.isChecked(),
            'confidence_threshold': self.confidence_slider.value() / 100.0,
            'auto_respond': self.auto_respond_cb.isChecked(),
            'response_delay': self.response_delay_spin.value(),
            'ai_model': self.ai_model_combo.currentText(),
            'enable_learning': self.learning_cb.isChecked()
        }
    
    def set_settings(self, settings: Dict[str, Any]):
        """Applique les paramètres."""
        # Bloquer les signaux pendant la mise à jour
        widgets = [
            self.auto_classify_cb, self.confidence_slider, self.auto_respond_cb,
            self.response_delay_spin, self.ai_model_combo, self.learning_cb
        ]
        
        for widget in widgets:
            widget.blockSignals(True)
        
        # Appliquer les valeurs
        self.auto_classify_cb.setChecked(settings.get('auto_classify', True))
        self.confidence_slider.setValue(int(settings.get('confidence_threshold', 0.75) * 100))
        self.auto_respond_cb.setChecked(settings.get('auto_respond', False))
        self.response_delay_spin.setValue(settings.get('response_delay', 5))
        
        model = settings.get('ai_model', 'Modèle local (rapide)')
        index = self.ai_model_combo.findText(model)
        if index >= 0:
            self.ai_model_combo.setCurrentIndex(index)
        
        self.learning_cb.setChecked(settings.get('enable_learning', True))
        
        # Débloquer les signaux
        for widget in widgets:
            widget.blockSignals(False)

class SettingsView(QWidget):
    """Vue des paramètres principale corrigée."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(0)
        
        # Titre principal
        title = QLabel("⚙️ Paramètres")
        title.setFont(QFont("Inter", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000; margin-bottom: 30px;")
        layout.addWidget(title)
        
        # Zone de scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #dee2e6;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
        """)
        
        # Contenu scrollable
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 20, 20)
        
        # Section IA
        self.ai_section = AIConfigSection()
        content_layout.addWidget(self.ai_section)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Style global
        self.setStyleSheet("""
            SettingsView {
                background-color: #ffffff;
            }
        """)