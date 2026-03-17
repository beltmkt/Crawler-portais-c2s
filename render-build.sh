#!/usr/bin/env bash
set -o errexit

CACHE_DIR=/opt/render/project/.render

# Baixa Chrome
if [ ! -f $CACHE_DIR/chrome/chrome-linux64/chrome ]; then
  echo "📦 Baixando Chrome..."
  mkdir -p $CACHE_DIR/chrome
  cd $CACHE_DIR/chrome
  wget -q https://storage.googleapis.com/chrome-for-testing-public/latest/linux64/chrome-linux64.zip
  unzip -q chrome-linux64.zip
  rm chrome-linux64.zip
  cd ~
fi

# Baixa ChromeDriver
if [ ! -f $CACHE_DIR/chromedriver/chromedriver ]; then
  echo "📦 Baixando ChromeDriver..."
  mkdir -p $CACHE_DIR/chromedriver
  cd $CACHE_DIR/chromedriver
  wget -q https://storage.googleapis.com/chrome-for-testing-public/latest/linux64/chromedriver-linux64.zip
  unzip -q chromedriver-linux64.zip
  rm chromedriver-linux64.zip
  mv chromedriver-linux64/chromedriver .
  rm -rf
