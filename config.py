"""
Configuracao do projeto.

Este arquivo funciona em qualquer computador. Ele descobre sozinho
onde o Tesseract esta instalado, nesta ordem:

    1. config_local.py, se existir  -> usado na maquina de quem
       desenvolve, com o caminho fixo. Esse arquivo NAO vai para o
       GitHub (veja o .gitignore).

    2. variavel de ambiente TESSERACT_PATH -> util em servidor ou
       quando o Tesseract esta num lugar incomum.

    3. locais onde o instalador do Tesseract costuma colocar o
       programa no Windows.

    4. o PATH do sistema.

Se nada for encontrado, o programa avisa com uma mensagem clara em
vez de quebrar com um erro tecnico.
"""

import os
import shutil
from pathlib import Path


PASTA_PROJETO = Path(__file__).parent

PASTA_NOTAS = PASTA_PROJETO / "notas"

PASTA_RESULTADO = PASTA_PROJETO / "resultado"


# Endereco para baixar o Tesseract, usado nas mensagens de erro
LINK_TESSERACT = "https://github.com/UB-Mannheim/tesseract/wiki"


def _locais_conhecidos():
    """
    Lugares onde o instalador do Tesseract costuma colocar o programa
    no Windows.
    """

    pastas = [
        r"C:\Program Files\Tesseract-OCR",
        r"C:\Program Files (x86)\Tesseract-OCR",
    ]

    for variavel in ("LOCALAPPDATA", "APPDATA", "USERPROFILE"):

        base = os.environ.get(variavel)

        if base:
            pastas.append(str(Path(base) / "Programs" / "Tesseract-OCR"))
            pastas.append(str(Path(base) / "Tesseract-OCR"))

    return [Path(p) / "tesseract.exe" for p in pastas]


def _do_config_local():
    """
    Usa o config_local.py, se a pessoa tiver criado um.
    """

    try:
        from config_local import CAMINHO_TESSERACT

    except Exception:
        return None

    if not CAMINHO_TESSERACT:
        return None

    caminho = Path(CAMINHO_TESSERACT)

    return caminho if caminho.exists() else None


def encontrar_tesseract():
    """
    Devolve o caminho do Tesseract, ou None se nao encontrar.
    """

    # 1. configuracao local de quem desenvolve
    caminho = _do_config_local()

    if caminho:
        return str(caminho)

    # 2. variavel de ambiente
    do_ambiente = os.getenv("TESSERACT_PATH")

    if do_ambiente and Path(do_ambiente).exists():
        return do_ambiente

    # 3. locais tipicos de instalacao no Windows
    for candidato in _locais_conhecidos():
        if candidato.exists():
            return str(candidato)

    # 4. PATH do sistema (funciona bem no Linux e no Mac)
    do_path = shutil.which("tesseract")

    if do_path:
        return do_path

    return None


CAMINHO_TESSERACT = encontrar_tesseract()


def verificar_tesseract():
    """
    Diz se o ambiente esta pronto para rodar o OCR.

    Devolve (ok, mensagem). Quando ok e False, a mensagem explica o
    que fazer -- ela e mostrada ao usuario na janela ou no terminal.
    """

    if not CAMINHO_TESSERACT:
        return False, (
            "O Tesseract nao foi encontrado neste computador.\n\n"
            "Ele e necessario para ler as notas digitalizadas.\n\n"
            "Como resolver:\n"
            f"  1. Baixe e instale o Tesseract: {LINK_TESSERACT}\n"
            "  2. Durante a instalacao, marque o idioma Portugues.\n"
            "  3. Abra o programa novamente.\n\n"
            "Se ja estiver instalado num local diferente do padrao, "
            "crie a variavel de ambiente TESSERACT_PATH apontando "
            "para o tesseract.exe."
        )

    # O idioma portugues e obrigatorio: o OCR e feito com lang="por"
    pasta_idiomas = Path(CAMINHO_TESSERACT).parent / "tessdata"

    if pasta_idiomas.is_dir():

        tem_portugues = (pasta_idiomas / "por.traineddata").exists()

        if not tem_portugues:
            return False, (
                "O Tesseract foi encontrado, mas o idioma Portugues "
                "nao esta instalado.\n\n"
                f"Pasta verificada: {pasta_idiomas}\n\n"
                "Reinstale o Tesseract marcando Portuguese em "
                "'Additional language data', ou copie o arquivo "
                "por.traineddata para essa pasta."
            )

    return True, f"Tesseract encontrado em: {CAMINHO_TESSERACT}"
