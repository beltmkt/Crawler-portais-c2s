# Substitua o conteúdo do arquivo atual
import time
import re
import requests
import os
import sys
import traceback
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

# ==============================================
# CONFIGURAÇÕES DA API
# ==============================================
app = Flask(__name__)
CORS(app)

# ==============================================
# CLASSE SCRAPER (CORRIGIDA)
# ==============================================
class ChavesScraper:
    def __init__(self, email, senha):
        self.email = email
        self.senha = senha
        self.imoveis = []
        self.session = requests.Session()
        
    def setup_driver(self):
        """Configura o ChromeDriver usando caminhos absolutos"""
        print("🔧 Configurando ChromeDriver...")
        
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Caminhos absolutos no Render
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser"
        ]
        
        driver_paths = [
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            "/usr/bin/chromium-driver"
        ]
        
        # Encontra o Chrome
        chrome_binary = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                print(f"✅ Chrome encontrado em: {path}")
                break
        
        if not chrome_binary:
            # Tenta encontrar com which
            try:
                chrome_binary = subprocess.check_output(["which", "google-chrome"], text=True).strip()
                if chrome_binary:
                    print(f"✅ Chrome encontrado via which: {chrome_binary}")
            except:
                pass
        
        if not chrome_binary:
            raise Exception("Chrome não encontrado. Verifique a instalação.")
        
        options.binary_location = chrome_binary
        
        # Encontra o ChromeDriver
        chromedriver_binary = None
        for path in driver_paths:
            if os.path.exists(path):
                chromedriver_binary = path
                print(f"✅ ChromeDriver encontrado em: {path}")
                break
        
        if not chromedriver_binary:
            # Tenta encontrar com which
            try:
                chromedriver_binary = subprocess.check_output(["which", "chromedriver"], text=True).strip()
                if chromedriver_binary:
                    print(f"✅ ChromeDriver encontrado via which: {chromedriver_binary}")
            except:
                pass
        
        if not chromedriver_binary:
            raise Exception("ChromeDriver não encontrado. Verifique a instalação.")
        
        # Inicializa o driver
        service = Service(chromedriver_binary)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Driver configurado com sucesso!")
    
    def login(self):
        """Faz login no site"""
        print("🔐 Fazendo login...")
        self.driver.get("https://www.chavesnamao.com.br/entrar/")
        time.sleep(5)
        
        try:
            # Tenta clicar no botão de email
            try:
                botao_email = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "span.spacing-1x > button"))
                )
                botao_email.click()
                time.sleep(2)
            except:
                pass
            
            # Preenche email
            campo_email = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#userLogin-input"))
            )
            campo_email.send_keys(self.email)
            time.sleep(1)
            
            # Preenche senha
            campo_senha = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            campo_senha.send_keys(self.senha)
            time.sleep(1)
            
            # Clica em entrar
            try:
                botao_entrar = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                botao_entrar.click()
            except:
                pass
            
            time.sleep(5)
            print("✅ Login realizado!")
            
        except Exception as e:
            print(f"❌ Erro no login: {e}")
            raise
    
    def ir_para_meus_anuncios(self):
        """Acessa a página de meus anúncios"""
        print("📋 Acessando Meus Anúncios...")
        self.driver.get("https://www.chavesnamao.com.br/minhaconta/meusanuncios/")
        time.sleep(5)
    
    def extrair_dados_basicos(self, id_anuncio):
        """Extrai dados básicos do anúncio"""
        print(f"\n📂 Processando anúncio ID: {id_anuncio}")
        
        dados = {
            'codigo': id_anuncio,
            'titulo': '',
            'preco_venda': '',
            'bairro': '',
            'quartos': 0,
            'area_util': 0,
            'fotos': []
        }
        
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            time.sleep(2)
            
            texto_pagina = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # Título
            try:
                titulo_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1')
                dados['titulo'] = titulo_elem.text.strip()
                print(f"   ✅ Título: {dados['titulo'][:80]}...")
            except:
                pass
            
            # Preço
            preco_match = re.search(r'R?\$\s*([\d.,]+(?:[.,]\d{3})*(?:[.,]\d{2})?)', texto_pagina)
            if preco_match:
                valor = preco_match.group(1).replace('.', '').replace(',', '.')
                if re.match(r'^\d+\.?\d*$', valor):
                    dados['preco_venda'] = valor
            
            # Bairro
            bairros = ['Batel', 'Água Verde', 'Centro', 'Bigorrilho', 'Mercês', 'Juvevê']
            for bairro in bairros:
                if bairro in texto_pagina:
                    dados['bairro'] = bairro
                    break
            
            # Quartos
            q_match = re.search(r'(\d+)\s*quartos?', texto_pagina, re.I)
            if q_match:
                dados['quartos'] = int(q_match.group(1))
            
            # Área
            a_match = re.search(r'(\d+[.,]?\d*)\s*m[²2]', texto_pagina, re.I)
            if a_match:
                dados['area_util'] = float(a_match.group(1).replace(',', '.'))
            
            # Fotos (apenas a primeira)
            imagens = self.driver.find_elements(By.CSS_SELECTOR, 'img[src*="imoveis/"]')
            for img in imagens[:3]:
                try:
                    src = img.get_attribute('src')
                    if src:
                        dados['fotos'].append(src.split('?')[0])
                except:
                    continue
            
        except Exception as e:
            print(f"❌ Erro no anúncio {id_anuncio}: {e}")
        
        return dados
    
    def processar_anuncios(self):
        """Processa os anúncios da lista"""
        print("\n🔍 Buscando anúncios...")
        time.sleep(3)
        
        links = self.driver.find_elements(By.CSS_SELECTOR, 'h2.anuncio-titulo a')[:3]  # Limite de 3
        
        for i, link in enumerate(links):
            try:
                url = link.get_attribute('href')
                if not url:
                    continue
                
                print(f"\n⏳ Processando anúncio {i+1}")
                self.driver.get(url)
                time.sleep(5)
                
                id_match = re.search(r'/(\d+)/', url)
                id_anuncio = id_match.group(1) if id_match else str(i+1)
                
                dados = self.extrair_dados_basicos(id_anuncio)
                self.imoveis.append(dados)
                
                self.driver.get("https://www.chavesnamao.com.br/minhaconta/meusanuncios/")
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Erro: {e}")
                continue
    
    def gerar_xml_simples(self):
        """Gera XML simples"""
        if not self.imoveis:
            return None
        
        root = ET.Element("ListingDataFeed")
        root.set("xmlns", "http://www.vivareal.com/schemas/1.0/VRSync")
        
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "Provider").text = self.email.split('@')[0].upper()
        ET.SubElement(header, "Email").text = self.email
        
        listings = ET.SubElement(root, "Listings")
        
        for imovel in self.imoveis:
            listing = ET.SubElement(listings, "Listing")
            ET.SubElement(listing, "ListingID").text = imovel.get('codigo', '')
            ET.SubElement(listing, "Title").text = imovel.get('titulo', '')
            
            if imovel.get('preco_venda'):
                ET.SubElement(listing, "SalePrice", currency="BRL").text = imovel['preco_venda']
            
            details = ET.SubElement(listing, "Details")
            ET.SubElement(details, "Bedrooms").text = str(imovel.get('quartos', 0))
            
            if imovel.get('fotos'):
                media = ET.SubElement(listing, "Media")
                for foto in imovel['fotos']:
                    ET.SubElement(media, "Item", medium="image").text = foto
            
            contact = ET.SubElement(listing, "ContactInfo")
            ET.SubElement(contact, "Email").text = self.email
        
        return ET.tostring(root, encoding="unicode")
    
    def run(self):
        """Executa o scraper"""
        try:
            self.setup_driver()
            self.login()
            self.ir_para_meus_anuncios()
            self.processar_anuncios()
            xml_content = self.gerar_xml_simples()
            
            return {
                'success': True,
                'total_anuncios': len(self.imoveis),
                'xml': xml_content
            }
            
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
            
        finally:
            if hasattr(self, 'driver'):
                try:
                    self.driver.quit()
                except:
                    pass

# ==============================================
# ENDPOINTS DA API
# ==============================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'online',
        'message': 'API do Crawler Chaves na Mão',
        'endpoints': {
            '/scraper': 'POST - Executa o crawler',
            '/health': 'GET - Verifica status'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/scraper', methods=['POST'])
def scraper():
    try:
        data = request.json
        email = data.get('email')
        senha = data.get('senha')
        
        if not email or not senha:
            return jsonify({'error': 'Email e senha obrigatórios'}), 400
        
        print(f"\n🚀 Iniciando crawler para: {email}")
        scraper = ChavesScraper(email, senha)
        resultado = scraper.run()
        
        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
'@ | Out-File -FilePath "crawler_chavesnamao.py" -Encoding UTF8 -Force

Write-Host "✅ crawler_chavesnamao.py atualizado!" -ForegroundColor Green
