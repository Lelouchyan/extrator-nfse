"""
Processamento das notas, separado da interface.

Tanto o main.py (linha de comando) quanto a interface gráfica usam
estas funções, para não existir lógica duplicada nos dois lugares.
"""

from pathlib import Path

import fitz

from leitor_pdf import ler_pagina
from nota_fiscal import NotaFiscal


def listar_pdfs(caminhos):
    """
    Recebe caminhos de arquivos e/ou pastas e devolve a lista de PDFs
    encontrados, sem repetição e em ordem alfabética.
    """

    encontrados = []

    for caminho in caminhos:

        caminho = Path(caminho)

        if caminho.is_dir():
            encontrados.extend(caminho.glob("*.pdf"))

        elif caminho.suffix.lower() == ".pdf":
            encontrados.append(caminho)

    # remove repetidos preservando o caminho absoluto
    unicos = {p.resolve(): p for p in encontrados}

    return sorted(unicos.values(), key=lambda p: p.name.lower())


def contar_paginas(arquivos):
    """
    Total de páginas de todos os PDFs, para a barra de progresso.
    """

    total = 0

    for arquivo in arquivos:

        try:
            pdf = fitz.open(arquivo)
            total += pdf.page_count
            pdf.close()

        except Exception:
            pass

    return total


def processar_pdfs(arquivos, log=print, ao_avancar=None, cancelado=None):
    """
    Lê os PDFs e devolve a lista de notas extraídas.

    log        -> função chamada com mensagens de texto
    ao_avancar -> função chamada a cada página processada
    cancelado  -> função que devolve True se o usuário pediu para parar
    """

    todas_notas = []

    for arquivo in arquivos:

        if cancelado and cancelado():
            log("Processamento cancelado pelo usuario.")
            break

        log(f"Arquivo: {arquivo.name}")

        try:
            pdf = fitz.open(arquivo)

        except Exception as erro:
            log(f"  Nao foi possivel abrir o arquivo: {erro}")
            continue

        for numero, pagina in enumerate(pdf):

            if cancelado and cancelado():
                break

            try:
                texto = ler_pagina(pagina)

                # página em branco ou ilegível
                if len(texto.strip()) < 50:
                    log(f"  Pagina {numero+1}: sem texto legivel, ignorada")

                else:
                    dados = NotaFiscal(texto).processar()
                    todas_notas.append(dados)

                    numero_nota = dados.get("numero_nota") or "?"
                    log(f"  Pagina {numero+1}: nota {numero_nota}")

            except Exception as erro:
                log(f"  Pagina {numero+1}: ERRO - {erro}")

            if ao_avancar:
                ao_avancar()

        pdf.close()

    return todas_notas
