import time


from core.mongo.MongoManager import MongoManager
from core.scrapping.falabella.Scrappy import FalabellaScraper


class FalabellaScraper: 
    def __init__(self): pass
    def scrape_products(self, url, category, clicks): 
        print(f"  [Simulación] Scrapeando {category}...")
        time.sleep(0.5)
        return [], None
class MongoManager:
    def __init__(self): pass
    def save_products(self, products, category_name): 
        return len(products)
# --------------------------------------------------------------------------


class FalabellaCrawler:
    def __init__(self, clicks = None):
        # Mismo léxico: AlkostoScraper se reemplaza por FalabellaScraper
        self.scraper = FalabellaScraper() 
        self.mongo_manager = MongoManager()
        self.clicks = clicks
        
        # Diccionario de URLs de Falabella (la única diferencia de datos con Alkosto)
        self.category_urls = {
            'smartphones': 'https://www.falabella.com.co/falabella-co/category/cat1022/celulares-y-smartphones',
            'portatiles': 'https://www.falabella.com.co/falabella-co/category/cat2016/portatiles',
            'computadores_escritorio': 'https://www.falabella.com.co/falabella-co/category/cat2018/computadores-de-escritorio-y-all-in-one',
            'tablets': 'https://www.falabella.com.co/falabella-co/category/cat1020/tablets-y-accesorios',
            'monitores': 'https://www.falabella.com.co/falabella-co/category/cat2023/monitores-y-pantallas',
            'televisores': 'https://www.falabella.com.co/falabella-co/category/cat7090036/televisores-y-cine-en-casa',
            'consolas': 'https://www.falabella.com.co/falabella-co/category/cat720238/consolas',
            'audifonos': 'https://www.falabella.com.co/falabella-co/category/cat1450005/audifonos',
            'accesorios_electronicos': 'https://www.falabella.com.co/falabella-co/category/cat2026/accesorios-computacion',
        }

    def crawl_category(self, category_name, url):
        """Crawlea una categoría específica para Falabella"""
        print(f"\n🚀 Iniciando crawling de: {category_name}")
        print(f"📁 URL: {url}")
        print(f"🔢 Modo: {'TODOS los productos' if self.clicks is None else f'{self.clicks} clicks'}")

        # La lógica es idéntica a la de Alkosto, solo cambia el scraper llamado
        products, error = self.scraper.scrape_products(url, category_name, clicks=self.clicks)

        if error:
            print(f"❌ Error en {category_name}: {error}")
            return []

        print(f"✅ {len(products)} productos con descuento encontrados en {category_name}")

        # Guardar en MongoDB
        if products:
            saved_count = self.mongo_manager.save_products(products, category_name)
            print(f"💾 {saved_count} productos guardados en MongoDB")

        return products

    def crawl_all_categories(self):
        """Crawlea todas las categorías de Falabella"""
        all_products = []

        for category_name, url in self.category_urls.items():
            products = self.crawl_category(category_name, url)
            all_products.extend(products)
            time.sleep(2)  # Mismo time.sleep(2) que el Alkosto original

        print(f"\n🎉 Crawling completado! Total: {len(all_products)} productos con descuento")
        return all_products

    def crawl_specific_categories(self, categories):
        """Crawlea categorías específicas de Falabella"""
        results = {}
        for category in categories:
            if category in self.category_urls:
                products = self.crawl_category(category, self.category_urls[category])
                results[category] = products
            else:
                print(f"⚠️ Categoría no encontrada: {category}")

        return results