import os
import re
import requests
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup

# ----------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------
URL_DO_FEED_DO_WORKANA = os.getenv("WORKANA_FEED_URL", "https://www.workana.com/jobs?category=it-programming&language=pt")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ID_DO_CHAT_DO_TELEGRAM = os.getenv("TELEGRAM_CHAT_ID")
# ----------------------------------------------------

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
        try:
            # Lógica principal do bot
            response = requests.get(URL_DO_FEED_DO_WORKANA)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Aqui entraria a lógica de processamento do feed
            self.wfile.write("Bot rodou com sucesso!".encode('utf-8'))
            
        except Exception as e:
            self.wfile.write(f"Erro no bot: {str(e)}".encode('utf-8'))
        return
