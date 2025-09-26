# main.py (o donde ejecutes tu código)

import time
import json
# Importa la clase FalabellaCrawler que definimos
# Asegúrate de que las rutas de importación sean correctas en tu proyecto
from core.scrapping.falabella.Scrapping import FalabellaCrawler
# from core.mongo.MongoManager import MongoManager # Descomenta si usas MongoDB


def run_falabella_crawler(limit_clicks: int = 1):
    """
    Ejecuta el crawler de Falabella.

    Args:
        limit_clicks: Número de veces que el scraper hará clic en "Mostrar más".
                      Usa 'None' para intentar cargar todos los productos.
                      Se recomienda usar 1 o 2 para pruebas rápidas.
    """
    start_time = time.time()
    
    # 1. Instanciar el crawler de Falabella
    # Si limit_clicks es None, intentará cargar todos los productos
    crawler = FalabellaCrawler(clicks=limit_clicks) 
    
    # 2. Iniciar el crawling en todas las categorías definidas
    all_products = crawler.crawl_all_categories()
    
    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "="*50)
    print("         ✨ RESUMEN DE CRAWLING FALABELLA ✨")
    print(f"| Total de productos con descuento encontrados: {len(all_products)}")
    print(f"| Duración total: {duration:.2f} segundos")
    print("="*50)
    
    # Opcional: Guardar los resultados en un archivo JSON para inspección
    if all_products:
        with open('falabella_descuentos.json', 'w', encoding='utf-8') as f:
            # Convertir objetos ProductBase a diccionarios serializables
            serializable_products = [p.dict() for p in all_products]
            json.dump(serializable_products, f, ensure_ascii=False, indent=4)
        print("💾 Resultados guardados en 'falabella_descuentos.json'")

if __name__ == "__main__":
    # Cambia '1' por 'None' para intentar cargar todos los productos (será más lento)
    run_falabella_crawler(limit_clicks=1)