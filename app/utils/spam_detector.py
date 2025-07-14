"""
Détecteur de spam avancé avec analyse multi-niveaux.
Combine règles expertes, machine learning et analyse comportementale.
"""

import logging
import re
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json

# Imports conditionnels
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import IsolationForest
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logger = logging.getLogger(__name__)

class AdvancedSpamDetector:
    """Détecteur de spam multi-niveaux avec apprentissage adaptatif."""
    
    def __init__(self, data_dir: str = "data/spam_detection/"):
        """
        Initialise le détecteur de spam.
        
        Args:
            data_dir: Répertoire pour les données du détecteur
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Base de données pour l'historique
        self.db_path = self.data_dir / "spam_detection.db"
        self._setup_database()
        
        # Modèles de détection
        self.vectorizer = None
        self.anomaly_detector = None
        self.spam_signatures = set()
        
        # Patterns de spam sophistiqués
        self._setup_spam_patterns()
        
        # Whitelist et blacklist
        self.sender_whitelist = set()
        self.sender_blacklist = set()
        self.domain_reputation = {}
        
        # Seuils de détection
        self.spam_threshold = 0.6
        self.suspicious_threshold = 0.4
        
        # Cache de détection
        self._detection_cache = {}
        self._cache_max_size = 1000
        
        # Statistiques
        self.stats = {
            'total_analyzed': 0,
            'spam_detected': 0,
            'false_positives': 0,
            'false_negatives': 0
        }
        
        # Charger les données existantes
        self._load_existing_data()
        
        logger.info("AdvancedSpamDetector initialisé")
    
    def _setup_database(self):
        """Configure la base de données de détection."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table des analyses de spam
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_analysis (
                    id INTEGER PRIMARY KEY,
                    email_hash TEXT UNIQUE,
                    subject TEXT,
                    sender TEXT,
                    domain TEXT,
                    is_spam BOOLEAN,
                    spam_score REAL,
                    detection_method TEXT,
                    reasons TEXT,
                    is_verified BOOLEAN DEFAULT FALSE,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des signatures de spam
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_signatures (
                    id INTEGER PRIMARY KEY,
                    signature_hash TEXT UNIQUE,
                    pattern_type TEXT,
                    pattern_value TEXT,
                    confidence REAL,
                    detection_count INTEGER DEFAULT 1,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table de réputation des domaines
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS domain_reputation (
                    id INTEGER PRIMARY KEY,
                    domain TEXT UNIQUE,
                    reputation_score REAL,
                    spam_count INTEGER DEFAULT 0,
                    legitimate_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des expéditeurs de confiance/bloqués
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sender_lists (
                    id INTEGER PRIMARY KEY,
                    sender_email TEXT UNIQUE,
                    list_type TEXT,
                    added_by TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur setup database spam: {e}")
    
    def _setup_spam_patterns(self):
        """Configure les patterns de détection de spam."""
        
        # Patterns de contenu spam
        self.spam_content_patterns = {
            'financial_scam': [
                r'\b(?:urgent|immediat).*(?:money|argent|transfer|virement)\b',
                r'\b(?:million|dollars?|euros?).*(?:inherit|heritage|testament)\b',
                r'\b(?:lottery|loterie|prize|prix).*(?:won|gagn[eé]|winner|gagnant)\b',
                r'\b(?:bank|banque).*(?:transfer|virement|account|compte)\b'
            ],
            'promotional_spam': [
                r'\b(?:gratuit|free|offre?).*(?:limit[eé]e?|special|exclusive)\b',
                r'\b(?:promo(?:tion)?|discount|reduction|remise).*\d+%\b',
                r'\b(?:achetez|buy).*(?:maintenant|now|immediately)\b',
                r'\b(?:derniere|last).*(?:chance|opportunit[eéy])\b'
            ],
            'pharmaceutical': [
                r'\b(?:viagra|cialis|pharmacy|pharmacie)\b',
                r'\b(?:pills|pilules|medication|medicament)\b',
                r'\b(?:prescription|ordonnance).*(?:required|necessaire)\b'
            ],
            'adult_content': [
                r'\b(?:adult|adulte|xxx|sex|dating|rencontre)\b',
                r'\b(?:casino|gambling|poker|bet|pari)\b'
            ],
            'phishing': [
                r'\b(?:verify|verifi[eéz]+).*(?:account|compte|identity|identit[eé])\b',
                r'\b(?:suspend[eéd]+|expired|expire).*(?:account|compte)\b',
                r'\b(?:click|cliquez).*(?:here|ici|link|lien)\b',
                r'\b(?:confirm|confirme[zr]).*(?:password|mot\s+de\s+passe)\b'
            ]
        }
        
        # Patterns d'expéditeur suspect
        self.suspicious_sender_patterns = [
            r'^[a-z0-9]{10,}@',  # Adresses aléatoires longues
            r'@(?:temp|guerrilla|10minute|throwaway)',  # Emails temporaires
            r'\.(?:tk|ml|ga|cf)$',  # Domaines gratuits suspects
            r'[0-9]{5,}',  # Beaucoup de chiffres dans l'email
            r'[^a-zA-Z0-9@.\-_]'  # Caractères spéciaux suspects
        ]
        
        # Patterns de sujet spam
        self.spam_subject_patterns = [
            r'^(?:RE:|FW:).*(?:URGENT|IMPORTANT).*!{2,}',  # Faux RE/FW urgents
            r'^[A-Z\s!]+$',  # Tout en majuscules
            r'[!]{3,}',  # Multiples points d'exclamation
            r'\$\d+|\d+€|\d+\s*(?:euro|dollar)',  # Montants d'argent
            r'\b(?:winner|gagnant|congratulation|felicitation)\b'  # Mots de victoire
        ]
        
        # Indicateurs de contenu généré automatiquement
        self.auto_generated_patterns = [
            r'(?:this\s+is\s+an?\s+)?(?:auto(?:matic)?[-\s]?(?:reply|response|message))',
            r'out\s+of\s+office|absence|vacation|vacances',
            r'delivery\s+(?:failure|notification)|bounce|undelivered',
            r'mailer[-\s]?daemon|postmaster|no[-\s]?reply'
        ]
    
    def analyze_email(self, subject: str, body: str, sender: str, 
                     sender_name: str = "", headers: Dict = None) -> Dict[str, Any]:
        """
        Analyse complète d'un email pour détecter le spam.
        
        Args:
            subject: Sujet de l'email
            body: Corps de l'email
            sender: Adresse de l'expéditeur
            sender_name: Nom de l'expéditeur
            headers: Headers de l'email (optionnel)
            
        Returns:
            Résultat d'analyse complet
        """
        try:
            # Créer un hash unique pour le cache
            email_content = f"{subject} {body} {sender}"
            email_hash = hashlib.md5(email_content.encode()).hexdigest()
            
            # Vérifier le cache
            if email_hash in self._detection_cache:
                return self._detection_cache[email_hash]
            
            # Initialiser le résultat
            analysis_result = {
                'email_hash': email_hash,
                'is_spam': False,
                'spam_score': 0.0,
                'confidence': 0.0,
                'reasons': [],
                'detection_method': 'multi_level',
                'analyzed_at': datetime.now().isoformat()
            }
            
            # 1. Vérification des listes blanches/noires
            whitelist_result = self._check_sender_lists(sender)
            if whitelist_result['decision'] is not None:
                analysis_result.update(whitelist_result)
                self._cache_result(email_hash, analysis_result)
                return analysis_result
            
            # 2. Analyse par règles expertes
            rule_analysis = self._rule_based_analysis(subject, body, sender, sender_name)
            analysis_result['spam_score'] += rule_analysis['score'] * 0.4
            analysis_result['reasons'].extend(rule_analysis['reasons'])
            
            # 3. Analyse de l'expéditeur et du domaine
            sender_analysis = self._analyze_sender_reputation(sender)
            analysis_result['spam_score'] += sender_analysis['score'] * 0.3
            analysis_result['reasons'].extend(sender_analysis['reasons'])
            
            # 4. Analyse du contenu avec ML (si disponible)
            if HAS_SKLEARN and self.vectorizer:
                ml_analysis = self._machine_learning_analysis(subject, body)
                analysis_result['spam_score'] += ml_analysis['score'] * 0.2
                analysis_result['reasons'].extend(ml_analysis['reasons'])
            
            # 5. Analyse comportementale
            behavioral_analysis = self._behavioral_analysis(subject, body, sender, headers)
            analysis_result['spam_score'] += behavioral_analysis['score'] * 0.1
            analysis_result['reasons'].extend(behavioral_analysis['reasons'])
            
            # 6. Normaliser le score et prendre la décision finale
            analysis_result['spam_score'] = min(analysis_result['spam_score'], 1.0)
            analysis_result['is_spam'] = analysis_result['spam_score'] > self.spam_threshold
            analysis_result['confidence'] = self._calculate_confidence(analysis_result)
            
            # 7. Catégoriser le niveau de risque
            analysis_result['risk_level'] = self._categorize_risk(analysis_result['spam_score'])
            
            # Sauvegarder et mettre en cache
            self._save_analysis(analysis_result, subject, sender)
            self._cache_result(email_hash, analysis_result)
            
            # Mettre à jour les statistiques
            self._update_stats(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Erreur analyse spam: {e}")
            return self._get_default_analysis()
    
    def _check_sender_lists(self, sender: str) -> Dict[str, Any]:
        """Vérifie les listes blanches et noires."""
        try:
            sender = sender.lower().strip()
            domain = self._extract_domain(sender)
            
            # Vérifier la whitelist
            if sender in self.sender_whitelist or domain in self.sender_whitelist:
                return {
                    'decision': False,  # Pas de spam
                    'is_spam': False,
                    'spam_score': 0.0,
                    'confidence': 0.95,
                    'reasons': ['sender_whitelisted'],
                    'detection_method': 'whitelist'
                }
            
            # Vérifier la blacklist
            if sender in self.sender_blacklist or domain in self.sender_blacklist:
                return {
                    'decision': True,  # C'est du spam
                    'is_spam': True,
                    'spam_score': 1.0,
                    'confidence': 0.95,
                    'reasons': ['sender_blacklisted'],
                    'detection_method': 'blacklist'
                }
            
            return {'decision': None}
            
        except Exception as e:
            logger.error(f"Erreur vérification listes: {e}")
            return {'decision': None}
    
    def _rule_based_analysis(self, subject: str, body: str, sender: str, sender_name: str) -> Dict[str, Any]:
        """Analyse basée sur des règles expertes."""
        try:
            score = 0.0
            reasons = []
            
            full_text = f"{subject} {body}".lower()
            
            # Analyser les patterns de contenu spam
            for category, patterns in self.spam_content_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, full_text, re.IGNORECASE):
                        matches += 1
                
                if matches > 0:
                    category_score = min(matches * 0.2, 0.6)
                    score += category_score
                    reasons.append(f'spam_content_{category}_{matches}_matches')
            
            # Analyser le sujet
            for pattern in self.spam_subject_patterns:
                if re.search(pattern, subject, re.IGNORECASE):
                    score += 0.15
                    reasons.append(f'suspicious_subject_pattern')
            
            # Analyser l'expéditeur
            for pattern in self.suspicious_sender_patterns:
                if re.search(pattern, sender, re.IGNORECASE):
                    score += 0.1
                    reasons.append(f'suspicious_sender_pattern')
            
            # Vérifier les auto-replies (pas du spam mais à éviter)
            for pattern in self.auto_generated_patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    score -= 0.2  # Réduire le score spam
                    reasons.append('auto_generated_message')
            
            # Analyser la structure du message
            structure_score, structure_reasons = self._analyze_message_structure(subject, body)
            score += structure_score
            reasons.extend(structure_reasons)
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'reasons': reasons
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse règles: {e}")
            return {'score': 0.0, 'reasons': []}
    
    def _analyze_message_structure(self, subject: str, body: str) -> Tuple[float, List[str]]:
        """Analyse la structure du message pour détecter les patterns spam."""
        try:
            score = 0.0
            reasons = []
            
            # Ratio sujet/corps suspect
            if subject and body:
                subject_len = len(subject)
                body_len = len(body)
                total_len = subject_len + body_len
                
                if total_len > 0:
                    subject_ratio = subject_len / total_len
                    
                    # Sujet trop long par rapport au corps
                    if subject_ratio > 0.7:
                        score += 0.1
                        reasons.append('subject_too_long_ratio')
                    
                    # Corps trop court
                    if body_len < 50 and subject_len > 20:
                        score += 0.1
                        reasons.append('body_too_short')
            
            # Compter les URLs
            url_count = len(re.findall(r'http[s]?://\S+', body))
            if url_count > 3:
                score += min(url_count * 0.05, 0.2)
                reasons.append(f'too_many_urls_{url_count}')
            
            # Ratio texte/liens
            if body and url_count > 0:
                text_length = len(re.sub(r'http[s]?://\S+', '', body))
                if text_length > 0:
                    link_ratio = url_count / (text_length / 100)  # URLs per 100 chars
                    if link_ratio > 0.5:
                        score += 0.15
                        reasons.append('high_link_density')
            
            # HTML suspect
            html_tags = len(re.findall(r'<[^>]+>', body))
            if html_tags > 10:
                score += 0.1
                reasons.append('excessive_html')
            
            # Caractères non-ASCII suspects
            non_ascii_count = sum(1 for c in f"{subject}{body}" if ord(c) > 127)
            total_chars = len(f"{subject}{body}")
            if total_chars > 0 and non_ascii_count / total_chars > 0.3:
                score += 0.1
                reasons.append('excessive_non_ascii')
            
            # Répétition de caractères
            if re.search(r'(.)\1{4,}', f"{subject}{body}"):
                score += 0.1
                reasons.append('character_repetition')
            
            return score, reasons
            
        except Exception as e:
            logger.error(f"Erreur analyse structure: {e}")
            return 0.0, []
    
    def _analyze_sender_reputation(self, sender: str) -> Dict[str, Any]:
        """Analyse la réputation de l'expéditeur."""
        try:
            score = 0.0
            reasons = []
            
            domain = self._extract_domain(sender)
            
            # Vérifier la réputation du domaine
            if domain in self.domain_reputation:
                reputation = self.domain_reputation[domain]
                if reputation < 0.3:
                    score += 0.4
                    reasons.append(f'bad_domain_reputation_{reputation:.2f}')
                elif reputation > 0.8:
                    score -= 0.2  # Bonus pour bonne réputation
                    reasons.append(f'good_domain_reputation_{reputation:.2f}')
            
            # Domaines temporaires ou suspects
            suspicious_domains = [
                'tempmail', 'guerrillamail', '10minutemail', 'throwaway',
                'mailinator', 'yopmail', 'temp-mail', 'dispostable'
            ]
            
            for suspicious in suspicious_domains:
                if suspicious in domain:
                    score += 0.5
                    reasons.append(f'temporary_email_domain_{suspicious}')
                    break
            
            # TLD suspects
            suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.top', '.click']
            for tld in suspicious_tlds:
                if domain.endswith(tld):
                    score += 0.3
                    reasons.append(f'suspicious_tld_{tld}')
                    break
            
            # Analyser l'historique récent
            recent_score = self._get_recent_sender_history(sender)
            score += recent_score['spam_score']
            reasons.extend(recent_score['reasons'])
            
            return {
                'score': min(max(score, 0.0), 1.0),
                'reasons': reasons
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse réputation: {e}")
            return {'score': 0.0, 'reasons': []}
    
    def _machine_learning_analysis(self, subject: str, body: str) -> Dict[str, Any]:
        """Analyse avec machine learning."""
        try:
            if not self.vectorizer or not self.anomaly_detector:
                return {'score': 0.0, 'reasons': []}
            
            # Vectoriser le texte
            text = f"{subject} {body}"
            text_vector = self.vectorizer.transform([text])
            
            # Détection d'anomalie
            anomaly_score = self.anomaly_detector.decision_function(text_vector)[0]
            
            # Convertir en score de spam (anomaly_score négatif = anomalie)
            if anomaly_score < -0.5:
                spam_score = min(abs(anomaly_score) / 2, 0.8)
                reasons = [f'ml_anomaly_detected_{anomaly_score:.3f}']
            else:
                spam_score = 0.0
                reasons = []
            
            return {
                'score': min(spam_score, 1.0),
                'reasons': reasons
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse ML: {e}")
            return {'score': 0.0, 'reasons': []}
    
    def _behavioral_analysis(self, subject: str, body: str, sender: str, headers: Dict) -> Dict[str, Any]:
        """Analyse comportementale avancée."""
        try:
            score = 0.0
            reasons = []
            
            # Analyser les patterns temporels
            temporal_score = self._analyze_temporal_patterns(sender)
            score += temporal_score['score']
            reasons.extend(temporal_score['reasons'])
            
            # Analyser les headers (si disponibles)
            if headers:
                header_score = self._analyze_headers(headers)
                score += header_score['score']
                reasons.extend(header_score['reasons'])
            
            # Détection de campagnes de spam
            campaign_score = self._detect_spam_campaign(subject, body, sender)
            score += campaign_score['score']
            reasons.extend(campaign_score['reasons'])
            
            return {
                'score': min(score, 1.0),
                'reasons': reasons
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse comportementale: {e}")
            return {'score': 0.0, 'reasons': []}
    
    def _analyze_temporal_patterns(self, sender: str) -> Dict[str, Any]:
        """Analyse les patterns temporels de l'expéditeur."""
        try:
            # Vérifier la fréquence d'envoi récente
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Compter les emails des dernières heures
            recent_time = datetime.now() - timedelta(hours=24)
            cursor.execute("""
                SELECT COUNT(*) FROM spam_analysis 
                WHERE sender = ? AND analyzed_at > ?
            """, (sender, recent_time.isoformat()))
            
            recent_count = cursor.fetchone()[0]
            conn.close()
            
            score = 0.0
            reasons = []
            
            # Trop d'emails récents du même expéditeur
            if recent_count > 10:
                score += min(recent_count * 0.05, 0.4)
                reasons.append(f'high_frequency_sender_{recent_count}_emails_24h')
            
            return {'score': score, 'reasons': reasons}
            
        except Exception as e:
            logger.error(f"Erreur analyse temporelle: {e}")
            return {'score': 0.0, 'reasons': []}
    
    def _analyze_headers(self, headers: Dict) -> Dict[str, Any]:
        """Analyse les headers de l'email."""
        try:
            score = 0.0
            reasons = []
            
            # Vérifier les SPF, DKIM, DMARC
            auth_results = headers.get('Authentication-Results', {})
            if isinstance(auth_results, dict):
                spf_result = auth_results.get('spf', 'none')
                dkim_result = auth_results.get('dkim', 'none')
                
                if spf_result == 'fail':
                    score += 0.3
                    reasons.append('spf_failure')
                
                if dkim_result == 'fail':
                    score += 0.2
                    reasons.append('dkim_failure')
            
            # Vérifier les relais suspects
            received_headers = headers.get('Received', [])
            if isinstance(received_headers, list):
                for received in received_headers:
                    if re.search(r'(?:tor|proxy|vpn)', received, re.IGNORECASE):
                        score += 0.2
                        reasons.append('suspicious_relay')
                        break
            
            return {'score': score, 'reasons': reasons}
            
        except Exception as e:
            logger.error(f"Erreur analyse headers: {e}")
            return {'score': 0.0, 'reasons': []}
    
    def _detect_spam_campaign(self, subject: str, body: str, sender: str) -> Dict[str, Any]:
        """Détecte les campagnes de spam."""
        try:
            # Créer une signature du message
            signature = self._create_message_signature(subject, body)
            
            # Vérifier si cette signature existe déjà
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT detection_count FROM spam_signatures 
                WHERE signature_hash = ?
            """, (signature,))
            
            result = cursor.fetchone()
            
            score = 0.0
            reasons = []
            
            if result:
                detection_count = result[0]
                if detection_count > 5:
                    score += min(detection_count * 0.1, 0.5)
                    reasons.append(f'known_spam_signature_{detection_count}_detections')
                
                # Mettre à jour le compteur
                cursor.execute("""
                    UPDATE spam_signatures 
                    SET detection_count = detection_count + 1,
                        last_seen = CURRENT_TIMESTAMP
                    WHERE signature_hash = ?
                """, (signature,))
            else:
                # Nouvelle signature
                cursor.execute("""
                    INSERT INTO spam_signatures 
                    (signature_hash, pattern_type, pattern_value, confidence)
                    VALUES (?, ?, ?, ?)
                """, (signature, 'content', f"{subject[:50]}...", 0.5))
            
            conn.commit()
            conn.close()
            
            return {'score': score, 'reasons': reasons}
            
        except Exception as e:
            logger.error(f"Erreur détection campagne: {e}")
            return {'score': 0.0, 'reasons': []}
    
    def _create_message_signature(self, subject: str, body: str) -> str:
        """Crée une signature unique du message."""
        try:
            # Normaliser le texte
            normalized_text = re.sub(r'\s+', ' ', f"{subject} {body}").lower()
            
            # Supprimer les éléments variables (dates, nombres, etc.)
            normalized_text = re.sub(r'\d+', 'NUM', normalized_text)
            normalized_text = re.sub(r'[^\w\s]', '', normalized_text)
            
            # Créer un hash
            return hashlib.md5(normalized_text.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Erreur création signature: {e}")
            return ""
    
    def _get_recent_sender_history(self, sender: str) -> Dict[str, Any]:
        """Récupère l'historique récent de l'expéditeur."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Historique des 30 derniers jours
            recent_time = datetime.now() - timedelta(days=30)
            cursor.execute("""
                SELECT AVG(spam_score), COUNT(*) 
                FROM spam_analysis 
                WHERE sender = ? AND analyzed_at > ?
            """, (sender, recent_time.isoformat()))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[1] > 0:  # Si on a des données
                avg_spam_score = result[0] or 0
                email_count = result[1]
                
                # Bonus/malus basé sur l'historique
                if avg_spam_score > 0.7:
                    return {
                        'spam_score': 0.3,
                        'reasons': [f'sender_history_high_spam_{avg_spam_score:.2f}']
                    }
                elif avg_spam_score < 0.2:
                    return {
                        'spam_score': -0.1,  # Bonus
                        'reasons': [f'sender_history_low_spam_{avg_spam_score:.2f}']
                    }
            
            return {'spam_score': 0.0, 'reasons': []}
            
        except Exception as e:
            logger.error(f"Erreur historique expéditeur: {e}")
            return {'spam_score': 0.0, 'reasons': []}
    
    def _extract_domain(self, email: str) -> str:
        """Extrait le domaine d'une adresse email."""
        try:
            match = re.search(r'@([^>]+)', email)
            return match.group(1).lower() if match else ""
        except:
            return ""
    
    def _calculate_confidence(self, analysis_result: Dict) -> float:
        """Calcule la confiance de la détection."""
        try:
            # Base sur le nombre de raisons trouvées
            reason_count = len(analysis_result['reasons'])
            base_confidence = min(reason_count * 0.1, 0.8)
            
            # Ajuster selon le score
            score = analysis_result['spam_score']
            if score > 0.8 or score < 0.2:
                base_confidence += 0.1
            
            return min(base_confidence, 0.95)
            
        except Exception as e:
            logger.error(f"Erreur calcul confiance: {e}")
            return 0.5
    
    def _categorize_risk(self, spam_score: float) -> str:
        """Catégorise le niveau de risque."""
        if spam_score >= 0.8:
            return 'HIGH'
        elif spam_score >= 0.6:
            return 'MEDIUM'
        elif spam_score >= 0.3:
            return 'LOW'
        else:
            return 'SAFE'
    
    def _save_analysis(self, analysis_result: Dict, subject: str, sender: str):
        """Sauvegarde l'analyse en base."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            domain = self._extract_domain(sender)
            
            cursor.execute("""
                INSERT OR REPLACE INTO spam_analysis 
                (email_hash, subject, sender, domain, is_spam, spam_score, 
                 detection_method, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_result['email_hash'],
                subject[:200],  # Limiter la taille
                sender[:100],
                domain,
                analysis_result['is_spam'],
                analysis_result['spam_score'],
                analysis_result['detection_method'],
                json.dumps(analysis_result['reasons'])
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde analyse: {e}")
    
    def _cache_result(self, email_hash: str, result: Dict):
        """Met en cache le résultat."""
        try:
            if len(self._detection_cache) >= self._cache_max_size:
                oldest_key = next(iter(self._detection_cache))
                del self._detection_cache[oldest_key]
            
            self._detection_cache[email_hash] = result
            
        except Exception as e:
            logger.error(f"Erreur cache: {e}")
    
    def _update_stats(self, analysis_result: Dict):
        """Met à jour les statistiques."""
        try:
            self.stats['total_analyzed'] += 1
            if analysis_result['is_spam']:
                self.stats['spam_detected'] += 1
                
        except Exception as e:
            logger.error(f"Erreur mise à jour stats: {e}")
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Retourne une analyse par défaut en cas d'erreur."""
        return {
            'is_spam': False,
            'spam_score': 0.0,
            'confidence': 0.3,
            'reasons': ['analysis_error'],
            'risk_level': 'UNKNOWN',
            'detection_method': 'fallback',
            'analyzed_at': datetime.now().isoformat(),
            'error': True
        }
    
    def add_to_whitelist(self, sender: str, added_by: str = "user"):
        """Ajoute un expéditeur à la whitelist."""
        try:
            sender = sender.lower().strip()
            self.sender_whitelist.add(sender)
            
            # Sauvegarder en base
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO sender_lists 
                (sender_email, list_type, added_by)
                VALUES (?, ?, ?)
            """, (sender, 'whitelist', added_by))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Expéditeur ajouté à la whitelist: {sender}")
            
        except Exception as e:
            logger.error(f"Erreur ajout whitelist: {e}")
    
    def add_to_blacklist(self, sender: str, added_by: str = "user"):
        """Ajoute un expéditeur à la blacklist."""
        try:
            sender = sender.lower().strip()
            self.sender_blacklist.add(sender)
            
            # Sauvegarder en base
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO sender_lists 
                (sender_email, list_type, added_by)
                VALUES (?, ?, ?)
            """, (sender, 'blacklist', added_by))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Expéditeur ajouté à la blacklist: {sender}")
            
        except Exception as e:
            logger.error(f"Erreur ajout blacklist: {e}")
    
    def update_domain_reputation(self, domain: str, is_spam: bool):
        """Met à jour la réputation d'un domaine."""
        try:
            domain = domain.lower().strip()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Récupérer les stats actuelles
            cursor.execute("""
                SELECT spam_count, legitimate_count FROM domain_reputation 
                WHERE domain = ?
            """, (domain,))
            
            result = cursor.fetchone()
            
            if result:
                spam_count, legit_count = result
                if is_spam:
                    spam_count += 1
                else:
                    legit_count += 1
            else:
                spam_count = 1 if is_spam else 0
                legit_count = 0 if is_spam else 1
            
            # Calculer le nouveau score de réputation
            total = spam_count + legit_count
            reputation_score = legit_count / total if total > 0 else 0.5
            
            # Mettre à jour
            cursor.execute("""
                INSERT OR REPLACE INTO domain_reputation 
                (domain, reputation_score, spam_count, legitimate_count, last_updated)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (domain, reputation_score, spam_count, legit_count))
            
            conn.commit()
            conn.close()
            
            # Mettre à jour le cache
            self.domain_reputation[domain] = reputation_score
            
        except Exception as e:
            logger.error(f"Erreur mise à jour réputation: {e}")
    
    def train_ml_models(self, retrain: bool = False):
        """Entraîne les modèles de machine learning."""
        try:
            if not HAS_SKLEARN:
                logger.warning("Sklearn non disponible pour l'entraînement ML")
                return
            
            # Charger les données d'entraînement
            training_data = self._load_training_data_for_ml()
            
            if len(training_data) < 50:
                logger.warning(f"Pas assez de données pour l'entraînement ML: {len(training_data)}")
                return
            
            # Préparer les données
            texts = [item['text'] for item in training_data]
            labels = [item['is_spam'] for item in training_data]
            
            # Créer le vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Vectoriser les textes
            X = self.vectorizer.fit_transform(texts)
            
            # Entraîner le détecteur d'anomalies
            # Utiliser seulement les emails légitimes pour l'entraînement
            legitimate_indices = [i for i, is_spam in enumerate(labels) if not is_spam]
            X_legitimate = X[legitimate_indices]
            
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            self.anomaly_detector.fit(X_legitimate.toarray())
            
            logger.info(f"Modèles ML entraînés avec {len(training_data)} exemples")
            
        except Exception as e:
            logger.error(f"Erreur entraînement ML: {e}")
    
    def _load_training_data_for_ml(self) -> List[Dict]:
        """Charge les données d'entraînement pour ML."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT subject, sender, is_spam FROM spam_analysis 
                WHERE is_verified = TRUE
                ORDER BY analyzed_at DESC
                LIMIT 1000
            """)
            
            data = []
            for row in cursor.fetchall():
                subject, sender, is_spam = row
                text = f"{subject} {sender}"
                data.append({
                    'text': text,
                    'is_spam': bool(is_spam)
                })
            
            conn.close()
            return data
            
        except Exception as e:
            logger.error(f"Erreur chargement données ML: {e}")
            return []
    
    def _load_existing_data(self):
        """Charge les données existantes depuis la base."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Charger les listes
            cursor.execute("""
                SELECT sender_email, list_type FROM sender_lists
            """)
            
            for sender, list_type in cursor.fetchall():
                if list_type == 'whitelist':
                    self.sender_whitelist.add(sender)
                elif list_type == 'blacklist':
                    self.sender_blacklist.add(sender)
            
            # Charger la réputation des domaines
            cursor.execute("""
                SELECT domain, reputation_score FROM domain_reputation
            """)
            
            for domain, reputation in cursor.fetchall():
                self.domain_reputation[domain] = reputation
            
            # Charger les signatures de spam
            cursor.execute("""
                SELECT signature_hash FROM spam_signatures 
                WHERE confidence > 0.7
            """)
            
            for (signature,) in cursor.fetchall():
                self.spam_signatures.add(signature)
            
            conn.close()
            
            logger.info(f"Données chargées: {len(self.sender_whitelist)} whitelist, "
                       f"{len(self.sender_blacklist)} blacklist, "
                       f"{len(self.domain_reputation)} domaines")
            
        except Exception as e:
            logger.error(f"Erreur chargement données: {e}")
    
    def provide_feedback(self, email_hash: str, is_actually_spam: bool):
        """Fournit un feedback sur une détection."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Récupérer l'analyse originale
            cursor.execute("""
                SELECT is_spam, sender FROM spam_analysis 
                WHERE email_hash = ?
            """, (email_hash,))
            
            result = cursor.fetchone()
            if not result:
                logger.warning(f"Analyse non trouvée pour hash: {email_hash}")
                return
            
            was_predicted_spam, sender = result
            
            # Marquer comme vérifié
            cursor.execute("""
                UPDATE spam_analysis 
                SET is_verified = TRUE, is_spam = ?
                WHERE email_hash = ?
            """, (is_actually_spam, email_hash))
            
            # Mettre à jour les statistiques
            if was_predicted_spam != is_actually_spam:
                if was_predicted_spam and not is_actually_spam:
                    self.stats['false_positives'] += 1
                elif not was_predicted_spam and is_actually_spam:
                    self.stats['false_negatives'] += 1
            
            # Mettre à jour la réputation du domaine
            domain = self._extract_domain(sender)
            if domain:
                self.update_domain_reputation(domain, is_actually_spam)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Feedback enregistré: {email_hash} -> spam={is_actually_spam}")
            
        except Exception as e:
            logger.error(f"Erreur feedback: {e}")
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de détection."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) FROM spam_analysis")
            total_analyzed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM spam_analysis WHERE is_spam = TRUE")
            spam_detected = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM spam_analysis WHERE is_verified = TRUE")
            verified_count = cursor.fetchone()[0]
            
            # Statistiques par période
            recent_time = datetime.now() - timedelta(days=7)
            cursor.execute("""
                SELECT COUNT(*) FROM spam_analysis 
                WHERE analyzed_at > ? AND is_spam = TRUE
            """, (recent_time.isoformat(),))
            recent_spam = cursor.fetchone()[0]
            
            # Top domaines spam
            cursor.execute("""
                SELECT domain, COUNT(*) FROM spam_analysis 
                WHERE is_spam = TRUE AND domain != ''
                GROUP BY domain
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """)
            top_spam_domains = cursor.fetchall()
            
            conn.close()
            
            # Calculer la précision
            total_predictions = self.stats['spam_detected'] + self.stats['false_positives']
            precision = (self.stats['spam_detected'] / total_predictions 
                        if total_predictions > 0 else 0)
            
            # Calculer le rappel
            actual_spam = self.stats['spam_detected'] + self.stats['false_negatives']
            recall = (self.stats['spam_detected'] / actual_spam 
                     if actual_spam > 0 else 0)
            
            return {
                'total_analyzed': total_analyzed,
                'spam_detected': spam_detected,
                'spam_rate': spam_detected / total_analyzed if total_analyzed > 0 else 0,
                'verified_count': verified_count,
                'recent_spam_7days': recent_spam,
                'false_positives': self.stats['false_positives'],
                'false_negatives': self.stats['false_negatives'],
                'precision': precision,
                'recall': recall,
                'top_spam_domains': top_spam_domains,
                'whitelist_size': len(self.sender_whitelist),
                'blacklist_size': len(self.sender_blacklist),
                'known_signatures': len(self.spam_signatures),
                'ml_models_ready': self.vectorizer is not None and self.anomaly_detector is not None
            }
            
        except Exception as e:
            logger.error(f"Erreur stats détection: {e}")
            return {'error': str(e)}
    
    def export_configuration(self) -> Dict[str, Any]:
        """Exporte la configuration pour sauvegarde."""
        try:
            return {
                'whitelist': list(self.sender_whitelist),
                'blacklist': list(self.sender_blacklist),
                'domain_reputation': self.domain_reputation,
                'spam_threshold': self.spam_threshold,
                'suspicious_threshold': self.suspicious_threshold,
                'stats': self.stats
            }
        except Exception as e:
            logger.error(f"Erreur export config: {e}")
            return {}
    
    def import_configuration(self, config: Dict[str, Any]):
        """Importe une configuration."""
        try:
            if 'whitelist' in config:
                self.sender_whitelist.update(config['whitelist'])
            
            if 'blacklist' in config:
                self.sender_blacklist.update(config['blacklist'])
            
            if 'domain_reputation' in config:
                self.domain_reputation.update(config['domain_reputation'])
            
            if 'spam_threshold' in config:
                self.spam_threshold = config['spam_threshold']
            
            if 'suspicious_threshold' in config:
                self.suspicious_threshold = config['suspicious_threshold']
            
            if 'stats' in config:
                self.stats.update(config['stats'])
            
            logger.info("Configuration importée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur import config: {e}")
    
    def clear_cache(self):
        """Vide le cache de détection."""
        self._detection_cache.clear()
        logger.info("Cache de détection vidé")
    
    def __del__(self):
        """Nettoyage lors de la destruction de l'objet."""
        try:
            # Sauvegarder les stats finales si nécessaire
            pass
        except:
            pass