#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build script..."

# Instala Firefox (muito mais simples que Chrome!)
apt-get update
apt-get install -y firefox-esr wget

# Baixa GeckoDriver
GECKO_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep tag_name | cut -d '"' -f 4)
echo "📦 Baixando GeckoDriver $GECKO_VERSION..."
wget -q -O /tmp/geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/$GECKO_VERSION/geckodriver-$GECKO_VERSION-linux64.tar.gz"
tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/
chmod +x /usr/local/bin/geckodriver

# Instala dependências Python
pip install -r requirements.txt

echo "✅ Build concluído!"
firefox --version
geckodriver --version
