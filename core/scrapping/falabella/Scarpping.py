from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

class ProductBase:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        return f"ProductBase(name='{self.name[:20]}...', brand='{self.brand}', discount_price_num={self.discount_price_num})"


def has_real_discount(discount_percent, original_price_num, discount_price_num):
    """
    Verifica si el producto tiene un descuento real y significativo
    """
   
    if not discount_percent or discount_percent == "0%" or "sin" in discount_percent.lower():
     
        pass


    if original_price_num == discount_price_num or original_price_num <= 0:
        return False
    
    
    if discount_price_num < original_price_num:
        
        if discount_price_num > original_price_num > 0:
            return False

        try:
            calculated_discount = (1 - (discount_price_num / original_price_num)) * 100
            if calculated_discount < 5:  
                return False
        except ZeroDivisionError:
            return False
            
        
        return True

    return False




class FalabellaScraper:
    def __init__(self):
       
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        self.base_url = "https://www.falabella.com.co"

    def clean_price(self, price_str):
        """Convierte precios de texto (e.g., '$ 1.299.900') a números"""
        if not price_str:
            return 0

        try:
            
            clean_str = price_str.replace('$', '').replace('.', '').replace(',', '').strip()
            
            return float(clean_str)
        except:
            return 0

    def extract_category_from_url(self, url):
        """Extrae categoría de la URL de Falabella"""
        if not url:
            return "Sin categoría"

        try:
           
            parts = url.split('/')
            
            
            for i in range(len(parts) - 1, -1, -1):
                part = parts[i]
                if part and 'cat' not in part:
                    
                    category_slug = part.split('?')[0].replace('-', ' ').strip()
                    if category_slug:
                        return category_slug.title()
            
            return "Electrónicos" 
        except:
            return "Sin categoría"

    def get_content_selenium(self, url, clicks=3):
        """Obtiene contenido HTML de la URL con Selenium y simula clicks"""
        driver = webdriver.Chrome(options=self.options)

        try:
            full_url = url if url.startswith('http') else f"{self.base_url}{url}"
            print(f"🌐 Accediendo a: {full_url}")
            driver.get(full_url)

           
            product_selector = "div.search-results-list"
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, product_selector))
                )
            except TimeoutException:
                print("Timeout: No se encontraron productos")
                return None, "No se encontraron productos"

            
            click_count = 0
            while True:
               
                if clicks is not None and click_count >= clicks:
                    break

                
                load_more_selector = "button.fb-btn.fb-btn-secondary.fb-btn-icon.fb-show-more"
                
                try:
                    boton = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, load_more_selector))
                    )
                    driver.execute_script("arguments[0].click();", boton)
                    click_count += 1
                    print(f"📋 Click #{click_count} en 'Mostrar más'")
                    time.sleep(3) 
                except Exception:
                    
                    print(f"✅ Fin de los productos ({click_count} clicks realizados)")
                    break

            return driver.page_source, None

        except Exception as e:
            error_msg = f"❌ Error durante el scraping: {str(e)}"
            print(error_msg)
            return None, error_msg
        finally:
            driver.quit()

    def scrape_products(self, url, category=None, clicks=None):
        """Scrapea productos de una URL específica y devuelve objetos ProductBase"""
        html_content, error = self.get_content_selenium(url, clicks=clicks)

        if error:
            return [], error

        product_info_list = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Selector para cada tarjeta de producto en Falabella
        product_items = soup.find_all('li', class_='search-results-list__item')

        print(f"📊 Encontrados {len(product_items)} productos para scrapear")

        for item in product_items:
            try:
                product_data = self.extract_product_data(item, url, category)
                if product_data:
                    product_info_list.append(product_data)
            except Exception as e:
                print(f"⚠️ Error extrayendo producto: {e}")
                continue

        return product_info_list, None

    def extract_product_data(self, item, source_url, forced_category=None) -> Optional[ProductBase]:
        """Extrae datos de un producto individual y devuelve ProductBase"""
    
        
      
        link_tag = item.find('a', class_='pod-link')
        if not link_tag or not link_tag.get('href'):
            return None

        product_url = link_tag['href']
        if not product_url.startswith('http'):
            product_url = f"{self.base_url}{product_url}"

        
        name_tag = item.find('b', class_='pod-subTitle')
        name = name_tag.get_text(strip=True) if name_tag else "Sin nombre"
        
       
        brand_tag = item.find('div', class_='pod-title')
        brand = brand_tag.get_text(strip=True) if brand_tag else "Sin marca"

        
        discount_price_tag = item.find('li', class_='price-list-item best-price')
        discount_price_text = discount_price_tag.find('span').get_text(strip=True) if discount_price_tag and discount_price_tag.find('span') else "0"
        
        old_price_tag = item.find('li', class_='price-list-item old-price')
        old_price_text = old_price_tag.find('span').get_text(strip=True) if old_price_tag and old_price_tag.find('span') else "Sin descuento"
        
       
        discount_percent_tag = item.find('span', class_='discount-badge')
        discount_percent = discount_percent_tag.get_text(strip=True) if discount_percent_tag else "0%"

        
        original_price_num = self.clean_price(old_price_text)
        discount_price_num = self.clean_price(discount_price_text)
        
      
        if not has_real_discount(discount_percent, original_price_num, discount_price_num):
           
            print(f"⏭️  Saltando producto sin descuento real o significativo: {name[:50]}...")
            return None

      
        image_tag = item.find('img', class_='pod-image')
        image_url = image_tag['src'] if image_tag and image_tag.get('src') else ""

       
        rating_tag = item.find('span', class_='falabella-rating-stars-2-average')
        rating = rating_tag.get_text(strip=True) if rating_tag else "Sin calificación"

        
        category = forced_category if forced_category else self.extract_category_from_url(product_url)
        
       
        buy_button = item.find('button', class_='fb-btn-primary')
        availability = "Disponible" if buy_button else "No disponible/Agotado"
        in_stock = "disponible" in availability.lower()
        
        
        specifications: Dict[str, Any] = {}


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
            specifications=specifications,
            availability=availability,
            in_stock=in_stock,
            source='falabella'
        )
