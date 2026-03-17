import time
import re
import requests
import os
import sys
import traceback
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

app = Flask(__name__)
CORS(app)

class ChavesScraper:
    def __init__(self, email, senha):
        self.email = email
        self.senha = senha
        self.imoveis = []
        self.session = requests.Session()
        
    def setup_driver(self):
        print("🔧 Configurando Chrome...")
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/opt/render/project/.render/chrome/chrome-linux64/chrome"
        ]
        
        chrome_binary = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                options.binary_location = chrome_binary
                print(f"✅ Chrome encontrado em: {path}")
                break
        
        if not chrome_binary:
            raise Exception("Chrome não encontrado")
        
        driver_paths = [
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            "/opt/render/project/.render/chromedriver/chromedriver"
        ]
        
        chromedriver_binary = None
        for path in driver_paths:
            if os.path.exists(path):
                chromedriver_binary = path
                print(f"✅ ChromeDriver encontrado em: {path}")
                break
        
        if not chromedriver_binary:
            raise Exception("ChromeDriver não encontrado")
        
        service = Service(chromedriver_binary)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 15)
        print("✅ Chrome configurado com sucesso!")
    
    def login(self):
        print("🔐 Fazendo login...")
        self.driver.get("https://www.chavesnamao.com.br/entrar/")
        time.sleep(3)
        
        try:
            botao_email = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "span.spacing-1x > button")
            ))
            botao_email.click()
            time.sleep(2)
        except:
            pass
        
        campo_email = self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#userLogin-input")
        ))
        campo_email.send_keys(self.email)
        time.sleep(1)
        
        campo_senha = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        campo_senha.send_keys(self.senha)
        time.sleep(1)
        
        try:
            botao_entrar = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            botao_entrar.click()
        except:
            botao_email.click()
        
        time.sleep(5)
        print("✅ Login realizado!")
    
    def ir_para_meus_anuncios(self):
        print("📋 Acessando Meus Anúncios...")
        self.driver.get("https://www.chavesnamao.com.br/minhaconta/meusanuncios/")
        time.sleep(5)
    
    def extrair_fotos_por_padrao(self, url_primeira_foto):
        fotos = []
        url_primeira_foto = url_primeira_foto.replace('/0262x0197/', '/1200x0800/')
        url_primeira_foto = url_primeira_foto.split('?')[0]
        
        match = re.search(r'(.+)-(\d{2})\.jpg', url_primeira_foto)
        if not match:
            fotos.append(url_primeira_foto)
            return fotos
        
        base_url = match.group(1)
        for i in range(20):
            numero = str(i).zfill(2)
            foto_url = f"{base_url}-{numero}.jpg"
            try:
                response = self.session.head(foto_url, timeout=2)
                if response.status_code == 200:
                    fotos.append(foto_url)
            except:
                if i > 5 and len(fotos) == i:
                    break
        return fotos[:15]
    
    def extrair_dados_completos(self, id_anuncio):
        print(f"\n📂 Processando ID: {id_anuncio}")
        dados = {'codigo': id_anuncio, 'titulo': '', 'preco_venda': '', 'bairro': '', 'fotos': []}
        
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            time.sleep(2)
            texto_pagina = self.driver.find_element(By.TAG_NAME, 'body').text
            
            try:
                titulo_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1')
                dados['titulo'] = titulo_elem.text.strip()
            except:
                pass
            
            preco_match = re.search(r'R?\$\s*([\d.,]+)', texto_pagina)
            if preco_match:
                dados['preco_venda'] = preco_match.group(1)
            
            bairros = ['Batel', 'Água Verde', 'Centro', 'Bigorrilho', 'Juvevê']
            for bairro in bairros:
                if bairro in texto_pagina:
                    dados['bairro'] = bairro
                    break
            
            imagens = self.driver.find_elements(By.CSS_SELECTOR, 'img[src*="imoveis/"]')
            for img in imagens[:5]:
                src = img.get_attribute('src')
                if src and id_anuncio in src:
                    dados['fotos'].append(src)
        except Exception as e:
            print(f"Erro: {e}")
        return dados
    
    def processar_anuncios(self):
        print("\n🔍 Coletando URLs...")
        time.sleep(3)
        urls = []
        links = self.driver.find_elements(By.CSS_SELECTOR, 'h2.anuncio-titulo a')
        for link in links[:3]:
            url = link.get_attribute('href')
            if url:
                urls.append(url)
        
        for i, url in enumerate(urls):
            try:
                self.driver.get(url)
                time.sleep(5)
                id_match = re.search(r'/(\d+)/', url)
                id_anuncio = id_match.group(1) if id_match else str(i+1)
                dados = self.extrair_dados_completos(id_anuncio)
                self.imoveis.append(dados)
                self.driver.get("https://www.chavesnamao.com.br/minhaconta/meusanuncios/")
                time.sleep(3)
            except:
                continue
    
    def gerar_xml(self):
        if not self.imoveis:
            return None
        root = ET.Element("ListingDataFeed")
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "Email").text = self.email
        listings = ET.SubElement(root, "Listings")
        for imovel in self.imoveis:
            listing = ET.SubElement(listings, "Listing")
            ET.SubElement(listing, "ListingID").text = imovel.get('codigo', '')
            ET.SubElement(listing, "Title").text = imovel.get('titulo', '')
        return ET.tostring(root, encoding="unicode")
    
    def run(self):
        try:
            self.setup_driver()
            self.login()
            self.ir_para_meus_anuncios()
            self.processar_anuncios()
            xml_content = self.gerar_xml()
            return {'success': True, 'total_anuncios': len(self.imoveis), 'xml': xml_content}
        except Exception as e:
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'online', 'endpoints': {'/scraper': 'POST', '/health': 'GET'}})

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
        scraper = ChavesScraper(email, senha)
        resultado = scraper.run()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
