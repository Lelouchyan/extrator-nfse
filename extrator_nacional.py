import re

from ocr_utils import tolerante


def procurar(padrao, texto):
    resultado = re.search(
        padrao,
        texto,
        re.IGNORECASE | re.DOTALL
    )

    if resultado:
        return resultado.group(1).strip()

    return ""


def _linha_seguinte(bloco, rotulo):
    """
    Devolve o conteúdo da linha logo abaixo daquela em que o rótulo
    aparece. Nesse modelo o OCR junta todos os rótulos de uma linha da
    tabela e joga todos os valores na linha de baixo.
    """
    resultado = re.search(
        tolerante(rotulo) + r"[^\n]*\n([^\n]*)",
        bloco,
        re.IGNORECASE
    )

    return resultado.group(1).strip() if resultado else ""


def extrair_cabecalho_nacional(bloco):

    nota = {}

    # "Numero da NFS-e | Competencia | Data e Hora da emissao" viram
    # uma linha só de rótulos, e os valores vêm todos na linha
    # seguinte: "3792 20/07/2026 20/07/2026 10:58:08"
    linha = _linha_seguinte(bloco, "NUMERO DA NFS-E")

    nota["numero_nota"] = procurar(r"^\s*(\d{1,10})\b", linha)

    datas = re.findall(
        r"\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2})?",
        linha
    )

    nota["data_competencia"] = datas[0] if len(datas) >= 1 else ""
    nota["data_emissao"] = datas[-1] if len(datas) >= 2 else ""

    # A "Chave de Acesso da NFS-e" faz o papel do código de
    # autenticidade. O OCR costuma quebrá-la em pedaços separados por
    # espaço ou por lixo (ex.: "33045572233 |46648000 1200..."),
    # então pegamos a linha inteira e juntamos só os dígitos.
    linha_chave = _linha_seguinte(bloco, "CHAVE DE ACESSO DA NFS-E")

    digitos = re.sub(r"\D", "", linha_chave)

    nota["codigo_autenticidade"] = digitos if len(digitos) >= 30 else ""

    return nota


def _primeiro_cnpj(bloco):
    """
    Procura o primeiro texto com cara de CNPJ/CPF no bloco.

    É mais confiável do que procurar depois do rótulo, porque o OCR
    costuma estragar o próprio rótulo (ex.: "CNPJ/CPEANIFO").
    """
    return procurar(
        r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})",
        bloco
    )


def _limpar_nome(valor):
    """
    A linha de valores traz o nome e o e-mail juntos, porque na nota
    eles são duas colunas lado a lado. Cortamos o que vier a partir do
    e-mail e removemos traços soltos no fim.
    """

    # corta a partir de algo com cara de e-mail/domínio
    valor = re.split(
        r"\s+\S*(?:@|\.COM|\.BR|\.GOV|\.NET|\.ORG)\S*",
        valor,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0]

    # remove traços/sinais soltos no fim
    valor = re.sub(r"[\s\-|]+$", "", valor)

    return valor.strip()


def extrair_prestador_nacional(bloco):

    return {
        "cnpj_prestador": _primeiro_cnpj(bloco),

        "prestador": _limpar_nome(
            _linha_seguinte(bloco, "NOME / NOME EMPRESARIAL")
        )
    }


def extrair_tomador_nacional(bloco):

    return {
        "cnpj_tomador": _primeiro_cnpj(bloco),

        "tomador": _limpar_nome(
            _linha_seguinte(bloco, "NOME / NOME EMPRESARIAL")
        )
    }


def _valor_na_linha_seguinte(bloco, rotulo):
    """
    Busca o rótulo (tolerante a OCR) e pega o primeiro valor da LINHA
    DE BAIXO, porque nesse modelo o OCR costuma juntar todos os
    rótulos de uma linha da tabela e todos os valores na linha
    seguinte (ex.: "IRRF CONTRIB. ... \\n R$ 1.144,29 - - -").
    """
    padrao = tolerante(rotulo) + r"[^\n]*\n\s*R?\$?\s*([\d.,]+)"
    return procurar(padrao, bloco)


