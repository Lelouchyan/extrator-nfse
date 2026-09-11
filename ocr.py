"""
Leitura por OCR das notas digitalizadas.

Usado quando o PDF nao tem camada de texto -- ou seja, quando a nota
e uma imagem e nao da para extrair o texto diretamente.
"""

import fitz
import pytesseract
from PIL import Image

from config import CAMINHO_TESSERACT, verificar_tesseract


# Aponta o pytesseract para o Tesseract encontrado pelo config.py.
# Quando nao encontra, deixamos seguir: quem chama o programa mostra
# a mensagem de ajuda antes de comecar a processar.
if CAMINHO_TESSERACT:
    pytesseract.pytesseract.tesseract_cmd = CAMINHO_TESSERACT


# Quanto maior, melhor o OCR le letras pequenas -- e mais lento fica.
ESCALA = 4


def fazer_ocr(pagina):
    """
    Converte a pagina do PDF em imagem e devolve o texto lido.
    """

    if not CAMINHO_TESSERACT:
        _, mensagem = verificar_tesseract()
        raise RuntimeError(mensagem)

    matriz = fitz.Matrix(ESCALA, ESCALA)

    pix = pagina.get_pixmap(matrix=matriz)

    imagem = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    texto = pytesseract.image_to_string(
        imagem,
        lang="por",
        config="--oem 3 --psm 6"
    )

    return texto
