from typing import Optional
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
# Asume que tienes un ProductBase y la función has_real_discount
from core.mongo.Schemas import ProductBase
from core.scrapping.alkosto.Scrapping import has_real_discount


class FalabellaScraper:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

    def clean_price(self, price_str):
        """Convierte precios de texto a números (adaptado para Falabella)"""
        if not price_str:
            return 0
        try:
            # Reemplaza caracteres comunes en Falabella: '$', '.', ' ', ',', 'CLP', 'ARS', etc.
            clean_str = price_str.replace('$', '').replace('.', '').replace(',', '').replace('CLP', '').strip()
            return float(clean_str)
        except:
            return 0

    def extract_category_from_url(self, url):
        """Extrae categoría de la URL para Falabella (ejemplo)"""
        if not url:
            return "Sin categoría"
        try:
            # Mapeo de paths a categorías de Falabella (Ejemplos)
            category_map = {
                'tecnologia/celulares': 'Smartphones',
                'tecnologia/computacion': 'Computadores',
                'electrohogar/televisores': 'Televisores',
                'videojuegos-consolas': 'Videojuegos',
            }
            for path, category in category_map.items():
                if path in url:
                    return category
            
            # Intento de inferencia más simple
            parts = url.split('/')
            if len(parts) > 4:
                return parts[3].replace('-', ' ').title() # Usa el segmento de la URL como categoría
            
            return "Electrónicos"
        except:
            return "Sin categoría"

    def get_content_selenium(self, url, clicks=3):
        """Obtiene contenido HTML de la URL de Falabella con Selenium"""
        driver = webdriver.Chrome(options=self.options)

        try:
            print(f"🌐 Accediendo a: {url}")
            driver.get(url)

            # --- SELECTOR CLAVE PARA FALABELLA: Elemento de producto ---
            # **NOTA:** Este selector (div[id^="testId-PodCard-"]) es un EJEMPLO,
            # DEBES encontrar el selector real.
            PRODUCT_CONTAINER_SELECTOR = "div[id^='testId-PodCard-']" 
            LOAD_MORE_BUTTON_SELECTOR = 'button[data-testid="load-more-btn"]'

            # Esperar carga inicial del primer producto
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, PRODUCT_CONTAINER_SELECTOR))
                )
            except TimeoutException:
                print("Timeout: No se encontraron productos o el selector inicial es incorrecto.")
                return None, "No se encontraron productos"

            # Lógica de "Mostrar Más"
            click_count = 0
            while True:
                if clicks is not None and click_count >= clicks:
                    break

                try:
                    boton = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, LOAD_MORE_BUTTON_SELECTOR))
                    )
                    driver.execute_script("arguments[0].click();", boton)
                    click_count += 1
                    print(f"📋 Click #{click_count} en 'Mostrar más'")
                    time.sleep(2)
                except Exception:
                    print(f"✅ Fin de los productos o botón no encontrado después de {click_count} clicks.")
                    break

            return driver.page_source, None

        except Exception as e:
            error_msg = f"❌ Error durante el scraping de Falabella: {str(e)}"
            print(error_msg)
            return None, error_msg
        finally:
            driver.quit()

    def scrape_products(self, url, category=None, clicks = None):
        """Scrapea productos de una URL de Falabella"""
        html_content, error = self.get_content_selenium(url,clicks=clicks)

        if error:
            return [], error

        product_info_list = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # --- SELECTOR PRINCIPAL DE LA TARJETA DE PRODUCTO ---
        # **NOTA:** DEBES ajustar este selector.
        product_items = soup.find_all('div', attrs={'id': lambda x: x and x.startswith('testId-PodCard-')})

        print(f"📊 Encontrados {len(product_items)} productos para scrapear")

        for item in product_items:
            try:
                product_data = self.extract_product_data(item, url, category)
                if product_data:
                    product_info_list.append(product_data)
            except Exception as e:
                # print(f"⚠️ Error extrayendo producto: {e}")
                continue

        return product_info_list, None

    def extract_product_data(self, item, source_url, forced_category=None) -> Optional[ProductBase]:
        """Extrae datos de un producto individual de Falabella"""
        # --- SELECTORES DE EJEMPLO PARA FALABELLA (DEBES VERIFICAR) ---
        
        # Nombre y Link
        name_tag = item.find('a', {'data-testid': 'product-pod-display-name'})
        name = name_tag.get_text(strip=True) if name_tag else "Sin nombre"
        product_url = f"https://www.falabella.com{name_tag['href']}" if name_tag and name_tag.get('href') else None

        # Precio con Descuento (Precio actual)
        # Buscar el precio más prominente (puede tener una clase como 'current-price')
        discount_price_tag = item.find('span', {'data-testid': 'current-price'}) 
        discount_price_text = discount_price_tag.get_text(strip=True) if discount_price_tag else "0"

        # Precio Original (Tachado)
        # Buscar el precio tachado (puede tener una clase como 'original-price')
        old_price_tag = item.find('span', {'data-testid': 'original-price'})
        old_price_text = old_price_tag.get_text(strip=True) if old_price_tag else "Sin descuento"
        
        # Descuento en Porcentaje (Generalmente un label)
        discount_percent_tag = item.find('div', class_='discount-percentage') # Ajustar selector
        discount_percent = discount_percent_tag.get_text(strip=True) if discount_percent_tag else "0%"

        # Limpiar precios para valores numéricos
        original_price_num = self.clean_price(old_price_text)
        discount_price_num = self.clean_price(discount_price_text)

        # 🔍 FILTRAR PRODUCTOS SIN DESCUENTO REAL (Usa la función de Alkosto)
        if not has_real_discount(discount_percent, original_price_num, discount_price_num):
            # print(f"⏭️  Saltando producto sin descuento: {name[:50]}...")
            return None

        # Marca (A menudo está en el título o en un tag específico)
        brand_tag = item.find('p', class_='brand-name') # Ajustar selector
        brand = brand_tag.get_text(strip=True) if brand_tag else "Sin marca"

        # Imagen
        image_tag = item.find('img', class_='pod-image') # Ajustar selector
        image_url = image_tag['src'] if image_tag and image_tag.get('src') else ""

        # Rating (Si Falabella lo tiene, buscar el selector)
        rating_tag = item.find('span', class_='f-rating-score') # Ajustar selector
        rating = rating_tag.get_text(strip=True) if rating_tag else "Sin calificación"

        # Categoría
        category = forced_category if forced_category else self.extract_category_from_url(product_url or source_url)

        # Crear y retornar objeto ProductBase (omitimos 'specifications' y asumimos disponibilidad)
        return ProductBase(
            name=name,
            brand=brand,
            category=category,
            product_url=product_url,
            source_url=source_url,
            discount_percent=discount_percent,
            rating=rating,
            original_price=old_price_text,
            original_price_num=original_price_num,
            discount_price=discount_price_text,
            discount_price_num=discount_price_num,
            image_url=image_url,
            specifications={}, # Dejar vacío o implementar lógica
            availability="Disponible",
            in_stock=True,
            source='falabella'
        )

