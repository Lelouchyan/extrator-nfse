import re


# Letras/números que o Tesseract costuma trocar entre si.
_CONFUSOES = {
    "O": "O0",
    "0": "O0",
    "I": "IL1",
    "L": "IL1",
    "1": "IL1",
    "S": "S5",
    "5": "S5",
    "B": "B8",
    "8": "B8",
    "C": "CG",
    "G": "CG",
}


def tolerante(literal):
    """
    Recebe um texto literal (ex.: "TRIBUTACAO MUNICIPAL") e devolve um
    trecho de regex que aceita as trocas de letra mais comuns do OCR
    (C por G, O por 0, I por 1/L, S por 5, B por 8) e tolera
    espaçamento diferente entre as palavras -- inclusive a ausência
    total de espaço, porque o OCR às vezes gruda as palavras
    (ex.: "EMITENTEDANFSE" em vez de "EMITENTE DA NFS-E").

    Isso é usado tanto para achar títulos de seção quanto rótulos de
    campo dentro do texto já normalizado (maiúsculo, sem acento).
    """

    partes = []

    for ch in literal:

        if ch == " ":
            partes.append(r"\s*")

        elif ch == "-":
            # O OCR frequentemente perde o hífen (ex.: "NFS-E" vira
            # "NFSE") ou o troca por um traço diferente.
            partes.append(r"[\s\-]*")

        elif ch.upper() in _CONFUSOES:
            classe = _CONFUSOES[ch.upper()]
            partes.append("[" + classe + "]")

        else:
            partes.append(re.escape(ch))

    return "".join(partes)
