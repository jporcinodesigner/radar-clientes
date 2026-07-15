"""
Vercel Serverless Function (Python Runtime)
Execução manual via HTTP GET
"""

import os
import re
import requests
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO (Mantida igual)
# ---------------------------------------------------------------------------
WORKANA_FEED_URL = os.getenv("WORKANA_FEED_URL", "https://www.workana.com/jobs?category=it-programming&language=pt")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
REQUEST_TIMEOUT = 15 

APPROVAL_KEYWORDS = ["desenvolvimento front-end", "front-end", "frontend", "landing page", "site estático", "sites estáticos", "código puro", "performance web", "performance", "conversão"]
REJECTION_KEYWORDS = ["wordpress", "elementor", "wix", "shopify", "cms", "template", "plugin", "plugins"]
MAX_PROPOSALS = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# ... (Mantenha as funções fetch_workana_page, extract_proposal_count, parse_projects, matches_filters e send_telegram_message exatamente como estavam) ...

# ---------------------------------------------------------------------------
# LÓGICA DO ROBÔ (Ajustada)
# ---------------------------------------------------------------------------

def run_pipeline():
    html = fetch_workana_page(WORKANA_FEED_URL)
    projects = parse_projects(html)
    results = []
    for project in projects:
        ok, reason = matches_filters(project)
        if ok:
            msg = f"🟢 *Nova vaga qualificada*\n*Título:* {project['title']}\n*Link:* {project['link']}\n*Motivo:* {reason}"
            send_telegram_message(msg)
            results.append(project['title'])
    return results

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Ao acessar o link, o pipeline é disparado
            vagas_encontradas = run_pipeline()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            
            mensagem = f"Execução manual finalizada! Vagas encontradas: {len(vagas_encontradas)}"
            self.wfile.write(mensagem.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Erro na execução: {str(e)}".encode())