import re


def procurar(padrao, texto):

    resultado = re.search(
        padrao,
        texto,
        re.IGNORECASE | re.DOTALL
    )

    if resultado:
        return resultado.group(1).strip()

    return ""


def interpretar_descricao(descricao):

    dados = {}

    # No modelo Goiânia a frase costuma vir "19a MEDICAO" (numero antes)
    # No modelo Nacional costuma vir "MEDICAO 19 MP" (numero depois)
    # Tentamos as duas ordens.
    dados["medicao"] = (
        procurar(r"(\d+)\s*A?\s*MEDICAO", descricao)
        or procurar(r"MEDICAO\s*(\d+)", descricao)
    )

    # No modelo Goiânia costuma vir "Contrato no 136/2024" (com o N do "no")
    # No modelo Nacional vem só "CONTRATO 136/2024". O N agora é opcional.
    dados["contrato"] = procurar(
        r"CONTRATO\s*N?\.?\s*([0-9]+/[0-9]+)",
        descricao
    )

    # Tentamos tanto "periodo de execucao:" quanto só "periodo"
    dados["periodo_execucao"] = (
        procurar(
            r"PERIODO DE EXECUCAO:\s*(\d{2}/\d{2}/\d{4}\s*A\s*\d{2}/\d{2}/\d{4})",
            descricao
        )
        or procurar(
            r"PERIODO\s*(?:DE)?\s*:?\s*(\d{2}/\d{2}/\d{4}\s*A\s*\d{2}/\d{2}/\d{4})",
            descricao
        )
    )

    dados["lote"] = procurar(
        r"LOTE\s*(\d+)",
        descricao
    )

    return dados