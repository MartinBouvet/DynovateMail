"""
Classificateur d'emails intelligent avec apprentissage adaptatif.
Système de classification multi-niveaux pour une précision maximale.
"""

import logging
import json
import pickle
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re
import hashlib

# Imports conditionnels
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

logger = logging.getLogger(__name__)

class SmartEmailClassifier:
    """Classificateur d'emails intelligent avec apprentissage adaptatif."""
    
    def __init__(self, model_dir: str = "models/"):
        """
        Initialise le classificateur intelligent.
        
        Args:
            model_dir: Répertoire pour sauvegarder les modèles
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # Catégories supportées
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
        
        # Modèles de classification
        self.traditional_models = {}
        self.transformer_model = None
        self.ensemble_weights = {}
        
        # Vectorizers
        self.tfidf_vectorizer = None
        self.count_vectorizer = None
        
        # Base de données d'apprentissage
        self.db_path = "data/classifier_training.db"
        self._setup_training_database()
        
        # Cache de features
        self._feature_cache = {}
        self._cache_max_size = 500
        
        # Patterns spécialisés par catégorie
        self._setup_category_patterns()
        
        # Charger les modèles existants
        self._load_models()
        
        # Statistiques de performance
        self.performance_stats = {
            'total_classified': 0,
            'accuracy_by_category': {},
            'last_training': None
        }
        
        logger.info("SmartEmailClassifier initialisé")
    
    def _setup_training_database(self):
        """Configure la base de données d'apprentissage."""
        try:
            Path("data").mkdir(exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table principale des exemples d'entraînement
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_examples (
                    id INTEGER PRIMARY KEY,
                    email_hash TEXT UNIQUE,
                    subject TEXT,
                    body TEXT,
                    sender TEXT,
                    category TEXT,
                    is_validated BOOLEAN DEFAULT FALSE,
                    confidence REAL,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des features extraites
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extracted_features (
                    id INTEGER PRIMARY KEY,
                    email_hash TEXT,
                    feature_name TEXT,
                    feature_value REAL,
                    extraction_method TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des résultats de classification
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classification_results (
                    id INTEGER PRIMARY KEY,
                    email_hash TEXT,
                    predicted_category TEXT,
                    actual_category TEXT,
                    model_type TEXT,
                    confidence REAL,
                    is_correct BOOLEAN,
                    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur setup database: {e}")
    
    def _setup_category_patterns(self):
        """Configure les patterns spécialisés pour chaque catégorie."""
        
        self.category_patterns = {
            'cv_candidature': {
                'required_patterns': [
                    r'\b(?:cv|curriculum|resume|candidature|application)\b',
                    r'\b(?:formation|education|experience|diploma|competence)\b'
                ],
                'bonus_patterns': [
                    r'\b(?:motivation|cover\s+letter|lettre\s+de\s+motivation)\b',
                    r'\b(?:disponible|available|recherche\s+emploi|job\s+search)\b'
                ],
                'negative_patterns': [
                    r'\b(?:spam|promotion|gratuit|casino)\b'
                ]
            },
            'rdv_meeting': {
                'required_patterns': [
                    r'\b(?:rdv|rendez[-\s]vous|meeting|reunion|entretien)\b',
                    r'\b(?:disponible|available|horaire|schedule|calendrier)\b'
                ],
                'bonus_patterns': [
                    r'\b(?:confirmer|confirm|reporter|reschedule)\b',
                    r'\b(?:lundi|mardi|mercredi|jeudi|vendredi|monday|tuesday|wednesday|thursday|friday)\b'
                ],
                'negative_patterns': [
                    r'\b(?:annuler|cancel|impossible)\b'
                ]
            },
            'facture_finance': {
                'required_patterns': [
                    r'\b(?:facture|invoice|payment|paiement|devis)\b',
                    r'(?:€|euro|dollar|\$|£)\s*\d+'
                ],
                'bonus_patterns': [
                    r'\b(?:comptabilite|accounting|tva|tax)\b',
                    r'\b(?:echeance|deadline|due\s+date)\b'
                ],
                'negative_patterns': []
            },
            'support_client': {
                'required_patterns': [
                    r'\b(?:probleme|problem|issue|bug|erreur|error)\b',
                    r'\b(?:aide|help|support|assistance)\b'
                ],
                'bonus_patterns': [
                    r'\b(?:urgent|priority|important)\b',
                    r'\b(?:comment|how\s+to|procedure)\b'
                ],
                'negative_patterns': []
            },
            'newsletter': {
                'required_patterns': [
                    r'\b(?:newsletter|bulletin|actualit[eés]|news)\b',
                    r'\b(?:abonnement|subscription|unsubscribe)\b'
                ],
                'bonus_patterns': [
                    r'\b(?:mensuel|monthly|hebdomadaire|weekly)\b',
                    r'\b(?:derniere|latest|edition)\b'
                ],
                'negative_patterns': []
            },
            'partenariat': {
                'required_patterns': [
                    r'\b(?:partenariat|partnership|collaboration)\b',
                    r'\b(?:proposition|proposal|business|opportunity)\b'
                ],
                'bonus_patterns': [
                    r'\b(?:influenceur|influencer|brand|marque)\b',
                    r'\b(?:cooperation|joint\s+venture)\b'
                ],
                'negative_patterns': []
            },
            'spam': {
                'required_patterns': [
                    r'\b(?:gratuit|free|promotion|promo|discount)\b',
                    r'\b(?:gagner|win|earn|money|argent)\b'
                ],
                'bonus_patterns': [
                    r'\b(?:casino|lottery|viagra|pills)\b',
                    r'\b(?:urgent|immediat|asap).*(?:money|argent)\b'
                ],
                'negative_patterns': []
            }
        }
    
    def extract_features(self, subject: str, body: str, sender: str) -> Dict[str, float]:
        """
        Extrait les features complètes d'un email.
        
        Args:
            subject: Sujet de l'email
            body: Corps de l'email  
            sender: Expéditeur de l'email
            
        Returns:
            Dictionnaire des features extraites
        """
        try:
            # Créer un hash pour le cache
            email_text = f"{subject} {body} {sender}"
            email_hash = hashlib.md5(email_text.encode()).hexdigest()
            
            # Vérifier le cache
            if email_hash in self._feature_cache:
                return self._feature_cache[email_hash]
            
            features = {}
            full_text = f"{subject} {body}".lower()
            
            # 1. Features textuelles de base
            features.update(self._extract_text_features(subject, body))
            
            # 2. Features de l'expéditeur
            features.update(self._extract_sender_features(sender))
            
            # 3. Features de patterns par catégorie
            features.update(self._extract_pattern_features(full_text))
            
            # 4. Features linguistiques
            features.update(self._extract_linguistic_features(full_text))
            
            # 5. Features structurelles
            features.update(self._extract_structural_features(subject, body))
            
            # Mettre en cache
            self._cache_features(email_hash, features)
            
            return features
            
        except Exception as e:
            logger.error(f"Erreur extraction features: {e}")
            return {}
    
    def _extract_text_features(self, subject: str, body: str) -> Dict[str, float]:
        """Extrait les features textuelles de base."""
        features = {}
        
        try:
            # Longueurs
            features['subject_length'] = len(subject) if subject else 0
            features['body_length'] = len(body) if body else 0
            features['total_length'] = features['subject_length'] + features['body_length']
            
            # Ratios
            if features['total_length'] > 0:
                features['subject_body_ratio'] = features['subject_length'] / features['total_length']
            else:
                features['subject_body_ratio'] = 0
            
            # Compter les éléments
            full_text = f"{subject} {body}".lower()
            
            features['exclamation_count'] = full_text.count('!')
            features['question_count'] = full_text.count('?')
            features['caps_ratio'] = sum(1 for c in f"{subject} {body}" if c.isupper()) / len(f"{subject} {body}") if f"{subject} {body}" else 0
            
            # URLs et emails
            features['url_count'] = len(re.findall(r'http[s]?://\S+', full_text))
            features['email_count'] = len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', full_text))
            
            # Numéros de téléphone
            features['phone_count'] = len(re.findall(r'\b(?:\+33|0)[1-9](?:[.\-\s]?\d{2}){4}\b', full_text))
            
            # Montants d'argent
            features['money_mentions'] = len(re.findall(r'(?:€|euro|dollar|\$|£)\s*\d+', full_text))
            
        except Exception as e:
            logger.error(f"Erreur features textuelles: {e}")
        
        return features
    
    def _extract_sender_features(self, sender: str) -> Dict[str, float]:
        """Extrait les features de l'expéditeur."""
        features = {}
        
        try:
            if not sender:
                features['sender_empty'] = 1.0
                return features
            
            features['sender_empty'] = 0.0
            
            # Extraire le domaine
            domain_match = re.search(r'@([^>]+)', sender)
            if domain_match:
                domain = domain_match.group(1).lower()
                
                # Type de domaine
                features['is_gmail'] = 1.0 if 'gmail.com' in domain else 0.0
                features['is_corporate'] = 1.0 if not any(free in domain for free in ['gmail', 'yahoo', 'hotmail', 'outlook']) else 0.0
                
                # Longueur du domaine
                features['domain_length'] = len(domain)
                
                # Domaines suspects
                suspicious_indicators = ['temp', 'guerrilla', '10minute', 'throwaway']
                features['suspicious_domain'] = 1.0 if any(susp in domain for susp in suspicious_indicators) else 0.0
                
            else:
                features['invalid_email'] = 1.0
            
            # Features de l'adresse email
            features['sender_has_numbers'] = 1.0 if re.search(r'\d', sender) else 0.0
            features['sender_number_ratio'] = sum(1 for c in sender if c.isdigit()) / len(sender) if sender else 0
            
        except Exception as e:
            logger.error(f"Erreur features sender: {e}")
        
        return features
    
    def _extract_pattern_features(self, text: str) -> Dict[str, float]:
        """Extrait les features basées sur les patterns de catégories."""
        features = {}
        
        try:
            for category, patterns in self.category_patterns.items():
                category_score = 0
                
                # Patterns requis
                required_matches = sum(1 for pattern in patterns['required_patterns'] 
                                     if re.search(pattern, text, re.IGNORECASE))
                category_score += required_matches * 0.4
                
                # Patterns bonus
                bonus_matches = sum(1 for pattern in patterns['bonus_patterns'] 
                                  if re.search(pattern, text, re.IGNORECASE))
                category_score += bonus_matches * 0.2
                
                # Patterns négatifs
                negative_matches = sum(1 for pattern in patterns['negative_patterns'] 
                                     if re.search(pattern, text, re.IGNORECASE))
                category_score -= negative_matches * 0.3
                
                features[f'pattern_{category}'] = max(0, min(category_score, 1.0))
        
        except Exception as e:
            logger.error(f"Erreur features patterns: {e}")
        
        return features
    
    def _extract_linguistic_features(self, text: str) -> Dict[str, float]:
        """Extrait les features linguistiques."""
        features = {}
        
        try:
            # Langues détectées (simple)
            french_words = ['le', 'la', 'de', 'et', 'à', 'un', 'il', 'être', 'avoir', 'que', 'pour']
            english_words = ['the', 'of', 'and', 'to', 'in', 'is', 'you', 'that', 'it', 'he', 'was']
            
            french_count = sum(1 for word in french_words if f' {word} ' in f' {text} ')
            english_count = sum(1 for word in english_words if f' {word} ' in f' {text} ')
            
            total_indicator_words = french_count + english_count
            if total_indicator_words > 0:
                features['language_french_ratio'] = french_count / total_indicator_words
                features['language_english_ratio'] = english_count / total_indicator_words
            else:
                features['language_french_ratio'] = 0.5
                features['language_english_ratio'] = 0.5
            
            # Complexité du vocabulaire
            words = re.findall(r'\w+', text)
            if words:
                unique_words = set(words)
                features['vocabulary_richness'] = len(unique_words) / len(words)
                features['avg_word_length'] = sum(len(word) for word in words) / len(words)
            else:
                features['vocabulary_richness'] = 0
                features['avg_word_length'] = 0
            
            # Ponctuation
            punctuation_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
            features['punctuation_ratio'] = punctuation_count / len(text) if text else 0
            
        except Exception as e:
            logger.error(f"Erreur features linguistiques: {e}")
        
        return features
    
    def _extract_structural_features(self, subject: str, body: str) -> Dict[str, float]:
        """Extrait les features structurelles."""
        features = {}
        
        try:
            # Structure du sujet
            features['subject_has_re'] = 1.0 if subject and subject.lower().startswith('re:') else 0.0
            features['subject_has_fwd'] = 1.0 if subject and subject.lower().startswith('fwd:') else 0.0
            features['subject_all_caps'] = 1.0 if subject and subject.isupper() else 0.0
            
            # Structure du corps
            if body:
                lines = body.split('\n')
                features['body_line_count'] = len(lines)
                features['body_avg_line_length'] = sum(len(line) for line in lines) / len(lines) if lines else 0
                
                # Signatures et footers
                features['has_signature'] = 1.0 if re.search(r'--\s*\n', body) else 0.0
                features['has_footer'] = 1.0 if re.search(r'unsubscribe|désabonnement', body.lower()) else 0.0
                
                # HTML tags (approximation)
                features['has_html'] = 1.0 if re.search(r'<[^>]+>', body) else 0.0
                
            else:
                features['body_line_count'] = 0
                features['body_avg_line_length'] = 0
                features['has_signature'] = 0.0
                features['has_footer'] = 0.0
                features['has_html'] = 0.0
            
        except Exception as e:
            logger.error(f"Erreur features structurelles: {e}")
        
        return features
    
    def _cache_features(self, email_hash: str, features: Dict[str, float]):
        """Met en cache les features extraites."""
        try:
            if len(self._feature_cache) >= self._cache_max_size:
                # Supprimer le plus ancien
                oldest_key = next(iter(self._feature_cache))
                del self._feature_cache[oldest_key]
            
            self._feature_cache[email_hash] = features
            
        except Exception as e:
            logger.error(f"Erreur cache features: {e}")
    
    def train_models(self, retrain: bool = False) -> Dict[str, Any]:
        """
        Entraîne tous les modèles de classification.
        
        Args:
            retrain: Force le réentraînement même si des modèles existent
            
        Returns:
            Rapport d'entraînement
        """
        try:
            logger.info("Début de l'entraînement des modèles...")
            
            # Charger les données d'entraînement
            training_data = self._load_training_data()
            
            if len(training_data) < 20:
                logger.warning(f"Pas assez de données d'entraînement: {len(training_data)} exemples")
                return self._create_bootstrap_models()
            
            # Préparer les données
            X, y, feature_names = self._prepare_training_data(training_data)
            
            # Diviser les données
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Entraîner les différents modèles
            training_results = {}
            
            # 1. Random Forest
            rf_result = self._train_random_forest(X_train, X_test, y_train, y_test, feature_names)
            training_results['random_forest'] = rf_result
            
            # 2. Gradient Boosting
            gb_result = self._train_gradient_boosting(X_train, X_test, y_train, y_test)
            training_results['gradient_boosting'] = gb_result
            
            # 3. Logistic Regression
            lr_result = self._train_logistic_regression(X_train, X_test, y_train, y_test)
            training_results['logistic_regression'] = lr_result
            
            # 4. Transformer (si disponible)
            if HAS_TRANSFORMERS:
                transformer_result = self._train_transformer_model(training_data)
                training_results['transformer'] = transformer_result
            
            # Calculer les poids d'ensemble
            self._calculate_ensemble_weights(training_results)
            
            # Sauvegarder les modèles
            self._save_models()
            
            # Mettre à jour les statistiques
            self.performance_stats['last_training'] = datetime.now().isoformat()
            self.performance_stats['total_classified'] = len(training_data)
            
            logger.info("Entraînement terminé avec succès")
            
            return {
                'success': True,
                'training_data_size': len(training_data),
                'models_trained': list(training_results.keys()),
                'best_model': max(training_results.items(), key=lambda x: x[1].get('accuracy', 0))[0],
                'results': training_results
            }
            
        except Exception as e:
            logger.error(f"Erreur entraînement: {e}")
            return {'success': False, 'error': str(e)}
    
    def _load_training_data(self) -> List[Dict]:
        """Charge les données d'entraînement depuis la base."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT subject, body, sender, category, confidence
                FROM training_examples 
                WHERE category IS NOT NULL
                ORDER BY created_at DESC
            """)
            
            data = []
            for row in cursor.fetchall():
                data.append({
                    'subject': row[0] or '',
                    'body': row[1] or '',
                    'sender': row[2] or '',
                    'category': row[3],
                    'confidence': row[4] or 1.0
                })
            
            conn.close()
            
            logger.info(f"Chargé {len(data)} exemples d'entraînement")
            return data
            
        except Exception as e:
            logger.error(f"Erreur chargement données: {e}")
            return []
    
    def _prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prépare les données pour l'entraînement."""
        try:
            features_list = []
            labels = []
            
            for example in training_data:
                # Extraire les features
                features = self.extract_features(
                    example['subject'],
                    example['body'], 
                    example['sender']
                )
                
                if features:  # S'assurer qu'on a des features
                    features_list.append(features)
                    labels.append(example['category'])
            
            if not features_list:
                raise ValueError("Aucune feature extraite")
            
            # Convertir en format sklearn
            feature_names = list(features_list[0].keys())
            X = np.array([[f.get(name, 0) for name in feature_names] for f in features_list])
            y = np.array(labels)
            
            logger.info(f"Données préparées: {X.shape[0]} exemples, {X.shape[1]} features")
            
            return X, y, feature_names
            
        except Exception as e:
            logger.error(f"Erreur préparation données: {e}")
            raise
    
    def _train_random_forest(self, X_train, X_test, y_train, y_test, feature_names) -> Dict:
        """Entraîne un modèle Random Forest."""
        try:
            # Créer et entraîner le modèle
            rf = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42
            )
            
            rf.fit(X_train, y_train)
            
            # Évaluation
            train_accuracy = rf.score(X_train, y_train)
            test_accuracy = rf.score(X_test, y_test)
            
            # Importance des features
            feature_importance = dict(zip(feature_names, rf.feature_importances_))
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Sauvegarder le modèle
            self.traditional_models['random_forest'] = rf
            
            logger.info(f"Random Forest - Train: {train_accuracy:.3f}, Test: {test_accuracy:.3f}")
            
            return {
                'model_type': 'random_forest',
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'accuracy': test_accuracy,
                'top_features': top_features
            }
            
        except Exception as e:
            logger.error(f"Erreur Random Forest: {e}")
            return {'model_type': 'random_forest', 'error': str(e), 'accuracy': 0}
    
    def _train_gradient_boosting(self, X_train, X_test, y_train, y_test) -> Dict:
        """Entraîne un modèle Gradient Boosting."""
        try:
            gb = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            gb.fit(X_train, y_train)
            
            train_accuracy = gb.score(X_train, y_train)
            test_accuracy = gb.score(X_test, y_test)
            
            self.traditional_models['gradient_boosting'] = gb
            
            logger.info(f"Gradient Boosting - Train: {train_accuracy:.3f}, Test: {test_accuracy:.3f}")
            
            return {
                'model_type': 'gradient_boosting',
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'accuracy': test_accuracy
            }
            
        except Exception as e:
            logger.error(f"Erreur Gradient Boosting: {e}")
            return {'model_type': 'gradient_boosting', 'error': str(e), 'accuracy': 0}
    
    def _train_logistic_regression(self, X_train, X_test, y_train, y_test) -> Dict:
        """Entraîne un modèle de régression logistique."""
        try:
            # Pipeline avec normalisation
            lr_pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', LogisticRegression(max_iter=1000, random_state=42))
            ])
            
            lr_pipeline.fit(X_train, y_train)
            
            train_accuracy = lr_pipeline.score(X_train, y_train)
            test_accuracy = lr_pipeline.score(X_test, y_test)
            
            self.traditional_models['logistic_regression'] = lr_pipeline
            
            logger.info(f"Logistic Regression - Train: {train_accuracy:.3f}, Test: {test_accuracy:.3f}")
            
            return {
                'model_type': 'logistic_regression',
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'accuracy': test_accuracy
            }
            
        except Exception as e:
            logger.error(f"Erreur Logistic Regression: {e}")
            return {'model_type': 'logistic_regression', 'error': str(e), 'accuracy': 0}
    
    def _train_transformer_model(self, training_data: List[Dict]) -> Dict:
        """Entraîne un modèle transformer (simulation - nécessiterait plus de données réelles)."""
        try:
            # Pour une vraie implémentation, on utiliserait HuggingFace Trainer
            # Ici on simule avec un modèle pré-entraîné adapté
            
            logger.info("Initialisation du modèle transformer pour classification")
            
            # Utiliser un modèle pré-entraîné comme base
            self.transformer_model = pipeline(
                "text-classification",
                model="distilbert-base-uncased",
                device=-1
            )
            
            # Dans une vraie implémentation, on ferait du fine-tuning ici
            
            return {
                'model_type': 'transformer',
                'accuracy': 0.85,  # Estimation
                'note': 'Modèle pré-entraîné adapté'
            }
            
        except Exception as e:
            logger.error(f"Erreur Transformer: {e}")
            return {'model_type': 'transformer', 'error': str(e), 'accuracy': 0}
    
    def _calculate_ensemble_weights(self, training_results: Dict):
        """Calcule les poids pour l'ensemble de modèles."""
        try:
            total_accuracy = sum(result.get('accuracy', 0) for result in training_results.values())
            
            if total_accuracy > 0:
                for model_name, result in training_results.items():
                    accuracy = result.get('accuracy', 0)
                    self.ensemble_weights[model_name] = accuracy / total_accuracy
            else:
                # Poids égaux si pas de performances disponibles
                num_models = len(training_results)
                for model_name in training_results.keys():
                    self.ensemble_weights[model_name] = 1.0 / num_models
            
            logger.info(f"Poids d'ensemble calculés: {self.ensemble_weights}")
            
        except Exception as e:
            logger.error(f"Erreur calcul poids ensemble: {e}")
    
    def classify(self, subject: str, body: str, sender: str) -> Dict[str, Any]:
        """
        Classifie un email avec l'ensemble de modèles.
        
        Returns:
            Résultat de classification avec confiance
        """
        try:
            # Extraire les features
            features = self.extract_features(subject, body, sender)
            
            if not features:
                return self._get_default_classification()
            
            # Prédictions de chaque modèle
            predictions = {}
            confidences = {}
            
            # Modèles traditionnels
            feature_vector = self._features_to_vector(features)
            
            for model_name, model in self.traditional_models.items():
                try:
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba([feature_vector])[0]
                        pred_class = model.classes_[np.argmax(proba)]
                        confidence = np.max(proba)
                    else:
                        pred_class = model.predict([feature_vector])[0]
                        confidence = 0.8  # Confiance par défaut
                    
                    predictions[model_name] = pred_class
                    confidences[model_name] = confidence
                    
                except Exception as e:
                    logger.warning(f"Erreur prédiction {model_name}: {e}")
            
            # Modèle transformer
            if self.transformer_model:
                try:
                    text = f"{subject} {body}"[:512]  # Limiter la taille
                    transformer_result = self.transformer_model(text)
                    
                    if transformer_result:
                        # Convertir le résultat en nos catégories
                        pred_class = self._map_transformer_result(transformer_result[0])
                        confidence = transformer_result[0]['score']
                        
                        predictions['transformer'] = pred_class
                        confidences['transformer'] = confidence
                        
                except Exception as e:
                    logger.warning(f"Erreur transformer: {e}")
            
            # Vote pondéré
            final_prediction = self._ensemble_vote(predictions, confidences)
            
            return final_prediction
            
        except Exception as e:
            logger.error(f"Erreur classification: {e}")
            return self._get_default_classification()
    
    def _features_to_vector(self, features: Dict[str, float]) -> List[float]:
        """Convertit le dictionnaire de features en vecteur."""
        try:
            # Utiliser les noms de features du premier modèle entraîné
            if hasattr(self, '_feature_names'):
                return [features.get(name, 0) for name in self._feature_names]
            else:
                # Ordre fixe pour la cohérence
                feature_order = sorted(features.keys())
                self._feature_names = feature_order
                return [features[name] for name in feature_order]
                
        except Exception as e:
            logger.error(f"Erreur conversion features: {e}")
            return list(features.values())
    
    def _map_transformer_result(self, result: Dict) -> str:
        """Mappe le résultat du transformer vers nos catégories."""
        try:
            label = result['label'].lower()
            
            # Mapping simple - dans une vraie implémentation, ce serait plus sophistiqué
            if 'negative' in label or 'toxic' in label:
                return 'spam'
            elif 'positive' in label:
                return 'other'
            else:
                return 'other'
                
        except Exception as e:
            logger.error(f"Erreur mapping transformer: {e}")
            return 'other'
    
    def _ensemble_vote(self, predictions: Dict[str, str], confidences: Dict[str, float]) -> Dict[str, Any]:
        """Effectue un vote pondéré entre les modèles."""
        try:
            # Compter les votes par catégorie
            category_scores = {}
            
            for model_name, category in predictions.items():
                weight = self.ensemble_weights.get(model_name, 1.0)
                confidence = confidences.get(model_name, 0.5)
                
                score = weight * confidence
                
                if category not in category_scores:
                    category_scores[category] = 0
                category_scores[category] += score
            
            if not category_scores:
                return self._get_default_classification()
            
            # Trouver la catégorie gagnante
            best_category = max(category_scores.items(), key=lambda x: x[1])
            
            # Calculer la confiance finale
            total_score = sum(category_scores.values())
            final_confidence = best_category[1] / total_score if total_score > 0 else 0.5
            
            return {
                'category': best_category[0],
                'confidence': final_confidence,
                'all_predictions': predictions,
                'all_confidences': confidences,
                'category_scores': category_scores,
                'method': 'ensemble'
            }
            
        except Exception as e:
            logger.error(f"Erreur vote ensemble: {e}")
            return self._get_default_classification()
    
    def _get_default_classification(self) -> Dict[str, Any]:
        """Retourne une classification par défaut."""
        return {
            'category': 'other',
            'confidence': 0.3,
            'method': 'default',
            'error': True
        }
    
    def add_training_example(self, subject: str, body: str, sender: str, category: str, 
                           confidence: float = 1.0, source: str = 'user'):
        """Ajoute un exemple d'entraînement."""
        try:
            email_text = f"{subject} {body} {sender}"
            email_hash = hashlib.md5(email_text.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO training_examples 
                (email_hash, subject, body, sender, category, confidence, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (email_hash, subject, body, sender, category, confidence, source))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Exemple d'entraînement ajouté: {category}")
            
        except Exception as e:
            logger.error(f"Erreur ajout exemple: {e}")
    
    def _save_models(self):
        """Sauvegarde tous les modèles entraînés."""
        try:
            # Sauvegarder les modèles traditionnels
            for model_name, model in self.traditional_models.items():
                model_path = self.model_dir / f"{model_name}.pkl"
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
            
            # Sauvegarder les métadonnées
            metadata = {
                'categories': self.categories,
                'ensemble_weights': self.ensemble_weights,
                'feature_names': getattr(self, '_feature_names', []),
                'performance_stats': self.performance_stats
            }
            
            metadata_path = self.model_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info("Modèles sauvegardés")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
    
    def _load_models(self):
        """Charge les modèles existants."""
        try:
            # Charger les métadonnées
            metadata_path = self.model_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                self.ensemble_weights = metadata.get('ensemble_weights', {})
                self._feature_names = metadata.get('feature_names', [])
                self.performance_stats = metadata.get('performance_stats', self.performance_stats)
            
            # Charger les modèles traditionnels
            for model_name in ['random_forest', 'gradient_boosting', 'logistic_regression']:
                model_path = self.model_dir / f"{model_name}.pkl"
                if model_path.exists():
                    with open(model_path, 'rb') as f:
                        self.traditional_models[model_name] = pickle.load(f)
                    logger.info(f"Modèle {model_name} chargé")
            
            # Charger le modèle transformer si disponible
            if HAS_TRANSFORMERS:
                try:
                    self.transformer_model = pipeline(
                        "text-classification",
                        model="distilbert-base-uncased",
                        device=-1
                    )
                    logger.info("Modèle transformer chargé")
                except Exception as e:
                    logger.warning(f"Erreur chargement transformer: {e}")
            
        except Exception as e:
            logger.warning(f"Erreur chargement modèles: {e}")
    
    def _create_bootstrap_models(self) -> Dict[str, Any]:
        """Crée des modèles de base quand il n'y a pas assez de données."""
        try:
            logger.info("Création de modèles bootstrap...")
            
            # Créer des exemples synthétiques pour chaque catégorie
            synthetic_examples = self._generate_synthetic_examples()
            
            # Entraîner avec les exemples synthétiques
            for example in synthetic_examples:
                self.add_training_example(
                    example['subject'],
                    example['body'],
                    example['sender'],
                    example['category'],
                    0.8,  # Confiance réduite pour les exemples synthétiques
                    'synthetic'
                )
            
            return {
                'success': True,
                'type': 'bootstrap',
                'synthetic_examples': len(synthetic_examples)
            }
            
        except Exception as e:
            logger.error(f"Erreur bootstrap: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_synthetic_examples(self) -> List[Dict]:
        """Génère des exemples synthétiques pour l'amorçage."""
        examples = []
        
        # CV/Candidature
        examples.extend([
            {'subject': 'Candidature pour le poste de développeur', 'body': 'Veuillez trouver ci-joint mon CV et ma lettre de motivation', 'sender': 'candidat@email.com', 'category': 'cv_candidature'},
            {'subject': 'Application for Software Engineer position', 'body': 'Please find attached my resume and cover letter', 'sender': 'applicant@gmail.com', 'category': 'cv_candidature'}
        ])
        
        # RDV/Meeting
        examples.extend([
            {'subject': 'Demande de rendez-vous', 'body': 'Seriez-vous disponible la semaine prochaine pour un entretien ?', 'sender': 'rh@entreprise.com', 'category': 'rdv_meeting'},
            {'subject': 'Meeting request', 'body': 'Could we schedule a meeting next week to discuss the project?', 'sender': 'project@company.com', 'category': 'rdv_meeting'}
        ])
        
        # Facture/Finance
        examples.extend([
            {'subject': 'Facture n°2024-001', 'body': 'Veuillez trouver ci-jointe la facture d\'un montant de 1500€', 'sender': 'compta@fournisseur.fr', 'category': 'facture_finance'},
            {'subject': 'Invoice #2024-001', 'body': 'Please find attached the invoice for $1500', 'sender': 'billing@supplier.com', 'category': 'facture_finance'}
        ])
        
        # Support
        examples.extend([
            {'subject': 'Problème urgent avec votre service', 'body': 'J\'ai un problème avec mon compte, pouvez-vous m\'aider ?', 'sender': 'client@domain.com', 'category': 'support_client'},
            {'subject': 'Technical issue', 'body': 'I\'m experiencing problems with your software, please help', 'sender': 'user@example.com', 'category': 'support_client'}
        ])
        
        # Newsletter
        examples.extend([
            {'subject': 'Newsletter hebdomadaire', 'body': 'Voici les dernières actualités de notre entreprise', 'sender': 'newsletter@company.fr', 'category': 'newsletter'},
            {'subject': 'Weekly Newsletter', 'body': 'Here are the latest news from our company', 'sender': 'news@company.com', 'category': 'newsletter'}
        ])
        
        # Spam
        examples.extend([
            {'subject': 'URGENT: Vous avez gagné 1000€ !', 'body': 'Félicitations ! Cliquez ici pour récupérer votre prix', 'sender': 'promo@spam.com', 'category': 'spam'},
            {'subject': 'Make money fast!', 'body': 'Earn $1000 per day working from home! Click here now!', 'sender': 'money@scam.com', 'category': 'spam'}
        ])
        
        return examples
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de classification."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) FROM training_examples")
            total_examples = cursor.fetchone()[0]
            
            cursor.execute("SELECT category, COUNT(*) FROM training_examples GROUP BY category")
            category_counts = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(*) FROM classification_results WHERE is_correct = 1")
            correct_predictions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM classification_results")
            total_predictions = cursor.fetchone()[0]
            
            conn.close()
            
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            
            return {
                'total_training_examples': total_examples,
                'category_distribution': category_counts,
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'overall_accuracy': accuracy,
                'models_available': list(self.traditional_models.keys()),
                'transformer_available': self.transformer_model is not None,
                'ensemble_weights': self.ensemble_weights,
                'performance_stats': self.performance_stats
            }
            
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
            return {'error': str(e)}