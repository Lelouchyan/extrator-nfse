"""
Interface grafica do extrator de NFS-e.

Para usar:

    python interface.py

Arrastar e soltar arquivos so funciona se a biblioteca tkinterdnd2
estiver instalada:

    pip install tkinterdnd2

Sem ela o programa continua funcionando normalmente -- basta usar os
botoes para escolher os arquivos ou a pasta.
"""

import os
import queue
import subprocess
import sys
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from config import verificar_tesseract
from processador import listar_pdfs, contar_paginas, processar_pdfs
from excel import salvar_excel


PASTA_RESULTADO = Path(__file__).parent / "resultado"


# Arrastar e soltar e opcional: se a biblioteca nao estiver instalada,
# o programa segue funcionando so com os botoes.
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    TEM_ARRASTAR = True

except Exception:
    TEM_ARRASTAR = False


class Aplicacao:

    def __init__(self, janela):

        self.janela = janela
        self.arquivos = []
        self.processando = False
        self.pedido_cancelar = False

        # fila usada para a thread de processamento mandar mensagens
        # para a interface com seguranca
        self.mensagens = queue.Queue()

        janela.title("Extrator de NFS-e")
        janela.geometry("780x560")
        janela.minsize(640, 480)

        self._montar_tela()
        self._checar_mensagens()
        self.janela.after(200, self._conferir_ambiente)

    def _conferir_ambiente(self):
        """
        Avisa logo na abertura se o Tesseract nao estiver instalado,
        em vez de deixar o erro aparecer so depois, em cada pagina.
        """

        ok, mensagem = verificar_tesseract()

        if ok:
            return

        self._escrever_log(mensagem)
        self._status("Tesseract nao encontrado - veja o andamento abaixo.")
        self.botao_processar.config(state="disabled")

        messagebox.showwarning("Tesseract nao encontrado", mensagem)

    # ------------------------------------------------------------------
    # Montagem da tela
    # ------------------------------------------------------------------

    def _montar_tela(self):

        principal = ttk.Frame(self.janela, padding=12)
        principal.pack(fill="both", expand=True)

        # --- topo: titulo e instrucao -----------------------------------

        ttk.Label(
            principal,
            text="Extrator de NFS-e",
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w")

        instrucao = (
            "Arraste os PDFs para a lista abaixo ou use os botoes."
            if TEM_ARRASTAR
            else "Use os botoes abaixo para escolher os PDFs ou a pasta."
        )

        ttk.Label(principal, text=instrucao).pack(anchor="w", pady=(2, 10))

        # --- botoes de selecao ------------------------------------------

        barra = ttk.Frame(principal)
        barra.pack(fill="x")

        self.botao_arquivos = ttk.Button(
            barra, text="Adicionar PDFs...", command=self.adicionar_arquivos
        )
        self.botao_arquivos.pack(side="left")

        self.botao_pasta = ttk.Button(
            barra, text="Adicionar pasta...", command=self.adicionar_pasta
        )
        self.botao_pasta.pack(side="left", padx=6)

        self.botao_limpar = ttk.Button(
            barra, text="Limpar lista", command=self.limpar
        )
        self.botao_limpar.pack(side="left")

        # --- lista de arquivos ------------------------------------------

        caixa = ttk.LabelFrame(principal, text="Arquivos", padding=6)
        caixa.pack(fill="both", expand=True, pady=10)

        rolagem = ttk.Scrollbar(caixa, orient="vertical")
        rolagem.pack(side="right", fill="y")

        self.lista = tk.Listbox(
            caixa,
            yscrollcommand=rolagem.set,
            activestyle="none",
            selectmode="extended"
        )
        self.lista.pack(fill="both", expand=True)

        rolagem.config(command=self.lista.yview)

        if TEM_ARRASTAR:
            self.lista.drop_target_register(DND_FILES)
            self.lista.dnd_bind("<<Drop>>", self._ao_soltar)

        # --- acao principal ---------------------------------------------

        acao = ttk.Frame(principal)
        acao.pack(fill="x")

        self.botao_processar = ttk.Button(
            acao,
            text="Gerar Excel",
            command=self.processar
        )
        self.botao_processar.pack(side="left")

        self.botao_cancelar = ttk.Button(
            acao,
            text="Cancelar",
            command=self.cancelar,
            state="disabled"
        )
        self.botao_cancelar.pack(side="left", padx=6)

        self.botao_abrir = ttk.Button(
            acao,
            text="Abrir pasta do resultado",
            command=self.abrir_resultado
        )
        self.botao_abrir.pack(side="right")

        # --- progresso ---------------------------------------------------

        self.progresso = ttk.Progressbar(principal, mode="determinate")
        self.progresso.pack(fill="x", pady=(10, 4))

        self.status = ttk.Label(principal, text="Pronto.")
        self.status.pack(anchor="w")

        # --- log ----------------------------------------------------------

        caixa_log = ttk.LabelFrame(principal, text="Andamento", padding=6)
        caixa_log.pack(fill="both", expand=True, pady=(10, 0))

        rolagem_log = ttk.Scrollbar(caixa_log, orient="vertical")
        rolagem_log.pack(side="right", fill="y")

        self.log = tk.Text(
            caixa_log,
            height=8,
            wrap="none",
            yscrollcommand=rolagem_log.set,
            state="disabled"
        )
        self.log.pack(fill="both", expand=True)

        rolagem_log.config(command=self.log.yview)

    # ------------------------------------------------------------------
    # Selecao de arquivos
    # ------------------------------------------------------------------

    def _ao_soltar(self, evento):

        # o tkinterdnd2 devolve os caminhos numa string unica
        caminhos = self.janela.tk.splitlist(evento.data)

        self._acrescentar(caminhos)

    def adicionar_arquivos(self):

        caminhos = filedialog.askopenfilenames(
            title="Escolha os PDFs das notas",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )

        self._acrescentar(caminhos)

    def adicionar_pasta(self):

        pasta = filedialog.askdirectory(title="Escolha a pasta com os PDFs")

        if pasta:
            self._acrescentar([pasta])

    def _acrescentar(self, caminhos):

        if not caminhos:
            return

        novos = listar_pdfs(caminhos)

        ja_tem = {p.resolve() for p in self.arquivos}

        adicionados = 0

        for arquivo in novos:

            if arquivo.resolve() in ja_tem:
                continue

            self.arquivos.append(arquivo)
            self.lista.insert("end", f"  {arquivo.name}")
            adicionados += 1

        if adicionados == 0:
            self._status("Nenhum PDF novo foi adicionado.")

        else:
            self._status(
                f"{len(self.arquivos)} arquivo(s) na lista."
            )

    def limpar(self):

        if self.processando:
            return

        self.arquivos = []
        self.lista.delete(0, "end")
        self._status("Lista limpa.")

    # ------------------------------------------------------------------
    # Processamento
    # ------------------------------------------------------------------

    def processar(self):

        if self.processando:
            return

        if not self.arquivos:
            messagebox.showinfo(
                "Nenhum arquivo",
                "Adicione pelo menos um PDF antes de gerar o Excel."
            )
            return

        self.processando = True
        self.pedido_cancelar = False

        self._limpar_log()
        self._travar_botoes(True)

        total = contar_paginas(self.arquivos) or len(self.arquivos)

        self.progresso.config(maximum=total, value=0)
        self._status("Processando...")

        # O trabalho pesado roda em outra thread para a janela nao
        # travar enquanto o OCR e executado.
        thread = threading.Thread(target=self._trabalhar, daemon=True)
        thread.start()

    def _trabalhar(self):
        """
        Roda na thread de trabalho. Nao mexe na interface diretamente:
        manda tudo pela fila de mensagens.
        """

        try:
            notas = processar_pdfs(
                self.arquivos,
                log=lambda t: self.mensagens.put(("log", t)),
                ao_avancar=lambda: self.mensagens.put(("passo", None)),
                cancelado=lambda: self.pedido_cancelar
            )

            if self.pedido_cancelar:
                self.mensagens.put(("fim", (None, "Cancelado.")))
                return

            if not notas:
                self.mensagens.put((
                    "fim",
                    (None, "Nenhuma nota foi encontrada nos arquivos.")
                ))
                return

            # salvar_excel escreve no terminal; redirecionamos essa
            # saida para o log da janela
            saida = _CapturarSaida(
                lambda t: self.mensagens.put(("log", t))
            )

            anterior = sys.stdout
            sys.stdout = saida

            try:
                salvar_excel(notas)

            finally:
                sys.stdout = anterior

            self.mensagens.put(("fim", (notas, None)))

        except Exception:
            self.mensagens.put(("fim", (None, traceback.format_exc())))

    def cancelar(self):

        if self.processando:
            self.pedido_cancelar = True
            self._status("Cancelando...")

    # ------------------------------------------------------------------
    # Ponte entre a thread e a interface
    # ------------------------------------------------------------------

    def _checar_mensagens(self):

        try:
            while True:

                tipo, conteudo = self.mensagens.get_nowait()

                if tipo == "log":
                    self._escrever_log(conteudo)

                elif tipo == "passo":
                    self.progresso.step(1)

                elif tipo == "fim":
                    self._terminar(*conteudo)

        except queue.Empty:
            pass

        self.janela.after(100, self._checar_mensagens)

    def _terminar(self, notas, erro):

        self.processando = False
        self._travar_botoes(False)

        if erro:
            self._status("Nao concluido.")
            self._escrever_log(erro)

            if not erro.startswith("Cancelado"):
                messagebox.showerror("Erro", erro)

            return

        self.progresso.config(value=self.progresso["maximum"])

        para_revisar = sum(
            1 for n in notas
            if _precisa_revisao(n)
        )

        resumo = f"Concluido: {len(notas)} nota(s) no Excel."

        if para_revisar:
            resumo += f" {para_revisar} marcada(s) para conferencia."

        self._status(resumo)

        messagebox.showinfo("Concluido", resumo)

    # ------------------------------------------------------------------
    # Utilidades da interface
    # ------------------------------------------------------------------

    def _travar_botoes(self, travar):

        estado = "disabled" if travar else "normal"

        for botao in (
            self.botao_arquivos,
            self.botao_pasta,
            self.botao_limpar,
            self.botao_processar
        ):
            botao.config(state=estado)

        self.botao_cancelar.config(state="normal" if travar else "disabled")

    def _status(self, texto):
        self.status.config(text=texto)

    def _escrever_log(self, texto):

        self.log.config(state="normal")
        self.log.insert("end", texto.rstrip() + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _limpar_log(self):

        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def abrir_resultado(self):

        PASTA_RESULTADO.mkdir(exist_ok=True)

        caminho = str(PASTA_RESULTADO)

        try:
            if os.name == "nt":
                os.startfile(caminho)

            elif sys.platform == "darwin":
                subprocess.Popen(["open", caminho])

            else:
                subprocess.Popen(["xdg-open", caminho])

        except Exception as erro:
            messagebox.showerror(
                "Nao foi possivel abrir",
                f"Abra manualmente:\n{caminho}\n\n{erro}"
            )


class _CapturarSaida:
    """
    Faz o papel do sys.stdout, mandando o texto para o log da janela.
    """

    def __init__(self, destino):
        self.destino = destino

    def write(self, texto):
        if texto.strip():
            self.destino(texto)

    def flush(self):
        pass


def _precisa_revisao(nota):
    """
    Usa a mesma regra do excel.py para contar quantas notas ficaram
    marcadas para conferencia.
    """

    from excel import _motivos_revisao

    return bool(_motivos_revisao(nota))


def main():

    if TEM_ARRASTAR:
        janela = TkinterDnD.Tk()

    else:
        janela = tk.Tk()

    Aplicacao(janela)

    janela.mainloop()


if __name__ == "__main__":
    main()
