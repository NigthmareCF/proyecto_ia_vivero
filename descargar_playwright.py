"""
descargar_playwright.py  (CORREGIDO)
======================================
Cambios respecto al original:
  - Corregida extracción de URLs: el evaluate_all anterior solo recogía
    miniaturas base64 o src vacíos de Google Images 2025/2026
  - Nueva estrategia triple: atributos del DOM + regex sobre page_source
    + interceptación de respuestas de red (la más efectiva)
  - Agregado stealth básico para evitar detección de bot
  - Agregado manejo de 'Mostrar más resultados'
  - Agregado pausa entre búsquedas para evitar rate-limit
"""

import os
import re
import time
import requests
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright, Page

BASE_DIR             = "dataset/raw"
MAX_POR_BUSQUEDA     = 300
MAX_SCROLLES_SIN_CAMBIO = 8
PAUSA_SCROLL         = 1.5


# ─── Términos de búsqueda ────────────────────────────────────────────────────

# busquedas_sano = [
#     "healthy bell pepper plant real photo",
#     "healthy capsicum annuum plant real photo",
#     "healthy sweet pepper leaves real photo",
#     "healthy bell pepper greenhouse real photo",
#     "healthy capsicum annuum leaves close up",
#     "healthy sweet pepper plant field",
#     "healthy bell pepper foliage crop",
#     "planta de pimiento sana foto real",
#     "chile pimiento sano hojas verdes foto",
#     "pimiento morron sano invernadero foto",
#     "capsicum annuum planta sana foto",
#     "hojas verdes sanas pimiento foto real",
#     "planta de pimentao saudavel foto",
#     "folhas saudaveis pimentao foto",
#     "capsicum annuum nathalie healthy plant",
#     "nathalie bell pepper healthy",
# ]

busquedas_atencion = [
    "bell pepper yellow leaves real photo",
    "capsicum nutrient deficiency real photo",
    "pepper leaf chlorosis real photo",
    "sweet pepper leaf stress real photo",
    "bell pepper wilting leaves photo",
    "pepper iron deficiency yellow leaves",
    "capsicum magnesium deficiency plant",
    "pimiento hojas amarillas foto real",
    "clorosis en pimiento foto real",
    "deficiencia nutricional pimiento foto",
    "hojas enrolladas pimiento foto real",
    "estres hidrico pimiento foto real",
    "pimentao folhas amarelas foto",
    "clorose em pimentao foto real",
    "nathalie pepper yellow leaves",
    "pimiento nathalie clorosis foto",
]

# busquedas_peligro = [
#     "bell pepper leaf disease real photo",
#     "capsicum bacterial spot real photo",
#     "pepper powdery mildew real photo",
#     "bell pepper aphids infestation photo",
#     "pepper whitefly damage real photo",
#     "capsicum fungal leaf disease photo",
#     "pepper leaf blight real photo",
#     "pepper thrips damage leaves photo",
#     "bell pepper mosaic virus photo",
#     "enfermedad hoja pimiento foto real",
#     "plaga en pimiento foto real",
#     "mancha bacteriana pimiento foto real",
#     "afidos en pimiento foto real",
#     "mosca blanca pimiento foto real",
#     "hongo en pimiento foto real",
#     "tizon en pimiento foto real",
#     "doenca folha pimentao foto real",
#     "praga em pimentao foto real",
#     "nathalie pepper disease photo",
# ]


# ─── Utilidades ──────────────────────────────────────────────────────────────

