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

def _codigo_autenticidade(bloco):
    """
    O código de autenticidade costuma ser quebrado pelo OCR em vários
    pedaços separados por espaço ou por lixo
    (ex.: "5208707 121028040900016200000000000582607 1784815072").

    Não dá para confiar na posição da linha: às vezes o OCR insere
    linhas de ruído entre o rótulo e os valores. Então varremos todas
    as linhas do cabeçalho, descartamos as datas/horas (que ficam nas
    colunas ao lado) e ficamos com a linha que sobrar com mais
    dígitos -- o código é, de longe, a maior sequência numérica do
    cabeçalho (50 dígitos, contra 10 de um telefone).
    """

    melhor = ""

    for linha in bloco.split("\n"):

        # Remove datas e horas para não misturar os dígitos delas
        limpa = re.sub(r"\d{2}/\d{2}/\d{4}", " ", linha)
        limpa = re.sub(r"\d{2}:\d{2}:\d{2}", " ", limpa)

        digitos = re.sub(r"\D", "", limpa)

        if len(digitos) > len(melhor):
            melhor = digitos

    if len(melhor) < 30:
        return ""

    # O código tem 50 dígitos; se sobrou lixo numérico no fim da
    # linha, ficamos apenas com os 50 primeiros.
    return melhor[:50]


def extrair_cabecalho(bloco):

    nota = {}

    # Data de geração
    datas = re.findall(
        r"\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2})?",
        bloco
    )

    if len(datas) >= 1:
        nota["data_emissao"] = datas[0]
    else:
        nota["data_emissao"] = ""

    if len(datas) >= 2:
        nota["data_competencia"] = datas[1]
    else:
        nota["data_competencia"] = ""

    # Código de autenticidade
    nota["codigo_autenticidade"] = _codigo_autenticidade(bloco)

    # Número da nota
    # A busca fica restrita ao próprio rótulo e, no máximo, à linha
    # logo abaixo dele (é onde fica a caixinha com o número).
    #
    # O "(" é proibido no meio do caminho de propósito: quando o OCR
    # não consegue ler a caixa do número, a busca antes avançava até
    # o telefone da prefeitura -- "Fone: (62)35243335" -- e devolvia
    # 62 para qualquer nota de Goiânia. Barrando o parêntese, o
    # telefone deixa de ser um candidato e caímos no plano B abaixo.
    resultado = re.search(
        tolerante("NUMERO DA NOTA FISCAL")
        + r"[^\d\n(]*\n?[^\d\n(]*?([0-9]{1,10})\b",
        bloco,
        re.I
    )

    nota["numero_nota"] = resultado.group(1) if resultado else ""

    # PLANO B: em muitas notas o OCR destrói a caixinha do canto
    # superior direito e o rótulo "Numero da Nota Fiscal" nem aparece
    # no texto. Nesses casos tentamos recuperar o número de dentro do
    # código de autenticidade, onde ele aparece num campo preenchido
    # com zeros à esquerda, logo antes do ano/mês da competência
    # (ex.: ...00000000000 [53] 2607...  -> nota 53, competência 07/2026).
    if not nota["numero_nota"]:
        nota["numero_nota"] = _numero_pelo_codigo(
            nota["codigo_autenticidade"],
            nota["data_competencia"]
        )

    return nota


def _numero_pelo_codigo(codigo, data_competencia):
    """
    Tenta deduzir o número da nota a partir do código de autenticidade.

    O código traz o número da nota preenchido com zeros à esquerda e,
    logo em seguida, o ano e o mês da competência (AAMM). Usamos esse
    ano/mês como âncora para saber onde o número termina.

    Só é usado quando a leitura normal (pelo rótulo) falha.
    """

    if not codigo or not data_competencia:
        return ""

    # data_competencia vem como DD/MM/AAAA -> montamos AAMM
    partes = re.search(r"\d{2}/(\d{2})/\d{2}(\d{2})", data_competencia)

    if not partes:
        return ""

    mes = partes.group(1)
    ano = partes.group(2)

    ancora = ano + mes

    # zeros à esquerda, o número (começando por dígito diferente de
    # zero) e, logo depois, o AAMM da competência
    resultado = re.search(
        r"0{4,}([1-9][0-9]{0,8})" + ancora,
        codigo
    )

    return resultado.group(1) if resultado else ""

def extrair_prestador(bloco):

    return {
        "cnpj_prestador": procurar(
            r"CNPJ/CPF/NIF:\s*([\d./-]+)",
            bloco
        ),

        "prestador": procurar(
            r"Nome/Razao Social:\s*(.*?)\n",
            bloco
        ),

        "nome_fantasia": procurar(
            r"Nome Fantasia:\s*(.*?)\n",
            bloco
        )
    }


def extrair_tomador(bloco):

    return {

        "cnpj_tomador": procurar(
            r"CNPJ/CPF/NIF:\s*([\d./-]+)",
            bloco
        ),

        "tomador": procurar(
            r"Nome/Razao Social:\s*(.*?)\n",
            bloco
        )
    }


def extrair_servico(bloco):

    return {

        "municipio": procurar(
            r"LOCAL DA PRESTACAO:\s*(.*?)\s*PAIS",
            bloco
        ),

        "valor_servico": procurar(
            r"V[L|I]\.?\s+DO\s+SERVICO:\s*R?\$?\s*([\d.,]+)",
            bloco
        ),

        "descricao": procurar(
            r"DESCRICAO DO SERVICO:\s*(.*?)(?=\nIMPOSTO|\Z)",
            bloco
        )
    }


def extrair_iss(bloco):

    return {

        "base_calculo": procurar(
            r"BASE DE CALCULO:\s*R\$([\d.,]+)",
            bloco
        ),

        "aliquota": procurar(
            r"ALIQUOTA:\s*([\d.,%]+)",
            bloco
        ),

        "iss": procurar(
            r"ISSQN:\s*R\$([\d.,]+)",
            bloco
        )
    }


def extrair_tributacao(bloco):

    return {

        "pis": procurar(
            r"PIS:\s*R\$([\d.,]+)",
            bloco
        ),

        "cofins": procurar(
            r"COFINS:\s*R\$([\d.,]+)",
            bloco
        ),

        "irrf": procurar(
            r"IRRF:\s*R\$([\d.,]+)",
            bloco
        )
    }


def extrair_nota(blocos):

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
            extrair_cabecalho(
                blocos["CABECALHO"]
            )
    )

    if "IDENTIFICACAO DO PRESTADOR" in blocos:
        nota.update(
            extrair_prestador(
                blocos["IDENTIFICACAO DO PRESTADOR"]
            )
        )

    if "IDENTIFICACAO DO TOMADOR" in blocos:
        nota.update(
            extrair_tomador(
                blocos["IDENTIFICACAO DO TOMADOR"]
            )
        )

    if "DADOS DO SERVICO PRESTADO" in blocos:
        nota.update(
            extrair_servico(
                blocos["DADOS DO SERVICO PRESTADO"]
            )
        )

    if "IMPOSTO SOBRE SERVICO DE QUALQUER NATUREZA" in blocos:
        nota.update(
            extrair_iss(
                blocos["IMPOSTO SOBRE SERVICO DE QUALQUER NATUREZA"]
            )
        )

    if "TRIBUTACAO NACIONAL" in blocos:
        nota.update(
            extrair_tributacao(
                blocos["TRIBUTACAO NACIONAL"]
            )
        )

    return nota