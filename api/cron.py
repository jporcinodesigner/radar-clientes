"""
Vercel Serverless Function (Python Runtime)
Endpoint: /api/cron
"""

import os
import re
import json
import hashlib
from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

WORKANA_FEED_URL = os.getenv(
    "WORKANA_FEED_URL",
    "https://www.workana.com/jobs?category=it-programming&language=pt",
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

REQUEST_TIMEOUT = 15 

APPROVAL_KEYWORDS = [
    "desenvolvimento front-end", "front-end", "frontend",
    "landing page", "site estático", "sites estáticos",
    "código puro", "performance web", "performance", "conversão",
]

REJECTION_KEYWORDS = [
    "wordpress", "elementor", "wix", "shopify", "cms", "template", "plugin", "plugins",
]

MAX_PROPOSALS = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

WORKANA_SELECTORS = {
    "project_card": "div.project-item",
    "title": "a.project-title",
    "description": "p.project-description",
    "proposals": "span.bids-info",
}

# ---------------------------------------------------------------------------
# LÓGICA DO ROBÔ
# ---------------------------------------------------------------------------

def fetch_workana_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text

def extract_proposal_count(text: str) -> int | None:
    if not text: return None
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None

def parse_projects(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(WORKANA_SELECTORS["project_card"])
    projects = []
    for card in cards:
        title_el = card.select_one(WORKANA_SELECTORS["title"])
        desc_el = card.select_one(WORKANA_SELECTORS["description"])
        proposals_el = card.select_one(WORKANA_SELECTORS["proposals"])
        if not title_el: continue
        title = title_el.get_text(strip=True)
        link = title_el.get("href", "")
        if link and link.startswith("/"): link = f"https://www.workana.com{link}"
        description = desc_el.get_text(strip=True) if desc_el else ""
        proposals_text = proposals_el.get_text(strip=True) if proposals_el else ""
        proposal_count = extract_proposal_count(proposals_text)
        projects.append({"title": title, "link": link, "description": description, "proposal_count": proposal_count})
    return projects

def matches_filters(project: dict) -> tuple[bool, str]:
    haystack = f"{project['title']} {project['description']}".lower()
    for word in REJECTION_KEYWORDS:
        if word in haystack: return False, f"Rejeitado: termo proibido '{word}'"
    matched_terms = [w for w in APPROVAL_KEYWORDS if w in haystack]
    if not matched_terms: return False, "Rejeitado: nenhum termo de aprovação"
    if project["proposal_count"] is None: return False, "Rejeitado: contagem de propostas indisponível"
    if project["proposal_count"] > MAX_PROPOSALS: return False, f"Rejeitado: {project['proposal_count']} propostas"
    return True, f"Aprovado: corresponde a '{', '.join(matched_terms)}'"

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)

def run_pipeline():
    html = fetch_workana_page(WORKANA_FEED_URL)
    projects = parse_projects(html)
    for project in projects:
        ok, reason = matches_filters(project)
        if ok:
            msg = f"🟢 *Nova vaga qualificada*\n*Título:* {project['title']}\n*Link:* {project['link']}\n*Motivo:* {reason}"
            send_telegram_message(msg)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            run_pipeline()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot executado com sucesso!")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())