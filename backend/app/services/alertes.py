"""
Service d'envoi d'alertes email pour les points sautés.

Un point sauté est détecté quand un chauffeur marque un bac comme
collecté alors qu'un bac plus tôt dans l'ordre planifié de sa tournée
n'a pas été vidé -- signe qu'il est passé devant sans le collecter.

L'entreprise propriétaire du camion reçoit un email récapitulatif.
Défaillant en douceur : un échec d'envoi (SMTP indisponible, config
absente) ne bloque jamais la collecte du chauffeur -- l'alerte reste
simplement marquée comme non envoyée en base (alerte_envoyee=False),
consultable plus tard par un admin.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def envoyer_alerte_point_saute(
    email_destinataire: str,
    entreprise_nom: str,
    camion_matricule: str,
    chauffeur_nom: str,
    bac_id: str,
    date_trajet: str,
) -> bool:
    """
    Envoie un email d'alerte pour un bac sauté. Renvoie True si l'envoi
    a réussi, False sinon (jamais d'exception propagée vers l'appelant).
    """
    if not settings.alertes_email_active:
        return False

    if not email_destinataire:
        return False

    sujet = f"CoDeCI — Bac non collecté ({camion_matricule})"
    corps = (
        f"Bonjour,\n\n"
        f"Un bac semble avoir été sauté lors de la tournée du "
        f"{date_trajet} pour {entreprise_nom}.\n\n"
        f"Camion : {camion_matricule}\n"
        f"Chauffeur : {chauffeur_nom}\n"
        f"Bac concerné (ID) : {bac_id}\n\n"
        f"Merci de vérifier avec le chauffeur si ce bac doit être "
        f"collecté lors d'un prochain passage.\n\n"
        f"— CoDeCI (message automatique)"
    )

    message = MIMEMultipart()
    message["From"] = settings.smtp_username
    message["To"] = email_destinataire
    message["Subject"] = sujet
    message.attach(MIMEText(corps, "plain", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as serveur:
            serveur.starttls()
            serveur.login(settings.smtp_username, settings.smtp_password)
            serveur.sendmail(settings.smtp_username, email_destinataire, message.as_string())
        return True
    except Exception:
        return False