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
# CLASSE SCRAPER (VERSÃO SIMPLIFICADA)
# ==============================================
class ChavesScraper:
    def __init__(self, email, senha):
        self.email = email
        self.senha = senha
        self.imoveis = []
        self.session = requests.Session()
        
    def setup_driver(self):
        """Configura o ChromeDriver de forma SIMPLES para o Render"""
        print("🔧 Configurando ChromeDriver...")
        
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # No Render, o Chromium está neste caminho
        options.binary_location = "/usr/bin/chromium"
        
        # Caminho fixo do ChromeDriver no Render
        service = Service("/usr/bin/chromedriver")
        
        try:
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 30)
            print("✅ ChromeDriver configurado com sucesso!")
        except Exception as e:
            print(f"❌ Erro na primeira tentativa: {e}")
            print("🔄 Tentando caminho alternativo...")
            
            # Segunda tentativa com caminhos alternativos
            chrome_paths = [
                "/usr/bin/chromium-browser",
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable"
            ]
            
            driver_paths = [
                "/usr/bin/chromium-driver",
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver"
            ]
            
            for chrome_path in chrome_paths:
                for driver_path in driver_paths:
                    try:
                        options.binary_location = chrome_path
                        service = Service(driver_path)
                        self.driver = webdriver.Chrome(service=service, options=options)
                        self.wait = WebDriverWait(self.driver, 30)
                        print(f"✅ Sucesso com Chrome: {chrome_path} e Driver: {driver_path}")
                        return
                    except:
                        continue
            
            raise Exception("Não foi possível configurar o ChromeDriver")
    
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
    
    def extrair_fotos_por_padrao(self, url_primeira_foto):
        """Extrai fotos do anúncio"""
        fotos = []
        if not url_primeira_foto:
            return fotos
        
        url_primeira_foto = url_primeira_foto.split('?')[0]
        match = re.search(r'(.+)-(\d{2})\.jpg', url_primeira_foto)
        
        if not match:
            fotos.append(url_primeira_foto)
            return fotos[:10]
        
        base_url = match.group(1)
        print(f"   📸 Base URL: {base_url}")
        
        for i in range(20):
            numero = str(i).zfill(2)
            foto_url = f"{base_url}-{numero}.jpg"
            
            try:
                response = self.session.head(foto_url, timeout=3)
                if response.status_code == 200:
                    fotos.append(foto_url)
                    print(f"      ✅ Foto {i:02d} encontrada")
                else:
                    if i > 3 and len(fotos) == i:
                        break
            except:
                if i > 3 and len(fotos) == i:
                    break
                continue
        
        print(f"   📸 Total de {len(fotos)} fotos encontradas")
        return fotos[:20]
    
    def extrair_dados_basicos(self, id_anuncio):
        """Extrai dados básicos do anúncio (versão simplificada)"""
        print(f"\n📂 Processando anúncio ID: {id_anuncio}")
        
        dados = {
            'codigo': id_anuncio,
            'titulo': '',
            'descricao': '',
            'tipo': 'Apartamento',
            'preco_venda': '',
            'cidade': 'Curitiba',
            'bairro': '',
            'quartos': 0,
            'banheiros': 0,
            'vagas': 0,
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
                    print(f"   Preço: R$ {dados['preco_venda']}")
            
            # Quartos
            q_match = re.search(r'(\d+)\s*quartos?', texto_pagina, re.I)
            if q_match:
                dados['quartos'] = int(q_match.group(1))
            
            # Banheiros
            b_match = re.search(r'(\d+)\s*banheiros?', texto_pagina, re.I)
            if b_match:
                dados['banheiros'] = int(b_match.group(1))
            
            # Vagas
            v_match = re.search(r'(\d+)\s*vagas?', texto_pagina, re.I)
            if v_match:
                dados['vagas'] = int(v_match.group(1))
            
            # Área
            a_match = re.search(r'(\d+[.,]?\d*)\s*m[²2]', texto_pagina, re.I)
            if a_match:
                dados['area_util'] = float(a_match.group(1).replace(',', '.'))
            
            # Fotos
            imagens = self.driver.find_elements(By.CSS_SELECTOR, 'img[src*="imoveis/"], img[src*="imn/"]')
            for img in imagens[:5]:  # Limite de 5 fotos
                try:
                    src = img.get_attribute('src')
                    if src and id_anuncio in src:
                        dados['fotos'].append(src)
                        if len(dados['fotos']) >= 5:
                            break
                except:
                    continue
            
            dados['descricao'] = dados['titulo']
            
        except Exception as e:
            print(f"❌ Erro no anúncio {id_anuncio}: {e}")
        
        return dados
    
    def processar_todos_anuncios(self):
        """Processa todos os anúncios da lista"""
        print("\n🔍 Procurando anúncios...")
        time.sleep(3)
        
        urls_anuncios = []
        links = self.driver.find_elements(By.CSS_SELECTOR, 'h2.anuncio-titulo a')
        
        for link in links[:5]:  # Limite de 5 anúncios para teste
            try:
                url = link.get_attribute('href')
                if url:
                    urls_anuncios.append(url)
                    id_match = re.search(r'/(\d+)/', url)
                    if id_match:
                        print(f"   URL encontrada: ID {id_match.group(1)}")
            except:
                continue
        
        print(f"📊 Total de {len(urls_anuncios)} URLs coletadas")
        
        for i, url in enumerate(urls_anuncios):
            print(f"\n⏳ Processando anúncio {i+1}/{len(urls_anuncios)}")
            
            try:
                self.driver.get(url)
                time.sleep(5)
                
                id_match = re.search(r'/(\d+)/', url)
                id_anuncio = id_match.group(1) if id_match else str(i+1)
                
                dados = self.extrair_dados_basicos(id_anuncio)
                self.imoveis.append(dados)
                print(f"   ✅ Anúncio adicionado!")
                
                self.driver.get("https://www.chavesnamao.com.br/minhaconta/meusanuncios/")
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Erro: {e}")
                continue
    
    def gerar_xml_simples(self):
        """Gera XML simples com os dados coletados"""
        print("\n📄 Gerando XML...")
        
        if len(self.imoveis) == 0:
            return None
        
        now = datetime.now()
        
        root = ET.Element("ListingDataFeed")
        root.set("xmlns", "http://www.vivareal.com/schemas/1.0/VRSync")
        
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "Provider").text = self.email.split('@')[0].upper()
        ET.SubElement(header, "Email").text = self.email
        
        listings = ET.SubElement(root, "Listings")
        
        for imovel in self.imoveis:
            listing = ET.SubElement(listings, "Listing")
            ET.SubElement(listing, "ListingID").text = str(imovel.get('codigo', ''))
            ET.SubElement(listing, "Title").text = imovel.get('titulo', '')
            ET.SubElement(listing, "TransactionType").text = "For Sale"
            
            location = ET.SubElement(listing, "Location")
            ET.SubElement(location, "City").text = imovel.get('cidade', 'Curitiba')
            if imovel.get('bairro'):
                ET.SubElement(location, "Neighborhood").text = imovel['bairro']
            
            details = ET.SubElement(listing, "Details")
            ET.SubElement(details, "Description").text = imovel.get('descricao', '')
            
            if imovel.get('preco_venda'):
                ET.SubElement(details, "SalePrice", currency="BRL").text = imovel['preco_venda']
            
            ET.SubElement(details, "Bedrooms").text = str(imovel.get('quartos', 0))
            ET.SubElement(details, "Bathrooms").text = str(imovel.get('banheiros', 0))
            ET.SubElement(details, "ParkingSpaces").text = str(imovel.get('vagas', 0))
            
            if imovel.get('area_util') > 0:
                ET.SubElement(details, "LivingArea", unit="square metres").text = str(imovel['area_util'])
            
            if imovel.get('fotos'):
                media = ET.SubElement(listing, "Media")
                for foto in imovel['fotos'][:5]:
                    item = ET.SubElement(media, "Item", medium="image")
                    item.text = foto
            
            contact = ET.SubElement(listing, "ContactInfo")
            ET.SubElement(contact, "Email").text = self.email
        
        return ET.tostring(root, encoding="unicode")
    
    def run(self):
        """Executa todo o processo"""
        try:
            self.setup_driver()
            self.login()
            self.ir_para_meus_anuncios()
            self.processar_todos_anuncios()
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
                'error': str(e),
                'traceback': traceback.format_exc()
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
