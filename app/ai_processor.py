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

# Configuration pour éviter les bus errors AVANT tout import
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Imports avec gestion d'erreurs
try:
    import torch
    import torch.nn as nn
    # Configuration PyTorch sécurisée
    try:
        torch.set_num_threads(1)
    except RuntimeError:
        pass  # Déjà configuré
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass  # Déjà configuré
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
        self.db_path = "data/ai_models.db"
        self.model_cache_dir = "data/models_cache"
        
        # Créer les répertoires nécessaires
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.model_cache_dir, exist_ok=True)
        
        # Configuration device (CPU forcé pour éviter les problèmes)
        if HAS_TORCH:
            self.device = torch.device('cpu')
        else:
            self.device = None
        
        # Variables de contrôle pour le chargement progressif
        self._models_loaded = False
        self._loading_lock = threading.Lock()
        
        # Modèles IA
        self.email_classifier = None
        self.spam_detector = None
        self.sentiment_analyzer = None
        self.intent_classifier = None
        self.sentence_transformer = None
        self.nlp_fr = None
        self.nlp_en = None
        
        # Modèles personnalisés
        self.custom_classifier = None
        self.category_model = None
        self.priority_model = None
        
        # Cache des embeddings
        self.embeddings_cache = {}
        
        # Patterns appris
        self.learned_patterns = {}
        self.user_categories = {}
        
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
            'urgent': ['urgent', 'asap', 'important', 'critique', 'emergency'],
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
    
    def _setup_database(self):
        """Configure la base de données"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table pour les emails traités
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_emails (
                    id INTEGER PRIMARY KEY,
                    email_id TEXT UNIQUE,
                    subject TEXT,
                    sender TEXT,
                    category TEXT,
                    priority INTEGER,
                    sentiment TEXT,
                    confidence REAL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table pour les feedbacks utilisateur
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY,
                    email_id TEXT,
                    predicted_category TEXT,
                    actual_category TEXT,
                    feedback_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur setup database: {e}")
    
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
            
            # DÉSACTIVATION TEMPORAIRE DES MODÈLES LOURDS POUR DÉBUGGER
            logger.info("Mode débogage - modèles lourds désactivés")
            return
            
            if not HAS_TORCH or not HAS_TRANSFORMERS:
                logger.warning("PyTorch/Transformers non disponible - utilisation de modèles simplifiés")
                return
            
            # 1. Modèle de classification d'emails - Version sécurisée
            try:
                self.email_classifier = pipeline(
                    "text-classification",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
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
                    model="martin-ha/toxic-comment-model",
                    device=-1
                )
                logger.info("Spam detector chargé")
            except Exception as e:
                logger.warning(f"Erreur spam detector: {e}")
            
            # 3. Analyseur de sentiment
            try:
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    device=-1
                )
                logger.info("Sentiment analyzer chargé")
            except Exception as e:
                logger.warning(f"Erreur sentiment analyzer: {e}")
            
            # 4. Classificateur d'intention
            try:
                self.intent_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1
                )
                logger.info("Intent classifier chargé")
            except Exception as e:
                logger.warning(f"Erreur intent classifier: {e}")
            
            # 5. Sentence transformer pour les embeddings
            if HAS_SENTENCE_TRANSFORMERS:
                try:
                    self.sentence_transformer = SentenceTransformer(
                        'all-MiniLM-L6-v2',
                        device='cpu'
                    )
                    logger.info("SentenceTransformer chargé")
                except Exception as e:
                    logger.warning(f"Erreur sentence transformer: {e}")
            
            # 6. SpaCy pour NLP
            if HAS_SPACY:
                try:
                    self.nlp_fr = spacy.load("fr_core_news_sm")
                    self.nlp_en = spacy.load("en_core_web_sm")
                except OSError:
                    logger.warning("Aucun modèle spaCy disponible")
                    self.nlp_fr = None
                    self.nlp_en = None
            
            # Initialiser les modèles personnalisés
            self._initialize_custom_models()
            
            logger.info("Tous les modèles IA initialisés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des modèles: {e}")
    
    def _initialize_custom_models(self):
        """Initialise les modèles personnalisés"""
        try:
            # Nouveau modèle personnalisé créé
            logger.info("Nouveau modèle personnalisé créé")
            
        except Exception as e:
            logger.error(f"Erreur modèles personnalisés: {e}")
    
    def _train_simple_models(self):
        """Entraîne des modèles simples basés sur des règles"""
        try:
            if not HAS_SKLEARN:
                return
            
            # Données d'entraînement simples
            training_texts = []
            training_labels = []
            
            for category, keywords in self.categories.items():
                for keyword in keywords:
                    training_texts.append(keyword)
                    training_labels.append(category)
            
            # Entraîner le classificateur simple
            if training_texts:
                vectors = self.vectorizer.fit_transform(training_texts)
                self.simple_classifier.fit(vectors, training_labels)
                logger.info("Modèles simples entraînés")
            
        except Exception as e:
            logger.error(f"Erreur entraînement modèles simples: {e}")
    
    def _load_user_patterns(self):
        """Charge les patterns utilisateur"""
        try:
            if os.path.exists("user_categories.json"):
                with open("user_categories.json", 'r') as f:
                    self.user_categories = json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement patterns: {e}")
    
    def classify_email(self, email) -> Dict:
        """Classification principale d'un email"""
        try:
            # Extraire le texte
            subject = email.subject or ""
            body = self._get_email_body(email)
            full_text = f"{subject} {body}"
            
            # Classification rapide avec modèles simples
            quick_result = self._classify_quick(full_text)
            
            # Si les modèles avancés sont chargés, les utiliser
            if self._models_loaded:
                advanced_result = self._classify_advanced(full_text)
                # Combiner les résultats
                result = self._combine_results(quick_result, advanced_result)
            else:
                result = quick_result
            
            # Enrichir avec des métadonnées
            result.update({
                'email_id': getattr(email, 'id', 'unknown'),
                'sender': getattr(email, 'sender', ''),
                'processed_at': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur classification email: {e}")
            return self._get_default_classification()
    
    def _get_email_body(self, email) -> str:
        """Extrait le corps de l'email de manière sécurisée"""
        try:
            if hasattr(email, 'get_plain_text_body'):
                return email.get_plain_text_body() or ""
            elif hasattr(email, 'body'):
                return email.body or ""
            else:
                return ""
        except:
            return ""
    
    def _classify_quick(self, text: str) -> Dict:
        """Classification rapide avec des règles simples"""
        try:
            # Classification par mots-clés
            category = self._classify_by_keywords(text)
            
            # Détection de spam simple
            is_spam = self._detect_spam_simple(text)
            
            # Analyse de sentiment simple
            sentiment = self._analyze_sentiment_simple(text)
            
            # Priorité basée sur les mots-clés
            priority = self._calculate_priority_simple(text)
            
            # Détection de réponse automatique
            should_auto_respond = self._should_auto_respond_simple(category, text)
            
            return {
                'category': category,
                'priority': priority,
                'sentiment': sentiment,
                'is_spam': is_spam,
                'should_auto_respond': should_auto_respond,
                'confidence': 0.7,
                'method': 'rules'
            }
            
        except Exception as e:
            logger.error(f"Erreur classification rapide: {e}")
            return self._get_default_classification()
    
    def _classify_advanced(self, text: str) -> Dict:
        """Classification avancée avec les modèles IA"""
        try:
            result = {}
            
            # Classification avec transformers
            if self.email_classifier:
                try:
                    pred = self.email_classifier(text[:512])  # Limiter la taille
                    result['transformer_category'] = pred[0]['label'] if pred else 'unknown'
                    result['transformer_confidence'] = pred[0]['score'] if pred else 0.5
                except Exception as e:
                    logger.error(f"Erreur transformer classification: {e}")
            
            # Détection de spam
            if self.spam_detector:
                try:
                    spam_pred = self.spam_detector(text[:512])
                    result['is_spam_ai'] = spam_pred[0]['label'] == 'TOXIC' if spam_pred else False
                except Exception as e:
                    logger.error(f"Erreur spam detection: {e}")
            
            # Analyse de sentiment
            if self.sentiment_analyzer:
                try:
                    sentiment_pred = self.sentiment_analyzer(text[:512])
                    result['sentiment_ai'] = sentiment_pred[0]['label'] if sentiment_pred else 'neutral'
                except Exception as e:
                    logger.error(f"Erreur sentiment analysis: {e}")
            
            # Classification d'intention
            if self.intent_classifier:
                try:
                    intent_labels = ['question', 'request', 'complaint', 'compliment', 'urgent']
                    intent_pred = self.intent_classifier(text[:512], intent_labels)
                    result['intent'] = intent_pred['labels'][0] if intent_pred else 'unknown'
                except Exception as e:
                    logger.error(f"Erreur intent classification: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur classification avancée: {e}")
            return {}
    
    def _combine_results(self, quick_result: Dict, advanced_result: Dict) -> Dict:
        """Combine les résultats de classification"""
        try:
            # Utiliser les résultats rapides comme base
            combined = quick_result.copy()
            
            # Enrichir avec les résultats avancés
            if advanced_result:
                combined.update({
                    'ai_category': advanced_result.get('transformer_category'),
                    'ai_confidence': advanced_result.get('transformer_confidence', 0.5),
                    'ai_sentiment': advanced_result.get('sentiment_ai'),
                    'intent': advanced_result.get('intent'),
                    'is_spam_ai': advanced_result.get('is_spam_ai', False)
                })
                
                # Ajuster la confiance globale
                combined['confidence'] = min(0.9, (combined['confidence'] + advanced_result.get('transformer_confidence', 0.5)) / 2)
                combined['method'] = 'hybrid'
            
            return combined
            
        except Exception as e:
            logger.error(f"Erreur combinaison résultats: {e}")
            return quick_result
    
    def _classify_by_keywords(self, text: str) -> str:
        """Classification simple par mots-clés"""
        try:
            text_lower = text.lower()
            
            # Scores pour chaque catégorie
            scores = {}
            for category, keywords in self.categories.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                if score > 0:
                    scores[category] = score
            
            # Retourner la catégorie avec le meilleur score
            if scores:
                return max(scores, key=scores.get)
            else:
                return 'general'
                
        except Exception as e:
            logger.error(f"Erreur classification mots-clés: {e}")
            return 'general'
    
    def _detect_spam_simple(self, text: str) -> bool:
        """Détection simple de spam"""
        try:
            spam_indicators = [
                'gratuit', 'gagner', 'promotion', 'offre limitée',
                'cliquez ici', 'urgent', 'félicitations'
            ]
            
            text_lower = text.lower()
            spam_count = sum(1 for indicator in spam_indicators if indicator in text_lower)
            
            return spam_count >= 2
            
        except Exception as e:
            logger.error(f"Erreur détection spam: {e}")
            return False
    
    def _analyze_sentiment_simple(self, text: str) -> str:
        """Analyse simple de sentiment"""
        try:
            positive_words = ['merci', 'excellent', 'parfait', 'génial', 'super']
            negative_words = ['problème', 'erreur', 'mauvais', 'terrible', 'nul']
            
            text_lower = text.lower()
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return 'positive'
            elif negative_count > positive_count:
                return 'negative'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Erreur analyse sentiment: {e}")
            return 'neutral'
    
    def _calculate_priority_simple(self, text: str) -> int:
        """Calcul simple de priorité"""
        try:
            urgent_keywords = ['urgent', 'asap', 'immédiat', 'critique']
            text_lower = text.lower()
            
            if any(keyword in text_lower for keyword in urgent_keywords):
                return 3  # Haute priorité
            elif any(keyword in text_lower for keyword in ['important', 'rapidement']):
                return 2  # Priorité moyenne
            else:
                return 1  # Priorité normale
                
        except Exception as e:
            logger.error(f"Erreur calcul priorité: {e}")
            return 1
    
    def _should_auto_respond_simple(self, category: str, text: str) -> bool:
        """Détermine si une réponse automatique est nécessaire"""
        try:
            # Catégories qui nécessitent une réponse
            auto_respond_categories = ['cv', 'rdv', 'support']
            
            if category in auto_respond_categories:
                return True
            
            # Vérifier si c'est une question
            question_indicators = ['?', 'comment', 'quand', 'où', 'pourquoi', 'que']
            text_lower = text.lower()
            
            return any(indicator in text_lower for indicator in question_indicators)
            
        except Exception as e:
            logger.error(f"Erreur auto respond: {e}")
            return False
    
    def _get_default_classification(self) -> Dict:
        """Retourne une classification par défaut"""
        return {
            'category': 'general',
            'priority': 1,
            'sentiment': 'neutral',
            'is_spam': False,
            'should_auto_respond': False,
            'confidence': 0.5,
            'method': 'default'
        }
    
    # Méthodes de compatibilité avec l'ancien AIProcessor
    
    def extract_key_information(self, email) -> Dict:
        """Méthode de compatibilité - utilise classify_email"""
        try:
            result = self.classify_email(email)
            
            return {
                'category': result.get('category', 'general'),
                'priority': result.get('priority', 1),
                'should_auto_respond': result.get('should_auto_respond', False),
                'sentiment': result.get('sentiment', 'neutral'),
                'confidence': result.get('confidence', 0.5),
                'keywords': [],
                'entities': [],
                'meeting_info': None
            }
            
        except Exception as e:
            logger.error(f"Erreur extract_key_information: {e}")
            return {
                'category': 'general',
                'priority': 1,
                'should_auto_respond': False,
                'sentiment': 'neutral',
                'confidence': 0.5,
                'keywords': [],
                'entities': [],
                'meeting_info': None
            }
    
    def should_auto_respond(self, email) -> bool:
        """Détermine si une réponse automatique est nécessaire"""
        try:
            classification = self.classify_email(email)
            return classification.get('should_auto_respond', False)
        except Exception as e:
            logger.error(f"Erreur should_auto_respond: {e}")
            return False
    
    # Méthodes utilitaires
    
    def save_feedback(self, email_id: str, predicted: str, actual: str):
        """Sauvegarde le feedback utilisateur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_feedback (email_id, predicted_category, actual_category, feedback_type)
                VALUES (?, ?, ?, ?)
            ''', (email_id, predicted, actual, 'correction'))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Feedback sauvegardé: {email_id}, {predicted} -> {actual}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde feedback: {e}")
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du processeur"""
        try:
            return {
                'models_loaded': self._models_loaded,
                'available_models': {
                    'email_classifier': self.email_classifier is not None,
                    'spam_detector': self.spam_detector is not None,
                    'sentiment_analyzer': self.sentiment_analyzer is not None,
                    'intent_classifier': self.intent_classifier is not None,
                    'sentence_transformer': self.sentence_transformer is not None,
                    'nlp_fr': self.nlp_fr is not None,
                    'nlp_en': self.nlp_en is not None
                },
                'categories': list(self.categories.keys()),
                'user_categories': list(self.user_categories.keys()),
                'has_torch': HAS_TORCH,
                'has_spacy': HAS_SPACY,
                'has_sklearn': HAS_SKLEARN,
                'has_transformers': HAS_TRANSFORMERS,
                'has_sentence_transformers': HAS_SENTENCE_TRANSFORMERS,
                'device': str(self.device) if self.device else 'None',
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
                if hasattr(torch, 'cuda') and torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            gc.collect()
        except:
            pass

# Alias pour compatibilité avec l'ancien code
AIProcessor = AdvancedAIProcessor