def asegurar_carpeta(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def contar_imagenes(carpeta: str) -> int:
    if not os.path.exists(carpeta):
        return 0
    return len([
        f for f in os.listdir(carpeta)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ])


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


def extraer_urls_de_pagina(page: Page) -> set:
    """
    Estrategia corregida triple para Google Images 2025/2026.
    """
    urls = set()

    # ── Estrategia 1: atributos correctos del DOM ──
    try:
        resultados = page.evaluate("""
            () => {
                const urls = new Set();

                // Imágenes normales con src http
                document.querySelectorAll('img[src]').forEach(img => {
                    const src = img.getAttribute('src') || '';
                    if (src.startsWith('http')) urls.add(src);
                });

                // Atributo data-iurl (Google reciente)
                document.querySelectorAll('[data-iurl]').forEach(el => {
                    const url = el.getAttribute('data-iurl') || '';
                    if (url.startsWith('http')) urls.add(url);
                });

                // Atributo data-ou (URL original en algunos layouts)
                document.querySelectorAll('[data-ou]').forEach(el => {
                    const url = el.getAttribute('data-ou') || '';
                    if (url.startsWith('http')) urls.add(url);
                });

                return Array.from(urls);
            }
        """)
        urls.update(resultados)
    except Exception:
        pass

    # ── Estrategia 2: regex sobre el HTML completo ──
    try:
        html = page.content()
        patron = r'https?://[^\s"\'\\<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\'\\<>]*)?'
        encontradas = re.findall(patron, html, re.IGNORECASE)
        for url in encontradas:
            if not any(x in url for x in [
                "gstatic.com/images/icons",
                "google.com/images/nav",
                "favicon", "1x1", "pixel", "logo",
            ]):
                urls.add(url)
    except Exception:
        pass

    return urls


def urls_google(page: Page, query: str, max_imgs: int) -> list:
    """
    Navega Google Images, hace scroll y recolecta URLs.
    Intercepta también respuestas de red para capturar imágenes reales.
    """
    urls_interceptadas = set()

    # ── Interceptar respuestas de imágenes reales de la red ──
    def on_response(response):
        try:
            ct = response.headers.get("content-type", "")
            url = response.url
            if "image" in ct and url.startswith("http"):
                if not any(x in url for x in ["gstatic.com/images/icons", "1x1", "pixel"]):
                    urls_interceptadas.add(url)
        except Exception:
            pass

    page.on("response", on_response)

    search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch&hl=es"
    page.goto(search_url, wait_until="networkidle", timeout=30000)
    time.sleep(2)

    urls        = set()
    ultimo_total = -1
    sin_cambio   = 0
    scroll_num   = 0

    while True:
        scroll_num += 1
        page.mouse.wheel(0, 2500)
        time.sleep(PAUSA_SCROLL)

        nuevas = extraer_urls_de_pagina(page)
        urls.update(nuevas)
        urls.update(urls_interceptadas)

        total_actual = len(urls)
        print(f"  Scroll {scroll_num:02d} — imágenes encontradas: {total_actual}")

        if total_actual == ultimo_total:
            sin_cambio += 1
        else:
            sin_cambio = 0

        ultimo_total = total_actual

        if total_actual >= max_imgs:
            break

        if sin_cambio >= MAX_SCROLLES_SIN_CAMBIO:
            print("  No se encontraron más imágenes nuevas.")
            break

        # Intentar "Ver más resultados"
        try:
            btn = page.locator("text=Ver más resultados").first
            if btn.is_visible():
                btn.click()
                time.sleep(2)
        except Exception:
            pass

    # Quitar interceptor
    page.remove_listener("response", on_response)

    return list(urls)[:max_imgs]


def descargar_busqueda(page: Page, clase: str, query: str) -> None:
    carpeta = os.path.join(BASE_DIR, clase)
    asegurar_carpeta(carpeta)

    print(f"\n[{clase}] Buscando: {query}")

    urls = urls_google(page, query, MAX_POR_BUSQUEDA)
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


def descargar_clase(page: Page, clase: str, busquedas: list) -> None:
    for query in busquedas:
        descargar_busqueda(page, clase, query)
        time.sleep(1.5)  # pausa entre búsquedas


def main():
    print("Iniciando Playwright...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )

        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            locale="es-GT",
        )

        # Stealth básico: ocultar que es un bot
        context.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

        page = context.new_page()

        try:
            #descargar_clase(page, "sano",     busquedas_sano)
            descargar_clase(page, "atencion", busquedas_atencion)
            #descargar_clase(page, "peligro",  busquedas_peligro)
        finally:
            browser.close()

    print("\n✅ Descarga con Playwright finalizada.")
    for clase in ["sano", "atencion", "peligro"]:
        print(f"  {clase}: {contar_imagenes(f'dataset/raw/{clase}')} imágenes")


if __name__ == "__main__":
    main()
