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
# CLASSE SCRAPER (VERSÃO FINAL CORRIGIDA)
# ==============================================
class ChavesScraper:
    def __init__(self, email, senha):
        self.email = email
        self.senha = senha
        self.imoveis = []
        self.session = requests.Session()
        
    def setup_driver(self):
        """Configura o ChromeDriver para o Render"""
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
        
        # No Render, o Chrome geralmente está neste caminho
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser"
        ]
        
        # Encontrar o Chrome
        chrome_binary = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                print(f"✅ Chrome encontrado em: {path}")
                break
        
        if not chrome_binary:
            try:
                chrome_binary = subprocess.check_output(["which", "google-chrome"], text=True).strip()
                if chrome_binary:
                    print(f"✅ Chrome encontrado via which: {chrome_binary}")
            except:
                pass
        
        if chrome_binary:
            options.binary_location = chrome_binary
        
        # Caminhos do ChromeDriver
        driver_paths = [
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            "/usr/bin/chromium-driver"
        ]
        
        # Encontrar o ChromeDriver
        chromedriver_binary = None
        for path in driver_paths:
            if os.path.exists(path):
                chromedriver_binary = path
                print(f"✅ ChromeDriver encontrado em: {path}")
                break
        
        if not chromedriver_binary:
            try:
                chromedriver_binary = subprocess.check_output(["which", "chromedriver"], text=True).strip()
                if chromedriver_binary:
                    print(f"✅ ChromeDriver encontrado via which: {chromedriver_binary}")
            except:
                pass
        
        # Se não encontrou, tenta baixar automaticamente
        if not chromedriver_binary:
            print("⚠️ ChromeDriver não encontrado, tentando baixar...")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                chromedriver_binary = ChromeDriverManager().install()
                print(f"✅ ChromeDriver baixado: {chromedriver_binary}")
            except Exception as e:
                print(f"❌ Erro ao baixar ChromeDriver: {e}")
                raise Exception("Não foi possível configurar o ChromeDriver")
        
        # Inicializar o driver
        service = Service(chromedriver_binary)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Driver configurado com sucesso!")
    
    def login(self):
        """Faz login no site"""
        print("🔐 Fazendo login...")
        try:
            self.driver.get("https://www.chavesnamao.com.br/entrar/")
            time.sleep(5)
            
            # Tentar clicar no botão de login com email
            try:
                botao_email = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "span.spacing-1x > button"))
                )
                botao_email.click()
                time.sleep(2)
            except:
                print("Botão de email não encontrado, continuando...")
            
            # Preencher email
            campo_email = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#userLogin-input"))
            )
            campo_email.send_keys(self.email)
            time.sleep(1)
            
            # Preencher senha
            campo_senha = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            campo_senha.send_keys(self.senha)
            time.sleep(1)
            
            # Clicar em entrar
            try:
                botao_entrar = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                botao_entrar.click()
            except:
                try:
                    botao_email.click()
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
        
        # Ajustar URL para tamanho grande
        url_primeira_foto = url_primeira_foto.replace('/0262x0197/', '/1200x0800/')
        url_primeira_foto = url_primeira_foto.replace('/0850x0450/', '/1200x0800/')
        url_primeira_foto = url_primeira_foto.split('?')[0]
        
        # Verificar padrão sequencial
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
    
    def extrair_caracteristicas_extras(self, texto_pagina):
        """Extrai características adicionais"""
        caracteristicas = []
        
        if not texto_pagina:
            return caracteristicas
        
        linhas = texto_pagina.split('\n')
        keywords = [
            'recepção', 'portaria', 'refeitório', 'terraço', 'jardim',
            'sala de reunião', 'estacionamento', 'elevador', 'copa',
            'ar condicionado', 'câmeras', 'segurança', 'cozinha',
            'piscina', 'churrasqueira', 'academia', 'salão de festas',
            'playground', 'quadra', 'sauna', 'gerador'
        ]
        
        for linha in linhas:
            linha = linha.strip()
            if len(linha) < 5 or len(linha) > 100:
                continue
            
            for keyword in keywords:
                if keyword.lower() in linha.lower():
                    caracteristicas.append(linha)
                    break
        
        return list(set(caracteristicas))[:20]
    
    def extrair_dados_completos(self, id_anuncio):
        """Extrai dados completos do anúncio"""
        print(f"\n📂 Processando anúncio ID: {id_anuncio}")
        
        dados = {
            'codigo': id_anuncio,
            'titulo': '',
            'descricao': '',
            'tipo': 'Apartamento',
            'subtipo': '',
            'preco_venda': '',
            'preco_locacao': '',
            'cidade': 'Curitiba',
            'bairro': '',
            'logradouro': '',
            'numero': '',
            'cep': '',
            'quartos': 0,
            'suites': 0,
            'banheiros': 0,
            'vagas': 0,
            'area_util': 0,
            'condominio': '',
            'iptu': '',
            'andar': '',
            'caracteristicas_extras': [],
            'fotos': []
        }
        
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            time.sleep(2)
            
            texto_pagina = self.driver.find_element(By.TAG_NAME, 'body').text
            print(f"   📄 Analisando página... ({len(texto_pagina)} caracteres)")
            
            # Título
            try:
                titulo_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1')
                dados['titulo'] = titulo_elem.text.strip()
                print(f"   ✅ Título: {dados['titulo'][:80]}...")
            except:
                titulo_pagina = self.driver.title
                if titulo_pagina:
                    dados['titulo'] = titulo_pagina.replace(' | Chaves na Mão', '').strip()
            
            # Código/Referência
            ref_match = re.search(r'Ref[.:]\s*([A-Z0-9-]+)', texto_pagina, re.I)
            if ref_match:
                dados['codigo'] = ref_match.group(1)
                print(f"   Código: {dados['codigo']}")
            
            # Preço
            preco_patterns = [
                r'Venda[:\s]*R?\$?\s*([\d.,]+(?:[.,]\d{3})*(?:[.,]\d{2})?)',
                r'R?\$\s*([\d.,]+(?:[.,]\d{3})*(?:[.,]\d{2})?)'
            ]
            
            for pattern in preco_patterns:
                match = re.search(pattern, texto_pagina, re.I)
                if match:
                    valor = match.group(1).replace('.', '').replace(',', '.')
                    if re.match(r'^\d+\.?\d*$', valor):
                        dados['preco_venda'] = valor
                        print(f"   Preço venda: R$ {dados['preco_venda']}")
                        break
            
            # Bairro
            bairros_conhecidos = [
                'Batel', 'Água Verde', 'Centro', 'Bigorrilho', 'Mercês',
                'Juvevê', 'Cabral', 'Hugo Lange', 'Portão', 'Rebouças',
                'Santa Felicidade', 'Campo Comprido', 'Ecoville'
            ]
            
            for bairro in bairros_conhecidos:
                if bairro in texto_pagina or bairro in dados['titulo']:
                    dados['bairro'] = bairro
                    break
            
            # Características
            q_match = re.search(r'(\d+)\s*quartos?', texto_pagina, re.I)
            if q_match:
                dados['quartos'] = int(q_match.group(1))
                print(f"   Quartos: {dados['quartos']}")
            
            s_match = re.search(r'(\d+)\s*suítes?', texto_pagina, re.I)
            if s_match:
                dados['suites'] = int(s_match.group(1))
            
            b_match = re.search(r'(\d+)\s*banheiros?', texto_pagina, re.I)
            if b_match:
                dados['banheiros'] = int(b_match.group(1))
                print(f"   Banheiros: {dados['banheiros']}")
            
            v_match = re.search(r'(\d+)\s*vagas?', texto_pagina, re.I)
            if v_match:
                dados['vagas'] = int(v_match.group(1))
                print(f"   Vagas: {dados['vagas']}")
            
            a_match = re.search(r'(\d+[.,]?\d*)\s*m[²2]', texto_pagina, re.I)
            if a_match:
                dados['area_util'] = float(a_match.group(1).replace(',', '.'))
                print(f"   Área: {dados['area_util']}m²")
            
            c_match = re.search(r'Condom[íi]nio[:\s]*R?\$?\s*([\d.,]+)', texto_pagina, re.I)
            if c_match:
                dados['condominio'] = c_match.group(1).replace('.', '').replace(',', '.')
                print(f"   Condomínio: R$ {dados['condominio']}")
            
            i_match = re.search(r'IPTU[:\s]*R?\$?\s*([\d.,]+)', texto_pagina, re.I)
            if i_match:
                dados['iptu'] = i_match.group(1).replace('.', '').replace(',', '.')
                print(f"   IPTU: R$ {dados['iptu']}")
            
            andar_match = re.search(r'(\d+)[º°]?\s*andar', texto_pagina, re.I)
            if andar_match:
                dados['andar'] = andar_match.group(1)
            
            # Tipo
            if 'Sala comercial' in texto_pagina:
                dados['tipo'] = 'Comercial'
                dados['subtipo'] = 'Sala Comercial'
            elif 'Cobertura' in texto_pagina:
                dados['tipo'] = 'Cobertura'
                dados['subtipo'] = 'Cobertura'
            
            # Características extras
            dados['caracteristicas_extras'] = self.extrair_caracteristicas_extras(texto_pagina)
            
            # Descrição
            descricao_partes = [dados['titulo']]
            
            if dados['caracteristicas_extras']:
                descricao_partes.append("\nCARACTERÍSTICAS DO IMÓVEL:")
                descricao_partes.extend([f"• {item}" for item in dados['caracteristicas_extras']])
            
            dados['descricao'] = '\n'.join(descricao_partes)
            
            # Fotos
            print("\n📸 Extraindo fotos...")
            
            primeira_foto = None
            imagens = self.driver.find_elements(By.CSS_SELECTOR, 'img[src*="imoveis/"], img[src*="imn/"]')
            
            for img in imagens:
                try:
                    src = img.get_attribute('src')
                    if src and id_anuncio in src and 'logo' not in src.lower():
                        primeira_foto = src
                        break
                except:
                    continue
            
            if primeira_foto:
                dados['fotos'] = self.extrair_fotos_por_padrao(primeira_foto)
                print(f"   📸 Total: {len(dados['fotos'])} fotos")
            
        except Exception as e:
            print(f"❌ Erro no anúncio {id_anuncio}: {e}")
        
        return dados
    
    def processar_todos_anuncios(self):
        """Processa todos os anúncios da lista"""
        print("\n🔍 Procurando anúncios...")
        time.sleep(3)
        
        print("📋 Coletando URLs dos anúncios...")
        urls_anuncios = []
        links = self.driver.find_elements(By.CSS_SELECTOR, 'h2.anuncio-titulo a')
        
        for link in links:
            try:
                url = link.get_attribute('href')
                if url and url not in urls_anuncios:
                    urls_anuncios.append(url)
                    id_match = re.search(r'/(\d+)/', url)
                    if id_match:
                        print(f"   URL encontrada: ID {id_match.group(1)}")
            except:
                continue
        
        print(f"📊 Total de {len(urls_anuncios)} URLs coletadas")
        
        # Limitar para evitar timeout no Render
        max_anuncios = min(len(urls_anuncios), 5)
        
        for i, url in enumerate(urls_anuncios[:max_anuncios]):
            print(f"\n{'='*60}")
            print(f"⏳ Processando anúncio {i+1}/{max_anuncios}")
            
            try:
                self.driver.get(url)
                print(f"   ✅ Abriu URL")
                time.sleep(5)
                
                id_match = re.search(r'/(\d+)/', url)
                id_anuncio = id_match.group(1) if id_match else str(i+1)
                
                dados = self.extrair_dados_completos(id_anuncio)
                
                self.imoveis.append(dados)
                print(f"   ✅ Anúncio ADICIONADO! Total na lista: {len(self.imoveis)}")
                
                self.driver.get("https://www.chavesnamao.com.br/minhaconta/meusanuncios/")
                print("   ↩️ Voltando para lista")
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Erro no anúncio {i+1}: {e}")
                try:
                    self.driver.get("https://www.chavesnamao.com.br/minhaconta/meusanuncios/")
                except:
                    pass
                time.sleep(3)
    
    def gerar_xml(self):
        """Gera XML Viva Real"""
        print("\n📄 Gerando XML...")
        
        if len(self.imoveis) == 0:
            print("❌ Nenhum anúncio para gerar XML!")
            return None
        
        now = datetime.now()
        publish_date = now.strftime("%Y-%m-%dT%H:%M:%S")
        list_date = now.strftime("%Y-%m-%d-%H:%M")
        
        root = ET.Element("ListingDataFeed")
        root.set("xmlns", "http://www.vivareal.com/schemas/1.0/VRSync")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "PublishDate").text = publish_date
        ET.SubElement(header, "Provider").text = self.email.split('@')[0].upper() + " NEGÓCIOS IMOBILIÁRIOS"
        ET.SubElement(header, "Email").text = self.email
        
        listings = ET.SubElement(root, "Listings")
        total_fotos = 0
        
        for idx, imovel in enumerate(self.imoveis):
            print(f"   📝 Adicionando anúncio {idx+1}")
            
            listing = ET.SubElement(listings, "Listing")
            
            ET.SubElement(listing, "ListingID").text = str(imovel.get('codigo', ''))
            ET.SubElement(listing, "ListDate").text = list_date
            ET.SubElement(listing, "LastUpdateDate").text = list_date
            
            if imovel.get('preco_venda'):
                ET.SubElement(listing, "TransactionType").text = "For Sale"
            else:
                ET.SubElement(listing, "TransactionType").text = "For Sale"
            
            ET.SubElement(listing, "Title").text = imovel.get('titulo', f"Imóvel {imovel.get('codigo', '')}")
            ET.SubElement(listing, "Featured").text = "false"
            ET.SubElement(listing, "PublicationType").text = "STANDARD"
            
            # Location
            location = ET.SubElement(listing, "Location")
            location.set("displayAddress", "Full")
            
            country = ET.SubElement(location, "Country")
            country.set("abbreviation", "BR")
            country.text = "Brasil"
            
            state = ET.SubElement(location, "State")
            state.set("abbreviation", "PR")
            state.text = "Paraná"
            
            city = ET.SubElement(location, "City")
            city.text = imovel.get('cidade', 'Curitiba')
            
            if imovel.get('bairro'):
                neighborhood = ET.SubElement(location, "Neighborhood")
                neighborhood.text = imovel['bairro']
            
            if imovel.get('logradouro'):
                ET.SubElement(location, "Address").text = imovel['logradouro']
            
            if imovel.get('numero'):
                ET.SubElement(location, "StreetNumber").text = imovel['numero']
            
            if imovel.get('cep'):
                postal = ET.SubElement(location, "PostalCode")
                postal.text = imovel['cep']
            
            # Details
            details = ET.SubElement(listing, "Details")
            
            description = ET.SubElement(details, "Description")
            description.text = imovel.get('descricao', imovel.get('titulo', ''))
            
            if imovel.get('preco_venda'):
                ET.SubElement(details, "SalePrice", currency="BRL").text = imovel['preco_venda']
            
            property_type = imovel.get('subtipo', imovel.get('tipo', 'Apartamento'))
            ET.SubElement(details, "PropertyType").text = property_type
            
            if imovel.get('area_util') and imovel['area_util'] > 0:
                ET.SubElement(details, "LivingArea", unit="square metres").text = str(imovel['area_util'])
            
            ET.SubElement(details, "Bedrooms").text = str(imovel.get('quartos', 0))
            ET.SubElement(details, "Bathrooms").text = str(imovel.get('banheiros', 0))
            ET.SubElement(details, "Suites").text = str(imovel.get('suites', 0))
            ET.SubElement(details, "ParkingSpaces").text = str(imovel.get('vagas', 0))
            
            if imovel.get('andar'):
                ET.SubElement(details, "Floor").text = imovel['andar']
            
            if imovel.get('iptu') and imovel['iptu'] != '0':
                ET.SubElement(details, "YearlyTax", currency="BRL").text = imovel['iptu']
            
            if imovel.get('condominio') and imovel['condominio'] != '0':
                ET.SubElement(details, "MonthlyFee", currency="BRL").text = imovel['condominio']
            
            ET.SubElement(details, "Features").text = " "
            
            # Media (fotos)
            if imovel.get('fotos') and len(imovel['fotos']) > 0:
                media = ET.SubElement(listing, "Media")
                for i, foto in enumerate(imovel['fotos'][:20]):
                    item = ET.SubElement(media, "Item", medium="image")
                    if i == 0:
                        item.set("primary", "true")
                    item.text = foto
                total_fotos += len(imovel['fotos'])
            
            # Contact Info
            contact = ET.SubElement(listing, "ContactInfo")
            
            contact_email = ET.SubElement(contact, "Email")
            contact_email.text = self.email
            
            contact_name = ET.SubElement(contact, "Name")
            contact_name.text = self.email.split('@')[0].upper() + " NEGÓCIOS IMOBILIÁRIOS"
            
            contact_phone = ET.SubElement(contact, "Telephone")
            contact_phone.text = "(41) 3092-1001"
            
            # Status
            status = ET.SubElement(listing, "Status")
            ET.SubElement(status, "PropertyStatus").text = "Available"
            status_date = ET.SubElement(status, "StatusDate")
            status_date.text = now.strftime('%d/%m/%Y')
        
        xml_str = ET.tostring(root, encoding="unicode")
        xml_pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
        xml_pretty = '\n'.join([line for line in xml_pretty.split('\n') if line.strip()])
        
        print(f"\n{'='*60}")
        print(f"✅ XML gerado com SUCESSO!")
        print(f"📊 Total de anúncios: {len(self.imoveis)}")
        print(f"📸 Total de fotos: {total_fotos}")
        print(f"{'='*60}")
        
        return xml_pretty
    
    def run(self):
        """Executa todo o processo"""
        try:
            self.setup_driver()
            self.login()
            self.ir_para_meus_anuncios()
            self.processar_todos_anuncios()
            xml_content = self.gerar_xml()
            
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
            print("\n🔚 Finalizando...")
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
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/scraper', methods=['POST'])
def scraper():
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'JSON inválido'}), 400
        
        email = data.get('email')
        senha = data.get('senha')
        
        if not email or not senha:
            return jsonify({'error': 'Email e senha obrigatórios'}), 400
        
        print(f"\n{'='*60}")
        print(f"🚀 Iniciando crawler para: {email}")
        print(f"{'='*60}")
        
        scraper = ChavesScraper(email, senha)
        resultado = scraper.run()
        
        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 500
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

# ==============================================
# PONTO DE ENTRADA
# ==============================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
