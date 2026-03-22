"""
descargar_icrawler.py  (CORREGIDO)
===================================
Cambios respecto al original:
  - Eliminado BingImageCrawler (bloqueado desde 2025)
  - Reemplazado por GoogleImageCrawler que sigue funcionando
  - Agregado feeder_threads y parser_threads para más velocidad
  - Agregado tiempo de espera entre búsquedas para evitar rate-limit
"""

import os
import time
from icrawler.builtin import GoogleImageCrawler

OBJETIVO_POR_CLASE   = 10_000
DESCARGA_POR_BUSQUEDA = 1_000   # Google limita ~1000 por búsqueda


def contar_imagenes(carpeta: str) -> int:
    if not os.path.exists(carpeta):
        return 0
    return len([
        f for f in os.listdir(carpeta)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp"))
    ])


def descargar(clase: str, busquedas: list, objetivo: int, cantidad_por_busqueda: int):
    carpeta_destino = f"dataset/raw/{clase}"
    os.makedirs(carpeta_destino, exist_ok=True)

    for busqueda in busquedas:
        total_actual = contar_imagenes(carpeta_destino)

        if total_actual >= objetivo:
            print(f"\n[{clase}] ✅ Objetivo alcanzado: {total_actual} imágenes.")
            break

        faltantes = objetivo - total_actual
        cantidad_descarga = min(cantidad_por_busqueda, faltantes)

        print(f"\n[{clase}] Buscando: {busqueda}")
        print(f"  Actual: {total_actual} | Faltan: {faltantes} | Intentando: {cantidad_descarga}")

        try:
            crawler = GoogleImageCrawler(
                feeder_threads=2,
                parser_threads=2,
                downloader_threads=6,
                storage={"root_dir": carpeta_destino}
            )
            crawler.crawl(
                keyword=busqueda,
                max_num=cantidad_descarga,
                file_idx_offset="auto",   # evita sobrescribir archivos existentes
            )
        except Exception as e:
            print(f"  [ERROR] {e}")

        nuevo_total = contar_imagenes(carpeta_destino)
        print(f"  [+] Nuevas en esta búsqueda: {nuevo_total - total_actual} | Total: {nuevo_total}")

        # Pausa para no disparar el rate-limit de Google
        time.sleep(2)

    final = contar_imagenes(carpeta_destino)
    print(f"\n[{clase}] Descarga finalizada: {final} imágenes.\n")


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

# ─── Ejecución ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    #descargar("sano",     busquedas_sano,     OBJETIVO_POR_CLASE, DESCARGA_POR_BUSQUEDA)
    descargar("atencion", busquedas_atencion, OBJETIVO_POR_CLASE, DESCARGA_POR_BUSQUEDA)
    #descargar("peligro",  busquedas_peligro,  OBJETIVO_POR_CLASE, DESCARGA_POR_BUSQUEDA)

    print("\n✅ Descarga con iCrawler finalizada.")
