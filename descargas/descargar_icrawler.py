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
    carpeta_destino = f"C:/Proyecto_IA_Vivero/dataset/raw/{clase}"
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

# ─── Ejecución ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    descargar("sano",     busquedas_sano,     OBJETIVO_POR_CLASE, DESCARGA_POR_BUSQUEDA)
    descargar("atencion", busquedas_atencion, OBJETIVO_POR_CLASE, DESCARGA_POR_BUSQUEDA)
    descargar("peligro",  busquedas_peligro,  OBJETIVO_POR_CLASE, DESCARGA_POR_BUSQUEDA)

    print("\n✅ Descarga con iCrawler finalizada.")
