"""
Execucao por linha de comando.

Le todos os PDFs da pasta "notas" e gera o Excel em "resultado".
Para a versao com janela, rode: python interface.py
"""

import sys

from config import PASTA_NOTAS, verificar_tesseract
from processador import listar_pdfs, processar_pdfs
from excel import salvar_excel


def main():

    # Conferir o ambiente antes de comecar evita repetir o mesmo erro
    # em todas as paginas do PDF.
    ok, mensagem = verificar_tesseract()

    if not ok:
        print()
        print("=" * 60)
        print(mensagem)
        print("=" * 60)
        return 1

    PASTA_NOTAS.mkdir(exist_ok=True)

    arquivos = listar_pdfs([PASTA_NOTAS])

    print(f"Foram encontrados {len(arquivos)} PDF(s).\n")

    if not arquivos:
        print(f"Coloque os PDFs das notas em: {PASTA_NOTAS}")
        return 0

    todas_notas = processar_pdfs(arquivos)

    print()
    print(f"Notas processadas: {len(todas_notas)}")

    salvar_excel(todas_notas)

    return 0


if __name__ == "__main__":
    sys.exit(main())
