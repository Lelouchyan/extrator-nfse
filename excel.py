import pandas as pd
from pathlib import Path


def salvar_excel(todas_notas):

    pasta = Path(__file__).parent / "resultado"
    pasta.mkdir(exist_ok=True)

    arquivo = pasta / "Notas_Fiscais.xlsx"

    df = pd.DataFrame(todas_notas)

    colunas = [
        "numero_nota",
        "data_emissao",
        "data_competencia",
        "codigo_autenticidade",

        "cnpj_prestador",
        "prestador",
        "nome_fantasia",

        "cnpj_tomador",
        "tomador",

        "municipio",
        "valor_servico",
        "descricao",

        "base_calculo",
        "aliquota",
        "iss",
        "pis",
        "cofins",
        "irrf",

        "medicao",
        "contrato",
        "periodo_execucao",
        "lote"
    ]

    if df.empty:
         print("Nenhuma nota foi encontrada.")
         return

    df = df[colunas]

    df.to_excel(arquivo, index=False)

    print()
    print("=" * 60)
    print("Excel gerado com sucesso!")
    print(arquivo)
    print("=" * 60)