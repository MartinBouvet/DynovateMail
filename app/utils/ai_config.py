"""
Configuration avancée pour les modèles IA et la classification.
Gère les paramètres, seuils et optimisations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ClassificationConfig:
    """Configuration pour la classification d'emails."""
    
    # Seuils de classification
    spam_threshold: float = 0.6
    suspicious_threshold: float = 0.4
    confidence_threshold: float = 0.5
    
    # Catégories supportées
    categories: list = None
    
    # Pondérations des méthodes de classification
    rule_based_weight: float = 0.4
    ml_weight: float = 0.3
    reputation_weight: float = 0.2
    behavioral_weight: float = 0.1
    
    # Configuration des modèles
    use_transformers: bool = True
    use_statistical_models: bool = True
    use_rule_based: bool = True
    
    # Performance
    cache_enabled: bool = True
    cache_max_size: int = 1000
    async_processing: bool = True
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = [
                'cv_candidature',
                'rdv_meeting',
                'facture_finance', 
                'support_client',
                'newsletter',
                'partenariat',
                'spam',
                'personal',
                'other'
            ]

@dataclass
class SpamDetectionConfig:
    """Configuration pour la détection de spam."""
    
    # Seuils de détection
    spam_threshold: float = 0.6
    suspicious_threshold: float = 0.4
    
    # Pondérations des analyses
    content_analysis_weight: float = 0.4
    sender_analysis_weight: float = 0.3
    ml_analysis_weight: float = 0.2
    behavioral_analysis_weight: float = 0.1
    
    # Configuration ML
    vectorizer_max_features: int = 5000
    anomaly_contamination: float = 0.1
    
    # Limites temporelles
    recent_history_hours: int = 24
    reputation_history_days: int = 30
    
    # Cache et performance
    enable_cache: bool = True
    cache_expiry_hours: int = 6

@dataclass
class ModelConfig:
    """Configuration des modèles IA."""
    
    # Modèles Transformers
    classification_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    spam_model: str = "unitary/toxic-bert"
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    
    # Configuration d'entraînement
    train_test_split: float = 0.2
    random_state: int = 42
    cross_validation_folds: int = 5
    
    # Modèles traditionnels
    rf_n_estimators: int = 100
    rf_max_depth: int = 10
    rf_min_samples_split: int = 5
    
    gb_n_estimators: int = 100
    gb_learning_rate: float = 0.1
    gb_max_depth: int = 6
    
    # Seuils de performance
    min_accuracy_threshold: float = 0.8
    min_training_samples: int = 50
    retrain_threshold_samples: int = 100

@dataclass
class PerformanceConfig:
    """Configuration de performance et optimisation."""
    
    # Threading
    max_workers: int = 2
    enable_async: bool = True
    
    # Mémoire
    max_memory_usage_mb: int = 1024
    clear_cache_frequency_hours: int = 12
    
    # Base de données
    db_vacuum_frequency_days: int = 7
    keep_history_days: int = 90
    
    # Logging
    log_level: str = "INFO"
    log_rotation_mb: int = 50
    log_backup_count: int = 5

