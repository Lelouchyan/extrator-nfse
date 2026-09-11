# Extrator de NFS-e

Extrai automaticamente os dados de notas fiscais de serviço eletrônicas (NFS-e) em PDF e consolida tudo em uma planilha Excel.

Lê tanto PDFs com texto quanto notas digitalizadas (imagem), usando OCR.

## O que ele faz

A partir de uma pasta com PDFs de notas, o programa gera uma planilha com uma linha por nota, contendo número, datas, prestador, tomador, município, valores, tributos e as informações extraídas da descrição do serviço (medição, contrato, período, lote).

A planilha traz ainda uma coluna **revisar**, que sinaliza as notas em que a leitura pode ter falhado — campo obrigatório vazio ou código de autenticidade incompleto. Essas linhas ficam destacadas em amarelo para conferência manual.

### Modelos de nota suportados

| Modelo | Exemplos |
|---|---|
| Padrão nacional (DANFSe) | Rio de Janeiro |
| Padrão ABRASF municipal | Goiânia, Aparecida de Goiânia |

O programa identifica o modelo sozinho, nota por nota — um mesmo PDF pode conter os dois.

## Instalação

### 1. Python

Instale o [Python 3.10 ou superior](https://www.python.org/downloads/). No Windows, marque a opção **"Add Python to PATH"** durante a instalação.

### 2. Tesseract (obrigatório)

O Tesseract é o motor de OCR, usado para ler as notas digitalizadas. Ele é um programa à parte e precisa ser instalado separadamente.

- **Windows:** baixe em [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- **Linux:** `sudo apt install tesseract-ocr tesseract-ocr-por`
- **macOS:** `brew install tesseract tesseract-lang`

> **Importante:** durante a instalação no Windows, em *Additional language data*, marque o idioma **Portuguese**. Sem ele o OCR não funciona.

O programa encontra o Tesseract sozinho nos locais de instalação padrão. Se você instalou em outro lugar, crie a variável de ambiente `TESSERACT_PATH` apontando para o `tesseract.exe`.

### 3. Dependências do projeto

Na pasta do projeto:

```bash
pip install -r requirements.txt
```

## Como usar

### Com janela (recomendado)

```bash
python interface.py
```

Adicione os PDFs pelos botões e clique em **Gerar Excel**. A planilha é salva em `resultado/`.

Para criar um atalho na Área de Trabalho e não precisar mais do terminal, rode uma vez:

```bash
python criar_atalho.py
```

Para arrastar e soltar os arquivos na janela, instale também `tkinterdnd2` (opcional — sem ele os botões funcionam normalmente).

### Pela linha de comando

Coloque os PDFs na pasta `notas/` e rode:

```bash
python main.py
```

## Estrutura do projeto

```
main.py               execução por linha de comando
interface.py          interface gráfica
criar_atalho.py       cria o atalho na Área de Trabalho
config.py             caminhos e localização do Tesseract

processador.py        percorre os PDFs página a página
leitor_pdf.py         decide entre texto nativo e OCR
ocr.py                OCR das páginas digitalizadas
ocr_utils.py          tolerância a erros comuns de OCR

normalizador.py       padroniza o texto (acentos, espaços)
limpeza.py            limpeza de quebras de linha
parser_nfse.py        identifica o modelo e divide em blocos
extrator.py           campos do modelo municipal
extrator_nacional.py  campos do modelo nacional
interpretador.py      lê medição, contrato, período e lote
nota_fiscal.py        junta tudo em uma nota

excel.py              gera a planilha e marca o que revisar
```

## Aviso sobre os dados

As pastas `notas/` e `resultado/` **não são versionadas**. Notas fiscais contêm CNPJ, valores, contratos e dados bancários de terceiros, e não devem ser publicadas.

Antes de subir qualquer alteração, confira que nenhum PDF ou planilha real está sendo incluído no commit.

## Limitações conhecidas

- O OCR pode errar dígitos em notas de baixa qualidade. Por isso existe a coluna `revisar` — **os valores devem ser conferidos por amostragem** antes de qualquer uso formal.
- O código de autenticidade às vezes é lido com 49 dígitos em vez de 50, quando o OCR perde um caractere na imagem. Essas notas ficam marcadas.
- Quando o número da nota não pode ser lido no cabeçalho, ele é deduzido do código de autenticidade. É uma inferência baseada no padrão observado, e não uma regra oficial documentada.
- Apenas os dois modelos citados acima são suportados. Outros layouts municipais exigem um extrator próprio.

## Licença

Uso pessoal e educacional.
