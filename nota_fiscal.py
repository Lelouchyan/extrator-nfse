from interpretador import interpretar_descricao
from normalizador import normalizar
from parser_nfse import dividir_blocos, MARCADORES, MARCADORES_NACIONAL, eh_modelo_nacional
from extrator import extrair_nota
from extrator_nacional import extrair_nota_nacional


class NotaFiscal:

    def __init__(self, texto):

        self.texto = texto
        self.blocos = {}
        self.dados = {}
        self.modelo = ""

    def processar(self):

        self.texto = normalizar(self.texto)

        if eh_modelo_nacional(self.texto):

            self.modelo = "nacional"
            self.blocos = dividir_blocos(self.texto, MARCADORES_NACIONAL)
            self.dados = extrair_nota_nacional(self.blocos)

        else:

            self.modelo = "goiania"
            self.blocos = dividir_blocos(self.texto, MARCADORES)
            self.dados = extrair_nota(self.blocos)

        if self.dados.get("descricao"):

            extras = interpretar_descricao(
                self.dados["descricao"]
            )

            self.dados.update(extras)

        return self.dados