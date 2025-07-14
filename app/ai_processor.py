"""
Processeur IA avancé pour l'analyse et la classification intelligente des emails.
Version améliorée avec détection précise des spams et classification intelligente.
"""

import logging
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import hashlib
import json

# Imports optionnels pour éviter les erreurs
try:
    import torch
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logger = logging.getLogger(__name__)

class AdvancedAIProcessor:
    """Processeur IA avancé pour l'analyse d'emails avec détection intelligente."""
    
    def __init__(self):
        """Initialise le processeur IA avec des modèles optimisés."""
        # Configuration des modèles
        self.model_configs = {
            'classification_model': 'cardiffnlp/twitter-roberta-base-emotion',
            'spam_model': 'martin-ha/toxic-comment-model',
            'sentiment_model': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
            'intent_model': 'microsoft/DialoGPT-medium'
        }
        
        # État des modèles
        self._models_loaded = False
        self._loading_lock = threading.Lock()
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        
        # Modèles IA
        self.email_classifier = None
        self.spam_detector = None
        self.sentiment_analyzer = None
        self.intent_classifier = None
        self.nlp = None
        
        # Modèles statistiques
        self.spam_vectorizer = None
        self.legitimate_vectorizer = None
        
        # Base de données pour le machine learning
        self.db_path = "data/ai_learning.db"
        self._setup_database()
        
        # Patterns et règles avancées
        self._setup_advanced_patterns()
        
        # Cache pour optimiser les performances
        self._classification_cache = {}
        self._cache_max_size = 1000
        
        # Charger les modèles de manière asynchrone
        self._initialize_models_async()
        
        logger.info("AdvancedAIProcessor initialisé")
    
    def _setup_advanced_patterns(self):
        """Configure les patterns avancés pour la classification."""
        
        # Patterns de spam plus sophistiqués
        self.spam_patterns = {
            'promotional': [
                r'\b(?:gratuit|free|offre?\s+(?:spéciale?|limitée?))\b',
                r'\b(?:promo(?:tion)?|reduction|discount|remise)\b',
                r'\b(?:gagn[eéz]+|win|earn|money|argent)\b',
                r'\b(?:casino|lottery|loterie|jeu|gambling)\b',
                r'\b(?:miracle|amazing|incroyable|fantastique)\b'
            ],
            'scam': [
                r'\b(?:urgent|emergency|immediat|asap)\b.*\b(?:money|argent|transfer)\b',
                r'\b(?:prince|princess|roi|reine|heritage|inheritance)\b',
                r'\b(?:lottery|loterie).*\b(?:winner|gagnant)\b',
                r'\b(?:click\s+here|cliquez\s+ici|suivez\s+ce\s+lien)\b'
            ],
            'phishing': [
                r'\b(?:verify|verifi[eéz]+|confirm|confirme[zr])\b.*\b(?:account|compte|password|mot\s+de\s+passe)\b',
                r'\b(?:suspended|suspendu|expired|expire|security|securite)\b',
                r'\b(?:bank|banque|paypal|amazon|google|microsoft)\b.*\b(?:account|compte)\b'
            ]
        }
        
        # Patterns de classification par contenu
        self.category_patterns = {
            'cv_candidature': [
                r'\b(?:cv|curriculum|resume|candidature|application|postul)\b',
                r'\b(?:recherche|search|looking\s+for|cherche).*\b(?:emploi|job|work|position|poste)\b',
                r'\b(?:experience|expérience|formation|education|diploma|diplome)\b',
                r'\b(?:motivation|cover\s+letter|lettre\s+(?:de\s+)?motivation)\b'
            ],
            'rdv_meeting': [
                r'\b(?:rdv|rendez[-\s]vous|meeting|reunion|entretien|rencontre)\b',
                r'\b(?:disponible?|available|libre|free).*\b(?:pour|for|le|on)\b',
                r'\b(?:calendrier|calendar|planning|agenda|schedule)\b',
                r'\b(?:confirme[zr]?|confirm|reporter|reschedule|annule[zr]?|cancel)\b'
            ],
            'facture_finance': [
                r'\b(?:facture|invoice|bill|payment|paiement|devis|quote)\b',
                r'\b(?:montant|amount|total|prix|price|cost|cout)\b',
                r'\b(?:€|euro|dollar|\$|£|pound)\s*\d+',
                r'\b(?:comptabilite|accounting|finance|budget)\b'
            ],
            'support_client': [
                r'\b(?:probleme|problem|issue|bug|erreur|error)\b',
                r'\b(?:support|aide|help|assistance|service\s+client)\b',
                r'\b(?:question|demand[eé]|request|besoin|need)\b',
                r'\b(?:urgent|priority|priorité|important)\b'
            ],
            'newsletter': [
                r'\b(?:newsletter|bulletin|news|actualit[eés])\b',
                r'\b(?:subscribe|abonnement|inscription|s\'abonner)\b',
                r'\b(?:unsubscribe|désabonnement|se\s+désabonner)\b',
                r'\b(?:weekly|mensuel|monthly|quotidien|daily)\b'
            ],
            'partenariat': [
                r'\b(?:partenariat|partnership|collaboration|collaborer)\b',
                r'\b(?:proposition|proposal|opportunit[eéy]|business)\b',
                r'\b(?:influenceur|influencer|sponsor|brand)\b',
                r'\b(?:cooperation|coopération|joint\s+venture)\b'
            ]
        }
        
        # Indicateurs d'urgence et de priorité
        self.urgency_patterns = [
            r'\b(?:urgent|emergency|immediat|asap|rush)\b',
            r'\b(?:deadline|date\s+limite|échéance)\b',
            r'\b(?:important|crucial|vital|critical)\b',
            r'[!]{2,}',  # Plusieurs points d'exclamation
            r'\b(?:please|s\'il\s+vous\s+plait|svp|help|aide)\b'
        ]
        
        # Patterns de réponse automatique à éviter
        self.auto_reply_avoid_patterns = [
            r'\b(?:auto[-\s]?reply|réponse\s+automatique|out\s+of\s+office|absent)\b',
            r'\b(?:vacation|vacances|congé|holiday)\b',
            r'\b(?:delivery\s+failure|échec\s+de\s+livraison|bounce|undelivered)\b',
            r'\b(?:noreply|no[-\s]?reply|ne\s+pas\s+répondre)\b'
        ]
    
    def _setup_database(self):
        """Configure la base de données pour l'apprentissage."""
        try:
            Path("data").mkdir(exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table pour stocker les classifications
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_classifications (
                    id INTEGER PRIMARY KEY,
                    email_hash TEXT UNIQUE,
                    subject TEXT,
                    sender TEXT,
                    category TEXT,
                    is_spam BOOLEAN,
                    sentiment TEXT,
                    priority INTEGER,
                    confidence REAL,
                    method TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table pour les feedbacks utilisateur
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY,
                    email_hash TEXT,
                    predicted_category TEXT,
                    actual_category TEXT,
                    feedback_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table pour les patterns de spam appris
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY,
                    pattern_type TEXT,
                    pattern_value TEXT,
                    confidence REAL,
                    usage_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur setup database: {e}")
    
    def _initialize_models_async(self):
        """Initialise les modèles de manière asynchrone."""
        def _load_models():
            try:
                with self._loading_lock:
                    self._initialize_models()
                    self._models_loaded = True
                    logger.info("Tous les modèles IA ont été chargés avec succès")
            except Exception as e:
                logger.error(f"Erreur chargement modèles async: {e}")
        
        # Démarrer le chargement en arrière-plan
        self.thread_pool.submit(_load_models)
    
    def _initialize_models(self):
        """Initialise tous les modèles IA de manière sécurisée."""
        try:
            logger.info("Initialisation des modèles IA avancés...")
            
            # Vérifier les dépendances
            if not HAS_TORCH:
                logger.warning("PyTorch non disponible - modèles simplifiés uniquement")
                return
            
            # 1. Classificateur d'emails spécialisé
            try:
                self.email_classifier = pipeline(
                    "text-classification",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1,  # Force CPU pour la stabilité
                    return_all_scores=True
                )
                logger.info("✅ Email classifier chargé")
            except Exception as e:
                logger.warning(f"⚠️ Erreur email classifier: {e}")
            
            # 2. Détecteur de spam avancé
            try:
                self.spam_detector = pipeline(
                    "text-classification",
                    model="unitary/toxic-bert",
                    device=-1,
                    return_all_scores=True
                )
                logger.info("✅ Spam detector chargé")
            except Exception as e:
                logger.warning(f"⚠️ Erreur spam detector: {e}")
            
            # 3. Analyseur de sentiment précis
            try:
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    device=-1,
                    return_all_scores=True
                )
                logger.info("✅ Sentiment analyzer chargé")
            except Exception as e:
                logger.warning(f"⚠️ Erreur sentiment analyzer: {e}")
            
            # 4. Modèle spaCy pour l'extraction d'entités
            if HAS_SPACY:
                try:
                    self.nlp = spacy.load("fr_core_news_sm")
                    logger.info("✅ spaCy français chargé")
                except:
                    try:
                        self.nlp = spacy.load("en_core_web_sm")
                        logger.info("✅ spaCy anglais chargé")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur spaCy: {e}")
            
            # 5. Initialiser les vectorizers pour les modèles statistiques
            if HAS_SKLEARN:
                self._initialize_statistical_models()
            
        except Exception as e:
            logger.error(f"Erreur générale initialisation modèles: {e}")
    
    def _initialize_statistical_models(self):
        """Initialise les modèles statistiques basés sur l'historique."""
        try:
            # Charger l'historique depuis la base de données
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Récupérer les emails légitimes et les spams
            cursor.execute("""
                SELECT subject || ' ' || COALESCE(sender, '') as text, is_spam
                FROM email_classifications 
                WHERE confidence > 0.8
            """)
            
            historical_data = cursor.fetchall()
            conn.close()
            
            if len(historical_data) > 10:  # Assez de données pour l'apprentissage
                texts = [item[0] for item in historical_data]
                labels = [item[1] for item in historical_data]
                
                # Créer des vectorizers séparés pour spam/légitime
                spam_texts = [text for text, is_spam in zip(texts, labels) if is_spam]
                legit_texts = [text for text, is_spam in zip(texts, labels) if not is_spam]
                
                if spam_texts:
                    self.spam_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                    self.spam_vectorizer.fit(spam_texts)
                
                if legit_texts:
                    self.legitimate_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                    self.legitimate_vectorizer.fit(legit_texts)
                
                logger.info(f"Modèles statistiques entraînés sur {len(historical_data)} emails")
            
        except Exception as e:
            logger.error(f"Erreur initialisation modèles statistiques: {e}")
    
    def classify_email(self, email) -> Dict[str, Any]:
        """
        Classifie un email avec une analyse multi-niveaux.
        
        Args:
            email: L'objet email à analyser
            
        Returns:
            Dictionnaire contenant tous les résultats d'analyse
        """
        try:
            # Extraire le texte de l'email
            subject = getattr(email, 'subject', '') or ""
            body = self._get_email_body(email)
            sender = getattr(email, 'sender', '') or ""
            
            # Créer un hash unique pour le cache
            email_text = f"{subject} {body} {sender}"
            email_hash = hashlib.md5(email_text.encode()).hexdigest()
            
            # Vérifier le cache
            if email_hash in self._classification_cache:
                return self._classification_cache[email_hash]
            
            # Classification multi-niveaux
            result = {
                'email_hash': email_hash,
                'processed_at': datetime.now().isoformat(),
                'processing_method': 'multi_level'
            }
            
            # 1. Analyse rapide avec des règles
            quick_analysis = self._quick_rule_based_analysis(subject, body, sender)
            result.update(quick_analysis)
            
            # 2. Analyse avancée avec IA (si disponible)
            if self._models_loaded:
                ai_analysis = self._advanced_ai_analysis(subject, body, sender)
                result = self._merge_analysis_results(result, ai_analysis)
            
            # 3. Analyse statistique basée sur l'historique
            statistical_analysis = self._statistical_analysis(subject, body, sender)
            result = self._merge_analysis_results(result, statistical_analysis)
            
            # 4. Calcul de la confiance finale
            result['final_confidence'] = self._calculate_final_confidence(result)
            
            # 5. Décision finale intelligente
            final_decision = self._make_final_decision(result)
            result.update(final_decision)
            
            # Mettre en cache et sauvegarder
            self._cache_result(email_hash, result)
            self._save_classification_to_db(result, subject, sender)
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur classification email: {e}")
            return self._get_default_classification()
    
    def _quick_rule_based_analysis(self, subject: str, body: str, sender: str) -> Dict[str, Any]:
        """Analyse rapide basée sur des règles expertes."""
        try:
            full_text = f"{subject} {body}".lower()
            
            # Détection de spam par règles
            spam_score = 0
            spam_reasons = []
            
            # Patterns de spam
            for spam_type, patterns in self.spam_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, full_text, re.IGNORECASE):
                        spam_score += 0.3
                        spam_reasons.append(f"{spam_type}:{pattern[:30]}")
            
            # Analyse de l'expéditeur
            sender_analysis = self._analyze_sender(sender)
            spam_score += sender_analysis['spam_score']
            
            # Classification par catégorie
            category_scores = {}
            for category, patterns in self.category_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, full_text, re.IGNORECASE))
                    score += matches * 0.2
                category_scores[category] = min(score, 1.0)
            
            # Catégorie principale
            main_category = max(category_scores.items(), key=lambda x: x[1])
            
            # Analyse de l'urgence
            urgency_score = 0
            for pattern in self.urgency_patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    urgency_score += 0.25
            
            # Détecter les réponses automatiques à éviter
            should_avoid_reply = False
            for pattern in self.auto_reply_avoid_patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    should_avoid_reply = True
                    break
            
            return {
                'rule_based': {
                    'is_spam': spam_score > 0.5,
                    'spam_score': min(spam_score, 1.0),
                    'spam_reasons': spam_reasons,
                    'category': main_category[0],
                    'category_confidence': main_category[1],
                    'category_scores': category_scores,
                    'urgency_score': min(urgency_score, 1.0),
                    'should_avoid_auto_reply': should_avoid_reply,
                    'sender_analysis': sender_analysis
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse règles: {e}")
            return {'rule_based': {'error': str(e)}}
    
    def _advanced_ai_analysis(self, subject: str, body: str, sender: str) -> Dict[str, Any]:
        """Analyse avancée avec les modèles IA."""
        try:
            full_text = f"{subject} {body}"
            # Limiter la taille pour les modèles
            text_sample = full_text[:512] if len(full_text) > 512 else full_text
            
            ai_results = {}
            
            # Classification avec le modèle principal
            if self.email_classifier:
                try:
                    classification = self.email_classifier(text_sample)
                    ai_results['transformer_classification'] = classification
                except Exception as e:
                    logger.warning(f"Erreur transformer classification: {e}")
            
            # Détection de spam IA
            if self.spam_detector:
                try:
                    spam_detection = self.spam_detector(text_sample)
                    ai_results['ai_spam_detection'] = spam_detection
                except Exception as e:
                    logger.warning(f"Erreur AI spam detection: {e}")
            
            # Analyse de sentiment
            if self.sentiment_analyzer:
                try:
                    sentiment = self.sentiment_analyzer(text_sample)
                    ai_results['sentiment_analysis'] = sentiment
                except Exception as e:
                    logger.warning(f"Erreur sentiment analysis: {e}")
            
            # Extraction d'entités avec spaCy
            if self.nlp:
                try:
                    doc = self.nlp(text_sample)
                    entities = {
                        'persons': [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
                        'orgs': [ent.text for ent in doc.ents if ent.label_ == "ORG"],
                        'dates': [ent.text for ent in doc.ents if ent.label_ == "DATE"],
                        'money': [ent.text for ent in doc.ents if ent.label_ == "MONEY"]
                    }
                    ai_results['entities'] = entities
                except Exception as e:
                    logger.warning(f"Erreur extraction entités: {e}")
            
            return {'ai_analysis': ai_results}
            
        except Exception as e:
            logger.error(f"Erreur analyse IA: {e}")
            return {'ai_analysis': {'error': str(e)}}
    
    def _statistical_analysis(self, subject: str, body: str, sender: str) -> Dict[str, Any]:
        """Analyse statistique basée sur l'historique."""
        try:
            if not HAS_SKLEARN or not self.spam_vectorizer:
                return {'statistical_analysis': {'available': False}}
            
            text = f"{subject} {body}"
            
            results = {'available': True}
            
            # Similarité avec les spams connus
            if self.spam_vectorizer:
                try:
                    text_vector = self.spam_vectorizer.transform([text])
                    # Calculer la similarité moyenne avec les spams de référence
                    # (simulation - dans une vraie implémentation, on aurait une matrice de référence)
                    spam_similarity = 0.1  # Placeholder
                    results['spam_similarity'] = spam_similarity
                except Exception as e:
                    logger.warning(f"Erreur calcul similarité spam: {e}")
            
            # Similarité avec les emails légitimes
            if self.legitimate_vectorizer:
                try:
                    text_vector = self.legitimate_vectorizer.transform([text])
                    legit_similarity = 0.8  # Placeholder
                    results['legitimate_similarity'] = legit_similarity
                except Exception as e:
                    logger.warning(f"Erreur calcul similarité légitime: {e}")
            
            return {'statistical_analysis': results}
            
        except Exception as e:
            logger.error(f"Erreur analyse statistique: {e}")
            return {'statistical_analysis': {'error': str(e)}}
    
    def _analyze_sender(self, sender: str) -> Dict[str, Any]:
        """Analyse approfondie de l'expéditeur."""
        try:
            analysis = {
                'spam_score': 0,
                'domain_reputation': 'unknown',
                'is_suspicious': False,
                'reasons': []
            }
            
            if not sender:
                analysis['spam_score'] = 0.2
                analysis['reasons'].append('no_sender')
                return analysis
            
            # Extraire le domaine
            domain_match = re.search(r'@([^>]+)', sender)
            if not domain_match:
                analysis['spam_score'] = 0.3
                analysis['reasons'].append('invalid_email_format')
                return analysis
            
            domain = domain_match.group(1).lower()
            
            # Domaines suspects
            suspicious_domains = [
                'tempmail', 'guerrillamail', '10minutemail', 'throwaway',
                'mailinator', 'yopmail', 'temp-mail'
            ]
            
            for suspicious in suspicious_domains:
                if suspicious in domain:
                    analysis['spam_score'] += 0.4
                    analysis['is_suspicious'] = True
                    analysis['reasons'].append(f'suspicious_domain:{suspicious}')
            
            # Domaines de confiance
            trusted_domains = [
                'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
                'apple.com', 'icloud.com', 'protonmail.com'
            ]
            
            if domain in trusted_domains:
                analysis['domain_reputation'] = 'trusted'
                analysis['spam_score'] = max(0, analysis['spam_score'] - 0.2)
            
            # Patterns suspects dans l'adresse
            if re.search(r'\d{5,}', sender):  # Beaucoup de chiffres
                analysis['spam_score'] += 0.1
                analysis['reasons'].append('many_numbers')
            
            if re.search(r'[^\w@.-]', sender):  # Caractères bizarres
                analysis['spam_score'] += 0.2
                analysis['reasons'].append('weird_characters')
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur analyse sender: {e}")
            return {'spam_score': 0, 'error': str(e)}
    
    def _merge_analysis_results(self, base_result: Dict, new_analysis: Dict) -> Dict:
        """Fusionne les résultats d'analyses multiples."""
        try:
            # Fusion simple - dans une vraie implémentation, on utiliserait une logique plus sophistiquée
            merged = base_result.copy()
            merged.update(new_analysis)
            return merged
        except Exception as e:
            logger.error(f"Erreur fusion résultats: {e}")
            return base_result
    
    def _calculate_final_confidence(self, analysis_result: Dict) -> float:
        """Calcule la confiance finale basée sur tous les indicateurs."""
        try:
            confidence_factors = []
            
            # Confiance des règles
            if 'rule_based' in analysis_result:
                rule_confidence = analysis_result['rule_based'].get('category_confidence', 0.5)
                confidence_factors.append(rule_confidence * 0.4)
            
            # Confiance IA
            if 'ai_analysis' in analysis_result:
                ai_data = analysis_result['ai_analysis']
                if 'transformer_classification' in ai_data:
                    # Prendre la confiance max des résultats transformer
                    transformer_conf = 0.7  # Placeholder
                    confidence_factors.append(transformer_conf * 0.5)
            
            # Confiance statistique
            if 'statistical_analysis' in analysis_result:
                stat_data = analysis_result['statistical_analysis']
                if stat_data.get('available', False):
                    stat_confidence = 0.6  # Placeholder
                    confidence_factors.append(stat_confidence * 0.1)
            
            # Calculer la moyenne pondérée
            if confidence_factors:
                final_confidence = sum(confidence_factors) / len(confidence_factors)
            else:
                final_confidence = 0.5
            
            return min(max(final_confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Erreur calcul confiance: {e}")
            return 0.5
    
    def _make_final_decision(self, analysis_result: Dict) -> Dict[str, Any]:
        """Prend les décisions finales basées sur toutes les analyses."""
        try:
            decisions = {}
            
            # Décision spam
            spam_indicators = []
            
            if 'rule_based' in analysis_result:
                rule_spam = analysis_result['rule_based'].get('is_spam', False)
                spam_score = analysis_result['rule_based'].get('spam_score', 0)
                spam_indicators.append((rule_spam, spam_score, 'rules'))
            
            if 'ai_analysis' in analysis_result:
                # Analyser les résultats IA pour spam
                ai_spam = False  # Placeholder - analyser les vrais résultats
                spam_indicators.append((ai_spam, 0.3, 'ai'))
            
            # Décision finale spam
            spam_votes = sum(1 for is_spam, score, method in spam_indicators if is_spam)
            total_votes = len(spam_indicators)
            
            decisions['is_spam'] = spam_votes > total_votes / 2
            decisions['spam_confidence'] = spam_votes / total_votes if total_votes > 0 else 0
            
            # Décision catégorie
            if 'rule_based' in analysis_result:
                decisions['category'] = analysis_result['rule_based'].get('category', 'other')
                decisions['category_confidence'] = analysis_result['rule_based'].get('category_confidence', 0.5)
            
            # Décision urgence
            urgency_score = 0
            if 'rule_based' in analysis_result:
                urgency_score = analysis_result['rule_based'].get('urgency_score', 0)
            
            decisions['priority'] = self._calculate_priority(urgency_score, decisions.get('category', 'other'))
            
            # Décision réponse automatique
            should_auto_respond = self._should_auto_respond(analysis_result, decisions)
            decisions['should_auto_respond'] = should_auto_respond
            
            # Sentiment final
            decisions['sentiment'] = self._extract_final_sentiment(analysis_result)
            
            return decisions
            
        except Exception as e:
            logger.error(f"Erreur décision finale: {e}")
            return {
                'is_spam': False,
                'category': 'other',
                'priority': 2,
                'should_auto_respond': False,
                'sentiment': 'neutral'
            }
    
    def _calculate_priority(self, urgency_score: float, category: str) -> int:
        """Calcule la priorité de 1 (urgent) à 5 (bas)."""
        try:
            # Base de priorité selon la catégorie
            category_priorities = {
                'support_client': 2,
                'rdv_meeting': 2,
                'cv_candidature': 3,
                'facture_finance': 2,
                'partenariat': 3,
                'newsletter': 4,
                'spam': 5
            }
            
            base_priority = category_priorities.get(category, 3)
            
            # Ajuster selon l'urgence
            if urgency_score > 0.7:
                priority = max(1, base_priority - 2)
            elif urgency_score > 0.4:
                priority = max(1, base_priority - 1)
            else:
                priority = base_priority
            
            return min(priority, 5)
            
        except Exception as e:
            logger.error(f"Erreur calcul priorité: {e}")
            return 3
    
    def _should_auto_respond(self, analysis_result: Dict, decisions: Dict) -> bool:
        """Détermine si une réponse automatique est appropriée."""
        try:
            # Ne jamais répondre aux spams
            if decisions.get('is_spam', False):
                return False
            
            # Ne pas répondre aux newsletters
            if decisions.get('category') == 'newsletter':
                return False
            
            # Vérifier les patterns d'évitement
            if 'rule_based' in analysis_result:
                if analysis_result['rule_based'].get('should_avoid_auto_reply', False):
                    return False
            
            # Catégories qui méritent une réponse
            auto_respond_categories = ['cv_candidature', 'rdv_meeting', 'support_client', 'partenariat']
            
            return decisions.get('category') in auto_respond_categories
            
        except Exception as e:
            logger.error(f"Erreur décision auto-réponse: {e}")
            return False
    
    def _extract_final_sentiment(self, analysis_result: Dict) -> str:
        """Extrait le sentiment final de l'email."""
        try:
            # Priorité à l'analyse IA si disponible
            if 'ai_analysis' in analysis_result:
                ai_sentiment = analysis_result['ai_analysis'].get('sentiment_analysis')
                if ai_sentiment:
                    # Analyser les résultats du sentiment analyzer
                    # (Placeholder - dans la vraie implémentation, analyser les scores)
                    return 'neutral'
            
            # Fallback sur l'analyse par règles
            urgency = analysis_result.get('rule_based', {}).get('urgency_score', 0)
            
            if urgency > 0.6:
                return 'urgent'
            elif urgency > 0.3:
                return 'concerned'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Erreur extraction sentiment: {e}")
            return 'neutral'
    
    def _get_email_body(self, email) -> str:
        """Extrait le corps de l'email de manière sécurisée."""
        try:
            # Essayer différentes méthodes d'extraction
            if hasattr(email, 'get_plain_text_body'):
                body = email.get_plain_text_body()
            elif hasattr(email, 'body'):
                body = email.body
            elif hasattr(email, 'get_body'):
                body = email.get_body()
            else:
                body = ""
            
            # Nettoyer le texte
            if body:
                # Supprimer les balises HTML basiques
                body = re.sub(r'<[^>]+>', '', str(body))
                # Normaliser les espaces
                body = re.sub(r'\s+', ' ', body)
                # Limiter la taille
                body = body[:2000] if len(body) > 2000 else body
            
            return body or ""
            
        except Exception as e:
            logger.error(f"Erreur extraction corps email: {e}")
            return ""
    
    def _cache_result(self, email_hash: str, result: Dict):
        """Met en cache le résultat pour éviter les recalculs."""
        try:
            # Gérer la taille du cache
            if len(self._classification_cache) >= self._cache_max_size:
                # Supprimer les plus anciens (FIFO simple)
                oldest_key = next(iter(self._classification_cache))
                del self._classification_cache[oldest_key]
            
            self._classification_cache[email_hash] = result
            
        except Exception as e:
            logger.error(f"Erreur mise en cache: {e}")
    
    def _save_classification_to_db(self, result: Dict, subject: str, sender: str):
        """Sauvegarde la classification en base pour l'apprentissage."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO email_classifications 
                (email_hash, subject, sender, category, is_spam, sentiment, priority, confidence, method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.get('email_hash', ''),
                subject[:200],  # Limiter la taille
                sender[:100],
                result.get('category', 'other'),
                result.get('is_spam', False),
                result.get('sentiment', 'neutral'),
                result.get('priority', 3),
                result.get('final_confidence', 0.5),
                result.get('processing_method', 'unknown')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde DB: {e}")
    
    def _get_default_classification(self) -> Dict[str, Any]:
        """Retourne une classification par défaut en cas d'erreur."""
        return {
            'category': 'other',
            'is_spam': False,
            'sentiment': 'neutral',
            'priority': 3,
            'should_auto_respond': False,
            'final_confidence': 0.3,
            'processing_method': 'default',
            'processed_at': datetime.now().isoformat(),
            'error': True
        }
    
    def add_user_feedback(self, email_hash: str, predicted_category: str, actual_category: str):
        """Ajoute un feedback utilisateur pour améliorer le modèle."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_feedback 
                (email_hash, predicted_category, actual_category, feedback_type)
                VALUES (?, ?, ?, ?)
            """, (email_hash, predicted_category, actual_category, 'correction'))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Feedback ajouté: {predicted_category} -> {actual_category}")
            
            # Relancer l'apprentissage si assez de feedbacks
            self._update_models_with_feedback()
            
        except Exception as e:
            logger.error(f"Erreur ajout feedback: {e}")
    
    def _update_models_with_feedback(self):
        """Met à jour les modèles basés sur les feedbacks utilisateur."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Compter les feedbacks
            cursor.execute("SELECT COUNT(*) FROM user_feedback")
            feedback_count = cursor.fetchone()[0]
            
            conn.close()
            
            # Relancer l'apprentissage si assez de données
            if feedback_count > 50 and feedback_count % 25 == 0:
                logger.info("Relancement de l'apprentissage avec les nouveaux feedbacks")
                self._retrain_statistical_models()
                
        except Exception as e:
            logger.error(f"Erreur mise à jour modèles: {e}")
    
    def _retrain_statistical_models(self):
        """Réentraîne les modèles statistiques avec les nouvelles données."""
        try:
            if not HAS_SKLEARN:
                return
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Récupérer toutes les classifications avec feedback
            cursor.execute("""
                SELECT ec.subject || ' ' || COALESCE(ec.sender, '') as text, 
                       COALESCE(uf.actual_category, ec.category) as category,
                       ec.is_spam
                FROM email_classifications ec
                LEFT JOIN user_feedback uf ON ec.email_hash = uf.email_hash
                WHERE ec.confidence > 0.5
            """)
            
            data = cursor.fetchall()
            conn.close()
            
            if len(data) > 20:
                # Réentraîner les vectorizers
                texts = [item[0] for item in data]
                spam_labels = [item[2] for item in data]
                
                spam_texts = [text for text, spam in zip(texts, spam_labels) if spam]
                legit_texts = [text for text, spam in zip(texts, spam_labels) if not spam]
                
                if len(spam_texts) > 5:
                    self.spam_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                    self.spam_vectorizer.fit(spam_texts)
                
                if len(legit_texts) > 5:
                    self.legitimate_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                    self.legitimate_vectorizer.fit(legit_texts)
                
                logger.info(f"Modèles réentraînés avec {len(data)} exemples")
            
        except Exception as e:
            logger.error(f"Erreur réentraînement: {e}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """Retourne le statut de tous les modèles."""
        return {
            'models_loaded': self._models_loaded,
            'email_classifier': self.email_classifier is not None,
            'spam_detector': self.spam_detector is not None,
            'sentiment_analyzer': self.sentiment_analyzer is not None,
            'nlp_model': self.nlp is not None,
            'statistical_models': {
                'spam_vectorizer': self.spam_vectorizer is not None,
                'legitimate_vectorizer': self.legitimate_vectorizer is not None
            },
            'dependencies': {
                'torch': HAS_TORCH,
                'spacy': HAS_SPACY,
                'sklearn': HAS_SKLEARN
            },
            'cache_size': len(self._classification_cache)
        }
    
    def clear_cache(self):
        """Vide le cache de classification."""
        self._classification_cache.clear()
        logger.info("Cache de classification vidé")
    
    def __del__(self):
        """Nettoyage lors de la destruction de l'objet."""
        try:
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=False)
        except:
            pass
AIProcessor = AdvancedAIProcessor
