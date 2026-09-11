import re

from ocr_utils import tolerante


# Modelo nacional / Goiânia
MARCADORES = [
    "CABECALHO",
    "IDENTIFICACAO DO PRESTADOR",
    "IDENTIFICACAO DO TOMADOR",
    "DADOS DO SERVICO PRESTADO",
    "IMPOSTO SOBRE SERVICO DE QUALQUER NATUREZA",
    "TRIBUTACAO NACIONAL",
    "IMPOSTO E CONTRIBUICAO SOBRE BENS E SERVICOS",
    "INFORMACOES COMPLEMENTARES"
]

# Modelo Nacional (DANFSe)
MARCADORES_NACIONAL = [
    "CABECALHO",
    "EMITENTE DA NFS-E",
    "TOMADOR DO SERVICO",
    "SERVICO PRESTADO",
    "TRIBUTACAO MUNICIPAL",
    "TRIBUTACAO FEDERAL",
    "VALOR TOTAL DA NFS-E",
    "TOTAIS APROXIMADOS DOS TRIBUTOS",
    "INFORMACOES COMPLEMENTARES"
]

# Marcador usado para decidir onde o "cabeçalho" (texto antes do primeiro
# bloco de verdade) termina, para cada conjunto de marcadores.
MARCADOR_INICIO_CORPO = {
    tuple(MARCADORES): "IDENTIFICACAO DO PRESTADOR",
    tuple(MARCADORES_NACIONAL): "EMITENTE DA NFS-E",
}


def dividir_blocos(texto, marcadores=None):

    if marcadores is None:
        marcadores = MARCADORES

    blocos = {}

    texto_maiusculo = texto.upper()

    posicoes = []

    for marcador in marcadores:

        if marcador == "CABECALHO":
            continue

        # O marcador só conta como título de seção quando começa uma
        # linha (evita confundir com um rótulo mais longo que contenha
        # o mesmo texto dentro, ex.: "TRIBUTACAO MUNICIPAL" dentro de
        # "CODIGO DE TRIBUTACAO MUNICIPAL"). Não exigimos mais que a
        # linha termine exatamente ali, porque o OCR às vezes gruda
        # lixo depois do título na mesma linha. Também toleramos as
        # trocas de letra mais comuns do OCR (C/G, O/0, I/1/L, S/5, B/8).
        padrao = r"(?:^|\n)" + tolerante(marcador) + r"(?=[^A-Z]|$)"

        resultado = re.search(padrao, texto_maiusculo)

        if resultado:
            indice = resultado.start()

            if texto_maiusculo[indice:indice+1] == "\n":
                indice += 1

            posicoes.append((indice, marcador))

    posicoes.sort()

    for i, (inicio, marcador) in enumerate(posicoes):

        if i == len(posicoes)-1:
            fim = len(texto)

        else:
            fim = posicoes[i+1][0]

        blocos[marcador] = texto[inicio:fim]

    # Tudo que vem antes do primeiro bloco de verdade é o cabeçalho.
    # Usamos a posição encontrada pela busca tolerante (e não um
    # find() literal), porque o OCR pode ter grudado as palavras do
    # título (ex.: "EMITENTEDANFSE").

    if posicoes:
        blocos["CABECALHO"] = texto[:posicoes[0][0]]

    return blocos


def eh_modelo_nacional(texto):

    texto_maiusculo = texto.upper()

    tem_emitente = re.search(
        tolerante("EMITENTE DA NFS-E"),
        texto_maiusculo
    )

    tem_tomador = re.search(
        tolerante("TOMADOR DO SERVICO"),
        texto_maiusculo
    )

    return bool(tem_emitente and tem_tomador)
