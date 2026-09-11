import fitz

from ocr import fazer_ocr


def ler_pagina(pagina):

    texto = pagina.get_text()

    if len(texto.strip()) > 300:
        return texto

    texto = fazer_ocr(pagina)

    return texto