"""
Détecteur de spam ultra-performant avec machine learning avancé
Remplace la détection basique par des algorithmes sophistiqués
"""

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from sklearn.ensemble import IsolationForest, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.neural_network import MLPClassifier
import re
import logging
from typing import Dict, List, Tuple, Optional
import pickle
import os
import json
from datetime import datetime, timedelta
import sqlite3
from email.utils import parseaddr
import tldextract
import whois
import dns.resolver
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)

class SpamNeuralNet(nn.Module):
    """Réseau de neurones spécialisé pour la détection de spam"""
    
    def __init__(self, input_size: int):
        super(SpamNeuralNet, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 2)  # Spam ou pas spam
        )
        
    def forward(self, x):
        return self.performance_stats.copy()
    
    # Méthodes utilitaires privées
    
    def _count_suspicious_urls(self, text: str) -> int:
        """Compte les URLs suspectes"""
        urls = re.findall(r'http[s]?://[^\s]+', text)
        suspicious_count = 0
        
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Patterns suspects
                if any(pattern in domain for pattern in [
                    'bit.ly', 'tinyurl', 't.co', 'goo.gl', 'short',
                    'click', 'redirect', 'track', 'campaign'
                ]):
                    suspicious_count += 1
                    
                # Domaines avec beaucoup de chiffres
                if len(re.findall(r'\d', domain)) > len(domain) * 0.3:
                    suspicious_count += 1
                    
            except Exception:
                suspicious_count += 1  # URL malformée = suspecte
                
        return suspicious_count
    
    def _is_suspicious_sender(self, sender: str) -> int:
        """Détermine si l'expéditeur est suspect (retourne 1 ou 0)"""
        if not sender or '@' not in sender:
            return 1
        
        local, domain = sender.split('@', 1)
        
        # Patterns suspects dans la partie locale
        if any(pattern in local.lower() for pattern in [
            'noreply', 'no-reply', 'donotreply', 'admin', 'support',
            'info', 'sales', 'marketing', 'promo', 'offer'
        ]):
            return 1
        
        # Trop de chiffres
        if len(re.findall(r'\d', local)) > len(local) * 0.5:
            return 1
        
        # Caractères suspects
        if re.search(r'[^\w\.\-]', local):
            return 1
            
        return 0
    
    def _get_sender_reputation(self, sender: str) -> float:
        """Récupère la réputation de l'expéditeur"""
        return self.sender_reputation.get(sender.lower(), 0.5)
    
    def _check_missing_headers(self, headers: Dict) -> int:
        """Vérifie les headers manquants"""
        required = ['From', 'To', 'Date', 'Message-ID', 'Subject']
        missing = sum(1 for h in required if h not in headers)
        return missing
    
    def _check_forged_headers(self, headers: Dict) -> int:
        """Vérifie les headers forgés"""
        forged_count = 0
        
        # Vérifications basiques
        if 'Received' not in headers:
            forged_count += 1
            
        if 'Return-Path' in headers and 'From' in headers:
            return_domain = headers['Return-Path'].split('@')[-1] if '@' in headers['Return-Path'] else ''
            from_domain = headers['From'].split('@')[-1] if '@' in headers['From'] else ''
            
            if return_domain and from_domain and return_domain != from_domain:
                forged_count += 1
                
        return forged_count
    
    def _save_feedback(self, feedback_data: Dict):
        """Sauvegarde le feedback en base de données"""
        try:
            db_path = os.path.join(self.model_path, "spam_feedback.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT,
                    is_spam BOOLEAN,
                    confidence REAL,
                    timestamp TEXT
                )
            ''')
            
            content_hash = hashlib.md5(feedback_data['content'].encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO spam_feedback (content_hash, is_spam, confidence, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (content_hash, feedback_data['is_spam'], 
                  feedback_data['confidence'], feedback_data['timestamp']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde feedback: {e}")
    
    def _load_reputation_data(self):
        """Charge les données de réputation"""
        try:
            # Chargement de la réputation des domaines
            domain_rep_path = os.path.join(self.model_path, "domain_reputation.json")
            if os.path.exists(domain_rep_path):
                with open(domain_rep_path, 'r') as f:
                    self.domain_reputation = json.load(f)
            
            # Chargement de la réputation des expéditeurs
            sender_rep_path = os.path.join(self.model_path, "sender_reputation.json")
            if os.path.exists(sender_rep_path):
                with open(sender_rep_path, 'r') as f:
                    self.sender_reputation = json.load(f)
                    
            # Chargement de la réputation des URLs
            url_rep_path = os.path.join(self.model_path, "url_reputation.json")
            if os.path.exists(url_rep_path):
                with open(url_rep_path, 'r') as f:
                    self.url_reputation = json.load(f)
                    
        except Exception as e:
            logger.error(f"Erreur chargement réputation: {e}")
    
    def _load_spam_patterns(self):
        """Charge les patterns de spam appris"""
        try:
            patterns_path = os.path.join(self.model_path, "spam_patterns.json")
            if os.path.exists(patterns_path):
                with open(patterns_path, 'r') as f:
                    self.spam_patterns = json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement patterns: {e}")
    
    def save_models(self):
        """Sauvegarde tous les modèles et données"""
        try:
            # Modèles ML classiques
            with open(os.path.join(self.model_path, "spam_gb.pkl"), 'wb') as f:
                pickle.dump(self.models['gradient_boosting'], f)
                
            with open(os.path.join(self.model_path, "spam_mlp.pkl"), 'wb') as f:
                pickle.dump(self.models['mlp'], f)
                
            with open(os.path.join(self.model_path, "anomaly_detector.pkl"), 'wb') as f:
                pickle.dump(self.models['anomaly'], f)
            
            # Vectoriseurs
            with open(os.path.join(self.model_path, "spam_tfidf.pkl"), 'wb') as f:
                pickle.dump(self.vectorizers['tfidf'], f)
                
            with open(os.path.join(self.model_path, "spam_count.pkl"), 'wb') as f:
                pickle.dump(self.vectorizers['count'], f)
                
            with open(os.path.join(self.model_path, "spam_char.pkl"), 'wb') as f:
                pickle.dump(self.vectorizers['char'], f)
            
            # Modèle neural
            torch.save(
                self.models['neural'].state_dict(),
                os.path.join(self.model_path, "spam_neural.pth")
            )
            
            # Modèle transformer (si fine-tuné)
            self.models['transformer'].save_pretrained(
                os.path.join(self.model_path, "spam_transformer")
            )
            self.tokenizers['transformer'].save_pretrained(
                os.path.join(self.model_path, "spam_transformer")
            )
            
            # Données de réputation
            with open(os.path.join(self.model_path, "domain_reputation.json"), 'w') as f:
                json.dump(self.domain_reputation, f, indent=2)
                
            with open(os.path.join(self.model_path, "sender_reputation.json"), 'w') as f:
                json.dump(self.sender_reputation, f, indent=2)
                
            with open(os.path.join(self.model_path, "url_reputation.json"), 'w') as f:
                json.dump(self.url_reputation, f, indent=2)
            
            # Patterns appris
            with open(os.path.join(self.model_path, "spam_patterns.json"), 'w') as f:
                json.dump(self.spam_patterns, f, indent=2)
            
            # Statistiques
            with open(os.path.join(self.model_path, "performance_stats.json"), 'w') as f:
                json.dump(self.performance_stats, f, indent=2)
            
            logger.info("Tous les modèles spam sauvegardés")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde modèles spam: {e}")
    
    def retrain_models(self, training_data: List[Dict] = None):
        """Réentraîne les modèles avec de nouvelles données"""
        try:
            if not training_data:
                # Chargement des données de feedback
                training_data = self._load_feedback_data()
            
            if len(training_data) < 50:
                logger.warning("Pas assez de données pour le réentraînement spam")
                return
            
            # Préparation des données
            texts = []
            labels = []
            features_list = []
            
            for item in training_data:
                text = f"{item.get('subject', '')} {item.get('body', '')}"
                texts.append(text)
                labels.append(1 if item.get('is_spam', False) else 0)
                
                # Extraction des features
                features = self._extract_spam_features(
                    item.get('subject', ''),
                    item.get('body', ''),
                    item.get('sender', ''),
                    item.get('headers', {})
                )
                features_list.append(self._prepare_feature_vector(features))
            
            # Mise à jour des vectoriseurs
            self.vectorizers['tfidf'].fit(texts)
            self.vectorizers['count'].fit(texts)
            self.vectorizers['char'].fit(texts)
            
            # Réentraînement des modèles classiques
            X = np.array(features_list)
            y = np.array(labels)
            
            self.models['gradient_boosting'].fit(X, y)
            self.models['mlp'].fit(X, y)
            self.models['anomaly'].fit(X[y == 0])  # Seulement sur les non-spam
            
            # Sauvegarde
            self.save_models()
            
            logger.info(f"Modèles spam réentraînés sur {len(training_data)} exemples")
            
        except Exception as e:
            logger.error(f"Erreur réentraînement spam: {e}")
    
    def _load_feedback_data(self) -> List[Dict]:
        """Charge les données de feedback pour réentraînement"""
        try:
            db_path = os.path.join(self.model_path, "spam_feedback.db")
            if not os.path.exists(db_path):
                return []
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT content_hash, is_spam, confidence, timestamp
                FROM spam_feedback
                ORDER BY timestamp DESC
                LIMIT 1000
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # Conversion en format utilisable
            feedback_data = []
            for row in rows:
                feedback_data.append({
                    'content_hash': row[0],
                    'is_spam': bool(row[1]),
                    'confidence': row[2],
                    'timestamp': row[3]
                })
            
            return feedback_data
            
        except Exception as e:
            logger.error(f"Erreur chargement feedback: {e}")
            return []

class AdvancedSpamDetector:
    """Détecteur de spam ultra-performant avec multiple approches"""
    
    def __init__(self, model_path: str = "spam_models/"):
        self.model_path = model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Modèles de détection
        self.models = {}
        self.vectorizers = {}
        
        # Bases de données de réputation
        self.sender_reputation = {}
        self.domain_reputation = {}
        self.url_reputation = {}
        
        # Patterns de spam appris
        self.spam_patterns = {
            'subject_patterns': [],
            'body_patterns': [],
            'sender_patterns': [],
            'url_patterns': []
        }
        
        # Cache et historique
        self.detection_cache = {}
        self.false_positives = set()
        self.confirmed_spam = set()
        
        # Métriques de performance
        self.performance_stats = {
            'total_processed': 0,
            'spam_detected': 0,
            'false_positives': 0,
            'accuracy': 0.0
        }
        
        self._initialize_models()
        self._load_reputation_data()
        self._load_spam_patterns()
    
    def _initialize_models(self):
        """Initialise tous les modèles de détection de spam"""
        try:
            os.makedirs(self.model_path, exist_ok=True)
            
            # 1. Modèle transformer spécialisé spam
            self._initialize_transformer_model()
            
            # 2. Réseau de neurones personnalisé
            self._initialize_neural_model()
            
            # 3. Modèles d'ensemble pour robustesse
            self._initialize_ensemble_models()
            
            # 4. Détecteur d'anomalies
            self._initialize_anomaly_detector()
            
            # 5. Vectoriseurs spécialisés
            self._initialize_vectorizers()
            
            logger.info("Modèles de détection spam initialisés")
            
        except Exception as e:
            logger.error(f"Erreur initialisation détecteur spam: {e}")
    
    def _initialize_transformer_model(self):
        """Initialise le modèle transformer spécialisé pour le spam"""
        try:
            model_name = "unitary/toxic-bert"
            transformer_path = os.path.join(self.model_path, "spam_transformer")
            
            if os.path.exists(transformer_path):
                self.models['transformer'] = AutoModelForSequenceClassification.from_pretrained(transformer_path)
                self.tokenizers = {'transformer': AutoTokenizer.from_pretrained(transformer_path)}
            else:
                self.models['transformer'] = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.tokenizers = {'transformer': AutoTokenizer.from_pretrained(model_name)}
            
            self.models['transformer'].to(self.device)
            logger.info("Modèle transformer spam initialisé")
            
        except Exception as e:
            logger.error(f"Erreur transformer spam: {e}")
    
    def _initialize_neural_model(self):
        """Initialise le réseau de neurones personnalisé"""
        try:
            neural_path = os.path.join(self.model_path, "spam_neural.pth")
            
            # Taille des features combinées
            input_size = 15000  # TF-IDF + features manuelles
            
            self.models['neural'] = SpamNeuralNet(input_size)
            
            if os.path.exists(neural_path):
                self.models['neural'].load_state_dict(
                    torch.load(neural_path, map_location=self.device)
                )
            
            self.models['neural'].to(self.device)
            logger.info("Modèle neural spam initialisé")
            
        except Exception as e:
            logger.error(f"Erreur neural spam: {e}")
    
    def _initialize_ensemble_models(self):
        """Initialise les modèles d'ensemble"""
        try:
            # Gradient Boosting pour patterns complexes
            gb_path = os.path.join(self.model_path, "spam_gb.pkl")
            if os.path.exists(gb_path):
                with open(gb_path, 'rb') as f:
                    self.models['gradient_boosting'] = pickle.load(f)
            else:
                self.models['gradient_boosting'] = GradientBoostingClassifier(
                    n_estimators=200,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                )
            
            # MLP pour patterns non-linéaires
            mlp_path = os.path.join(self.model_path, "spam_mlp.pkl")
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
            
            logger.info("Modèles d'ensemble spam initialisés")
            
        except Exception as e:
            logger.error(f"Erreur ensemble spam: {e}")
    
    def _initialize_anomaly_detector(self):
        """Initialise le détecteur d'anomalies"""
        try:
            anomaly_path = os.path.join(self.model_path, "anomaly_detector.pkl")
            
            if os.path.exists(anomaly_path):
                with open(anomaly_path, 'rb') as f:
                    self.models['anomaly'] = pickle.load(f)
            else:
                self.models['anomaly'] = IsolationForest(
                    contamination=0.1,
                    random_state=42,
                    n_estimators=100
                )
            
            logger.info("Détecteur d'anomalies initialisé")
            
        except Exception as e:
            logger.error(f"Erreur détecteur anomalies: {e}")
    
    def _initialize_vectorizers(self):
        """Initialise les vectoriseurs spécialisés"""
        try:
            # TF-IDF pour mots spam
            tfidf_path = os.path.join(self.model_path, "spam_tfidf.pkl")
            if os.path.exists(tfidf_path):
                with open(tfidf_path, 'rb') as f:
                    self.vectorizers['tfidf'] = pickle.load(f)
            else:
                self.vectorizers['tfidf'] = TfidfVectorizer(
                    max_features=10000,
                    ngram_range=(1, 3),
                    lowercase=True,
                    stop_words='english',
                    min_df=2,
                    max_df=0.95
                )
            
            # Count vectorizer pour fréquences
            count_path = os.path.join(self.model_path, "spam_count.pkl")
            if os.path.exists(count_path):
                with open(count_path, 'rb') as f:
                    self.vectorizers['count'] = pickle.load(f)
            else:
                self.vectorizers['count'] = CountVectorizer(
                    max_features=5000,
                    ngram_range=(1, 2),
                    lowercase=True
                )
            
            # Vectorizer pour caractères (obfuscation)
            char_path = os.path.join(self.model_path, "spam_char.pkl")
            if os.path.exists(char_path):
                with open(char_path, 'rb') as f:
                    self.vectorizers['char'] = pickle.load(f)
            else:
                self.vectorizers['char'] = TfidfVectorizer(
                    analyzer='char',
                    ngram_range=(2, 5),
                    max_features=3000
                )
            
            logger.info("Vectoriseurs spam initialisés")
            
        except Exception as e:
            logger.error(f"Erreur vectoriseurs spam: {e}")
    
    def detect_spam(self, subject: str, body: str, sender: str, headers: Dict = None) -> Dict:
        """
        Détection de spam ultra-performante avec analyse multicritères
        """
        try:
            # Cache check
            content_hash = hashlib.md5(f"{subject}{body}{sender}".encode()).hexdigest()
            if content_hash in self.detection_cache:
                return self.detection_cache[content_hash]
            
            # Extraction de features complètes
            features = self._extract_spam_features(subject, body, sender, headers)
            
            # Analyses multiples
            results = {}
            
            # 1. Analyse transformer
            transformer_result = self._analyze_with_transformer(f"{subject} {body}")
            results['transformer'] = transformer_result
            
            # 2. Analyse avec réseau de neurones
            neural_result = self._analyze_with_neural(features)
            results['neural'] = neural_result
            
            # 3. Analyse avec modèles d'ensemble
            ensemble_result = self._analyze_with_ensemble(features)
            results['ensemble'] = ensemble_result
            
            # 4. Détection d'anomalies
            anomaly_result = self._detect_anomalies(features)
            results['anomaly'] = anomaly_result
            
            # 5. Analyse heuristique avancée
            heuristic_result = self._advanced_heuristic_analysis(subject, body, sender, headers)
            results['heuristic'] = heuristic_result
            
            # 6. Vérification de réputation
            reputation_result = self._check_reputation(sender, features.get('urls', []))
            results['reputation'] = reputation_result
            
            # Fusion intelligente des résultats
            final_result = self._intelligent_spam_fusion(results, features)
            
            # Cache du résultat
            self.detection_cache[content_hash] = final_result
            
            # Limitation du cache
            if len(self.detection_cache) > 5000:
                oldest_keys = list(self.detection_cache.keys())[:1000]
                for key in oldest_keys:
                    del self.detection_cache[key]
            
            # Mise à jour des statistiques
            self._update_stats(final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Erreur détection spam: {e}")
            return self._fallback_spam_result()
    
    def _extract_spam_features(self, subject: str, body: str, sender: str, headers: Dict = None) -> Dict:
        """Extraction complète de features pour la détection de spam"""
        full_text = f"{subject} {body}"
        
        features = {
            # Features textuelles basiques
            'text_length': len(full_text),
            'subject_length': len(subject),
            'body_length': len(body),
            'word_count': len(full_text.split()),
            'sentence_count': len([s for s in full_text.split('.') if s.strip()]),
            
            # Features de ponctuation et style
            'exclamation_count': full_text.count('!'),
            'question_count': full_text.count('?'),
            'caps_count': sum(1 for c in full_text if c.isupper()),
            'caps_ratio': sum(1 for c in full_text if c.isupper()) / len(full_text) if full_text else 0,
            'digit_count': sum(1 for c in full_text if c.isdigit()),
            'special_char_count': sum(1 for c in full_text if not c.isalnum() and not c.isspace()),
            
            # Features de contenu suspect
            'money_mentions': len(re.findall(r'[\$€£¥₹]\s*\d+|gratuit|free|prize|winner', full_text.lower())),
            'urgent_words': len(re.findall(r'urgent|asap|immediate|limited time|act now', full_text.lower())),
            'action_words': len(re.findall(r'click|buy|purchase|order|subscribe|download', full_text.lower())),
            
            # Features d'URLs et liens
            'url_count': len(re.findall(r'http[s]?://[^\s]+', full_text)),
            'urls': re.findall(r'http[s]?://[^\s]+', full_text),
            'suspicious_urls': self._count_suspicious_urls(full_text),
            'shortened_urls': len(re.findall(r'bit\.ly|tinyurl|t\.co|goo\.gl', full_text.lower())),
            
            # Features de l'expéditeur
            'sender_domain': sender.split('@')[1] if '@' in sender else '',
            'sender_suspicious': self._is_suspicious_sender(sender),
            'sender_reputation': self._get_sender_reputation(sender),
            
            # Features de headers (si disponibles)
            'missing_headers': self._check_missing_headers(headers) if headers else 0,
            'forged_headers': self._check_forged_headers(headers) if headers else 0,
            
            # Features de contenu avancées
            'html_content': '<html>' in body.lower() or '<body>' in body.lower(),
            'image_count': len(re.findall(r'<img|\.jpg|\.png|\.gif', body.lower())),
            'attachment_keywords': len(re.findall(r'attachment|pièce jointe|download|télécharger', full_text.lower())),
            
            # Features de langage
            'non_ascii_ratio': sum(1 for c in full_text if ord(c) > 127) / len(full_text) if full_text else 0,
            'repeated_chars': len(re.findall(r'(.)\1{3,}', full_text)),
            'excessive_spacing': len(re.findall(r'\s{3,}', full_text)),
            
            # Features temporelles
            'sent_hour': datetime.now().hour,  # Heure d'envoi (approximative)
            'weekend_sent': datetime.now().weekday() >= 5,
        }
        
        # Features vectorisées
        try:
            features['tfidf_features'] = self.vectorizers['tfidf'].transform([full_text]).toarray()[0]
            features['count_features'] = self.vectorizers['count'].transform([full_text]).toarray()[0]
            features['char_features'] = self.vectorizers['char'].transform([full_text]).toarray()[0]
        except:
            # Vectoriseurs pas encore entraînés
            features['tfidf_features'] = np.zeros(10000)
            features['count_features'] = np.zeros(5000)
            features['char_features'] = np.zeros(3000)
        
        return features
    
    def _analyze_with_transformer(self, text: str) -> Dict:
        """Analyse avec le modèle transformer"""
        try:
            inputs = self.tokenizers['transformer'](
                text,
                return_tensors='pt',
                truncation=True,
                padding=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.models['transformer'](**inputs)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
            # Probabilité que ce soit toxique/spam
            spam_prob = probabilities[0][1].item() if probabilities.shape[1] > 1 else probabilities[0][0].item()
            
            return {
                'is_spam': spam_prob > 0.5,
                'confidence': spam_prob,
                'method': 'transformer'
            }
            
        except Exception as e:
            logger.error(f"Erreur transformer: {e}")
            return {'is_spam': False, 'confidence': 0.5, 'method': 'transformer'}
    
    def _analyze_with_neural(self, features: Dict) -> Dict:
        """Analyse avec le réseau de neurones personnalisé"""
        try:
            # Préparation des features
            feature_vector = self._prepare_feature_vector(features)
            feature_tensor = torch.FloatTensor(feature_vector).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.models['neural'](feature_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=-1)
                
            spam_prob = probabilities[0][1].item()
            
            return {
                'is_spam': spam_prob > 0.5,
                'confidence': spam_prob,
                'method': 'neural'
            }
            
        except Exception as e:
            logger.error(f"Erreur neural: {e}")
            return {'is_spam': False, 'confidence': 0.5, 'method': 'neural'}
    
    def _analyze_with_ensemble(self, features: Dict) -> Dict:
        """Analyse avec les modèles d'ensemble"""
        try:
            # Préparation des features pour ML classique
            feature_vector = self._prepare_feature_vector(features)
            
            results = {}
            
            # Gradient Boosting
            if hasattr(self.models['gradient_boosting'], 'predict_proba'):
                gb_proba = self.models['gradient_boosting'].predict_proba([feature_vector])[0]
                results['gradient_boosting'] = {
                    'is_spam': gb_proba[1] > 0.5,
                    'confidence': gb_proba[1]
                }
            
            # MLP
            if hasattr(self.models['mlp'], 'predict_proba'):
                mlp_proba = self.models['mlp'].predict_proba([feature_vector])[0]
                results['mlp'] = {
                    'is_spam': mlp_proba[1] > 0.5,
                    'confidence': mlp_proba[1]
                }
            
            # Moyenne pondérée
            if results:
                avg_confidence = np.mean([r['confidence'] for r in results.values()])
                return {
                    'is_spam': avg_confidence > 0.5,
                    'confidence': avg_confidence,
                    'method': 'ensemble',
                    'sub_results': results
                }
            
            return {'is_spam': False, 'confidence': 0.5, 'method': 'ensemble'}
            
        except Exception as e:
            logger.error(f"Erreur ensemble: {e}")
            return {'is_spam': False, 'confidence': 0.5, 'method': 'ensemble'}
    
    def _detect_anomalies(self, features: Dict) -> Dict:
        """Détection d'anomalies dans les patterns"""
        try:
            feature_vector = self._prepare_feature_vector(features)
            
            # Prédiction d'anomalie (-1 = anomalie, 1 = normal)
            anomaly_score = self.models['anomaly'].decision_function([feature_vector])[0]
            is_anomaly = self.models['anomaly'].predict([feature_vector])[0] == -1
            
            # Conversion en probabilité
            anomaly_prob = 1 / (1 + np.exp(anomaly_score))  # Sigmoid
            
            return {
                'is_spam': is_anomaly,
                'confidence': anomaly_prob if is_anomaly else 1 - anomaly_prob,
                'anomaly_score': anomaly_score,
                'method': 'anomaly'
            }
            
        except Exception as e:
            logger.error(f"Erreur détection anomalies: {e}")
            return {'is_spam': False, 'confidence': 0.5, 'method': 'anomaly'}
    
    def _advanced_heuristic_analysis(self, subject: str, body: str, sender: str, headers: Dict = None) -> Dict:
        """Analyse heuristique avancée avec règles sophistiquées"""
        spam_score = 0.0
        reasons = []
        
        full_text = f"{subject} {body}".lower()
        
        # 1. Mots-clés spam pondérés
        spam_keywords = {
            'viagra': 0.9, 'casino': 0.8, 'lottery': 0.9, 'winner': 0.7,
            'free money': 0.9, 'guarantee': 0.6, 'act now': 0.7, 'limited time': 0.6,
            'congratulations': 0.5, 'click here': 0.7, 'buy now': 0.8,
            'gratuit': 0.7, 'gagnant': 0.8, 'félicitations': 0.5, 'cliquez ici': 0.7
        }
        
        for keyword, weight in spam_keywords.items():
            if keyword in full_text:
                spam_score += weight
                reasons.append(f"Mot-clé spam: {keyword}")
        
        # 2. Patterns suspects dans le sujet
        suspicious_subject_patterns = [
            r'fw:\s*fw:\s*fw:', r're:\s*re:\s*re:', r'!!!+', r'\$\$\$+',
            r'urgent.*urgent', r'free.*free', r'winner.*winner'
        ]
        
        for pattern in suspicious_subject_patterns:
            if re.search(pattern, subject.lower()):
                spam_score += 0.5
                reasons.append(f"Pattern suspect dans le sujet: {pattern}")
        
        # 3. Ratio HTML/texte suspect
        html_tags = len(re.findall(r'<[^>]+>', body))
        if html_tags > 10 and len(body.strip()) < 200:
            spam_score += 0.6
            reasons.append("Ratio HTML/texte suspect")
        
        # 4. Excès de liens
        url_count = len(re.findall(r'http[s]?://[^\s]+', full_text))
        text_length = len(full_text.split())
        if url_count > 0 and text_length > 0:
            url_ratio = url_count / text_length
            if url_ratio > 0.1:  # Plus de 10% de mots sont des URLs
                spam_score += 0.7
                reasons.append("Excès de liens")
        
        # 5. Caractères suspects et obfuscation
        if re.search(r'[^\w\s]{3,}', full_text):  # 3+ caractères spéciaux consécutifs
            spam_score += 0.4
            reasons.append("Caractères suspects")
        
        # 6. Domaine expéditeur suspect
        if '@' in sender:
            domain = sender.split('@')[1].lower()
            suspicious_domains = [
                'temp-mail', 'guerrillamail', '10minutemail', 'throwaway',
                'mailinator', 'sharklasers'
            ]
            if any(susp in domain for susp in suspicious_domains):
                spam_score += 0.8
                reasons.append("Domaine expéditeur suspect")
        
        # 7. Headers manquants ou suspects
        if headers:
            required_headers = ['From', 'To', 'Date', 'Message-ID']
            missing_headers = [h for h in required_headers if h not in headers]
            if missing_headers:
                spam_score += len(missing_headers) * 0.2
                reasons.append(f"Headers manquants: {missing_headers}")
        
        # Normalisation du score
        final_score = min(1.0, spam_score / 3.0)  # Normalise sur 3 points max
        
        return {
            'is_spam': final_score > 0.6,
            'confidence': final_score,
            'reasons': reasons,
            'method': 'heuristic'
        }
    
    def _check_reputation(self, sender: str, urls: List[str]) -> Dict:
        """Vérification de réputation de l'expéditeur et URLs"""
        reputation_score = 0.0
        issues = []
        
        # Réputation de l'expéditeur
        if '@' in sender:
            domain = sender.split('@')[1].lower()
            
            # Vérification dans la base de réputation
            domain_rep = self.domain_reputation.get(domain, 0.5)
            sender_rep = self.sender_reputation.get(sender.lower(), 0.5)
            
            if domain_rep < 0.3:
                reputation_score += 0.4
                issues.append(f"Domaine de mauvaise réputation: {domain}")
            
            if sender_rep < 0.3:
                reputation_score += 0.3
                issues.append(f"Expéditeur de mauvaise réputation")
        
        # Vérification des URLs
        for url in urls[:10]:  # Limite à 10 URLs
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Vérification dans la base d'URLs malveillantes
                url_rep = self.url_reputation.get(domain, 0.5)
                if url_rep < 0.3:
                    reputation_score += 0.2
                    issues.append(f"URL suspecte: {domain}")
                
                # Vérification de patterns suspects
                if any(pattern in domain for pattern in ['bit.ly', 'tinyurl', 'short']):
                    reputation_score += 0.1
                    issues.append(f"URL raccourcie suspecte: {domain}")
                    
            except Exception:
                continue
        
        final_score = min(1.0, reputation_score)
        
        return {
            'is_spam': final_score > 0.5,
            'confidence': final_score,
            'issues': issues,
            'method': 'reputation'
        }
    
    def _intelligent_spam_fusion(self, results: Dict, features: Dict) -> Dict:
        """Fusion intelligente de tous les résultats de détection"""
        try:
            # Pondération adaptative basée sur la fiabilité
            weights = {
                'transformer': 0.25,
                'neural': 0.20,
                'ensemble': 0.20,
                'heuristic': 0.20,
                'reputation': 0.10,
                'anomaly': 0.05
            }
            
            # Ajustement des poids selon le contexte
            text_length = features.get('text_length', 0)
            if text_length < 50:  # Textes très courts
                weights['heuristic'] += 0.1
                weights['reputation'] += 0.1
            elif text_length > 2000:  # Textes très longs
                weights['transformer'] += 0.1
                weights['neural'] += 0.1
            
            # Calcul du score pondéré
            total_score = 0.0
            valid_methods = 0
            method_details = {}
            
            for method, result in results.items():
                if method in weights and 'confidence' in result:
                    confidence = result['confidence']
                    weight = weights[method]
                    
                    if result.get('is_spam', False):
                        contribution = confidence * weight
                    else:
                        contribution = (1 - confidence) * weight * -1
                    
                    total_score += contribution
                    valid_methods += 1
                    
                    method_details[method] = {
                        'is_spam': result.get('is_spam', False),
                        'confidence': confidence,
                        'weight': weight,
                        'contribution': contribution
                    }
            
            # Normalisation
            if valid_methods > 0:
                # Conversion en probabilité
                final_probability = 1 / (1 + np.exp(-total_score * 10))  # Sigmoid amplifié
            else:
                final_probability = 0.5
            
            # Décision finale
            is_spam = final_probability > 0.6  # Seuil légèrement élevé pour éviter faux positifs
            
            # Collecte des raisons
            all_reasons = []
            for method, result in results.items():
                if result.get('is_spam') and 'reasons' in result:
                    all_reasons.extend(result['reasons'])
                elif result.get('is_spam') and 'issues' in result:
                    all_reasons.extend(result['issues'])
            
            return {
                'is_spam': is_spam,
                'confidence': final_probability,
                'spam_probability': final_probability,
                'total_score': total_score,
                'method_details': method_details,
                'reasons': all_reasons[:10],  # Limite à 10 raisons
                'fusion_method': 'intelligent_weighted',
                'methods_used': list(results.keys())
            }
            
        except Exception as e:
            logger.error(f"Erreur fusion spam: {e}")
            return self._fallback_spam_result()
    
    def _prepare_feature_vector(self, features: Dict) -> np.ndarray:
        """Prépare un vecteur de features pour les modèles ML"""
        try:
            # Features numériques de base
            numeric_features = [
                features.get('text_length', 0),
                features.get('subject_length', 0),
                features.get('word_count', 0),
                features.get('caps_ratio', 0),
                features.get('exclamation_count', 0),
                features.get('question_count', 0),
                features.get('url_count', 0),
                features.get('money_mentions', 0),
                features.get('urgent_words', 0),
                features.get('action_words', 0),
                features.get('suspicious_urls', 0),
                features.get('sender_suspicious', 0),
                features.get('sender_reputation', 0.5),
                features.get('html_content', 0),
                features.get('image_count', 0),
                features.get('non_ascii_ratio', 0),
                features.get('repeated_chars', 0),
                features.get('sent_hour', 12),
                features.get('weekend_sent', 0)
            ]
            
            # Combinaison avec features vectorisées
            tfidf_features = features.get('tfidf_features', np.zeros(10000))
            count_features = features.get('count_features', np.zeros(5000))
            
            # Concaténation
            full_vector = np.concatenate([
                np.array(numeric_features),
                tfidf_features[:10000],  # Limite pour éviter surcharge mémoire
                count_features[:5000]
            ])
            
            return full_vector
            
        except Exception as e:
            logger.error(f"Erreur préparation features: {e}")
            return np.zeros(15019)  # Taille par défaut
    
    def _fallback_spam_result(self) -> Dict:
        """Résultat de secours en cas d'erreur"""
        return {
            'is_spam': False,
            'confidence': 0.5,
            'spam_probability': 0.5,
            'method_details': {},
            'reasons': [],
            'fusion_method': 'fallback',
            'methods_used': []
        }
    
    def learn_from_feedback(self, email_content: str, is_spam: bool, confidence: float):
        """Apprentissage à partir du feedback utilisateur"""
        try:
            # Mise à jour des statistiques
            if is_spam and confidence < 0.6:
                self.performance_stats['false_positives'] += 1
            
            # Stockage pour réentraînement
            feedback_data = {
                'content': email_content,
                'is_spam': is_spam,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
            
            # Sauvegarde en base
            self._save_feedback(feedback_data)
            
            logger.info(f"Feedback spam intégré: {is_spam} (confiance: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Erreur apprentissage spam: {e}")
    
    def _update_stats(self, result: Dict):
        """Met à jour les statistiques de performance"""
        self.performance_stats['total_processed'] += 1
        if result.get('is_spam', False):
            self.performance_stats['spam_detected'] += 1
    
    def get_performance_stats(self) -> Dict:
        """Retourne les statistiques de performance"""
        total = self.performance_stats['total_processed']
        if total > 0:
            self.performance_stats['accuracy'] = 1 - (self.performance_stats['false_positives'] / total)
        
        return self