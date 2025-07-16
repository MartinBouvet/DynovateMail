class AIConfigSection(QWidget):
    """Section de configuration IA."""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface de la section IA."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Titre de section
        title = QLabel("🤖 Configuration IA")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #000000; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Classification automatique
        self.auto_classify_cb = QCheckBox()
        self.auto_classify_cb.setChecked(True)
        self.auto_classify_cb.stateChanged.connect(self._on_settings_changed)
        
        classify_card = SettingCard(
            "Classification automatique",
            "Active la classification intelligente des emails par l'IA",
            self.auto_classify_cb
        )
        layout.addWidget(classify_card)
        
        # Seuil de confiance
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(50, 95)
        self.confidence_slider.setValue(75)
        self.confidence_slider.valueChanged.connect(self._on_settings_changed)
        
        confidence_container = QWidget()
        confidence_layout = QHBoxLayout(confidence_container)
        confidence_layout.setContentsMargins(0, 0, 0, 0)
        confidence_layout.addWidget(self.confidence_slider)
        
        self.confidence_label = QLabel("75%")
        self.confidence_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.confidence_label.setMinimumWidth(40)
        confidence_layout.addWidget(self.confidence_label)
        
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v}%")
        )
        
        confidence_card = SettingCard(
            "Seuil de confiance IA",
            "Niveau minimum de confiance requis pour les classifications automatiques",
            confidence_container
        )
        layout.addWidget(confidence_card)
        
        # Réponses automatiques
        self.auto_respond_cb = QCheckBox()
        self.auto_respond_cb.setChecked(False)
        self.auto_respond_cb.stateChanged.connect(self._on_settings_changed)
        
        auto_respond_card = SettingCard(
            "Réponses automatiques",
            "Permet à l'IA d'envoyer des réponses automatiques selon vos règles",
            self.auto_respond_cb
        )
        layout.addWidget(auto_respond_card)
        
        # Délai de réponse
        self.response_delay_spin = QSpinBox()
        self.response_delay_spin.setRange(1, 60)
        self.response_delay_spin.setValue(5)
        self.response_delay_spin.setSuffix(" min")
        self.response_delay_spin.valueChanged.connect(self._on_settings_changed)
        
        delay_card = SettingCard(
            "Délai avant envoi automatique",
            "Temps d'attente avant l'envoi automatique d'une réponse",
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
        self.ai_model_combo.currentTextChanged.connect(self._on_settings_changed)
        
        model_card = SettingCard(
            "Modèle d'IA",
            "Choisissez le modèle d'intelligence artificielle à utiliser",
            self.ai_model_combo
        )
        layout.addWidget(model_card)
        
        # Apprentissage
        self.learning_cb = QCheckBox()
        self.learning_cb.setChecked(True)
        self.learning_cb.stateChanged.connect(self._on_settings_changed)
        
        learning_card = SettingCard(
            "Apprentissage automatique",
            "L'IA apprend de vos corrections pour améliorer ses performances",
            self.learning_cb
        )
        layout.addWidget(learning_card)
    
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
        self.auto_classify_cb.blockSignals(True)
        self.confidence_slider.blockSignals(True)
        self.auto_respond_cb.blockSignals(True)
        self.response_delay_spin.blockSignals(True)
        self.ai_model_combo.blockSignals(True)
        self.learning_cb.blockSignals(True)
        
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
        self.auto_classify_cb.blockSignals(False)
        self.confidence_slider.blockSignals(False)
        self.auto_respond_cb.blockSignals(False)
        self.response_delay_spin.blockSignals(False)
        self.ai_model_combo.blockSignals(False)
        self.learning_cb.blockSignals(False)