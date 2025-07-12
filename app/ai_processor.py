"""
Processeur IA Ultra-Performant pour la gestion d'emails
Version corrigée sans bus error - garde toute la puissance IA
"""

import logging
import numpy as np
import re
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pickle
from collections import Counter
import gc
import threading
from concurrent.futures import ThreadPoolExecutor

# Imports avec gestion d'erreurs
try:
    import torch
    import torch.nn as nn
    # Configuration PyTorch pour éviter les bus errors
    torch.set_num_threads(2)  # Limite le nombre de threads
    torch.set_num_interop_threads(1)
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("PyTorch non disponible")

try:
    from transformers import (
        AutoTokenizer, AutoModelForSequenceClassification,
        pipeline, AutoModel
    )
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("Transformers non disponible")

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("SentenceTransformers non disponible")

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

try:
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logger = logging.getLogger(__name__)

class AdvancedAIProcessor:
    """Processeur IA avancé pour emails avec apprentissage adaptatif"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
        # Configuration de base
        self.device = torch.device('cpu')  # Force CPU pour éviter les problèmes GPU
        
        # Variables de contrôle pour le chargement progressif
        self._models_loaded = False
        self._loading_lock = threading.Lock()
        
        # Modèles
        self.models = {}
        self.tokenizers = {}
        
        # Base de données pour l'apprentissage
        self.db_path = "email_learning.db"
        self.user_feedback_db = "user_feedback.db"
        
        # Cache des embeddings
        self.embeddings_cache = {}
        
        # Modèles de classification
        self.email_classifier = None
        self.spam_detector = None
        self.priority_analyzer = None
        self.sentiment_analyzer = None
        self.intent_classifier = None
        
        # Modèle pour les embeddings sémantiques
        self.sentence_transformer = None
        
        # Patterns appris
        self.learned_patterns = {}
        self.user_categories = {}
        
        # NLP
        self.nlp = None
        
        # Catégories par défaut
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
            'urgent': ['urgent', 'asap', 'immédiat', 'critique', 'emergency'],
            'general': ['bonjour', 'merci', 'information', 'question']
        }
        
        # Pool de threads pour éviter les problèmes de concurrence
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        
        # Vectoriseur simple
        if HAS_SKLEARN:
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            self.simple_classifier = RandomForestClassifier(n_estimators=50, random_state=42)
        
        # Initialisation immédiate des composants essentiels
        self._setup_database()
        self._load_user_patterns()
        self._train_simple_models()
        
        # Initialisation différée des modèles lourds
        self._initialize_models_async()
    
    def _initialize_models_async(self):
        """Initialise les modèles de manière asynchrone pour éviter les bus errors"""
        def _load_models():
            try:
                with self._loading_lock:
                    self._initialize_models()
                    self._models_loaded = True
            except Exception as e:
                logger.error(f"Erreur chargement modèles async: {e}")
        
        # Démarrer le chargement en arrière-plan
        self.thread_pool.submit(_load_models)
    
    def _initialize_models(self):
        """Initialise tous les modèles IA avancés de manière sécurisée"""
        try:
            logger.info("Initialisation des modèles IA avancés...")
            
            if not HAS_TORCH or not HAS_TRANSFORMERS:
                logger.warning("PyTorch/Transformers non disponible - utilisation de modèles simplifiés")
                return
            
            # Configuration pour éviter les problèmes mémoire
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'
            
            # 1. Modèle de classification d'emails - Version sécurisée
            try:
                self.email_classifier = pipeline(
                    "text-classification",
                    model="distilbert-base-uncased-finetuned-sst-2-english",  # Modèle plus léger
                    device=-1,  # Force CPU
                    return_all_scores=False
                )
                logger.info("Email classifier chargé")
            except Exception as e:
                logger.warning(f"Erreur email classifier: {e}")
            
            # 2. Détecteur de spam - Version simplifiée
            try:
                self.spam_detector = pipeline(
                    "text-classification",
                    model="martin-ha/toxic-comment-model",  # Modèle plus stable
                    device=-1
                )
                logger.info("Spam detector chargé")
            except Exception as e:
                logger.warning(f"Erreur spam detector: {e}")
            
            # 3. Analyseur de sentiment - Version robuste
            try:
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1,
                    return_all_scores=False
                )
                logger.info("Sentiment analyzer chargé")
            except Exception as e:
                logger.warning(f"Erreur sentiment analyzer: {e}")
            
            # 4. Classificateur d'intention - Charge en dernier
            try:
                self.intent_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1
                )
                logger.info("Intent classifier chargé")
            except Exception as e:
                logger.warning(f"Erreur intent classifier: {e}")
            
            # 5. Modèle pour embeddings sémantiques - Le plus critique
            if HAS_SENTENCE_TRANSFORMERS:
                try:
                    # Charge avec des paramètres sécurisés
                    self.sentence_transformer = SentenceTransformer(
                        'all-MiniLM-L6-v2',  # Modèle plus léger
                        device='cpu'  # Force CPU
                    )
                    # Configuration pour éviter les problèmes
                    self.sentence_transformer.max_seq_length = 256  # Limite la longueur
                    logger.info("SentenceTransformer chargé")
                except Exception as e:
                    logger.warning(f"Erreur SentenceTransformer: {e}")
                    self.sentence_transformer = None
            
            # 6. Modèle NLP pour extraction d'entités
            if HAS_SPACY:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    logger.info("spaCy chargé")
                except OSError:
                    logger.warning("Aucun modèle spaCy disponible")
            
            # 7. Modèle de classification personnalisé
            self._initialize_custom_classifier()
            
            # Nettoyage mémoire
            gc.collect()
            
            logger.info("Tous les modèles IA initialisés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des modèles: {e}")
    
    def _initialize_custom_classifier(self):
        """Initialise le classificateur personnalisé"""
        try:
            model_path = "custom_email_classifier.pkl"
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.custom_classifier = pickle.load(f)
                logger.info("Modèle personnalisé chargé")
            else:
                if HAS_SKLEARN:
                    self.custom_classifier = RandomForestClassifier(
                        n_estimators=100,
                        random_state=42,
                        n_jobs=1  # Évite les problèmes de parallélisation
                    )
                    logger.info("Nouveau modèle personnalisé créé")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du classificateur personnalisé: {e}")
    
    def _setup_database(self):
        """Configure la base de données pour l'apprentissage adaptatif"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT,
                    body TEXT,
                    sender TEXT,
                    category TEXT,
                    priority INTEGER,
                    sentiment TEXT,
                    intent TEXT,
                    embedding BLOB,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_confirmed BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT,
                    pattern_data TEXT,
                    confidence REAL,
                    usage_count INTEGER DEFAULT 1,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER,
                    predicted_category TEXT,
                    actual_category TEXT,
                    feedback_type TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de la base de données: {e}")
    
    def _train_simple_models(self):
        """Entraîne des modèles simples avec des données de base"""
        if not HAS_SKLEARN:
            return
            
        try:
            # Données d'entraînement simulées
            texts = []
            labels = []
            
            for category, keywords in self.categories.items():
                for keyword in keywords:
                    # Créer des phrases d'exemple
                    example_texts = [
                        f"Bonjour, je vous écris concernant {keyword}",
                        f"Voici mon {keyword} pour votre attention",
                        f"Pourriez-vous m'aider avec {keyword} s'il vous plaît",
                        f"Information importante sur {keyword}",
                        f"Demande relative à {keyword}"
                    ]
                    texts.extend(example_texts)
                    labels.extend([category] * len(example_texts))
            
            # Vectorisation et entraînement
            X = self.vectorizer.fit_transform(texts)
            self.simple_classifier.fit(X, labels)
            
            logger.info("Modèles simples entraînés")
            
        except Exception as e:
            logger.error(f"Erreur entraînement modèles simples: {e}")
    
    def classify_email(self, email) -> Dict:
        """Classification ultra-performante d'un email avec gestion sécurisée"""
        try:
            # Préparation du texte avec limitation de taille
            text = f"{email.subject} {email.body}"
            text_clean = self._preprocess_text(text)
            
            # Limitation de la taille pour éviter les problèmes mémoire
            if len(text_clean) > 2000:
                text_clean = text_clean[:2000]
            
            # Classification principale avec fallback
            if self._models_loaded and self.sentence_transformer:
                # Classification sémantique avancée
                semantic_category = self._classify_semantic_safe(text_clean)
            else:
                # Classification simple
                semantic_category = self._classify_simple(text_clean)
            
            # Classification par patterns
            pattern_category = self._classify_by_patterns(email)
            
            # Classification par intention (si modèles chargés)
            if self._models_loaded and self.intent_classifier:
                intent = self._classify_intent_safe(text_clean)
            else:
                intent = self._classify_intent_simple(text_clean)
            
            # Analyse de priorité
            priority = self._analyze_priority_advanced(email)
            
            # Détection de spam
            spam_score = self._detect_spam_safe(email)
            
            # Analyse de sentiment
            sentiment = self._analyze_sentiment_safe(text_clean)
            
            # Extraction d'entités
            entities = self._extract_entities_advanced(text_clean)
            
            # Fusion intelligente des résultats
            final_category = self._smart_fusion(semantic_category, pattern_category, intent, entities)
            
            # Calcul de la confiance
            confidence = self._calculate_confidence(semantic_category, pattern_category, intent)
            
            # Apprentissage adaptatif (asynchrone)
            self.thread_pool.submit(self._learn_from_classification, email, final_category, confidence)
            
            result = {
                'category': final_category,
                'confidence': confidence,
                'priority': priority,
                'spam_score': spam_score,
                'sentiment': sentiment,
                'intent': intent,
                'entities': entities,
                'semantic_category': semantic_category,
                'pattern_category': pattern_category,
                'reading_time': self._estimate_reading_time(text),
                'response_required': self._needs_response(text),
                'meeting_request': self._is_meeting_request(text),
                'action_items': self._extract_action_items(text),
                'key_topics': self._extract_key_topics(text)
            }
            
            logger.info(f"Email classifié: {final_category} (confiance: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {e}")
            return self._fallback_classification()
    
    def _classify_semantic_safe(self, text: str) -> Dict:
        """Classification sémantique sécurisée"""
        try:
            if not self.sentence_transformer:
                return self._classify_simple(text)
            
            # Limitation de taille pour éviter les problèmes
            if len(text) > 512:
                text = text[:512]
            
            # Génération de l'embedding avec gestion d'erreur
            try:
                with torch.no_grad():  # Évite l'accumulation de gradients
                    embedding = self.sentence_transformer.encode(
                        [text], 
                        batch_size=1,
                        show_progress_bar=False,
                        convert_to_numpy=True
                    )
            except Exception as e:
                logger.warning(f"Erreur embedding: {e}")
                return self._classify_simple(text)
            
            # Comparaison avec les catégories connues
            categories_embeddings = self._get_category_embeddings()
            
            if categories_embeddings is not None:
                try:
                    similarities = cosine_similarity(embedding, categories_embeddings)[0]
                    best_idx = np.argmax(similarities)
                    best_score = similarities[best_idx]
                    
                    categories = list(self.user_categories.keys()) if self.user_categories else list(self.categories.keys())
                    if best_score > 0.7 and best_idx < len(categories):
                        return {
                            'category': categories[best_idx],
                            'confidence': float(best_score),
                            'method': 'semantic'
                        }
                except Exception as e:
                    logger.warning(f"Erreur similarité: {e}")
            
            # Fallback vers classification simple
            return self._classify_simple(text)
            
        except Exception as e:
            logger.error(f"Erreur classification sémantique: {e}")
            return self._classify_simple(text)
    
    def _classify_intent_safe(self, text: str) -> Dict:
        """Classification d'intention sécurisée"""
        try:
            if not self.intent_classifier:
                return self._classify_intent_simple(text)
            
            # Limitation de taille
            if len(text) > 256:
                text = text[:256]
            
            # Labels d'intention prédéfinis
            candidate_labels = [
                "demande d'information",
                "demande de rendez-vous", 
                "candidature emploi",
                "réclamation",
                "proposition commerciale"
            ]
            
            try:
                result = self.intent_classifier(text, candidate_labels)
                return {
                    'intent': result['labels'][0],
                    'confidence': result['scores'][0]
                }
            except Exception as e:
                logger.warning(f"Erreur intent classification: {e}")
                return self._classify_intent_simple(text)
            
        except Exception as e:
            logger.error(f"Erreur classification d'intention: {e}")
            return self._classify_intent_simple(text)
    
    def _detect_spam_safe(self, email) -> float:
        """Détection de spam sécurisée"""
        try:
            text = f"{email.subject} {email.body}"
            
            # Détection simple par mots-clés
            spam_keywords = [
                'gratuit', 'free', 'urgent', 'cliquez', 'click', 'promotion',
                'offre', 'viagra', 'casino', 'lottery', 'winner', 'gagnant'
            ]
            
            text_lower = text.lower()
            spam_score = sum(1 for keyword in spam_keywords if keyword in text_lower)
            spam_score = min(1.0, spam_score / 3.0)  # Normaliser
            
            # Détection avec IA si disponible et modèles chargés
            if self._models_loaded and self.spam_detector:
                try:
                    # Limitation de taille
                    if len(text) > 512:
                        text = text[:512]
                    
                    result = self.spam_detector(text)
                    if isinstance(result, list) and len(result) > 0:
                        if result[0]['label'] in ['TOXIC', 'SPAM', '1']:
                            spam_score = max(spam_score, result[0]['score'])
                except Exception as e:
                    logger.warning(f"Erreur spam detection IA: {e}")
            
            return float(spam_score)
            
        except Exception as e:
            logger.error(f"Erreur détection spam: {e}")
            return 0.0
    
    def _analyze_sentiment_safe(self, text: str) -> Dict:
        """Analyse de sentiment sécurisée"""
        try:
            if self._models_loaded and self.sentiment_analyzer:
                try:
                    # Limitation de taille
                    if len(text) > 512:
                        text = text[:512]
                    
                    result = self.sentiment_analyzer(text)
                    if isinstance(result, list) and len(result) > 0:
                        return {
                            'label': result[0]['label'],
                            'confidence': result[0]['score']
                        }
                    elif isinstance(result, dict):
                        return {
                            'label': result['label'],
                            'confidence': result['score']
                        }
                except Exception as e:
                    logger.warning(f"Erreur sentiment IA: {e}")
            
            # Analyse simple de sentiment
            positive_words = ['merci', 'excellent', 'parfait', 'super', 'génial']
            negative_words = ['problème', 'erreur', 'bug', 'mauvais', 'déçu']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return {'label': 'POSITIVE', 'confidence': 0.7}
            elif negative_count > positive_count:
                return {'label': 'NEGATIVE', 'confidence': 0.7}
            else:
                return {'label': 'NEUTRAL', 'confidence': 0.6}
                
        except Exception as e:
            logger.error(f"Erreur analyse sentiment: {e}")
            return {'label': 'NEUTRAL', 'confidence': 0.5}
    
    # Toutes les autres méthodes restent identiques à la version précédente...
    
    def _classify_simple(self, text: str) -> Dict:
        """Classification simple basée sur des mots-clés"""
        try:
            text_lower = text.lower()
            
            # Recherche par mots-clés
            best_category = 'general'
            best_score = 0
            
            for category, keywords in self.categories.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                if score > best_score:
                    best_score = score
                    best_category = category
            
            # Classification avec sklearn si disponible
            if HAS_SKLEARN and hasattr(self, 'simple_classifier'):
                try:
                    X = self.vectorizer.transform([text])
                    sklearn_category = self.simple_classifier.predict(X)[0]
                    sklearn_proba = max(self.simple_classifier.predict_proba(X)[0])
                    
                    if sklearn_proba > 0.6:
                        best_category = sklearn_category
                        best_score = sklearn_proba
                except:
                    pass
            
            return {
                'category': best_category,
                'confidence': min(1.0, best_score + 0.3),
                'method': 'simple'
            }
            
        except Exception as e:
            logger.error(f"Erreur classification simple: {e}")
            return {'category': 'general', 'confidence': 0.5, 'method': 'fallback'}
    
    def _classify_by_patterns(self, email) -> Dict:
        """Classification basée sur les patterns appris de l'utilisateur"""
        try:
            # Extraction des features de l'email
            features = self._extract_email_features(email)
            
            # Pour l'instant, utilisation de règles simples
            subject_lower = email.subject.lower()
            body_lower = email.body.lower()
            
            if any(word in subject_lower for word in ['cv', 'candidature', 'resume']):
                return {'category': 'cv', 'confidence': 0.8, 'method': 'patterns'}
            elif any(word in subject_lower for word in ['rdv', 'meeting', 'rendez-vous']):
                return {'category': 'rdv', 'confidence': 0.8, 'method': 'patterns'}
            elif any(word in body_lower for word in ['urgent', 'asap', 'immédiat']):
                return {'category': 'urgent', 'confidence': 0.7, 'method': 'patterns'}
            
            return {'category': None, 'confidence': 0, 'method': 'patterns'}
            
        except Exception as e:
            logger.error(f"Erreur classification par patterns: {e}")
            return {'category': None, 'confidence': 0, 'method': 'patterns'}
    
    def _extract_email_features(self, email) -> Dict:
        """Extraction simple des features d'un email"""
        try:
            text = f"{email.subject} {email.body}"
            return {
                'length': len(text),
                'word_count': len(text.split()),
                'has_question': '?' in text,
                'has_exclamation': '!' in text,
                'sender_domain': email.get_sender_email().split('@')[1] if '@' in email.get_sender_email() else '',
                'subject_length': len(email.subject),
                'body_length': len(email.body)
            }
        except Exception as e:
            logger.error(f"Erreur extraction features: {e}")
            return {}
    
    def _classify_intent_simple(self, text: str) -> Dict:
        """Classification d'intention simplifiée"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['cv', 'candidature', 'emploi']):
            return {'intent': 'candidature emploi', 'confidence': 0.8}
        elif any(word in text_lower for word in ['rdv', 'rendez-vous', 'meeting']):
            return {'intent': 'demande de rendez-vous', 'confidence': 0.8}
        elif '?' in text:
            return {'intent': "demande d'information", 'confidence': 0.6}
        else:
            return {'intent': 'general', 'confidence': 0.5}
    
    def _analyze_priority_advanced(self, email) -> int:
        """Analyse de priorité avancée"""
        try:
            text = f"{email.subject} {email.body}".lower()
            priority_score = 1
            
            # Mots-clés d'urgence
            urgent_keywords = ['urgent', 'asap', 'immédiat', 'critique', 'important', 'deadline']
            for keyword in urgent_keywords:
                if keyword in text:
                    priority_score += 1
            
            # Analyse du domaine expéditeur
            sender = email.get_sender_email()
            if self._is_professional_email(sender):
                priority_score += 1
            
            return min(5, priority_score)
            
        except Exception as e:
            logger.error(f"Erreur analyse priorité: {e}")
            return 1
    
    def _extract_entities_advanced(self, text: str) -> Dict:
        """Extraction d'entités avancée"""
        try:
            entities = {
                'persons': [],
                'organizations': [],
                'dates': [],
                'money': [],
                'locations': [],
                'emails': [],
                'phone_numbers': [],
                'urls': []
            }
            
            # Extraction avec spaCy si disponible
            if self._models_loaded and self.nlp:
                try:
                    doc = self.nlp(text[:1000])  # Limite la taille
                    for ent in doc.ents:
                        if ent.label_ == 'PERSON':
                            entities['persons'].append(ent.text)
                        elif ent.label_ == 'ORG':
                            entities['organizations'].append(ent.text)
                        elif ent.label_ == 'DATE':
                            entities['dates'].append(ent.text)
                        elif ent.label_ == 'MONEY':
                            entities['money'].append(ent.text)
                        elif ent.label_ == 'GPE':
                            entities['locations'].append(ent.text)
                except Exception as e:
                    logger.warning(f"Erreur spaCy: {e}")
            
            # Extraction avec regex
            entities['emails'].extend(
                re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            )
            entities['phone_numbers'].extend(
                re.findall(r'\b(?:\+33|0)[1-9](?:[.\-\s]?\d{2}){4}\b', text)
            )
            entities['urls'].extend(
                re.findall(r'http[s]?://[^\s]+', text)
            )
            entities['money'].extend(
                re.findall(r'[€$£]\s*\d+(?:[.,]\d{2})?', text)
            )
            
            return entities
            
        except Exception as e:
            logger.error(f"Erreur extraction entités: {e}")
            return {}
    
    def _smart_fusion(self, semantic, pattern, intent, entities) -> str:
        """Fusion intelligente des résultats de classification"""
        candidates = []
        
        if semantic.get('confidence', 0) > 0.6:
            candidates.append((semantic['category'], semantic['confidence'] * 0.4))
        
        if pattern.get('confidence', 0) > 0.5:
            candidates.append((pattern['category'], pattern['confidence'] * 0.3))
        
        if intent.get('confidence', 0) > 0.5:
            intent_to_category = self._map_intent_to_category(intent['intent'])
            candidates.append((intent_to_category, intent['confidence'] * 0.3))
        
        if candidates:
            return max(candidates, key=lambda x: x[1])[0]
        
        return 'general'
    
    def _map_intent_to_category(self, intent: str) -> str:
        """Mappe une intention vers une catégorie"""
        mapping = {
            'candidature emploi': 'cv',
            'demande de rendez-vous': 'rdv',
            "demande d'information": 'general',
            'proposition commerciale': 'commercial',
            'réclamation': 'support'
        }
        return mapping.get(intent, 'general')
    
    def _calculate_confidence(self, semantic, pattern, intent) -> float:
        """Calcule la confiance globale de la classification"""
        confidences = []
        
        if semantic.get('confidence'):
            confidences.append(semantic['confidence'])
        if pattern.get('confidence'):
            confidences.append(pattern['confidence'])
        if intent.get('confidence'):
            confidences.append(intent['confidence'])
        
        if confidences:
            return np.mean(confidences)
        return 0.5
    
    def _learn_from_classification(self, email, final_category, confidence):
        """Apprentissage adaptatif simple (exécuté de manière asynchrone)"""
        try:
            # Stockage simple en base
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO email_data (subject, body, sender, category, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (email.subject, email.body[:500], email.get_sender_email(), 
                  final_category, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur apprentissage: {e}")
    
    def _fallback_classification(self) -> Dict:
        """Classification de secours"""
        return {
            'category': 'general',
            'confidence': 0.3,
            'priority': 1,
            'spam_score': 0.0,
            'sentiment': {'label': 'NEUTRAL', 'confidence': 0.5},
            'intent': {'intent': 'general', 'confidence': 0.5},
            'entities': {},
            'method': 'fallback',
            'reading_time': 0,
            'response_required': False,
            'meeting_request': False,
            'action_items': [],
            'key_topics': []
        }
    
    # Méthodes utilitaires
    
    def _preprocess_text(self, text: str) -> str:
        """Préprocessing du texte avec limitation de taille"""
        try:
            text = re.sub(r'<[^>]+>', '', text)  # Supprimer HTML
            text = re.sub(r'\s+', ' ', text).strip()  # Normaliser espaces
            # Limitation de taille pour éviter les problèmes mémoire
            if len(text) > 2000:
                text = text[:2000]
            return text
        except:
            return ""
    
    def _get_category_embeddings(self):
        """Récupère les embeddings des catégories"""
        if not self.user_categories:
            return None
        
        try:
            embeddings = []
            for category_data in self.user_categories.values():
                embedding = category_data.get('embedding', [])
                if embedding:
                    embeddings.append(embedding)
            
            return np.array(embeddings) if embeddings else None
        except:
            return None
    
    def _is_professional_email(self, email_address: str) -> bool:
        """Détermine si une adresse email est professionnelle"""
        try:
            personal_domains = [
                'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                'free.fr', 'orange.fr', 'wanadoo.fr', 'sfr.fr'
            ]
            
            domain = email_address.split('@')[1].lower()
            return domain not in personal_domains
            
        except Exception:
            return False
    
    def _estimate_reading_time(self, text: str) -> int:
        """Estime le temps de lecture en minutes"""
        try:
            word_count = len(text.split())
            return max(1, word_count // 200)
        except:
            return 1
    
    def _needs_response(self, text: str) -> bool:
        """Détermine si une réponse est nécessaire"""
        try:
            response_indicators = ['?', 'pourriez-vous', 'pouvez-vous', 'question', 'demande']
            text_lower = text.lower()
            return any(indicator in text_lower for indicator in response_indicators)
        except:
            return False
    
    def _is_meeting_request(self, text: str) -> bool:
        """Détermine si c'est une demande de réunion"""
        try:
            meeting_keywords = ['rendez-vous', 'meeting', 'réunion', 'rdv', 'disponibilité']
            text_lower = text.lower()
            return any(keyword in text_lower for keyword in meeting_keywords)
        except:
            return False
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extrait les éléments d'action du texte"""
        try:
            action_patterns = [
                r'il faut ([^.!?]+)',
                r'vous devez ([^.!?]+)',
                r'merci de ([^.!?]+)',
                r'pourriez-vous ([^.!?]+)'
            ]
            
            actions = []
            for pattern in action_patterns:
                matches = re.findall(pattern, text.lower())
                actions.extend(matches)
            
            return actions[:5]
        except:
            return []
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extrait les sujets clés du texte"""
        try:
            words = re.findall(r'\b\w{4,}\b', text.lower())
            common_words = ['bonjour', 'merci', 'cordialement', 'avec', 'pour', 'dans', 'vous', 'nous']
            filtered_words = [w for w in words if w not in common_words]
            word_counts = Counter(filtered_words)
            return [word for word, count in word_counts.most_common(5)]
        except:
            return []
    
    def _load_user_patterns(self):
        """Charge les patterns utilisateur"""
        try:
            if os.path.exists("user_categories.json"):
                with open("user_categories.json", 'r') as f:
                    self.user_categories = json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement patterns: {e}")
    
    # Méthodes de compatibilité avec l'ancien AIProcessor
    
    def extract_key_information(self, email) -> Dict:
        """Méthode de compatibilité - utilise classify_email"""
        try:
            result = self.classify_email(email)
            
            return {
                'category': result.get('category', 'general'),
                'priority': result.get('priority', 1),
                'should_auto_respond': result.get('category') in ['cv', 'rdv', 'support'],
                'sentiment': result.get('sentiment', {'label': 'neutral', 'confidence': 0.5}),
                'confidence': result.get('confidence', 0.5),
                'spam_score': result.get('spam_score', 0.0),
                'entities': result.get('entities', {}),
                'reading_time': result.get('reading_time', 0),
                'response_required': result.get('response_required', False),
                'meeting_request': result.get('meeting_request', False),
                'action_items': result.get('action_items', []),
                'key_topics': result.get('key_topics', [])
            }
        except Exception as e:
            logger.error(f"Erreur extract_key_information: {e}")
            return {
                'category': 'general',
                'priority': 1,
                'should_auto_respond': False,
                'sentiment': {'label': 'neutral', 'confidence': 0.5},
                'confidence': 0.5,
                'spam_score': 0.0,
                'entities': {},
                'reading_time': 0,
                'response_required': False,
                'meeting_request': False,
                'action_items': [],
                'key_topics': []
            }
    
    def should_auto_respond(self, email) -> bool:
        """Détermine si une réponse automatique est nécessaire"""
        try:
            info = self.extract_key_information(email)
            return info.get('should_auto_respond', False)
        except Exception as e:
            logger.error(f"Erreur should_auto_respond: {e}")
            return False
    
    def get_email_insights(self, email) -> Dict:
        """Génère des insights sur un email"""
        try:
            classification = self.classify_email(email)
            
            insights = {
                'classification': classification,
                'reading_time': classification.get('reading_time', 0),
                'response_required': classification.get('response_required', False),
                'deadline_detected': self._extract_deadlines(email.body),
                'meeting_request': classification.get('meeting_request', False),
                'action_items': classification.get('action_items', []),
                'key_topics': classification.get('key_topics', []),
                'sender_analysis': self._analyze_sender_profile(email.get_sender_email()),
                'follow_up_suggested': self._suggest_follow_up(email)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Erreur génération insights: {e}")
            return {'classification': self._fallback_classification()}
    
    def _extract_deadlines(self, text: str) -> List[str]:
        """Extrait les échéances du texte"""
        try:
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b'
            ]
            
            deadlines = []
            for pattern in date_patterns:
                matches = re.findall(pattern, text.lower())
                deadlines.extend(matches)
            
            return deadlines[:3]
        except:
            return []
    
    def _analyze_sender_profile(self, sender_email: str) -> Dict:
        """Analyse le profil de l'expéditeur"""
        try:
            return {
                'email': sender_email,
                'domain': sender_email.split('@')[1] if '@' in sender_email else '',
                'is_professional': self._is_professional_email(sender_email),
                'reputation': 'unknown'
            }
        except:
            return {'email': sender_email, 'reputation': 'unknown'}
    
    def _suggest_follow_up(self, email) -> bool:
        """Suggère si un suivi est nécessaire"""
        try:
            text = f"{email.subject} {email.body}".lower()
            follow_up_keywords = ['suivi', 'follow-up', 'relance', 'réponse attendue']
            return any(keyword in text for keyword in follow_up_keywords)
        except:
            return False
    
    def learn_from_feedback(self, email_id: str, predicted: str, actual: str, confidence: float = 0.5):
        """Apprentissage à partir du feedback utilisateur (asynchrone)"""
        def _store_feedback():
            try:
                conn = sqlite3.connect(self.user_feedback_db)
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email_id TEXT,
                        predicted_category TEXT,
                        actual_category TEXT,
                        confidence REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    INSERT INTO user_feedback 
                    (email_id, predicted_category, actual_category, confidence)
                    VALUES (?, ?, ?, ?)
                ''', (email_id, predicted, actual, confidence))
                
                conn.commit()
                conn.close()
                
                logger.info(f"Feedback intégré: {predicted} -> {actual}")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'apprentissage: {e}")
        
        # Exécution asynchrone pour éviter les blocages
        self.thread_pool.submit(_store_feedback)
    
    def create_custom_category(self, name: str, examples: List[str], rules: Dict = None):
        """Création d'une catégorie personnalisée"""
        def _create_category():
            try:
                # Génération d'embeddings pour les exemples si possible
                if self._models_loaded and self.sentence_transformer:
                    with torch.no_grad():
                        embeddings = self.sentence_transformer.encode(examples)
                        avg_embedding = np.mean(embeddings, axis=0)
                else:
                    avg_embedding = np.zeros(384)
                
                # Stockage de la nouvelle catégorie
                self.user_categories[name] = {
                    'embedding': avg_embedding.tolist(),
                    'examples': examples,
                    'rules': rules or {},
                    'created_at': datetime.now().isoformat(),
                    'usage_count': 0
                }
                
                # Sauvegarde
                self._save_user_categories()
                
                logger.info(f"Catégorie personnalisée créée: {name}")
                
            except Exception as e:
                logger.error(f"Erreur création catégorie: {e}")
        
        # Exécution asynchrone
        self.thread_pool.submit(_create_category)
    
    def _save_user_categories(self):
        """Sauvegarde les catégories utilisateur"""
        try:
            with open("user_categories.json", 'w') as f:
                json.dump(self.user_categories, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde catégories: {e}")
    
    def get_performance_stats(self) -> Dict:
        """Retourne les statistiques de performance"""
        try:
            return {
                'models_loaded': self._models_loaded,
                'models_status': {
                    'sentence_transformer': self.sentence_transformer is not None,
                    'email_classifier': self.email_classifier is not None,
                    'spam_detector': self.spam_detector is not None,
                    'sentiment_analyzer': self.sentiment_analyzer is not None,
                    'intent_classifier': self.intent_classifier is not None,
                    'nlp': self.nlp is not None
                },
                'categories': list(self.categories.keys()),
                'user_categories': list(self.user_categories.keys()),
                'has_torch': HAS_TORCH,
                'has_spacy': HAS_SPACY,
                'has_sklearn': HAS_SKLEARN,
                'has_transformers': HAS_TRANSFORMERS,
                'has_sentence_transformers': HAS_SENTENCE_TRANSFORMERS,
                'device': str(self.device),
                'cache_size': len(self.embeddings_cache)
            }
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
            return {}
    
    def __del__(self):
        """Nettoyage lors de la destruction de l'objet"""
        try:
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=False)
            
            # Nettoyage mémoire
            if HAS_TORCH:
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            gc.collect()
        except:
            pass

# Alias pour compatibilité avec l'ancien code
AIProcessor = AdvancedAIProcessor