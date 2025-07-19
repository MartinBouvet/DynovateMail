#!/usr/bin/env python3
"""
Classification intelligente des emails avec scoring multicritères et apprentissage.
"""
import logging
import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import sqlite3
import hashlib
from pathlib import Path

# Imports conditionnels pour éviter les erreurs
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    logging.warning("Module spaCy non disponible - fonctionnement en mode dégradé")

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning("Module transformers non disponible - fonctionnement en mode dégradé")

logger = logging.getLogger(__name__)

@dataclass
class EmailAnalysis:
    """Résultat d'analyse d'un email."""
    category: str
    confidence: float
    priority: int  # 1=urgent, 5=low
    should_auto_respond: bool
    suggested_response: Optional[str]
    extracted_info: Dict
    reasoning: str

class SmartClassifier:
    """Classificateur intelligent avec apprentissage et context awareness."""
    
    def __init__(self, model_path: str = "app/data/classifier.db"):
        self.model_path = model_path
        self.nlp = None
        self.sentiment_analyzer = None
        self._init_models()
        self._init_database()
        
        # Patterns de détection améliorés
        self.patterns = {
            'cv': [
                r'\b(cv|curriculum|résumé|candidature|postule|emploi|poste|job)\b',
                r'\b(experience|compétence|formation|diplôme|qualification)\b',
                r'\b(lettre de motivation|cover letter)\b'
            ],
            'rdv': [
                r'\b(rendez[-\s]?vous|meeting|réunion|entretien|call)\b',
                r'\b(disponible|créneau|calendrier|planning)\b',
                r'\b(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b',
                r'\d{1,2}[h:]\d{2}|\d{1,2}h\d{2}|\d{1,2}:\d{2}'
            ],
            'facture': [
                r'\b(facture|invoice|bill|payment|paiement)\b',
                r'\b(montant|prix|coût|€|euro|dollar|\$)\b',
                r'\b(due|échéance|deadline)\b'
            ],
            'support': [
                r'\b(aide|help|support|problème|issue|bug)\b',
                r'\b(erreur|error|panne|dysfonctionnement)\b',
                r'\b(urgent|critique|emergency)\b'
            ],
            'spam': [
                r'\b(gratuit|free|promo|offre|reduction|discount)\b',
                r'\b(cliquez|click|urgent|limited|limité)\b',
                r'[A-Z]{3,}.*[A-Z]{3,}'  # Beaucoup de majuscules
            ]
        }
        
        # Mots-clés d'évitement pour auto-réponse
        self.avoid_auto_response = [
            r'\b(ne pas répondre|do not reply|noreply)\b',
            r'\b(automatique|automatic|newsletter)\b',
            r'\b(notification|alert|reminder)\b'
        ]
    
    def _init_models(self):
        """Initialise les modèles NLP."""
        try:
            # Modèle spaCy pour l'analyse linguistique
            if HAS_SPACY:
                self.nlp = spacy.load("fr_core_news_sm")
            
            # Pipeline Transformers pour l'analyse de sentiment
            if HAS_TRANSFORMERS:
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    return_all_scores=True
                )
            
            logger.info("Modèles IA initialisés avec succès")
        except Exception as e:
            logger.error(f"Erreur initialisation modèles: {e}")
            # Fallback sans modèles avancés
            self.nlp = None
            self.sentiment_analyzer = None
    
    def _init_database(self):
        """Initialise la base de données pour l'apprentissage."""
        try:
            # Créer le dossier si nécessaire
            Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.model_path)
            cursor = conn.cursor()
            
            # Table pour stocker les corrections utilisateur
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_corrections (
                    id INTEGER PRIMARY KEY,
                    email_hash TEXT UNIQUE,
                    original_category TEXT,
                    corrected_category TEXT,
                    timestamp DATETIME,
                    confidence REAL
                )
            ''')
            
            # Table pour l'historique des performances
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY,
                    date DATE,
                    total_emails INTEGER,
                    correct_classifications INTEGER,
                    accuracy REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Base de données d'apprentissage initialisée")
        except Exception as e:
            logger.error(f"Erreur init base de données: {e}")
    
    def analyze_email(self, email_data: Dict) -> EmailAnalysis:
        """
        Analyse complète d'un email avec scoring multicritères.
        
        Args:
            email_data: Dict avec subject, body, sender, date etc.
            
        Returns:
            EmailAnalysis avec tous les résultats
        """
        try:
            # Extraction du contenu
            subject = email_data.get('subject', '').lower()
            body = email_data.get('body', '').lower()
            sender = email_data.get('sender', '').lower()
            full_text = f"{subject} {body}".strip()
            
            # Scoring multicritères
            category_scores = self._calculate_category_scores(full_text, sender)
            best_category = max(category_scores.items(), key=lambda x: x[1])
            
            # Analyse de priorité
            priority = self._calculate_priority(full_text, best_category[0])
            
            # Décision auto-réponse
            should_respond = self._should_auto_respond(full_text, best_category[0])
            
            # Extraction d'informations spécifiques
            extracted_info = self._extract_specific_info(full_text, best_category[0])
            
            # Génération de réponse suggérée
            suggested_response = None
            if should_respond:
                suggested_response = self._generate_response_suggestion(
                    email_data, best_category[0], extracted_info
                )
            
            # Explication du raisonnement
            reasoning = self._explain_reasoning(category_scores, best_category)
            
            return EmailAnalysis(
                category=best_category[0],
                confidence=best_category[1],
                priority=priority,
                should_auto_respond=should_respond,
                suggested_response=suggested_response,
                extracted_info=extracted_info,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Erreur analyse email: {e}")
            return self._fallback_analysis()
    
    def _calculate_category_scores(self, text: str, sender: str) -> Dict[str, float]:
        """Calcule les scores pour chaque catégorie."""
        scores = {'general': 0.1}  # Score de base
        
        for category, patterns in self.patterns.items():
            score = 0.0
            
            # Score basé sur les patterns regex
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches * 0.3
            
            # Bonus pour certains expéditeurs
            if category == 'facture' and any(word in sender for word in ['billing', 'invoice', 'facture']):
                score += 0.4
            elif category == 'cv' and 'candidat' in text:
                score += 0.5
            elif category == 'rdv' and any(word in text for word in ['calendly', 'zoom', 'teams']):
                score += 0.4
            
            # Analyse NLP avancée si disponible
            if self.nlp:
                score += self._nlp_category_score(text, category)
            
            # Apprentissage utilisateur
            score += self._get_user_learning_bonus(text, category)
            
            scores[category] = min(score, 1.0)  # Cap à 1.0
        
        return scores
    
    def _nlp_category_score(self, text: str, category: str) -> float:
        """Score basé sur l'analyse NLP avancée."""
        try:
            if not self.nlp:
                return 0.0
                
            doc = self.nlp(text[:1000])  # Limite pour les performances
            
            # Entités nommées pertinentes
            entities = [ent.label_ for ent in doc.ents]
            
            category_entities = {
                'cv': ['PERSON', 'ORG'],
                'rdv': ['DATE', 'TIME', 'PERSON'],
                'facture': ['MONEY', 'DATE', 'ORG'],
                'support': ['PRODUCT', 'ORG']
            }
            
            relevant_entities = category_entities.get(category, [])
            entity_score = len([e for e in entities if e in relevant_entities]) * 0.1
            
            return min(entity_score, 0.3)
        except:
            return 0.0
    
    def _get_user_learning_bonus(self, text: str, category: str) -> float:
        """Bonus basé sur l'apprentissage des corrections utilisateur."""
        try:
            email_hash = hashlib.md5(text.encode()).hexdigest()
            
            conn = sqlite3.connect(self.model_path)
            cursor = conn.cursor()
            
            # Chercher des corrections similaires
            cursor.execute('''
                SELECT corrected_category, confidence FROM user_corrections 
                WHERE email_hash = ? OR corrected_category = ?
                ORDER BY timestamp DESC LIMIT 5
            ''', (email_hash, category))
            
            results = cursor.fetchall()
            conn.close()
            
            if results:
                # Moyenne pondérée des corrections récentes
                total_weight = 0
                weighted_bonus = 0
                for corrected_cat, confidence in results:
                    weight = confidence if corrected_cat == category else -confidence
                    weighted_bonus += weight * 0.2
                    total_weight += abs(weight)
                
                return weighted_bonus / max(total_weight, 1) if total_weight > 0 else 0
            
            return 0.0
        except:
            return 0.0
    
    def _calculate_priority(self, text: str, category: str) -> int:
        """Calcule la priorité de l'email (1=urgent, 5=low)."""
        base_priorities = {
            'support': 2,
            'rdv': 2,
            'facture': 3,
            'cv': 4,
            'spam': 5,
            'general': 3
        }
        
        priority = base_priorities.get(category, 3)
        
        # Mots-clés d'urgence
        urgent_keywords = ['urgent', 'emergency', 'critique', 'asap', 'immédiat']
        if any(keyword in text for keyword in urgent_keywords):
            priority = max(1, priority - 2)
        
        # Analyse de sentiment pour détecter la frustration
        if self.sentiment_analyzer:
            try:
                sentiment = self.sentiment_analyzer(text[:500])
                if sentiment and len(sentiment) > 0 and len(sentiment[0]) > 0:
                    negative_score = next((s['score'] for s in sentiment[0] if s['label'] == 'NEGATIVE'), 0)
                    if negative_score > 0.7:
                        priority = max(1, priority - 1)
            except:
                pass
        
        return min(priority, 5)
    
    def _should_auto_respond(self, text: str, category: str) -> bool:
        """Détermine si une réponse automatique est appropriée."""
        # Ne jamais répondre aux spams
        if category == 'spam':
            return False
        
        # Vérifier les patterns d'évitement
        for pattern in self.avoid_auto_response:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Catégories qui méritent une réponse
        auto_respond_categories = ['cv', 'rdv', 'support']
        
        return category in auto_respond_categories
    
    def _extract_specific_info(self, text: str, category: str) -> Dict:
        """Extrait des informations spécifiques selon la catégorie."""
        info = {}
        
        if category == 'rdv':
            # Extraction de dates/heures
            date_patterns = [
                r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
                r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b',
                r'\b(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b'
            ]
            
            time_patterns = [
                r'\b(\d{1,2}):(\d{2})\b',
                r'\b(\d{1,2})h(\d{2})\b',
                r'\b(\d{1,2})h\b'
            ]
            
            dates = []
            times = []
            
            for pattern in date_patterns:
                dates.extend(re.findall(pattern, text, re.IGNORECASE))
            
            for pattern in time_patterns:
                times.extend(re.findall(pattern, text))
            
            info['potential_dates'] = dates
            info['potential_times'] = times
        
        elif category == 'cv':
            # Extraction d'informations candidat
            if self.nlp:
                try:
                    doc = self.nlp(text)
                    persons = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
                    info['candidate_names'] = persons[:3]  # Max 3 noms
                except:
                    pass
        
        elif category == 'facture':
            # Extraction de montants
            money_patterns = [
                r'(\d+[,.]?\d*)\s*€',
                r'€\s*(\d+[,.]?\d*)',
                r'(\d+[,.]?\d*)\s*euros?'
            ]
            
            amounts = []
            for pattern in money_patterns:
                amounts.extend(re.findall(pattern, text, re.IGNORECASE))
            
            info['amounts'] = amounts[:5]  # Max 5 montants
        
        return info
    
    def _generate_response_suggestion(self, email_data: Dict, category: str, extracted_info: Dict) -> str:
        """Génère une suggestion de réponse contextuelle."""
        sender_name = email_data.get('sender_name', 'Monsieur/Madame')
        
        templates = {
            'cv': f"""Bonjour {sender_name},

Merci pour votre candidature et l'intérêt que vous portez à notre entreprise.

Nous avons bien reçu votre CV et nous l'examinerons attentivement. Nous vous recontacterons dans les meilleurs délais si votre profil correspond à nos besoins actuels.

Cordialement,
[Votre nom]""",

            'rdv': f"""Bonjour {sender_name},

Merci pour votre demande de rendez-vous.

Je consulte mon planning et vous propose les créneaux suivants :
- [Date 1] à [Heure 1]
- [Date 2] à [Heure 2]

N'hésitez pas à me confirmer le créneau qui vous convient le mieux.

Cordialement,
[Votre nom]""",

            'support': f"""Bonjour {sender_name},

Merci de nous avoir contactés concernant votre demande d'assistance.

Nous avons bien pris en compte votre message et notre équipe technique va examiner votre problème. Nous vous apporterons une réponse dans les plus brefs délais.

Cordialement,
L'équipe support"""
        }
        
        return templates.get(category, f"Bonjour {sender_name},\n\nMerci pour votre message. Nous vous répondrons rapidement.\n\nCordialement,")
    
    def _explain_reasoning(self, scores: Dict[str, float], best_category: Tuple[str, float]) -> str:
        """Génère une explication du raisonnement de classification."""
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        explanation = f"Classé comme '{best_category[0]}' (confiance: {best_category[1]:.2f})\n"
        explanation += f"Scores alternatifs: "
        explanation += ", ".join([f"{cat}: {score:.2f}" for cat, score in top_3[1:]])
        
        return explanation
    
    def _fallback_analysis(self) -> EmailAnalysis:
        """Analyse de fallback en cas d'erreur."""
        return EmailAnalysis(
            category='general',
            confidence=0.1,
            priority=3,
            should_auto_respond=False,
            suggested_response=None,
            extracted_info={},
            reasoning="Analyse par défaut (erreur)"
        )
    
    def learn_from_correction(self, email_data: Dict, original_category: str, corrected_category: str):
        """Apprend d'une correction utilisateur."""
        try:
            text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
            email_hash = hashlib.md5(text.encode()).hexdigest()
            
            conn = sqlite3.connect(self.model_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_corrections 
                (email_hash, original_category, corrected_category, timestamp, confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (email_hash, original_category, corrected_category, datetime.now(), 0.8))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Correction apprise: {original_category} -> {corrected_category}")
        except Exception as e:
            logger.error(f"Erreur apprentissage correction: {e}")