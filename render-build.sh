#!/usr/bin/env bash
# render-build.sh - Instala Chrome e dependências

echo "🚀 Iniciando build script..."

# Atualiza pacotes
apt-get update

# Instala dependências do Chrome
apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    xdg-utils

# Baixa e instala Chrome
echo "📦 Baixando Chrome..."
wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i /tmp/chrome.deb || apt-get install -f -y
rm /tmp/chrome.deb

# Verifica instalação
echo "✅ Chrome instalado em: $(which google-chrome)"
google-chrome --version

# Baixa ChromeDriver compatível
echo "📦 Baixando ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+' | head -1)
echo "📌 Versão do Chrome detectada: $CHROME_VERSION"

# Tenta baixar ChromeDriver da versão específica
CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip"
wget -q -O /tmp/chromedriver.zip $CHROMEDRIVER_URL || {
    echo "⚠️ Versão específica não encontrada, baixando a última estável..."
    CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/latest/linux64/chromedriver-linux64.zip"
    wget -q -O /tmp/chromedriver.zip $CHROMEDRIVER_URL
}

unzip -o /tmp/chromedriver.zip -d /tmp/
mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver
rm -rf /tmp/chromedriver*

# Verifica instalação
echo "✅ ChromeDriver instalado em: $(which chromedriver)"
chromedriver --version

# Instala dependências Python
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

echo "✅ Build concluído com sucesso!"