class AIConfiguration:
    """Gestionnaire de configuration IA centralisé."""
    
    def __init__(self, config_dir: str = "config/"):
        """
        Initialise le gestionnaire de configuration.
        
        Args:
            config_dir: Répertoire des fichiers de configuration
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "ai_config.json"
        
        # Configurations par défaut
        self.classification = ClassificationConfig()
        self.spam_detection = SpamDetectionConfig()
        self.models = ModelConfig()
        self.performance = PerformanceConfig()
        
        # Métadonnées
        self.metadata = {
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'update_count': 0
        }
        
        # Charger la configuration existante
        self.load_configuration()
    
    def load_configuration(self) -> bool:
        """
        Charge la configuration depuis le fichier.
        
        Returns:
            True si la configuration a été chargée, False sinon
        """
        try:
            if not self.config_file.exists():
                logger.info("Fichier de configuration non trouvé, utilisation des valeurs par défaut")
                self.save_configuration()
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Charger chaque section
            if 'classification' in config_data:
                self.classification = ClassificationConfig(**config_data['classification'])
            
            if 'spam_detection' in config_data:
                self.spam_detection = SpamDetectionConfig(**config_data['spam_detection'])
            
            if 'models' in config_data:
                self.models = ModelConfig(**config_data['models'])
            
            if 'performance' in config_data:
                self.performance = PerformanceConfig(**config_data['performance'])
            
            if 'metadata' in config_data:
                self.metadata.update(config_data['metadata'])
            
            logger.info("Configuration IA chargée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur chargement configuration: {e}")
            return False
    
    def save_configuration(self) -> bool:
        """
        Sauvegarde la configuration actuelle.
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            # Mettre à jour les métadonnées
            self.metadata['last_updated'] = datetime.now().isoformat()
            self.metadata['update_count'] += 1
            
            # Préparer les données
            config_data = {
                'classification': asdict(self.classification),
                'spam_detection': asdict(self.spam_detection),
                'models': asdict(self.models),
                'performance': asdict(self.performance),
                'metadata': self.metadata
            }
            
            # Sauvegarder avec backup
            backup_file = self.config_file.with_suffix('.json.backup')
            if self.config_file.exists():
                self.config_file.rename(backup_file)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info("Configuration IA sauvegardée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")
            # Restaurer le backup si nécessaire
            if backup_file.exists() and not self.config_file.exists():
                backup_file.rename(self.config_file)
            return False
    
    def update_classification_config(self, **kwargs) -> bool:
        """Met à jour la configuration de classification."""
        try:
            for key, value in kwargs.items():
                if hasattr(self.classification, key):
                    setattr(self.classification, key, value)
                else:
                    logger.warning(f"Attribut de classification inconnu: {key}")
            
            return self.save_configuration()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour config classification: {e}")
            return False
    
    def update_spam_config(self, **kwargs) -> bool:
        """Met à jour la configuration de détection de spam."""
        try:
            for key, value in kwargs.items():
                if hasattr(self.spam_detection, key):
                    setattr(self.spam_detection, key, value)
                else:
                    logger.warning(f"Attribut de spam detection inconnu: {key}")
            
            return self.save_configuration()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour config spam: {e}")
            return False
    
    def update_model_config(self, **kwargs) -> bool:
        """Met à jour la configuration des modèles."""
        try:
            for key, value in kwargs.items():
                if hasattr(self.models, key):
                    setattr(self.models, key, value)
                else:
                    logger.warning(f"Attribut de modèle inconnu: {key}")
            
            return self.save_configuration()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour config modèles: {e}")
            return False
    
    def update_performance_config(self, **kwargs) -> bool:
        """Met à jour la configuration de performance."""
        try:
            for key, value in kwargs.items():
                if hasattr(self.performance, key):
                    setattr(self.performance, key, value)
                else:
                    logger.warning(f"Attribut de performance inconnu: {key}")
            
            return self.save_configuration()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour config performance: {e}")
            return False
    
    def get_model_path(self, model_name: str) -> Path:
        """Retourne le chemin d'un modèle."""
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        return models_dir / f"{model_name}.pkl"
    
    def get_data_path(self, data_name: str) -> Path:
        """Retourne le chemin d'un fichier de données."""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        return data_dir / data_name
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valide la configuration actuelle.
        
        Returns:
            Rapport de validation
        """
        issues = []
        warnings = []
        
        # Validation des seuils
        if not (0 <= self.classification.spam_threshold <= 1):
            issues.append("spam_threshold doit être entre 0 et 1")
        
        if not (0 <= self.classification.confidence_threshold <= 1):
            issues.append("confidence_threshold doit être entre 0 et 1")
        
        # Validation des pondérations
        total_weight = (self.classification.rule_based_weight + 
                       self.classification.ml_weight + 
                       self.classification.reputation_weight + 
                       self.classification.behavioral_weight)
        
        if abs(total_weight - 1.0) > 0.01:
            warnings.append(f"Les pondérations de classification ne somment pas à 1.0 ({total_weight:.3f})")
        
        # Validation des modèles
        if self.models.min_training_samples < 10:
            warnings.append("min_training_samples très bas, recommandé >= 50")
        
        if self.models.min_accuracy_threshold > 0.95:
            warnings.append("min_accuracy_threshold très élevé, difficile à atteindre")
        
        # Validation performance
        if self.performance.max_workers > 4:
            warnings.append("max_workers élevé, peut consommer beaucoup de ressources")
        
        if self.performance.max_memory_usage_mb < 512:
            warnings.append("max_memory_usage_mb bas, peut limiter les performances")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'total_weight': total_weight
        }
    
    def reset_to_defaults(self):
        """Remet la configuration aux valeurs par défaut."""
        self.classification = ClassificationConfig()
        self.spam_detection = SpamDetectionConfig()
        self.models = ModelConfig()
        self.performance = PerformanceConfig()
        
        self.metadata['last_updated'] = datetime.now().isoformat()
        self.metadata['update_count'] += 1
        
        self.save_configuration()
        logger.info("Configuration remise aux valeurs par défaut")
    
    def export_config(self) -> Dict[str, Any]:
        """Exporte la configuration pour partage."""
        return {
            'classification': asdict(self.classification),
            'spam_detection': asdict(self.spam_detection),
            'models': asdict(self.models),
            'performance': asdict(self.performance),
            'metadata': self.metadata
        }
    
    def import_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Importe une configuration.
        
        Args:
            config_data: Données de configuration à importer
            
        Returns:
            True si l'import a réussi
        """
        try:
            # Valider les données avant import
            if not isinstance(config_data, dict):
                raise ValueError("config_data doit être un dictionnaire")
            
            # Sauvegarder la config actuelle comme backup
            backup_config = self.export_config()
            
            try:
                # Importer chaque section
                if 'classification' in config_data:
                    self.classification = ClassificationConfig(**config_data['classification'])
                
                if 'spam_detection' in config_data:
                    self.spam_detection = SpamDetectionConfig(**config_data['spam_detection'])
                
                if 'models' in config_data:
                    self.models = ModelConfig(**config_data['models'])
                
                if 'performance' in config_data:
                    self.performance = PerformanceConfig(**config_data['performance'])
                
                # Valider la nouvelle configuration
                validation = self.validate_configuration()
                if not validation['valid']:
                    raise ValueError(f"Configuration invalide: {validation['issues']}")
                
                # Sauvegarder
                if self.save_configuration():
                    logger.info("Configuration importée avec succès")
                    return True
                else:
                    raise Exception("Erreur sauvegarde")
                
            except Exception as e:
                # Restaurer la configuration backup
                logger.error(f"Erreur import, restauration backup: {e}")
                self.import_config(backup_config)
                return False
                
        except Exception as e:
            logger.error(f"Erreur import configuration: {e}")
            return False
    
    def optimize_for_performance(self):
        """Optimise la configuration pour les performances."""
        # Réduire la cache size si peu de mémoire
        if self.performance.max_memory_usage_mb < 1024:
            self.classification.cache_max_size = 500
            self.spam_detection.enable_cache = True
        
        # Ajuster les workers selon la mémoire
        if self.performance.max_memory_usage_mb < 512:
            self.performance.max_workers = 1
        elif self.performance.max_memory_usage_mb < 1024:
            self.performance.max_workers = 2
        
        # Désactiver les modèles lourds si nécessaire
        if self.performance.max_memory_usage_mb < 512:
            self.classification.use_transformers = False
            self.models.classification_model = "distilbert-base-uncased"  # Plus léger
        
        self.save_configuration()
        logger.info("Configuration optimisée pour les performances")
    
    def optimize_for_accuracy(self):
        """Optimise la configuration pour la précision."""
        # Augmenter les seuils de confiance
        self.classification.confidence_threshold = 0.7
        self.spam_detection.spam_threshold = 0.7
        
        # Utiliser tous les modèles disponibles
        self.classification.use_transformers = True
        self.classification.use_statistical_models = True
        self.classification.use_rule_based = True
        
        # Augmenter les échantillons d'entraînement
        self.models.min_training_samples = 100
        self.models.retrain_threshold_samples = 200
        
        # Pondérations équilibrées
        self.classification.rule_based_weight = 0.3
        self.classification.ml_weight = 0.4
        self.classification.reputation_weight = 0.2
        self.classification.behavioral_weight = 0.1
        
        self.save_configuration()
        logger.info("Configuration optimisée pour la précision")
    
    def get_runtime_config(self) -> Dict[str, Any]:
        """Retourne la configuration pour utilisation runtime."""
        return {
            'classification': {
                'spam_threshold': self.classification.spam_threshold,
                'confidence_threshold': self.classification.confidence_threshold,
                'categories': self.classification.categories,
                'weights': {
                    'rule_based': self.classification.rule_based_weight,
                    'ml': self.classification.ml_weight,
                    'reputation': self.classification.reputation_weight,
                    'behavioral': self.classification.behavioral_weight
                },
                'cache_enabled': self.classification.cache_enabled,
                'cache_max_size': self.classification.cache_max_size
            },
            'spam_detection': {
                'spam_threshold': self.spam_detection.spam_threshold,
                'suspicious_threshold': self.spam_detection.suspicious_threshold,
                'weights': {
                    'content': self.spam_detection.content_analysis_weight,
                    'sender': self.spam_detection.sender_analysis_weight,
                    'ml': self.spam_detection.ml_analysis_weight,
                    'behavioral': self.spam_detection.behavioral_analysis_weight
                },
                'cache_enabled': self.spam_detection.enable_cache
            },
            'models': {
                'classification_model': self.models.classification_model,
                'spam_model': self.models.spam_model,
                'sentiment_model': self.models.sentiment_model,
                'min_accuracy': self.models.min_accuracy_threshold,
                'min_samples': self.models.min_training_samples
            },
            'performance': {
                'max_workers': self.performance.max_workers,
                'async_enabled': self.performance.enable_async,
                'max_memory_mb': self.performance.max_memory_usage_mb
            }
        }
    
    def get_config_summary(self) -> str:
        """Retourne un résumé de la configuration."""
        validation = self.validate_configuration()
        
        summary = f"""
Configuration IA - Résumé
========================

📊 Classification:
- Seuil spam: {self.classification.spam_threshold}
- Seuil confiance: {self.classification.confidence_threshold}
- Catégories: {len(self.classification.categories)}
- Cache: {"✅" if self.classification.cache_enabled else "❌"}

🛡️ Détection Spam:
- Seuil spam: {self.spam_detection.spam_threshold}
- Seuil suspect: {self.spam_detection.suspicious_threshold}
- Analyse ML: {"✅" if self.spam_detection.ml_analysis_weight > 0 else "❌"}

🤖 Modèles:
- Transformers: {"✅" if self.classification.use_transformers else "❌"}
- Modèles statistiques: {"✅" if self.classification.use_statistical_models else "❌"}
- Min échantillons: {self.models.min_training_samples}

⚡ Performance:
- Workers: {self.performance.max_workers}
- Mémoire max: {self.performance.max_memory_usage_mb} MB
- Async: {"✅" if self.performance.enable_async else "❌"}

🔍 Validation:
- Statut: {"✅ Valide" if validation['valid'] else "❌ Erreurs"}
- Issues: {len(validation['issues'])}
- Warnings: {len(validation['warnings'])}

📅 Métadonnées:
- Version: {self.metadata['version']}
- Dernière MAJ: {self.metadata['last_updated'][:19]}
- Mises à jour: {self.metadata['update_count']}
"""
        
        if validation['issues']:
            summary += f"\n❌ Problèmes:\n" + "\n".join(f"  - {issue}" for issue in validation['issues'])
        
        if validation['warnings']:
            summary += f"\n⚠️  Avertissements:\n" + "\n".join(f"  - {warning}" for warning in validation['warnings'])
        
        return summary.strip()

# Instance globale pour utilisation dans l'application
ai_config = AIConfiguration()

def get_ai_config() -> AIConfiguration:
    """Retourne l'instance de configuration IA."""
    return ai_config

def load_ai_config(config_path: Optional[str] = None) -> AIConfiguration:
    """
    Charge la configuration IA.
    
    Args:
        config_path: Chemin optionnel vers le fichier de config
        
    Returns:
        Instance de configuration
    """
    global ai_config
    
    if config_path:
        config_dir = Path(config_path).parent
        ai_config = AIConfiguration(str(config_dir))
    
    return ai_config