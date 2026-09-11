import re
import unicodedata


def normalizar(texto):

    # Remove caracteres invisíveis
    texto = texto.replace("\xa0", " ")

    # Remove espaços duplicados
    texto = re.sub(r"[ \t]+", " ", texto)

    # Remove linhas em branco repetidas
    texto = re.sub(r"\n+", "\n", texto)

    # Remove acentos
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode()

    return texto.upper().strip()