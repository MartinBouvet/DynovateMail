#!/usr/bin/env python3
"""
Interface en ligne de commande pour Gmail Assistant IA.
Version simplifiée sans interface graphique.
"""
import os
import sys
import logging
from dotenv import load_dotenv

from utils.auth import authenticate_gmail
from utils.logger import setup_logger
from utils.config import load_config
from gmail_client import GmailClient

# Configurer le logging
logger = setup_logger()

def display_menu():
    """Affiche le menu principal."""
    print("\n" + "="*50)
    print("GMAIL ASSISTANT IA - INTERFACE CLI")
    print("="*50)
    print("1. Lire les derniers emails")
    print("2. Lire les emails non lus")
    print("3. Envoyer un email")
    print("4. Rechercher des emails")
    print("5. Quitter")
    print("="*50)
    return input("Choisissez une option (1-5): ")

def display_email(email, index=None):
    """Affiche un email dans la console."""
    print("\n" + "-"*70)
    if index is not None:
        print(f"EMAIL #{index}")
    print(f"De: {email.sender}")
    print(f"À: {email.recipient}")
    print(f"Date: {email.date}")
    print(f"Sujet: {email.subject}")
    print("-"*70)
    print(f"Corps: \n{email.body[:500]}...")
    if len(email.body) > 500:
        print("... (message tronqué)")
    print("-"*70)

def compose_email(gmail_client):
    """Interface pour composer et envoyer un email."""
    print("\n" + "="*50)
    print("COMPOSER UN EMAIL")
    print("="*50)
    
    to = input("Destinataire (email): ")
    subject = input("Sujet: ")
    print("Corps (terminez par une ligne contenant uniquement '.'): ")
    
    body_lines = []
    line = input()
    while line != ".":
        body_lines.append(line)
        line = input()
    
    body = "\n".join(body_lines)
    
    # Confirmation
    print("\nRésumé de l'email:")
    print(f"À: {to}")
    print(f"Sujet: {subject}")
    print(f"Corps: \n{body}")
    
    confirm = input("\nEnvoyer cet email? (o/n): ")
    
    if confirm.lower() == 'o':
        success = gmail_client.send_email(to, subject, body)
        if success:
            print("Email envoyé avec succès!")
        else:
            print("Erreur lors de l'envoi de l'email.")
    else:
        print("Envoi annulé.")

def search_emails(gmail_client):
    """Interface pour rechercher des emails."""
    print("\n" + "="*50)
    print("RECHERCHER DES EMAILS")
    print("="*50)
    
    query = input("Recherche (sujet, expéditeur, etc.): ")
    
    print(f"Recherche des emails correspondant à '{query}'...")
    emails = gmail_client.list_messages(query=query)
    
    if not emails:
        print("Aucun email trouvé.")
        return
    
    print(f"\n{len(emails)} emails trouvés.")
    display_emails(emails)

def display_emails(emails):
    """Affiche une liste d'emails et permet d'en sélectionner un."""
    if not emails:
        print("Aucun email à afficher.")
        return
    
    for i, email in enumerate(emails, 1):
        print(f"{i}. De: {email.get_sender_name()} - Sujet: {email.subject}")
    
    while True:
        choice = input("\nEntrez un numéro pour voir l'email complet (ou 'q' pour quitter): ")
        
        if choice.lower() == 'q':
            break
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(emails):
                display_email(emails[index])
            else:
                print("Numéro invalide.")
        except ValueError:
            print("Veuillez entrer un numéro valide.")

def main():
    """Fonction principale pour démarrer l'application CLI."""
    try:
        # Charger les variables d'environnement
        load_dotenv()
        
        # Charger la configuration
        config = load_config()
        
        print("Authentification auprès de Gmail...")
        # S'authentifier auprès de Gmail
        credentials = authenticate_gmail()
        
        if not credentials:
            logger.error("Échec de l'authentification Gmail.")
            print("Impossible de s'authentifier auprès de Gmail. Vérifiez votre fichier client_secret.json.")
            sys.exit(1)
        
        # Initialiser le client Gmail
        gmail_client = GmailClient(credentials)
        print("Authentification réussie!")
        
        # Boucle principale
        while True:
            choice = display_menu()
            
            if choice == '1':
                print("Chargement des derniers emails...")
                emails = gmail_client.list_messages(max_results=10)
                display_emails(emails)
                
            elif choice == '2':
                print("Chargement des emails non lus...")
                emails = gmail_client.list_messages(max_results=10, query="is:unread")
                display_emails(emails)
                
            elif choice == '3':
                compose_email(gmail_client)
                
            elif choice == '4':
                search_emails(gmail_client)
                
            elif choice == '5':
                print("Au revoir!")
                break
                
            else:
                print("Option invalide. Veuillez réessayer.")
    
    except Exception as e:
        logger.exception(f"Erreur lors du démarrage de l'application: {e}")
        print(f"Une erreur s'est produite: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()