def extrair_servico_nacional(bloco):

    return {
        # A descrição começa na LINHA SEGUINTE ao rótulo, porque na
        # mesma linha do rótulo ainda vêm as colunas vazias
        # (ex.: "Descricao do Servico , - - -").
        # Rede de segurança: mesmo que o próximo título de seção não
        # seja reconhecido (erro de OCR), paramos antes de "TRIBUTA..."
        # para não engolir o resto da página.
        "descricao": procurar(
            tolerante("DESCRICAO DO SERVICO") + r"[^\n]*\n(.*?)"
            r"(?=\nTRIBUTA|\Z)",
            bloco
        )
    }


def extrair_tributacao_municipal_nacional(bloco):

    dados = {
        "valor_servico": _valor_na_linha_seguinte(bloco, "VALOR DO SERVICO"),
        "base_calculo": _valor_na_linha_seguinte(bloco, "BC ISSQN"),
    }

    # A linha "BC ISSQN | Aliquota Aplicada | Retencao do ISSQN |
    # ISSQN Apurado" costuma virar, na linha de baixo:
    # "R$ X 5,00% NAO RETIDO R$ Y" -- pegamos os 2 valores em R$ e o
    # percentual de uma vez, na ordem em que aparecem. Se o texto não
    # vier "grudado" assim (ex.: OCR mais limpo, cada campo na sua
    # linha), caímos no plano B: procurar cada rótulo separadamente.
    resultado = re.search(
        r"R\$\s*[\d.,]+\s+([\d.,]+\s*%)\s+\S+(?:\s+\S+)*?\s+R\$\s*([\d.,]+)",
        bloco,
        re.I
    )

    if resultado:
        dados["aliquota"] = resultado.group(1).strip()
        dados["iss"] = resultado.group(2).strip()
    else:
        dados["aliquota"] = procurar(
            tolerante("ALIQUOTA APLICADA") + r"\D{0,20}?([\d.,]+\s*%?)",
            bloco
        )
        dados["iss"] = procurar(
            tolerante("ISSQN APURADO") + r"\D{0,20}?R?\$?\s*([\d.,]+)",
            bloco
        )

    # O município de prestação aparece nessa seção no formato
    # "NOME DA CIDADE - UF" (ex.: "ABADIA DE GOIAS - GO"). Esse
    # padrão é bem mais confiável do que tentar achar o valor logo
    # depois do rótulo "Local da Prestação". Fica restrito a uma
    # única linha para não misturar com o rótulo da linha de cima.
    dados["municipio"] = procurar(
        r"([A-Z][A-Z\. ]{1,40}? - [A-Z]{2})\b",
        bloco
    )

    return dados


def extrair_tributacao_federal_nacional(bloco):

    return {
        "irrf": _valor_na_linha_seguinte(bloco, "IRRF"),
        "pis": _valor_na_linha_seguinte(bloco, "PIS - DEBITO"),
        "cofins": _valor_na_linha_seguinte(bloco, "COFINS - DEBITO"),
    }


def extrair_nota_nacional(blocos):

    nota = {
        "numero_nota": "",
        "data_emissao": "",
        "data_competencia": "",
        "codigo_autenticidade": "",

        "cnpj_prestador": "",
        "prestador": "",
        "nome_fantasia": "",

        "cnpj_tomador": "",
        "tomador": "",

        "municipio": "",
        "valor_servico": "",
        "descricao": "",

        "base_calculo": "",
        "aliquota": "",
        "iss": "",
        "pis": "",
        "cofins": "",
        "irrf": "",

        "medicao": "",
        "contrato": "",
        "periodo_execucao": "",
        "lote": ""
    }

    if "CABECALHO" in blocos:
        nota.update(
            extrair_cabecalho_nacional(blocos["CABECALHO"])
        )

    if "EMITENTE DA NFS-E" in blocos:
        nota.update(
            extrair_prestador_nacional(blocos["EMITENTE DA NFS-E"])
        )

    if "TOMADOR DO SERVICO" in blocos:
        nota.update(
            extrair_tomador_nacional(blocos["TOMADOR DO SERVICO"])
        )

    if "SERVICO PRESTADO" in blocos:
        nota.update(
            extrair_servico_nacional(blocos["SERVICO PRESTADO"])
        )

    if "TRIBUTACAO MUNICIPAL" in blocos:
        nota.update(
            extrair_tributacao_municipal_nacional(blocos["TRIBUTACAO MUNICIPAL"])
        )

    if "TRIBUTACAO FEDERAL" in blocos:
        nota.update(
            extrair_tributacao_federal_nacional(blocos["TRIBUTACAO FEDERAL"])
        )

    return nota
