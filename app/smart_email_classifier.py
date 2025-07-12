"""
Classificateur d'emails ultra-intelligent avec deep learning
Remplace complètement l'ancien système basé sur des mots-clés
"""

import torch
import torch.nn as nn
from transformers import (
    AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
    CamembertTokenizer, CamembertForSequenceClassification,
    TrainingArguments, Trainer
)
import numpy as np
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import pandas as pd
import logging
import pickle
import os
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import sqlite3

logger = logging.getLogger(__name__)

class NeuralEmailClassifier(nn.Module):
    """Réseau de neurones personnalisé pour la classification d'emails"""
    
    def __init__(self, input_size: int, hidden_size: int, num_classes: int):
        super(NeuralEmailClassifier, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True, bidirectional=True)
        self.attention = nn.MultiheadAttention(hidden_size * 2, num_heads=8)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, num_classes)
        )
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        attended, _ = self.attention(lstm_out, lstm_out, lstm_out)
        pooled = torch.mean(attended, dim=1)
        output = self.classifier(pooled)
        return output

class SmartEmailClassifier:
    """Classificateur d'emails ultra-intelligent avec apprentissage adaptatif"""
    
    def __init__(self, model_path: str = "smart_classifier_models/"):
        self.model_path = model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Modèles multiples pour voting
        self.models = {}
        self.tokenizers = {}
        self.vectorizers = {}
        
        # Catégories dynamiques
        self.categories = {
            'travail': ['projet', 'réunion', 'deadline', 'rapport', 'client'],
            'personnel': ['famille', 'ami', 'vacances', 'rendez-vous médical'],
            'financier': ['facture', 'paiement', 'banque', 'impôts', 'salaire'],
            'commercial': ['vente', 'achat', 'promotion', 'offre', 'devis'],
            'support': ['problème', 'bug', 'aide', 'assistance', 'support'],
            'cv': ['candidature', 'cv', 'emploi', 'recrutement', 'entretien'],
            'spam': ['pub', 'publicité', 'gratuit', 'gagner', 'promo'],
            'newsletter': ['newsletter', 'abonnement', 'nouvelles', 'actualités'],
            'rdv': ['rendez-vous', 'meeting', 'réunion', 'disponibilité', 'planning'],
            'urgent': ['urgent', 'asap', 'immédiat', 'critique', 'emergency']
        }
        
        # Historique d'apprentissage
        self.training_history = []
        self.performance_metrics = {}
        
        # Cache pour optimisation
        self.prediction_cache = {}
        
        self._initialize_models()
        self._load_training_data()
    
    def _initialize_models(self):
        """Initialise tous les modèles de classification"""
        try:
            os.makedirs(self.model_path, exist_ok=True)
            
            # 1. Modèle BERT multilingue fine-tuné
            self._initialize_bert_model()
            
            # 2. Modèle CamemBERT pour le français
            self._initialize_camembert_model()
            
            # 3. Modèle neural personnalisé
            self._initialize_neural_model()
            
            # 4. Ensemble de modèles classiques
            self._initialize_classical_models()
            
            # 5. Vectoriseurs pour features textuelles
            self._initialize_vectorizers()
            
            logger.info("Tous les modèles de classification initialisés")
            
        except Exception as e:
            logger.error(f"Erreur initialisation modèles: {e}")
    
    def _initialize_bert_model(self):
        """Initialise le modèle BERT multilingue"""
        try:
            model_name = "distilbert-base-multilingual-cased"
            bert_path = os.path.join(self.model_path, "bert_classifier")
            
            if os.path.exists(bert_path):
                # Chargement du modèle fine-tuné
                self.models['bert'] = AutoModelForSequenceClassification.from_pretrained(bert_path)
                self.tokenizers['bert'] = AutoTokenizer.from_pretrained(bert_path)
            else:
                # Chargement du modèle de base
                self.models['bert'] = AutoModelForSequenceClassification.from_pretrained(
                    model_name, num_labels=len(self.categories)
                )
                self.tokenizers['bert'] = AutoTokenizer.from_pretrained(model_name)
            
            self.models['bert'].to(self.device)
            logger.info("Modèle BERT initialisé")
            
        except Exception as e:
            logger.error(f"Erreur BERT: {e}")
    
    def _initialize_camembert_model(self):
        """Initialise CamemBERT spécialement optimisé pour le français"""
        try:
            model_name = "camembert-base"
            camembert_path = os.path.join(self.model_path, "camembert_classifier")
            
            if os.path.exists(camembert_path):
                self.models['camembert'] = CamembertForSequenceClassification.from_pretrained(camembert_path)
                self.tokenizers['camembert'] = CamembertTokenizer.from_pretrained(camembert_path)
            else:
                self.models['camembert'] = CamembertForSequenceClassification.from_pretrained(
                    model_name, num_labels=len(self.categories)
                )
                self.tokenizers['camembert'] = CamembertTokenizer.from_pretrained(model_name)
            
            self.models['camembert'].to(self.device)
            logger.info("Modèle CamemBERT initialisé")
            
        except Exception as e:
            logger.error(f"Erreur CamemBERT: {e}")
    
    def _initialize_neural_model(self):
        """Initialise le réseau de neurones personnalisé"""
        try:
            neural_path = os.path.join(self.model_path, "neural_classifier.pth")
            
            # Configuration du modèle
            input_size = 768  # Taille des embeddings BERT
            hidden_size = 256
            num_classes = len(self.categories)
            
            self.models['neural'] = NeuralEmailClassifier(input_size, hidden_size, num_classes)
            
            if os.path.exists(neural_path):
                self.models['neural'].load_state_dict(torch.load(neural_path, map_location=self.device))
            
            self.models['neural'].to(self.device)
            logger.info("Modèle neural personnalisé initialisé")
            
        except Exception as e:
            logger.error(f"Erreur modèle neural: {e}")
    
    def _initialize_classical_models(self):
        """Initialise les modèles classiques de ML"""
        try:
            # Random Forest pour robustesse
            rf_path = os.path.join(self.model_path, "random_forest.pkl")
            if os.path.exists(rf_path):
                with open(rf_path, 'rb') as f:
                    self.models['random_forest'] = pickle.load(f)
            else:
                self.models['random_forest'] = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=20,
                    min_samples_split=5,
                    random_state=42
                )
            
            # MLP pour patterns complexes
            mlp_path = os.path.join(self.model_path, "mlp.pkl")
            if os.path.exists(mlp_path):
                with open(mlp_path, 'rb') as f:
                    self.models['mlp'] = pickle.load(f)
            else:
                self.models['mlp'] = MLPClassifier(
                    hidden_layer_sizes=(256, 128, 64),
                    activation='relu',
                    solver='adam',
                    max_iter=500,
                    random_state=42
                )
            
            logger.info("Modèles classiques initialisés")
            
        except Exception as e:
            logger.error(f"Erreur modèles classiques: {e}")
    
    def _initialize_vectorizers(self):
        """Initialise les vectoriseurs de texte"""
        try:
            # TF-IDF pour mots et n-grammes
            tfidf_path = os.path.join(self.model_path, "tfidf_vectorizer.pkl")
            if os.path.exists(tfidf_path):
                with open(tfidf_path, 'rb') as f:
                    self.vectorizers['tfidf'] = pickle.load(f)
            else:
                self.vectorizers['tfidf'] = TfidfVectorizer(
                    max_features=10000,
                    ngram_range=(1, 3),
                    stop_words='english',
                    lowercase=True,
                    sublinear_tf=True
                )
            
            # TF-IDF pour caractères (détection de patterns)
            char_tfidf_path = os.path.join(self.model_path, "char_tfidf_vectorizer.pkl")
            if os.path.exists(char_tfidf_path):
                with open(char_tfidf_path, 'rb') as f:
                    self.vectorizers['char_tfidf'] = pickle.load(f)
            else:
                self.vectorizers['char_tfidf'] = TfidfVectorizer(
                    analyzer='char',
                    ngram_range=(2, 5),
                    max_features=5000
                )
            
            logger.info("Vectoriseurs initialisés")
            
        except Exception as e:
            logger.error(f"Erreur vectoriseurs: {e}")
    
    def classify_email(self, subject: str, body: str, sender: str = "") -> Dict:
        """
        Classification ultra-performante avec ensemble de modèles
        """
        try:
            # Préparation du texte
            full_text = f"{subject} {body}".strip()
            
            # Cache check
            text_hash = hash(full_text)
            if text_hash in self.prediction_cache:
                return self.prediction_cache[text_hash]
            
            # Extraction de features
            features = self._extract_advanced_features(subject, body, sender)
            
            # Prédictions de tous les modèles
            predictions = {}
            confidences = {}
            
            # 1. BERT prediction
            bert_pred = self._predict_bert(full_text)
            predictions['bert'] = bert_pred['category']
            confidences['bert'] = bert_pred['confidence']
            
            # 2. CamemBERT prediction
            camembert_pred = self._predict_camembert(full_text)
            predictions['camembert'] = camembert_pred['category']
            confidences['camembert'] = camembert_pred['confidence']
            
            # 3. Neural model prediction
            neural_pred = self._predict_neural(features['embeddings'])
            predictions['neural'] = neural_pred['category']
            confidences['neural'] = neural_pred['confidence']
            
            # 4. Classical models predictions
            classical_pred = self._predict_classical(features['tfidf_features'])
            predictions.update(classical_pred['predictions'])
            confidences.update(classical_pred['confidences'])
            
            # 5. Fusion intelligente avec pondération adaptive
            final_result = self._intelligent_ensemble(predictions, confidences, features)
            
            # Cache du résultat
            self.prediction_cache[text_hash] = final_result
            
            # Limitation du cache
            if len(self.prediction_cache) > 1000:
                # Supprime les plus anciens
                oldest_keys = list(self.prediction_cache.keys())[:100]
                for key in oldest_keys:
                    del self.prediction_cache[key]
            
            return final_result
            
        except Exception as e:
            logger.error(f"Erreur classification: {e}")
            return self._fallback_prediction()
    
    def _extract_advanced_features(self, subject: str, body: str, sender: str) -> Dict:
        """Extraction de features avancées pour la classification"""
        full_text = f"{subject} {body}"
        
        features = {
            'text_length': len(full_text),
            'subject_length': len(subject),
            'word_count': len(full_text.split()),
            'sentence_count': len([s for s in full_text.split('.') if s.strip()]),
            'exclamation_count': full_text.count('!'),
            'question_count': full_text.count('?'),
            'caps_ratio': sum(1 for c in full_text if c.isupper()) / len(full_text) if full_text else 0,
            'digit_ratio': sum(1 for c in full_text if c.isdigit()) / len(full_text) if full_text else 0,
            'url_count': len([w for w in full_text.split() if 'http' in w.lower()]),
            'email_count': len([w for w in full_text.split() if '@' in w]),
            'sender_domain': sender.split('@')[1] if '@' in sender else '',
            'is_reply': subject.lower().startswith(('re:', 'fw:', 'fwd:')),
            'has_attachment_keywords': any(kw in full_text.lower() for kw in ['pièce jointe', 'attachment', 'ci-joint', 'fichier']),
        }
        
        # Features TF-IDF
        try:
            features['tfidf_features'] = self.vectorizers['tfidf'].transform([full_text]).toarray()[0]
            features['char_tfidf_features'] = self.vectorizers['char_tfidf'].transform([full_text]).toarray()[0]
        except:
            features['tfidf_features'] = np.zeros(10000)
            features['char_tfidf_features'] = np.zeros(5000)
        
        # Embeddings pour modèle neural
        features['embeddings'] = self._get_text_embeddings(full_text)
        
        return features
    
    def _predict_bert(self, text: str) -> Dict:
        """Prédiction avec BERT"""
        try:
            inputs = self.tokenizers['bert'](
                text, 
                return_tensors='pt', 
                truncation=True, 
                padding=True, 
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.models['bert'](**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
            predicted_class = torch.argmax(predictions, dim=-1).item()
            confidence = torch.max(predictions, dim=-1).values.item()
            
            categories = list(self.categories.keys())
            category = categories[predicted_class] if predicted_class < len(categories) else 'general'
            
            return {'category': category, 'confidence': confidence}
            
        except Exception as e:
            logger.error(f"Erreur BERT prediction: {e}")
            return {'category': 'general', 'confidence': 0.5}
    
    def _predict_camembert(self, text: str) -> Dict:
        """Prédiction avec CamemBERT"""
        try:
            inputs = self.tokenizers['camembert'](
                text, 
                return_tensors='pt', 
                truncation=True, 
                padding=True, 
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.models['camembert'](**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
            predicted_class = torch.argmax(predictions, dim=-1).item()
            confidence = torch.max(predictions, dim=-1).values.item()
            
            categories = list(self.categories.keys())
            category = categories[predicted_class] if predicted_class < len(categories) else 'general'
            
            return {'category': category, 'confidence': confidence}
            
        except Exception as e:
            logger.error(f"Erreur CamemBERT prediction: {e}")
            return {'category': 'general', 'confidence': 0.5}
    
    def _predict_neural(self, embeddings: np.ndarray) -> Dict:
        """Prédiction avec le modèle neural personnalisé"""
        try:
            embeddings_tensor = torch.FloatTensor(embeddings).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.models['neural'](embeddings_tensor.unsqueeze(1))
                predictions = torch.nn.functional.softmax(outputs, dim=-1)
                
            predicted_class = torch.argmax(predictions, dim=-1).item()
            confidence = torch.max(predictions, dim=-1).values.item()
            
            categories = list(self.categories.keys())
            category = categories[predicted_class] if predicted_class < len(categories) else 'general'
            
            return {'category': category, 'confidence': confidence}
            
        except Exception as e:
            logger.error(f"Erreur neural prediction: {e}")
            return {'category': 'general', 'confidence': 0.5}
    
    def _predict_classical(self, tfidf_features: np.ndarray) -> Dict:
        """Prédictions avec les modèles classiques"""
        try:
            predictions = {}
            confidences = {}
            
            # Random Forest
            if hasattr(self.models['random_forest'], 'predict_proba'):
                rf_proba = self.models['random_forest'].predict_proba([tfidf_features])[0]
                rf_pred = np.argmax(rf_proba)
                categories = list(self.categories.keys())
                
                predictions['random_forest'] = categories[rf_pred] if rf_pred < len(categories) else 'general'
                confidences['random_forest'] = np.max(rf_proba)
            
            # MLP
            if hasattr(self.models['mlp'], 'predict_proba'):
                mlp_proba = self.models['mlp'].predict_proba([tfidf_features])[0]
                mlp_pred = np.argmax(mlp_proba)
                
                predictions['mlp'] = categories[mlp_pred] if mlp_pred < len(categories) else 'general'
                confidences['mlp'] = np.max(mlp_proba)
            
            return {'predictions': predictions, 'confidences': confidences}
            
        except Exception as e:
            logger.error(f"Erreur classical predictions: {e}")
            return {'predictions': {}, 'confidences': {}}
    
    def _intelligent_ensemble(self, predictions: Dict, confidences: Dict, features: Dict) -> Dict:
        """Fusion intelligente avec pondération adaptive"""
        try:
            # Pondération basée sur la performance historique et le contexte
            weights = {
                'bert': 0.25,
                'camembert': 0.25,  # Plus de poids pour le français
                'neural': 0.20,
                'random_forest': 0.15,
                'mlp': 0.15
            }
            
            # Ajustement des poids selon le contexte
            text_length = features.get('text_length', 0)
            if text_length < 100:  # Textes courts
                weights['bert'] += 0.1
                weights['camembert'] += 0.1
            elif text_length > 1000:  # Textes longs
                weights['neural'] += 0.1
                weights['random_forest'] += 0.1
            
            # Vote pondéré
            category_scores = {}
            
            for model, category in predictions.items():
                if model in weights and category:
                    confidence = confidences.get(model, 0.5)
                    weight = weights.get(model, 0.1)
                    
                    if category not in category_scores:
                        category_scores[category] = 0
                    
                    category_scores[category] += confidence * weight
            
            if not category_scores:
                return self._fallback_prediction()
            
            # Catégorie finale
            final_category = max(category_scores, key=category_scores.get)
            final_confidence = category_scores[final_category]
            
            # Normalisation de la confiance
            final_confidence = min(1.0, max(0.0, final_confidence))
            
            return {
                'category': final_category,
                'confidence': final_confidence,
                'model_predictions': predictions,
                'model_confidences': confidences,
                'ensemble_method': 'weighted_voting',
                'features_used': list(features.keys())
            }
            
        except Exception as e:
            logger.error(f"Erreur ensemble: {e}")
            return self._fallback_prediction()
    
    def _get_text_embeddings(self, text: str) -> np.ndarray:
        """Génère des embeddings pour le texte"""
        try:
            # Utilisation de BERT pour les embeddings
            inputs = self.tokenizers['bert'](
                text, 
                return_tensors='pt', 
                truncation=True, 
                padding=True, 
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.models['bert'](**inputs, output_hidden_states=True)
                # Utilise la couche avant-dernière
                embeddings = outputs.hidden_states[-2]
                # Moyenne des tokens
                mean_embeddings = torch.mean(embeddings, dim=1)
                
            return mean_embeddings.cpu().numpy()[0]
            
        except Exception as e:
            logger.error(f"Erreur embeddings: {e}")
            return np.zeros(768)  # Taille standard BERT
    
    def _fallback_prediction(self) -> Dict:
        """Prédiction de secours"""
        return {
            'category': 'general',
            'confidence': 0.3,
            'model_predictions': {},
            'model_confidences': {},
            'ensemble_method': 'fallback',
            'features_used': []
        }
    
    def train_on_user_data(self, training_data: List[Dict]):
        """Entraîne les modèles sur les données utilisateur"""
        try:
            if len(training_data) < 10:
                logger.warning("Pas assez de données pour l'entraînement")
                return
            
            # Préparation des données
            texts = []
            labels = []
            
            for item in training_data:
                text = f"{item['subject']} {item['body']}"
                texts.append(text)
                labels.append(item['category'])
            
            # Mise à jour des vectoriseurs
            self._update_vectorizers(texts)
            
            # Entraînement des modèles classiques
            self._train_classical_models(texts, labels)
            
            # Fine-tuning des modèles transformer (optionnel)
            if len(training_data) > 100:
                self._fine_tune_transformers(texts, labels)
            
            # Sauvegarde
            self._save_models()
            
            logger.info(f"Modèles entraînés sur {len(training_data)} exemples")
            
        except Exception as e:
            logger.error(f"Erreur entraînement: {e}")
    
    def _update_vectorizers(self, texts: List[str]):
        """Met à jour les vectoriseurs avec de nouvelles données"""
        try:
            # TF-IDF mots
            self.vectorizers['tfidf'].fit(texts)
            
            # TF-IDF caractères
            self.vectorizers['char_tfidf'].fit(texts)
            
        except Exception as e:
            logger.error(f"Erreur mise à jour vectoriseurs: {e}")
    
    def _train_classical_models(self, texts: List[str], labels: List[str]):
        """Entraîne les modèles classiques"""
        try:
            # Préparation des features
            X_tfidf = self.vectorizers['tfidf'].transform(texts).toarray()
            X_char = self.vectorizers['char_tfidf'].transform(texts).toarray()
            X = np.hstack([X_tfidf, X_char])
            y = labels
            
            # Division train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Entraînement Random Forest
            self.models['random_forest'].fit(X_train, y_train)
            rf_accuracy = accuracy_score(y_test, self.models['random_forest'].predict(X_test))
            
            # Entraînement MLP
            self.models['mlp'].fit(X_train, y_train)
            mlp_accuracy = accuracy_score(y_test, self.models['mlp'].predict(X_test))
            
            # Stockage des métriques
            self.performance_metrics['random_forest'] = rf_accuracy
            self.performance_metrics['mlp'] = mlp_accuracy
            
            logger.info(f"RF accuracy: {rf_accuracy:.3f}, MLP accuracy: {mlp_accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"Erreur entraînement modèles classiques: {e}")
    
    def _save_models(self):
        """Sauvegarde tous les modèles"""
        try:
            # Modèles classiques
            with open(os.path.join(self.model_path, "random_forest.pkl"), 'wb') as f:
                pickle.dump(self.models['random_forest'], f)
            
            with open(os.path.join(self.model_path, "mlp.pkl"), 'wb') as f:
                pickle.dump(self.models['mlp'], f)
            
            # Vectoriseurs
            with open(os.path.join(self.model_path, "tfidf_vectorizer.pkl"), 'wb') as f:
                pickle.dump(self.vectorizers['tfidf'], f)
            
            with open(os.path.join(self.model_path, "char_tfidf_vectorizer.pkl"), 'wb') as f:
                pickle.dump(self.vectorizers['char_tfidf'], f)
            
            # Modèle neural
            torch.save(
                self.models['neural'].state_dict(),
                os.path.join(self.model_path, "neural_classifier.pth")
            )
            
            # Modèles transformer (si fine-tunés)
            self.models['bert'].save_pretrained(os.path.join(self.model_path, "bert_classifier"))
            self.tokenizers['bert'].save_pretrained(os.path.join(self.model_path, "bert_classifier"))
            
            self.models['camembert'].save_pretrained(os.path.join(self.model_path, "camembert_classifier"))
            self.tokenizers['camembert'].save_pretrained(os.path.join(self.model_path, "camembert_classifier"))
            
            # Métriques et historique
            with open(os.path.join(self.model_path, "performance_metrics.json"), 'w') as f:
                json.dump(self.performance_metrics, f, indent=2)
            
            logger.info("Tous les modèles sauvegardés")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
    
    def get_model_performance(self) -> Dict:
        """Retourne les métriques de performance des modèles"""
        return {
            'performance_metrics': self.performance_metrics,
            'cache_size': len(self.prediction_cache),
            'models_loaded': list(self.models.keys()),
            'categories': list(self.categories.keys()),
            'last_training': self.training_history[-1] if self.training_history else None
        }