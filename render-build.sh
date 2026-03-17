#!/usr/bin/env bash
echo "🚀 Iniciando build script..."

# Instala Chrome
apt-get update
apt-get install -y wget gnupg unzip curl

# Baixa e instala Chrome
wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i /tmp/chrome.deb || apt-get install -f -y
rm /tmp/chrome.deb

# Instala ChromeDriver
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip"
unzip -o /tmp/chromedriver.zip -d /tmp/
mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Instala dependências Python
pip install -r requirements.txt

echo "✅ Build concluído!"
