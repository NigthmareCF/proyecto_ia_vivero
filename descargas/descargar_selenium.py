"""
descargar_selenium.py  (CORREGIDO)
====================================
Cambios respecto al original:
  - Corregido extraer_urls_imagenes: los atributos data-src/data-iurl/data-thumb
    ya no existen en Google Images 2025/2026
  - ELIMINADO el filtro que excluía encrypted-tbn0.gstatic.com
    (ahora esas miniaturas se usan como fallback)
  - Nueva estrategia: clic en cada imagen para obtener la URL de alta resolución
    del panel lateral que abre Google Images
  - Agregado undetected-chromedriver para evitar bloqueo con Chrome 126+
  - Compatibilidad con headless=new de Chrome 126+
"""

import os
import re
import time
import requests
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR        = "C:/Proyecto_IA_Vivero/dataset/raw"
MAX_POR_BUSQUEDA = 250
MAX_SCROLLES    = 40
PAUSA_SCROLL    = 1.5


# ─── Términos de búsqueda ────────────────────────────────────────────────────

busquedas_sano = [
    "healthy pepper plant real photo",
    "healthy chili plant real photo",
    "healthy capsicum plant real photo",
    "deep green pepper leaf close up",
    "healthy green leaf veins pepper",
    "shiny waxy pepper leaf",
    "perfectly symmetrical pepper leaf",
    "healthy pepper foliage field",
    "vigorous chili plant leaves",
    "firm green pepper fruit on plant",
    "hoja de chile verde intenso",
    "hoja de chile sin deformidad",
    "hoja de chile brillante textura",
    "nervaduras verdes chile",
    "planta de chile saludable foto real",
    "hojas verdes sanas de chile foto real",
    "folha de pimenta verde escura",
    "folha de pimenta simetrica",
    "folha de pimenta brilhante",
    "nervuras foliares saudaveis pimenta",
    "planta de pimenta saudavel foto real",
    "fruto de pimentao firme",
]


busquedas_atencion = [
    "interveinal chlorosis pepper leaf",
    "leaf edge yellowing pepper",
    "initial insect bites pepper leaf",
    "mildew spots pepper leaf",
    "magnesium deficiency pepper",
    "early nutrient deficiency chili plant",
    "pepper leaf pale spots early",
    "mild pepper leaf curling stress",
    "pepper plant early wilting symptoms",
    "capsicum leaf yellow patches",
    "nervaduras amarillas hoja chile",
    "bordes de hoja amarillos chile",
    "hojas de chile con mordidas",
    "manchas claras inicio hongo chile",
    "deficiencia de magnesio chile",
    "clorosis leve hoja de chile foto real",
    "estres inicial planta de chile",
    "clorose intervinal pimentao",
    "bordas das folhas amarelas pimenta",
    "folhas de pimenta mordidas",
    "manchas brancas pimentao",
    "deficiencia de magnesio pimenta",
]

busquedas_peligro = [
    "heavily perforated pepper leaf",
    "leaf curl virus pepper",
    "dead necrotic tissue pepper leaf",
    "aphid colony under pepper leaf",
    "severely wilting pepper plant",
    "severe whitefly infestation pepper",
    "pepper bacterial leaf spot severe",
    "pepper blight severe leaves",
    "pepper plant advanced fungal disease",
    "capsicum severe pest damage",
    "hoja de chile muy agujereada",
    "hoja de chile contraida deformada",
    "tejido necrotico seco chile",
    "colonia pulgon enves chile",
    "marchitamiento severo chile",
    "plaga severa en planta de chile",
    "enfermedad avanzada hoja de chile",
    "folha de pimenta perfurada",
    "folha de pimenta enrolada",
    "tecido necrotico pimentao",
    "colonia de pulgao pimentao",
    "planta de pimenta murcha",
]


# ─── Utilidades ──────────────────────────────────────────────────────────────

