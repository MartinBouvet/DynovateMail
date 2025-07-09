"""
Module contenant des templates pour les réponses automatiques aux emails.
"""
import logging
from typing import Dict, Any
from string import Template

logger = logging.getLogger(__name__)

# Templates de réponses par catégorie
TEMPLATES = {
    "default": Template("""
Bonjour $recipient_name,

Merci pour votre email. Je l'ai bien reçu et je vous répondrai dans les plus brefs délais.

Cordialement,
$sender_name
$signature
"""),

    "meeting_request": Template("""
Bonjour $recipient_name,

Merci pour votre invitation à la réunion "$meeting_subject" prévue le $meeting_date à $meeting_time.

$meeting_response

Cordialement,
$sender_name
$signature
"""),

    "information_request": Template("""
Bonjour $recipient_name,

Merci pour votre demande d'information. $information_response

N'hésitez pas à me contacter si vous avez d'autres questions.

Cordialement,
$sender_name
$signature
"""),

    "job_application": Template("""
Cher(e) $recipient_name,

Nous accusons réception de votre candidature pour le poste de $job_title. 

Votre candidature a bien été enregistrée et sera examinée par notre équipe de recrutement dans les plus brefs délais. Nous vous contacterons si votre profil correspond à nos besoins.

Cordialement,
$sender_name
Service des Ressources Humaines
$signature
"""),

    "out_of_office": Template("""
Bonjour,

Merci pour votre email. Je suis actuellement absent(e) du bureau du $absence_start_date au $absence_end_date et n'ai qu'un accès limité à mes emails.

$absence_message

Pour toute urgence, veuillez contacter $emergency_contact.

Cordialement,
$sender_name
$signature
""")
}


def generate_response_from_template(template_name: str, variables: Dict[str, Any]) -> str:
    """
    Génère une réponse à partir d'un template et de variables.
    
    Args:
        template_name: Nom du template à utiliser.
        variables: Dictionnaire des variables à remplacer dans le template.
        
    Returns:
        La réponse générée.
    """
    try:
        # Obtenir le template (utiliser le template par défaut si non trouvé)
        template = TEMPLATES.get(template_name, TEMPLATES["default"])
        
        # Ajouter une signature vide si non fournie
        if "signature" not in variables:
            variables["signature"] = ""
        
        # Générer la réponse
        response = template.substitute(variables)
        
        return response.strip()
    
    except KeyError as e:
        logger.error(f"Variable manquante dans le template: {e}")
        return f"Erreur: Variable manquante dans le template: {e}"
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la réponse: {e}")
        return "Erreur lors de la génération de la réponse."


# Exemples d'utilisation des templates

def get_default_response(recipient_name: str, sender_name: str, signature: str = "") -> str:
    """
    Génère une réponse par défaut.
    
    Args:
        recipient_name: Nom du destinataire.
        sender_name: Nom de l'expéditeur.
        signature: Signature de l'email.
        
    Returns:
        La réponse générée.
    """
    variables = {
        "recipient_name": recipient_name,
        "sender_name": sender_name,
        "signature": signature
    }
    
    return generate_response_from_template("default", variables)


def get_meeting_response(recipient_name: str, sender_name: str, meeting_subject: str,
                         meeting_date: str, meeting_time: str, accept: bool = True,
                         signature: str = "") -> str:
    """
    Génère une réponse à une invitation de réunion.
    
    Args:
        recipient_name: Nom du destinataire.
        sender_name: Nom de l'expéditeur.
        meeting_subject: Sujet de la réunion.
        meeting_date: Date de la réunion.
        meeting_time: Heure de la réunion.
        accept: True si la réunion est acceptée, False sinon.
        signature: Signature de l'email.
        
    Returns:
        La réponse générée.
    """
    meeting_response = "Je confirme ma participation à cette réunion." if accept else \
                      "Malheureusement, je ne pourrai pas participer à cette réunion."
    
    variables = {
        "recipient_name": recipient_name,
        "sender_name": sender_name,
        "meeting_subject": meeting_subject,
        "meeting_date": meeting_date,
        "meeting_time": meeting_time,
        "meeting_response": meeting_response,
        "signature": signature
    }
    
    return generate_response_from_template("meeting_request", variables)


def get_out_of_office_response(sender_name: str, absence_start_date: str,
                               absence_end_date: str, emergency_contact: str = "",
                               absence_message: str = "", signature: str = "") -> str:
    """
    Génère une réponse d'absence du bureau.
    
    Args:
        sender_name: Nom de l'expéditeur.
        absence_start_date: Date de début d'absence.
        absence_end_date: Date de fin d'absence.
        emergency_contact: Contact en cas d'urgence.
        absence_message: Message personnalisé d'absence.
        signature: Signature de l'email.
        
    Returns:
        La réponse générée.
    """
    if not emergency_contact:
        emergency_contact = "un collègue"
    
    variables = {
        "sender_name": sender_name,
        "absence_start_date": absence_start_date,
        "absence_end_date": absence_end_date,
        "absence_message": absence_message,
        "emergency_contact": emergency_contact,
        "signature": signature
    }
    
    return generate_response_from_template("out_of_office", variables)