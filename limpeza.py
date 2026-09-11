import re


def limpar_texto(texto):

    # Padroniza quebras de linha
    texto = texto.replace("\r", "\n")

    # Remove espaços repetidos
    texto = re.sub(r"[ \t]+", " ", texto)

    # Remove muitas linhas em branco
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()