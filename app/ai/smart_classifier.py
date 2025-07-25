#!/usr/bin/env python3
"""
Classification intelligente avec génération de réponses améliorée.
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
    """Classificateur intelligent avec génération de réponses."""
    
    def __init__(self, model_path: str = "app/data/classifier.db"):
        self.model_path = model_path
        self._init_database()
        
        # Templates de réponses améliorés
        self.response_templates = {
            'cv': {
                'template': """Bonjour {sender_name},

Merci pour votre candidature et l'intérêt que vous portez à notre entreprise.

Nous avons bien reçu votre CV et nous l'examinerons attentivement. Notre équipe RH va étudier votre profil et nous vous recontacterons dans les meilleurs délais si votre candidature retient notre attention.

Nous vous remercions pour le temps que vous avez consacré à votre candidature.

Cordialement,
L'équipe Recrutement""",
                'should_respond': True
            },
            'rdv': {
                'template': """Bonjour {sender_name},

Merci pour votre demande de rendez-vous.

Je consulte mon planning et vous propose les créneaux suivants :
- Lundi prochain à 14h00
- Mardi prochain à 10h30
- Mercredi prochain à 16h00

N'hésitez pas à me confirmer le créneau qui vous convient le mieux ou à me proposer d'autres alternatives.

Dans l'attente de notre rencontre.

Cordialement,
{user_name}""",
                'should_respond': True
            },
            'support': {
                'template': """Bonjour {sender_name},

Merci de nous avoir contactés concernant votre demande d'assistance.

Nous avons bien pris en compte votre message et notre équipe technique va examiner votre problème. Vous devriez recevoir une réponse détaillée de notre part dans les prochaines heures.

En cas d'urgence, n'hésitez pas à nous contacter par téléphone.

Cordialement,
L'équipe Support Technique""",
                'should_respond': True
            },
            'facture': {
                'template': """Bonjour {sender_name},

Nous accusons réception de votre message concernant la facturation.

Votre demande a été transmise à notre service comptabilité qui vous répondra dans les meilleurs délais avec les informations demandées.

Cordialement,
Le service Facturation""",
                'should_respond': False
            },
            'spam': {
                'template': "",
                'should_respond': False
            },
            'general': {
                'template': """Bonjour {sender_name},

Merci pour votre message.

Nous l'avons bien reçu et nous vous répondrons dans les plus brefs délais.

Cordialement,
L'équipe""",
                'should_respond': False
            }
        }
        
        # Patterns de détection améliorés
        self.patterns = {
            'cv': [
                r'\b(cv|curriculum|résumé|candidature|postule|emploi|poste|job)\b',
                r'\b(experience|compétence|formation|diplôme|qualification)\b',
                r'\b(lettre de motivation|cover letter)\b',
                r'\b(recherche un poste|recherche d\'emploi)\b'
            ],
            'rdv': [
                r'\b(rendez[-\s]?vous|meeting|réunion|entretien|call|appointment)\b',
                r'\b(disponible|créneau|calendrier|planning)\b',
                r'\b(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b',
                r'\d{1,2}[h:]\d{2}|\d{1,2}h\d{2}|\d{1,2}:\d{2}',
                r'\b(quand êtes-vous|êtes-vous libre|pouvons-nous nous voir)\b'
            ],
            'facture': [
                r'\b(facture|invoice|bill|payment|paiement)\b',
                r'\b(montant|prix|coût|€|euro|dollar|\$)\b',
                r'\b(due|échéance|deadline|devis)\b'
            ],
            'support': [
                r'\b(aide|help|support|problème|issue|bug)\b',
                r'\b(erreur|error|panne|dysfonctionnement)\b',
                r'\b(urgent|critique|emergency|assistance)\b',
                r'\b(ne fonctionne pas|ne marche pas|problème avec)\b'
            ],
            'spam': [
                r'\b(gratuit|free|promo|offre|reduction|discount)\b',
                r'\b(cliquez|click|urgent|limited|limité)\b',
                r'[A-Z]{3,}.*[A-Z]{3,}',  # Beaucoup de majuscules
                r'\b(félicitations|congratulations|winner|gagnant)\b'
            ]
        }
        
        logger.info("SmartClassifier initialisé avec templates de réponses")
    
    def _init_database(self):
        """Initialise la base de données."""
        try:
            Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.model_path)
            cursor = conn.cursor()
            
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
            
            conn.commit()
            conn.close()
            logger.info("Base de données classificateur initialisée")
        except Exception as e:
            logger.error(f"Erreur init base de données: {e}")
    
    def analyze_email(self, email_data: Dict) -> EmailAnalysis:
        """Analyse complète d'un email avec génération de réponse."""
        try:
            subject = email_data.get('subject', '').lower()
            body = email_data.get('body', '').lower()
            sender = email_data.get('sender', '').lower()
            sender_name = email_data.get('sender_name', 'Monsieur/Madame')
            full_text = f"{subject} {body}".strip()
            
            # Classification
            category_scores = self._calculate_category_scores(full_text, sender)
            best_category = max(category_scores.items(), key=lambda x: x[1])
            
            # Priorité
            priority = self._calculate_priority(full_text, best_category[0])
            
            # Décision de réponse automatique
            should_respond = self._should_auto_respond(full_text, best_category[0], best_category[1])
            
            # Génération de réponse si appropriée
            suggested_response = None
            if should_respond:
                suggested_response = self._generate_response(
                    best_category[0], sender_name, email_data
                )
            
            # Extraction d'informations
            extracted_info = self._extract_specific_info(full_text, best_category[0])
            
            # Raisonnement
            reasoning = self._explain_reasoning(category_scores, best_category, should_respond)
            
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
        scores = {'general': 0.1}
        
        for category, patterns in self.patterns.items():
            score = 0.0
            
            # Score basé sur les patterns
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches * 0.3
            
            # Bonus pour certains expéditeurs
            if category == 'facture' and any(word in sender for word in ['billing', 'invoice', 'facture']):
                score += 0.4
            elif category == 'cv' and 'candidat' in text:
                score += 0.5
            elif category == 'support' and any(word in sender for word in ['support', 'help', 'assistance']):
                score += 0.4
            
            scores[category] = min(score, 1.0)
        
        return scores
    
    def _calculate_priority(self, text: str, category: str) -> int:
        """Calcule la priorité de l'email."""
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
        urgent_keywords = ['urgent', 'emergency', 'critique', 'asap', 'immédiat', 'rapidement']
        if any(keyword in text for keyword in urgent_keywords):
            priority = max(1, priority - 2)
        
        return min(priority, 5)
    
    def _should_auto_respond(self, text: str, category: str, confidence: float) -> bool:
        """Détermine si une réponse automatique est appropriée."""
        # Vérifier la configuration de la catégorie
        template_config = self.response_templates.get(category, {})
        if not template_config.get('should_respond', False):
            return False
        
        # Vérifier la confiance minimale
        if confidence < 0.7:
            return False
        
        # Patterns d'évitement
        avoid_patterns = [
            r'\b(ne pas répondre|do not reply|noreply)\b',
            r'\b(automatique|automatic|newsletter)\b',
            r'\b(notification|alert|reminder)\b'
        ]
        
        for pattern in avoid_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    def _generate_response(self, category: str, sender_name: str, email_data: Dict) -> str:
        """Génère une réponse personnalisée."""
        template_config = self.response_templates.get(category, {})
        template = template_config.get('template', '')
        
        if not template:
            return None
        
        # Personnalisation du nom d'expéditeur
        if not sender_name or sender_name in ['Monsieur/Madame', '']:
            sender_name = "Monsieur/Madame"
        elif len(sender_name) > 30:
            sender_name = sender_name[:30] + "..."
        
        # Variables pour le template
        template_vars = {
            'sender_name': sender_name,
            'user_name': '[Votre nom]',
            'company_name': '[Votre entreprise]'
        }
        
        # Personnalisation selon la catégorie
        try:
            response = template.format(**template_vars)
            
            # Ajout d'éléments contextuels
            if category == 'rdv':
                response = self._enhance_rdv_response(response, email_data)
            elif category == 'cv':
                response = self._enhance_cv_response(response, email_data)
            elif category == 'support':
                response = self._enhance_support_response(response, email_data)
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur génération réponse: {e}")
            return f"Bonjour {sender_name},\n\nMerci pour votre message. Nous vous répondrons rapidement.\n\nCordialement,"
    
    def _enhance_rdv_response(self, response: str, email_data: Dict) -> str:
        """Améliore la réponse pour les RDV."""
        # Analyser si des créneaux spécifiques sont mentionnés
        text = email_data.get('body', '') + ' ' + email_data.get('subject', '')
        
        # Rechercher des mentions de jours/heures
        day_mentions = re.findall(r'\b(lundi|mardi|mercredi|jeudi|vendredi)\b', text.lower())
        time_mentions = re.findall(r'\b(\d{1,2})[h:](\d{2})\b', text.lower())
        
        if day_mentions or time_mentions:
            response += "\n\nP.S.: J'ai noté vos préférences horaires et m'efforcerai de vous proposer des créneaux correspondants."
        
        return response
    
    def _enhance_cv_response(self, response: str, email_data: Dict) -> str:
        """Améliore la réponse pour les CV."""
        # Analyser si un poste spécifique est mentionné
        text = email_data.get('subject', '') + ' ' + email_data.get('body', '')
        
        job_patterns = [
            r'poste de (.{1,30})',
            r'candidature (.{1,30})',
            r'emploi (.{1,30})'
        ]
        
        for pattern in job_patterns:
            match = re.search(pattern, text.lower())
            if match:
                job_title = match.group(1).strip()
                response += f"\n\nConcernant le poste de {job_title}, nous étudierons attentivement votre profil."
                break
        
        return response
    
    def _enhance_support_response(self, response: str, email_data: Dict) -> str:
        """Améliore la réponse pour le support."""
        text = email_data.get('body', '') + ' ' + email_data.get('subject', '')
        
        # Détecter l'urgence
        urgent_keywords = ['urgent', 'critique', 'bloqué', 'down', 'panne']
        
        if any(keyword in text.lower() for keyword in urgent_keywords):
            response = response.replace(
                "dans les prochaines heures",
                "en priorité absolue et vous contacterons dans l'heure qui suit"
            )
        
        return response
    
    def _extract_specific_info(self, text: str, category: str) -> Dict:
        """Extrait des informations spécifiques."""
        info = {}
        
        if category == 'rdv':
            # Extraction de dates/heures
            dates = re.findall(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', text)
            times = re.findall(r'\b(\d{1,2}):(\d{2})\b', text)
            days = re.findall(r'\b(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b', text.lower())
            
            info['potential_dates'] = dates[:3]
            info['potential_times'] = times[:3]
            info['mentioned_days'] = days[:3]
        
        elif category == 'cv':
            # Extraction de postes mentionnés
            job_patterns = [
                r'poste de (.{1,50})',
                r'candidature (.{1,50})',
                r'emploi (.{1,50})'
            ]
            
            for pattern in job_patterns:
                matches = re.findall(pattern, text.lower())
                if matches:
                    info['job_positions'] = matches[:3]
                    break
        
        elif category == 'support':
            # Extraction de produits/services mentionnés
            product_keywords = ['logiciel', 'application', 'site', 'service', 'produit']
            products = []
            for keyword in product_keywords:
                pattern = f'{keyword} (.{{1,30}})'
                matches = re.findall(pattern, text.lower())
                products.extend(matches)
            
            info['mentioned_products'] = products[:3]
        
        return info
    
    def _explain_reasoning(self, scores: Dict[str, float], best_category: Tuple[str, float], should_respond: bool) -> str:
        """Génère une explication du raisonnement."""
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        explanation = f"Classé comme '{best_category[0]}' (confiance: {best_category[1]:.2f})\n"
        explanation += f"Scores alternatifs: "
        explanation += ", ".join([f"{cat}: {score:.2f}" for cat, score in top_3[1:]])
        
        if should_respond:
            explanation += "\nRéponse automatique recommandée."
        else:
            explanation += "\nRéponse automatique non recommandée."
        
        return explanation
    
    def _fallback_analysis(self) -> EmailAnalysis:
        """Analyse de fallback."""
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