# Workana Job Bot — Vercel Cron + Telegram

Monitora vagas na Workana, aplica filtros de aprovação/rejeição/concorrência e
envia as oportunidades qualificadas para o Telegram.

## ⚠️ Leia antes de usar

1. **Scraping pode violar os Termos de Uso da Workana.** Verifique a política
   da plataforma. Se existir uma API oficial ou um feed RSS, prefira usá-los —
   são mais estáveis e não correm risco de bloqueio de conta/IP.
2. **Os seletores CSS em `api/cron.py` (`WORKANA_SELECTORS`) são um ponto de
   partida, não a solução final.** O HTML da Workana muda com frequência.
   Antes do primeiro deploy:
   - Abra a página de vagas no navegador.
   - Botão direito num card de projeto → **Inspecionar**.
   - Atualize `project_card`, `title`, `description` e `proposals` em
     `WORKANA_SELECTORS` com as classes reais que você encontrar.
3. **Vercel Cron no plano Hobby (gratuito) só permite execução 1x por dia.**
   Para rodar de hora em hora (`0 * * * *`) você precisa do plano **Pro**.
   No Hobby, ajuste `vercel.json` para algo como `"0 9 * * *"` (uma vez por dia).
4. Se a página exigir login para mostrar o número de propostas ou a descrição
   completa, o scraping público não vai conseguir esses dados — nesse caso
   seria necessário automatizar um login real, o que tem implicações de
   segurança e de Termos de Uso ainda maiores.

## Estrutura de pastas

```
workana-bot/
├── api/
│   └── cron.py          # função serverless (endpoint /api/cron)
├── vercel.json           # configuração do cron job
├── requirements.txt       # dependências Python
├── .env.example            # modelo de variáveis de ambiente
└── README.md
```

A Vercel detecta automaticamente qualquer arquivo `.py` dentro de `api/` como
uma Serverless Function em Python — não é necessário configurar nada além do
`vercel.json`.

## Passo a passo de deploy

### 1. Criar o bot no Telegram
1. Fale com [@BotFather](https://t.me/BotFather) no Telegram.
2. `/newbot` → siga as instruções → copie o **token** gerado.
3. Envie uma mensagem qualquer para o seu novo bot.
4. Acesse `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates` no navegador
   e copie o valor de `"chat":{"id": ...}` — esse é o seu `CHAT_ID`.

### 2. Subir o projeto para o GitHub
```bash
cd workana-bot
git init
git add .
git commit -m "Setup inicial do bot de vagas Workana"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/workana-bot.git
git push -u origin main
```
> Não faça commit do arquivo `.env` real — apenas do `.env.example`.

### 3. Deploy na Vercel
1. Acesse [vercel.com](https://vercel.com) → **Add New Project** → importe o
   repositório do GitHub.
2. Em **Environment Variables**, adicione:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - (opcional) `WORKANA_FEED_URL`
3. Clique em **Deploy**.
4. Após o deploy, a Vercel lê automaticamente `vercel.json` e agenda o Cron
   Job — confirme em **Project → Settings → Cron Jobs**.

### 4. Testar manualmente
Acesse no navegador:
```
https://SEU_PROJETO.vercel.app/api/cron
```
Isso dispara a função na hora e retorna um JSON de resumo, por exemplo:
```json
{
  "status": "ok",
  "summary": {
    "total_encontradas": 12,
    "aprovadas": 1,
    "rejeitadas": 11,
    "enviadas_com_sucesso": ["Título da vaga aprovada"],
    "erros_envio": []
  }
}
```

## Personalizando os filtros

Edite as listas no topo de `api/cron.py`:
- `APPROVAL_KEYWORDS` — termos que precisam aparecer (título + descrição).
- `REJECTION_KEYWORDS` — termos que descartam a vaga imediatamente.
- `MAX_PROPOSALS` — limite máximo de propostas já enviadas.

## Limitações conhecidas

- Sem deduplicação: se a mesma vaga continuar na listagem na próxima execução
  do cron, ela será enviada de novo. Para evitar isso, seria necessário
  persistir os `fingerprint` já enviados em algum storage externo (ex: Vercel
  KV, Redis, ou um banco simples), já que funções serverless não mantêm
  estado entre execuções.
- Sem tratamento de captcha/Cloudflare challenge — se a Workana apresentar
  esse tipo de proteção, o `requests.get` simples vai falhar e a função vai
  retornar erro 500.
