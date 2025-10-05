#!/usr/bin/env python3
"""
Processeur IA pour l'analyse et le traitement des emails - VERSION CORRIGÉE
Corrections: Analyse robuste, réponses contextuelles, extraction d'infos
"""
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from models.email_model import Email

logger = logging.getLogger(__name__)


@dataclass
class EmailAnalysis:
    """Résultat de l'analyse IA d'un email."""
    category: str
    confidence: float
    priority: int  # 1-5
    sentiment: str  # positive, negative, neutral
    should_auto_respond: bool
    suggested_response: Optional[str]
    extracted_info: Dict[str, Any]
    reasoning: str


class AIProcessor:
    """Processeur IA pour analyser et traiter les emails - CORRIGÉ."""
    
    def __init__(self):
        """Initialise le processeur IA."""
        
        # Patterns de détection par catégorie
        self.category_patterns = {
            'cv': [
                r'\bcv\b', r'curriculum', r'candidature', r'postuler',
                r'poste', r'recrutement', r'embauche', r'lettre de motivation',
                r'portfolio', r'expérience professionnelle'
            ],
            'rdv': [
                r'rendez-vous', r'r[ée]union', r'rencontre', r'meeting',
                r'disponible', r'disponibilit[ée]', r'calendrier',
                r'conf[ée]rence', r'call', r'entretien', r'rendez vous'
            ],
            'facture': [
                r'facture', r'paiement', r'montant', r'invoice',
                r'devis', r'prix', r'tarif', r'€', r'euro',
                r'virement', r'règlement', r'total', r'TVA'
            ],
            'support': [
                r'probl[èe]me', r'bug', r'erreur', r'aide', r'support',
                r'dysfonctionnement', r'ne fonctionne pas', r'panne',
                r'assistance', r'question', r'comment', r'aide'
            ],
            'partenariat': [
                r'partenariat', r'collaboration', r'coop[ée]ration',
                r'projet commun', r'ensemble', r'proposition',
                r'opportunit[ée]', r'synergie'
            ],
            'spam': [
                r'gagner', r'gratuit', r'cliquez ici', r'urgent',
                r'offre limit[ée]e', r'casino', r'viagra', r'crypto',
                r'investissement garanti', r'loterie', r'héritage'
            ]
        }
        
        # Mots-clés de sentiment
        self.sentiment_keywords = {
            'positive': [
                'merci', 'excellent', 'parfait', 'super', 'génial',
                'bravo', 'félicitations', 'content', 'satisfait', 'ravi'
            ],
            'negative': [
                'déçu', 'problème', 'mauvais', 'insatisfait', 'erreur',
                'bug', 'inacceptable', 'frustré', 'mécontent'
            ]
        }
        
        logger.info("AIProcessor initialisé avec patterns améliorés")
    
    def process_email(self, email: Email) -> EmailAnalysis:
        """
        Traite et analyse un email - MÉTHODE PRINCIPALE CORRIGÉE.
        
        Args:
            email: L'email à analyser
            
        Returns:
            EmailAnalysis: Résultat de l'analyse
        """
        try:
            logger.info(f"Analyse IA de l'email: {email.id}")
            
            # Combiner sujet et corps pour l'analyse
            text = f"{email.subject or ''} {email.body or ''} {email.snippet or ''}".lower()
            
            # === CATÉGORISATION ===
            category, confidence = self._categorize_email(text)
            
            # === PRIORITÉ ===
            priority = self._calculate_priority(email, text, category)
            
            # === SENTIMENT ===
            sentiment = self._analyze_sentiment(text)
            
            # === EXTRACTION D'INFORMATIONS ===
            extracted_info = self._extract_information(text, category)
            
            # === DÉCISION DE RÉPONSE AUTO ===
            should_auto_respond = self._should_auto_respond(
                email, category, sentiment, extracted_info
            )
            
            # === GÉNÉRATION DE RÉPONSE ===
            suggested_response = None
            if should_auto_respond:
                suggested_response = self._generate_response(
                    email, category, extracted_info, sentiment
                )
            
            # === RAISONNEMENT ===
            reasoning = self._generate_reasoning(
                category, confidence, priority, sentiment, should_auto_respond
            )
            
            analysis = EmailAnalysis(
                category=category,
                confidence=confidence,
                priority=priority,
                sentiment=sentiment,
                should_auto_respond=should_auto_respond,
                suggested_response=suggested_response,
                extracted_info=extracted_info,
                reasoning=reasoning
            )
            
            logger.info(
                f"Analyse terminée: {category} (confiance: {confidence:.2f}, "
                f"priorité: {priority}, sentiment: {sentiment})"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse IA: {e}")
            return self._create_fallback_analysis(email)
    
    def _categorize_email(self, text: str) -> tuple[str, float]:
        """Catégorise l'email - CORRIGÉ."""
        scores = {}
        
        for category, patterns in self.category_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                count = len(re.findall(pattern, text, re.IGNORECASE))
                if count > 0:
                    matches += 1
                    score += count
            
            # Score pondéré
            if matches > 0:
                scores[category] = (score, matches / len(patterns))
        
        if not scores:
            return ('general', 0.3)
        
        # Trouver la catégorie avec le meilleur score
        best_category = max(scores.items(), key=lambda x: (x[1][0], x[1][1]))
        category = best_category[0]
        confidence = min(0.95, 0.5 + (best_category[1][1] * 0.5))
        
        return (category, confidence)
    
    def _calculate_priority(self, email: Email, text: str, category: str) -> int:
        """Calcule la priorité de l'email - CORRIGÉ."""
        priority = 3  # Priorité par défaut
        
        # Mots-clés d'urgence
        urgent_keywords = ['urgent', 'asap', 'immédiat', 'rapide', 'prioritaire']
        if any(keyword in text for keyword in urgent_keywords):
            priority += 2
        
        # Catégories prioritaires
        if category in ['rdv', 'support', 'facture']:
            priority += 1
        
        # Emails non lus
        if not email.is_read:
            priority += 1
        
        # Limiter entre 1 et 5
        return max(1, min(5, priority))
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyse le sentiment - CORRIGÉ."""
        positive_count = sum(
            1 for keyword in self.sentiment_keywords['positive']
            if keyword in text
        )
        negative_count = sum(
            1 for keyword in self.sentiment_keywords['negative']
            if keyword in text
        )
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_information(self, text: str, category: str) -> Dict[str, Any]:
        """Extrait des informations spécifiques - CORRIGÉ."""
        info = {}
        
        # Dates potentielles
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)',
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        if dates:
            info['potential_dates'] = dates[:3]  # Max 3
        
        # Heures
        time_pattern = r'\d{1,2}h\d{0,2}'
        times = re.findall(time_pattern, text)
        if times:
            info['potential_times'] = times[:3]
        
        # Montants (pour factures)
        if category == 'facture':
            money_pattern = r'\d+[,.]?\d*\s*€'
            amounts = re.findall(money_pattern, text)
            if amounts:
                info['amounts'] = amounts
        
        # Emails dans le texte
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        if emails:
            info['mentioned_emails'] = emails[:3]
        
        # Téléphones
        phone_pattern = r'(?:0|\+33)[1-9](?:[\s.-]?\d{2}){4}'
        phones = re.findall(phone_pattern, text)
        if phones:
            info['phone_numbers'] = phones
        
        return info
    
    def _should_auto_respond(self, email: Email, category: str,
                            sentiment: str, extracted_info: Dict) -> bool:
        """Détermine si une réponse automatique est appropriée - CORRIGÉ."""
        
        # Ne jamais répondre aux emails probablement automatiques
        if self._is_likely_auto_response(email):
            return False
        
        # Ne pas répondre au spam
        if category == 'spam':
            return False
        
        # Répondre aux catégories appropriées
        auto_respond_categories = ['cv', 'rdv', 'support', 'partenariat']
        if category not in auto_respond_categories:
            return False
        
        # Éviter les réponses en boucle
        if self._sender_response_limit_reached(email.sender):
            return False
        
        return True
    
    def _generate_response(self, email: Email, category: str,
                          extracted_info: Dict, sentiment: str) -> str:
        """Génère une réponse suggérée - CORRIGÉ."""
        
        sender_name = email.get_sender_name() if hasattr(email, 'get_sender_name') else email.sender.split('@')[0]
        
        # Templates de réponses par catégorie
        templates = {
            'cv': f"""Bonjour {sender_name},

Merci pour votre candidature et votre intérêt pour notre entreprise.

Nous avons bien reçu votre CV et votre lettre de motivation. Notre équipe de recrutement va examiner votre profil avec attention.

Nous vous recontacterons dans les prochains jours si votre profil correspond à nos besoins actuels.

Cordialement,
L'équipe Dynovate""",
            
            'rdv': f"""Bonjour {sender_name},

Merci pour votre message concernant un rendez-vous.

Je suis disponible pour échanger avec vous. Pourriez-vous me proposer quelques créneaux qui vous conviennent ?

Dans l'attente de votre retour.

Cordialement""",
            
            'support': f"""Bonjour {sender_name},

Merci de nous avoir contactés concernant votre demande d'assistance.

Votre ticket a été enregistré et notre équipe support va traiter votre demande dans les plus brefs délais.

Nous reviendrons vers vous rapidement avec une solution.

Cordialement,
L'équipe Support Dynovate""",
            
            'partenariat': f"""Bonjour {sender_name},

Merci pour votre intérêt concernant une potentielle collaboration.

Votre proposition nous intéresse. Nous aimerions en discuter plus en détail avec vous.

Pourriez-vous nous proposer un créneau pour un premier échange téléphonique ou visioconférence ?

Dans l'attente de votre retour.

Cordialement,
L'équipe Dynovate"""
        }
        
        base_response = templates.get(category, f"""Bonjour {sender_name},

Merci pour votre message. Nous l'avons bien reçu et y répondrons dans les plus brefs délais.

Cordialement""")
        
        # Personnaliser selon les informations extraites
        if category == 'rdv' and extracted_info.get('potential_dates'):
            dates = ', '.join(extracted_info['potential_dates'][:2])
            base_response += f"\n\nJ'ai noté les dates suivantes mentionnées : {dates}"
        
        return base_response
    
    def _generate_reasoning(self, category: str, confidence: float,
                           priority: int, sentiment: str,
                           should_auto_respond: bool) -> str:
        """Génère une explication du raisonnement."""
        reasons = []
        
        reasons.append(f"Catégorisé comme '{category}' avec {confidence*100:.0f}% de confiance")
        reasons.append(f"Priorité {priority}/5")
        reasons.append(f"Sentiment {sentiment}")
        
        if should_auto_respond:
            reasons.append("Réponse automatique suggérée")
        else:
            reasons.append("Nécessite une attention humaine")
        
        return " | ".join(reasons)
    
    def _is_likely_auto_response(self, email: Email) -> bool:
        """Détecte si l'email est probablement une réponse automatique."""
        indicators = [
            'noreply', 'no-reply', 'donotreply', 'ne-pas-repondre',
            'automatic', 'automatique', 'auto-generated',
            'out of office', 'absent du bureau', 'absence',
            'notification', 'system', 'daemon'
        ]
        
        sender_lower = (email.sender or '').lower()
        subject_lower = (email.subject or '').lower()
        body_lower = (email.body or '')[:500].lower()
        
        return any(
            indicator in sender_lower or 
            indicator in subject_lower or 
            indicator in body_lower 
            for indicator in indicators
        )
    
    def _sender_response_limit_reached(self, sender: str) -> bool:
        """Vérifie si la limite de réponses à cet expéditeur est atteinte."""
        # TODO: Implémenter avec une vraie base de données
        # Pour l'instant, on retourne False (pas de limite)
        return False
    
    def _create_fallback_analysis(self, email: Email) -> EmailAnalysis:
        """Crée une analyse de fallback en cas d'erreur."""
        return EmailAnalysis(
            category='general',
            confidence=0.1,
            priority=3,
            sentiment='neutral',
            should_auto_respond=False,
            suggested_response=None,
            extracted_info={},
            reasoning="Analyse de secours suite à une erreur"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du processeur IA."""
        return {
            'categories_available': list(self.category_patterns.keys()),
            'sentiment_types': ['positive', 'negative', 'neutral'],
            'auto_response_enabled': True
        }