#!/usr/bin/env bash
# render-build.sh - Versão que não usa apt-get
set -o errexit

# Diretório para cache
CACHE_DIR=/opt/render/project/.render

# Baixa Chrome (apenas se não estiver em cache)
if [ ! -f $CACHE_DIR/chrome/chrome ]; then
  echo "📦 Baixando Chrome..."
  mkdir -p $CACHE_DIR/chrome
  cd $CACHE_DIR/chrome
  wget -q https://storage.googleapis.com/chrome-for-testing-public/latest/linux64/chrome-linux64.zip
  unzip -q chrome-linux64.zip
  rm chrome-linux64.zip
  cd ~
fi

# Baixa ChromeDriver (apenas se não estiver em cache)
if [ ! -f $CACHE_DIR/chromedriver/chromedriver ]; then
  echo "📦 Baixando ChromeDriver..."
  mkdir -p $CACHE_DIR/chromedriver
  cd $CACHE_DIR/chromedriver
  wget -q https://storage.googleapis.com/chrome-for-testing-public/latest/linux64/chromedriver-linux64.zip
  unzip -q chromedriver-linux64.zip
  rm chromedriver-linux64.zip
  mv chromedriver-linux64/chromedriver .
  rm -rf chromedriver-linux64
  cd ~
fi

# Instala dependências Python
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

echo "✅ Build concluído!"