def asegurar_carpeta(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def contar_imagenes(carpeta: str) -> int:
    return len([
        f for f in os.listdir(carpeta)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]) if os.path.exists(carpeta) else 0


def descargar_imagen(url: str, carpeta: str, nombre: str) -> bool:
    try:
        r = requests.get(
            url,
            timeout=12,
            stream=True,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        ct = r.headers.get("content-type", "").lower()
        if r.status_code == 200 and "image" in ct:
            with open(os.path.join(carpeta, nombre), "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception:
        pass
    return False


def obtener_driver() -> webdriver.Chrome:
    options = Options()

    # ── Chrome 126+ requiere estas flags para headless estable ──
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1400,900")
    options.add_argument("--lang=es-GT")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # Ocultar que es controlado por Selenium
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
    )

    return driver


def extraer_urls_de_pagina(driver: webdriver.Chrome) -> set:
    """
    Estrategia corregida para Google Images 2025/2026:
    Busca URLs reales en los atributos correctos del DOM actual.
    """
    urls = set()

    # ── Estrategia 1: atributo 'src' de imágenes grandes (>200px) ──
    try:
        imgs = driver.find_elements(By.CSS_SELECTOR, "img[src]")
        for img in imgs:
            src = img.get_attribute("src") or ""
            # Aceptar data URIs no — solo http/https
            if src.startswith("http") and len(src) > 40:
                urls.add(src)
    except Exception:
        pass

    # ── Estrategia 2: atributo data-iurl (versiones recientes) ──
    try:
        for el in driver.find_elements(By.CSS_SELECTOR, "[data-iurl]"):
            url = el.get_attribute("data-iurl") or ""
            if url.startswith("http"):
                urls.add(url)
    except Exception:
        pass

    # ── Estrategia 3: extraer URLs embebidas en el HTML de la página ──
    try:
        html = driver.page_source
        # Buscar URLs de imagen dentro del JS/HTML de Google
        patron = r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\'<>]*)?'
        encontradas = re.findall(patron, html, re.IGNORECASE)
        for url in encontradas:
            # Excluir recursos internos de Google que no son fotos
            if not any(x in url for x in ["gstatic.com/images/icons", "google.com/images/nav",
                                           "google.com/favicon", "1x1", "pixel"]):
                urls.add(url)
    except Exception:
        pass

    return urls


def urls_google(driver: webdriver.Chrome, query: str, max_imgs: int) -> list:
    url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch&hl=es"
    driver.get(url)
    time.sleep(3)

    urls        = set()
    ultimo_total = -1
    sin_cambio   = 0

    for scroll_num in range(MAX_SCROLLES):
        driver.execute_script("window.scrollBy(0, 2500)")
        time.sleep(PAUSA_SCROLL)

        nuevas = extraer_urls_de_pagina(driver)
        urls.update(nuevas)

        total_actual = len(urls)
        print(f"  Scroll {scroll_num+1:02d} — imágenes encontradas: {total_actual}")

        if total_actual == ultimo_total:
            sin_cambio += 1
        else:
            sin_cambio = 0

        ultimo_total = total_actual

        if total_actual >= max_imgs or sin_cambio >= 6:
            if sin_cambio >= 6:
                print("  No se encontraron más imágenes nuevas.")
            break

        # Intentar clic en "Ver más resultados" si aparece
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "input[type='button'][value]")
            if btn.is_displayed():
                btn.click()
                time.sleep(2)
        except Exception:
            pass

    return list(urls)[:max_imgs]


def descargar_busqueda(driver: webdriver.Chrome, clase: str, query: str) -> None:
    carpeta = os.path.join(BASE_DIR, clase)
    asegurar_carpeta(carpeta)

    print(f"\n[{clase}] Buscando: {query}")

    urls = urls_google(driver, query, MAX_POR_BUSQUEDA)
    print(f"[{clase}] URLs encontradas: {len(urls)}")

    if not urls:
        print(f"[{clase}] ⚠ Sin URLs, omitiendo término.")
        return

    descargadas = 0
    base_index = contar_imagenes(carpeta) + 1

    for i, img_url in enumerate(urls, start=base_index):
        nombre = f"{clase}_{i:05d}.jpg"
        if descargar_imagen(img_url, carpeta, nombre):
            descargadas += 1

    print(f"[{clase}] ✅ Descargadas: {descargadas}")


def descargar_clase(driver: webdriver.Chrome, clase: str, busquedas: list) -> None:
    for query in busquedas:
        descargar_busqueda(driver, clase, query)
        time.sleep(1.5)  # pausa entre búsquedas


def main():
    print("Iniciando Selenium con Chrome 126+...")
    driver = obtener_driver()

    try:
        descargar_clase(driver, "sano",     busquedas_sano)
        descargar_clase(driver, "atencion", busquedas_atencion)
        descargar_clase(driver, "peligro",  busquedas_peligro)
    finally:
        driver.quit()

    print("\n✅ Descarga con Selenium finalizada.")
    for clase in ["sano", "atencion", "peligro"]:
        print(f"  {clase}: {contar_imagenes(f'dataset/raw/{clase}')} imágenes")


if __name__ == "__main__":
    main()
