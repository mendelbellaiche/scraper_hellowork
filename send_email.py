#!/usr/bin/env python3

import argparse
import html
import json
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from dotenv import load_dotenv

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def format_elapsed(date_publication):
    if not date_publication:
        return ""
    try:
        published = datetime.fromisoformat(date_publication.replace("Z", "+00:00"))
    except ValueError:
        return ""

    now = datetime.now(timezone.utc)
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)

    delta = now - published
    seconds = delta.total_seconds()

    if seconds < 3600:
        minutes = max(int(seconds // 60), 0)
        return f"il y a {minutes} min" if minutes else "à l'instant"
    if seconds < 86400:
        hours = int(seconds // 3600)
        return f"il y a {hours} h"
    days = int(seconds // 86400)
    return f"il y a {days} j" if days > 1 else "il y a 1 j"


def load_jobs(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def build_text_body(jobs):
    if not jobs:
        return "Aucune offre à envoyer."

    parts = []
    for job in jobs:
        parts.append(
            "\n".join([
                "=" * 80,
                f"TITRE: {job.get('titre', '')}",
                f"ENTREPRISE: {job.get('entreprise', '')}",
                f"SALAIRE: {job.get('salaire', '')}",
                f"RECHERCHE(S): {', '.join(job.get('mots_cles', []) or [])}",
                f"PUBLIÉE: {job.get('date_publication', '') or 'inconnue'}"
                + (f" ({format_elapsed(job.get('date_publication'))})" if job.get('date_publication') else ""),
                f"URL: {job.get('url', '')}",
                f"DATE RECUPERATION: {job.get('date_recuperation', '')}",
                "",
                "DESCRIPTION:",
                job.get("description", ""),
            ])
        )
    return "\n\n".join(parts)


def build_html_body(jobs):
    if not jobs:
        return "<p>Aucune offre à envoyer.</p>"

    cards = []
    for job in jobs:
        titre = html.escape(job.get("titre", "") or "Sans titre")
        entreprise = html.escape(job.get("entreprise", "") or "—")
        salaire = html.escape(job.get("salaire", "") or "Non précisé")
        mots_cles = html.escape(", ".join(job.get("mots_cles", []) or []))
        elapsed = html.escape(format_elapsed(job.get("date_publication")))
        url = html.escape(job.get("url", ""))
        date = html.escape(job.get("date_recuperation", ""))
        description = html.escape(job.get("description", "")).replace("\n", "<br>")

        cards.append(f"""
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border:1px solid #e2e5ea;border-radius:10px;margin-bottom:20px;">
          <tr>
            <td style="padding:20px 24px;">
              <div style="font-size:18px;font-weight:700;color:#1a1a2e;margin-bottom:6px;">
                {titre}
              </div>
              <div style="font-size:14px;color:#4a4f5a;margin-bottom:12px;">
                {entreprise} &nbsp;•&nbsp; <span style="color:#0a7a3d;font-weight:600;">{salaire}</span>
              </div>
              <div style="font-size:11px;color:#6a70ff;font-weight:600;margin-bottom:12px;text-transform:uppercase;">
                Recherche(s) : {mots_cles or "—"}
                {f" &nbsp;•&nbsp; Publiée {elapsed}" if elapsed else ""}
              </div>
              <div style="font-size:13px;line-height:1.6;color:#5c6270;margin-bottom:14px;">
                {description}
              </div>
              <a href="{url}"
                 style="display:inline-block;background:#0057ff;color:#ffffff;text-decoration:none;
                        font-size:13px;font-weight:600;padding:9px 16px;border-radius:6px;">
                Voir l'offre
              </a>
              <div style="font-size:11px;color:#9aa0ab;margin-top:12px;">
                Récupérée le {date}
              </div>
            </td>
          </tr>
        </table>
        """)

    return f"""
    <html>
      <body style="margin:0;padding:0;background:#f2f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f2f4f7;padding:24px 0;">
          <tr>
            <td align="center">
              <table role="presentation" width="600" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding-bottom:20px;">
                    <div style="font-size:22px;font-weight:800;color:#1a1a2e;">
                      Offres HelloWork
                    </div>
                    <div style="font-size:13px;color:#5c6270;">
                      {len(jobs)} offre(s) trouvée(s)
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>
                    {"".join(cards)}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


def send_email(sender, password, recipient, subject, jobs):
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(build_text_body(jobs))
    message.add_alternative(build_html_body(jobs), subtype="html")

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(sender, password)
        server.send_message(message)


def parse_args():
    parser = argparse.ArgumentParser(description="Envoie les offres de offres.json par email")
    parser.add_argument(
        "--file",
        default="./offres/offres.json",
        help="Chemin du fichier JSON des offres (défaut : ./offres/offres.json)"
    )
    parser.add_argument(
        "--to",
        default=None,
        help="Adresse email destinataire (défaut : GMAIL_ADDRESS, i.e. on s'envoie à soi-même)"
    )
    parser.add_argument(
        "--subject",
        default="Offres HelloWork",
        help="Sujet de l'email (défaut : 'Offres HelloWork')"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    load_dotenv()

    sender = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")

    if not sender or not password:
        raise SystemExit(
            "GMAIL_ADDRESS et GMAIL_APP_PASSWORD doivent être définis dans le fichier .env"
        )

    recipient = args.to or sender

    jobs = load_jobs(args.file)

    subject = args.subject if jobs else f"{args.subject} - Aucune nouvelle offre"
    send_email(sender, password, recipient, subject, jobs)
    print(f"Email envoyé à {recipient} ({len(jobs)} offre(s))")

if __name__ == "__main__":
    main()