# --- CLASE CRAWLER (Adaptación de AlkostoCrawler) ---

class FalabellaCrawler:
    def __init__(self, clicks = None):
        self.scraper = FalabellaScraper()
        # self.mongo_manager = MongoManager() # Asume que tienes un MongoManager
        self.clicks = clicks
        self.category_urls = {
            # URLs de EJEMPLO de categorías de Falabella, DEBES verificar las rutas
            'smartphones': 'https://www.falabella.com.co/categoria/tecnologia/celulares',
            'portatiles': 'https://www.falabella.com.co/categoria/tecnologia/computacion/laptops',
            'televisores': 'https://www.falabella.com.co/categoria/electrohogar/televisores',
            'videojuegos': 'https://www.falabella.com.co/categoria/videojuegos-consolas',
            # Añade más categorías de Falabella según necesidad
        }

    def crawl_category(self, category_name, url):
        """Crawlea una categoría específica"""
        print(f"\n🚀 Iniciando crawling de Falabella: {category_name}")
        print(f"📁 URL: {url}")
        print(f"🔢 Modo: {'TODOS los productos' if self.clicks is None else f'{self.clicks} clicks'}")

        products, error = self.scraper.scrape_products(url, category_name, clicks=self.clicks)

        if error:
            print(f"❌ Error en {category_name}: {error}")
            return []

        print(f"✅ {len(products)} productos con descuento encontrados en {category_name}")

        # # Descomenta para guardar en MongoDB
        # if products:
        #     saved_count = self.mongo_manager.save_products(products, category_name)
        #     print(f"💾 {saved_count} productos guardados en MongoDB")

        return products

    def crawl_all_categories(self):
        """Crawlea todas las categorías de Falabella"""
        all_products = []
        for category_name, url in self.category_urls.items():
            products = self.crawl_category(category_name, url)
            all_products.extend(products)
            time.sleep(2)  # Pausa entre categorías

        print(f"\n🎉 Crawling Falabella completado! Total: {len(all_products)} productos con descuento")
        return all_products

# Ejemplo de uso:
# crawler = FalabellaCrawler(clicks=1) # Limitar a 1 click para pruebas rápidas
# results = crawler.crawl_all_categories()
# print(results)