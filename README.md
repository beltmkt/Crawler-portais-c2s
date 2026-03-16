# 🏠 Crawler Chaves na Mão - API

API para extrair dados de imóveis do site Chaves na Mão.

## 🚀 Endpoints

### \POST /scraper\
Executa o crawler e retorna XML no formato Viva Real.

**Body (JSON):**
\\\json
{
  "email": "seu@email.com",
  "senha": "sua_senha"
}
\\\

**Resposta:**
\\\json
{
  "success": true,
  "total_anuncios": 10,
  "xml": "<?xml version...>"
}
\\\

### \GET /health\
Verifica se a API está online.

### \GET /\
Informações da API.

## 🛠️ Deploy no Render

1. Conecte este repositório ao Render
2. Configure:
   - **Build Command:** \pip install -r requirements.txt\
   - **Start Command:** \gunicorn crawler_chavesnamao:app\

## 📦 Dependências

- Flask
- Selenium
- webdriver-manager
- gunicorn

## ⚙️ Variáveis de Ambiente

- \PORT\ (opcional) - Porta da aplicação (default: 5000)
