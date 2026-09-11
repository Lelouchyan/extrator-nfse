"""
Cria um atalho do Extrator de NFS-e na Area de Trabalho.

Rode uma unica vez:

    python criar_atalho.py

Depois disso, basta dar dois cliques no atalho -- nao precisa mais
abrir o terminal nem digitar comando.

Nao precisa instalar nada: o atalho e criado pelo proprio Windows,
atraves de um script temporario do Windows Script Host.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


NOME_ATALHO = "Extrator de NFS-e"

PASTA_PROJETO = Path(__file__).parent.resolve()

ALVO = PASTA_PROJETO / "interface.py"

ICONE = PASTA_PROJETO / "icone.ico"


def achar_pythonw():
    """
    Procura o pythonw.exe -- e o Python sem janela preta de terminal.

    Se nao encontrar, usa o python.exe normal (funciona igual, mas
    abre um terminal junto com a janela).
    """

    atual = Path(sys.executable)

    candidato = atual.with_name("pythonw.exe")

    if candidato.exists():
        return candidato

    # em algumas instalacoes o pythonw fica na pasta Scripts
    candidato = atual.parent / "Scripts" / "pythonw.exe"

    if candidato.exists():
        return candidato

    print("Aviso: pythonw.exe nao encontrado.")
    print("O atalho vai abrir uma janela de terminal junto com o programa.")

    return atual


def achar_area_de_trabalho():
    """
    Descobre a pasta da Area de Trabalho, inclusive quando ela esta
    sincronizada com o OneDrive (comum em maquina corporativa).
    """

    candidatas = []

    perfil = os.environ.get("USERS")

    if perfil:
        candidatas.append(Path(perfil) / "Desktop")
        candidatas.append(Path(perfil) / "Área de Trabalho")

    onedrive = os.environ.get("OneDrive") or os.environ.get("OneDrive - Subsecretaria de Tecnologia da Informação")

    if onedrive:
        candidatas.insert(0, Path(onedrive) / "Desktop")
        candidatas.insert(1, Path(onedrive) / "Área de Trabalho")

    for pasta in candidatas:
        if pasta.is_dir():
            return pasta

    return None


def criar_atalho(destino):
    """
    Cria o arquivo .lnk usando um script VBS temporario.

    Esse e o jeito de criar atalho no Windows sem depender de
    biblioteca externa (como o pywin32).
    """

    pythonw = achar_pythonw()

    caminho_lnk = destino / f"{NOME_ATALHO}.lnk"

    linhas = [
        'Set oWS = WScript.CreateObject("WScript.Shell")',
        f'sLinkFile = "{caminho_lnk}"',
        'Set oLink = oWS.CreateShortcut(sLinkFile)',
        f'oLink.TargetPath = "{pythonw}"',
        f'oLink.Arguments = """{ALVO}"""',
        f'oLink.WorkingDirectory = "{PASTA_PROJETO}"',
        f'oLink.Description = "Extrai dados de NFS-e para Excel"',
    ]

    if ICONE.exists():
        linhas.append(f'oLink.IconLocation = "{ICONE}"')

    linhas.append('oLink.Save')

    with tempfile.NamedTemporaryFile(
        "w", suffix=".vbs", delete=False, encoding="cp1252"
    ) as arquivo:
        arquivo.write("\n".join(linhas))
        caminho_vbs = arquivo.name

    try:
        subprocess.run(
            ["cscript", "//nologo", caminho_vbs],
            check=True,
            capture_output=True
        )

    finally:
        try:
            os.unlink(caminho_vbs)
        except OSError:
            pass

    return caminho_lnk


def main():

    if os.name != "nt":
        print("Este script cria atalho no Windows.")
        return

    if not ALVO.exists():
        print(f"Nao encontrei o arquivo: {ALVO}")
        print("Rode este script de dentro da pasta do projeto.")
        return

    destino = achar_area_de_trabalho()

    if destino is None:
        print("Nao consegui localizar a Area de Trabalho.")
        print("Crie o atalho manualmente (veja as instrucoes).")
        return

    try:
        caminho = criar_atalho(destino)

    except Exception as erro:
        print("Nao foi possivel criar o atalho automaticamente.")
        print(erro)
        return

    print("=" * 60)
    print("Atalho criado com sucesso!")
    print(caminho)
    print()
    print("De dois cliques nele para abrir o programa.")
    print("=" * 60)


if __name__ == "__main__":
    main()
