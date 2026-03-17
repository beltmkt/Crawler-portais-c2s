#!/usr/bin/env bash
set -o errexit

echo "🚀 Instalando Firefox..."

# Instala Firefox via apt (muito mais simples!)
apt-get update
apt-get install -y firefox-esr  # ou firefox

# Baixa GeckoDriver
GECKO_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep tag_name | cut -d '"' -f 4)
wget -q -O /tmp/geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/$GECKO_VERSION/geckodriver-$GECKO_VERSION-linux64.tar.gz"
tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/
chmod +x /usr/local/bin/geckodriver

echo "✅ Firefox e GeckoDriver instalados!"
firefox --version
geckodriver --version
